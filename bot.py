# -*- coding: utf-8 -*-

import telebot
import os
import time
import sqlite3
from datetime import datetime

from telebot import types
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
print("TOKEN:", TOKEN)
bot = telebot.TeleBot(TOKEN)

yuan_rate = 13  # Текущий курс юаня
service_fee = 490  # Комиссия сервиса



ADMIN_ID = 5787541824

# Команда для изменения курса юаня
@bot.message_handler(commands=['set_yuan_rate'])
def set_yuan_rate(message):
    if message.chat.id == ADMIN_ID:
        try:
            rate = float(message.text.split()[1])  # Извлекаем курс из команды
            global yuan_rate
            yuan_rate = rate
            bot.send_message(message.chat.id, f"Курс юаня успешно обновлен: {yuan_rate} ₽")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Ошибка: используйте формат /set_yuan_rate <курс>")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")

# Команда для изменения комиссии
@bot.message_handler(commands=['set_service_fee'])
def set_service_fee(message):
    if message.chat.id == ADMIN_ID:
        try:
            fee = int(message.text.split()[1])  # Извлекаем комиссию из команды
            global service_fee
            service_fee = fee
            bot.send_message(message.chat.id, f"Комиссия успешно обновлена: {service_fee} ₽")
        except (IndexError, ValueError):
            bot.send_message(message.chat.id, "Ошибка: используйте формат /set_service_fee <комиссия>")
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")


@bot.message_handler(commands=['start'])
def start_command(message):
    connect = None
    cursor = None
    try:


        connect = sqlite3.connect("users.db")
        cursor = connect.cursor()


        cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, 
                    username TEXT, 
                    first_name TEXT, 
                    start_date TEXT
                )
            """)
        connect.commit()

        # Данные пользователя
        user_id = message.chat.id
        username = message.chat.username if message.chat.username else "Не указан"
        first_name = message.chat.first_name if message.chat.first_name else "Не указано"
        start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute(
                "INSERT INTO users (id, username, first_name, start_date) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, start_date)
            )
            connect.commit()

    except sqlite3.Error as error:
        print(f"Ошибка базы данных: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connect is not None:
            connect.close()


    # Создание кнопки "Главное меню 🏠"
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_menu_button = types.KeyboardButton("Главное меню 🏠")
    reply_markup.add(main_menu_button)

    # Отправляем приветственное сообщение с reply-кнопкой
    bot.send_message(
        message.chat.id,
        'Привет! Я бот группы Sneaker Lab 🤖 \n\nПомогу быстро рассчитать цену и оформить заказ с POIZON и других площадок 🛍'
        '\n\nНажмите «Главное меню 🏠» для начала работы',
        reply_markup=reply_markup
    )


from telebot.apihelper import ApiTelegramException

@bot.message_handler(commands=['send_photo'])
def send_photo_all(message):
    if message.chat.id != ADMIN_ID:
        return

    msg = bot.send_message(message.chat.id, "Отправь фото с подписью (это и будет рассылка)")
    bot.register_next_step_handler(msg, process_photo_broadcast)


def process_photo_broadcast(message):
    if not message.photo:
        bot.send_message(message.chat.id, "Нужно отправить именно фото")
        return

    photo_id = message.photo[-1].file_id
    caption = message.caption if message.caption else ""

    connect = None
    cursor = None

    try:
        connect = sqlite3.connect("users.db")
        cursor = connect.cursor()

        cursor.execute("SELECT id FROM users")
        users = cursor.fetchall()

        total = len(users)
        success = 0
        failed = 0

        bot.send_message(message.chat.id, f"🚀 Начинаю рассылку по {total} пользователям")

        for i, user in enumerate(users):
            user_id = user[0]

            try:
                bot.send_photo(user_id, photo_id, caption=caption)
                success += 1

            except ApiTelegramException as tg_error:
                failed += 1
                print(f"Telegram ошибка {user_id}: {tg_error}")

            except Exception as other_error:
                failed += 1
                print(f"Другая ошибка {user_id}: {other_error}")

            # анти-бан
            time.sleep(0.05)

            if i % 25 == 0 and i != 0:
                time.sleep(1)

        bot.send_message(
            message.chat.id,
            f"✅ Готово\n\nОтправлено: {success}\nОшибки: {failed}"
        )

    except sqlite3.Error as db_error:
        bot.send_message(message.chat.id, f"Ошибка БД: {db_error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connect is not None:
            connect.close()


@bot.message_handler(commands=['check_db'])
def check_db(message):
    connect = sqlite3.connect("users.db")
    cursor = connect.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.close()
    connect.close()

    bot.send_message(message.chat.id, f"В базе {len(users)} пользователей")






@bot.message_handler(func=lambda message: message.text == "Главное меню 🏠")
def go_to_main_menu(message):

    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton('Рассчитать стоимость 💰', callback_data='calculate')
    markup.add(btn1)
    btn2 = types.InlineKeyboardButton('Экспресс доставка ✈️', callback_data='express')
    markup.add(btn2)
    btn3 = types.InlineKeyboardButton('Оформить заказ 🛍', callback_data='order')
    markup.add(btn3)
    btn4 = types.InlineKeyboardButton('Отзывы о нашей работе 📌', url='https://vk.com/sneakerlab_shop?w=wall-217353568_366')
    markup.add(btn4)
    btn5 = types.InlineKeyboardButton('Ответы на популярные вопросы 📚', callback_data='Faq')
    markup.add(btn5)
    btn6 = types.InlineKeyboardButton('Как пользоваться приложением ❓', url= 'https://teletype.in/@s-96032/eCLUj5xxAJK')
    markup.add(btn6)
    btn7 = types.InlineKeyboardButton('🚛 Доставка', callback_data='ship')
    btn8 = types.InlineKeyboardButton('Актуальный курс 💹', callback_data='exchange')
    markup.add(btn7, btn8)
    btn9 = types.InlineKeyboardButton('Комиссия сервиса 🫰🏼', callback_data='commision')
    markup.add(btn9)
    btn10 = types.InlineKeyboardButton('Задать вопрос ✍️', url= 'https://t.me/yamakasi24')
    markup.add(btn10)
    btn11 = types.InlineKeyboardButton('Cкачать Poizon iOS', url='https://apps.apple.com/ru/app/%E5%BE%97%E7%89%A9-%E5%BE%97%E5%88%B0%E8%BF%90%E5%8A%A8x%E6%BD%AE%E6%B5%81x%E5%A5%BD%E7%89%A9/id1012871328')
    markup.add(btn11)
    btn12 = types.InlineKeyboardButton('Скачать Poizon Android', url='https://m.anxinapk.com/rj/12201303.html?')
    markup.add(btn12)


    bot.send_message(message.chat.id, "Выберите нужный раздел:", reply_markup=markup)



@bot.callback_query_handler(func=lambda callback: True)
def callback_massage(callback):
    if callback.data == 'calculate':
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('Куртки / Ветровки 🧥', callback_data='jackets')
        markup.add(btn1)
        btn2 = types.InlineKeyboardButton('Худи / Свитшоты 🥋', callback_data='hoodies')
        markup.add(btn2)
        btn3 = types.InlineKeyboardButton('Рубашки / Лонгсливы 👔', callback_data='shirts')
        markup.add(btn3)
        btn4 = types.InlineKeyboardButton('Футболки / Шорты 👕', callback_data='tshirt')
        markup.add(btn4)
        btn5 = types.InlineKeyboardButton('Брюки / Джинсы 👖', callback_data='jeans')
        markup.add(btn5)
        btn6 = types.InlineKeyboardButton('Тяжелая обувь / Ботинки 🥾', callback_data='boots')
        markup.add(btn6)
        btn7 = types.InlineKeyboardButton('Кроссовки 👟', callback_data='sneakers')
        markup.add(btn7)
        btn8 = types.InlineKeyboardButton('Нижнее белье / Носки 👙🧦', callback_data='underwear')
        markup.add(btn8)
        btn9 = types.InlineKeyboardButton('Часы / Парфюм / Косметика 💄', callback_data='beaty')
        markup.add(btn9)
        btn10 = types.InlineKeyboardButton('Другое ', callback_data='others')
        markup.add(btn10)

        bot.send_message(callback.message.chat.id,"Выберите категорию товара:", reply_markup=markup)

    elif callback.data == 'express':
        bot.send_message(callback.message.chat.id, "Введите стоимость товара в юанях:")
        bot.register_next_step_handler(callback.message, calculate_express_price)

    elif callback.data == 'exchange':
        bot.send_message(callback.message.chat.id, f"Текущий курс юаня: {yuan_rate} ₽ \n \n"
                                                   f"Почему наш курс выше чем курс ЦБ?\n \n"
                                                   f"Курс Центробанка — это справочная цифра, по которой валюту никто не продает. В обменниках и банках курс всегда выше, потому что туда включают наценки и комиссии за переводы 🇨🇳")


    elif callback.data == 'commision':
        bot.send_message(callback.message.chat.id,f"Комиссия сервиса составляет: {service_fee}₽"
                                                  f"\n\nВ стоимость комиссии входит: \n\n"
                                                  f"- Выкуп товара по лучшему курсу 💹\n\n"
                                                  f"Полностью берем на себя процесс оформления заказа, а также предоставляем один из самых выгодных курсов юаня на рынке, чтобы ваши покупки были еще выгодней\n\n"
                                                  f"- Организация доставки из Китая в Россию ✈️\n\n"
                                                  f"Мы берем на себя все этапы логистики, от склада в Китае до Вашего города\n\n"
                                                  f"- Консультация и поддержка 🧑🏻‍💻\n\n"
                                                  f"Мы всегда готовы ответить на ваши вопросы на любом этапе: от выбора товара до получения посылки")




    elif callback.data == 'ship':

        bot.send_message(callback.message.chat.id, "Poizon -> склад в Китае 🇨🇳\n \nДоставка Poizon в среднем занимает 3-5 дней в зависимости от товара, сроки доставки вы можете увидеть справа от цены. \n \n"
                                                    "🇨🇳 Китай -> Москва 🇷🇺 \n \n"
                                                   "После получения товара на складе в Китае ваш товар упаковывается и отправляется в Москву, после отправки доставка занимает:\n \n9 - 13 дней экспресс доставка \n19 - 25 дней обычная доставка \n\n(зимой могут быть задержки связанные с погодными условиями) \n \n"
                                                   "Доставка по России 🇷🇺 \n \nПосле получения товара в Москве, мы отправляем посылки через CDEK 🚛 \n \nСроки доставки по России вы можете посмотреть в приложении или на сайте CDEKa ⏳\n\n"
                                                   "------------------------------------------"
                                                   "Точную стоимость доставки можно рассчитать в боте указав категорию товара, если нет нужной категории товара доставка рассчитывается по прибытию товара на склад в Китае по тарифу 900₽/кг ⚖️")


    elif callback.data == 'Faq':
        markup = types.InlineKeyboardMarkup()

        # Кнопки FAQ
        btn1 = types.InlineKeyboardButton('Что такое Poizon?', url= "https://teletype.in/@s-96032/qWbwSSHskP5")
        btn2 = types.InlineKeyboardButton('Как поменять язык на Poizon?', url= "https://teletype.in/@s-96032/EXRYNMuRFgq")
        btn3 = types.InlineKeyboardButton('На Poizon оригинал?', url= "https://teletype.in/@s-96032/22oaM12XMgM")
        btn4 = types.InlineKeyboardButton('Как правильно подобрать размер 📏', url="https://teletype.in/@s-96032/mMsR6yKSaME")
        btn5 = types.InlineKeyboardButton('В какие страны доставляете?', callback_data='countries')
        btn6 = types.InlineKeyboardButton('Есть ли возврат?', callback_data='returns')

        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        markup.add(btn4)
        markup.add(btn5)
        markup.add(btn6)

        # Отправляем сообщение с кнопками
        bot.send_message(callback.message.chat.id, "Выберите интересующий вас вопрос:", reply_markup=markup)



    elif callback.data == 'countries':
        bot.send_message(callback.message.chat.id,

                         "Россия 🇷🇺\n \nБеларусь 🇧🇾\n \nКазахстан 🇰🇿")

    elif callback.data == 'returns':
        bot.send_message(callback.message.chat.id,
                         "На возврат товара Poizon предоставляет 7 дней с момента его получения. Датой получения считается момент поступления товара на склад в Китае."
                         "Учитывая, что доставка из Китая в Россию занимает определённое время, оформить возврат в рамках установленного срока становится невозможно.")

    elif callback.data == 'order':
        bot.send_message(
            callback.message.chat.id,
            "Для оформления заказа отправьте менеджеру: \n \n"
            "- Ссылку или фото товара \n \n"
            "- Размер / Цвет \n \n"
            "- Способ доставки (Обычная или экспресс)",

        reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("Связаться", url="https://t.me/yamakasi24")
            )
        )


    elif callback.data in ['jackets', 'hoodies', 'shirts', "tshirt","jeans", "boots", "sneakers", "underwear", "beaty", "others"]:
        # Сохраняем выбранную категорию
        category = callback.data
        bot.send_message(callback.message.chat.id, "Введите стоимость товара в юанях:")
        bot.register_next_step_handler(callback.message, get_price, category)


def get_price(message, category):
    try:
        item_price = float(message.text)
        delivery_costs = {
            'jackets': 1890,
            'hoodies': 1090,
            'shirts': 890,
            'tshirt': 790,
            'jeans': 1090,
            'boots': 2390,
            'sneakers': 1690,
            'underwear': 490,
            'beaty': 990,
            'others': 0
        }
        delivery_cost = delivery_costs.get(category, 0)

        # Формула расчёта
        total_price = (item_price * 0.03 + item_price) * yuan_rate + delivery_cost + service_fee

        # Отправляем результат
        rounded_price = round(total_price, -1)  # Округляем до ближайшего десятка
        rounded_price = int(rounded_price)  # Преобразуем в целое число

        if category == 'others':
             message_text = (
                f"Итоговая стоимость товара без учета доставки: {rounded_price} ₽\n\n"
                f"В стоимость товара уже включены:\n\n"
                f"- Страховка товара 3%\n"
                f"- Комиссия сервиса {service_fee}₽\n\n"
                f"Доставка оплачивается после получения товара на складе в Китае по тарифу 900₽ / кг 🚛"
            )

        else:
            message_text = (
                f"Итоговая стоимость товара с доставкой до Москвы: {rounded_price} ₽\n\n"
                f"В стоимость товара уже включены:\n\n"
                f"- Доставка Пекин -> Москва\n"
                f"- Страховка товара 3%\n"
                f"- Комиссия сервиса {service_fee}₽ \n\n"
                f"Доставка CDEK оплачивается при получении товара в ПВЗ в среднем это 350-450₽ в зависимости от региона доставки 🚛"

            )

        bot.send_message(message.chat.id, message_text)

    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: введите корректную стоимость товара в числовом формате.")


def calculate_express_price(message):
    try:
        item_price = float(message.text)  # Получаем стоимость товара от пользователя
        total_price = (item_price * 0.03 + item_price) * yuan_rate + service_fee  # Формула расчета

        # Округляем итоговую стоимость
        rounded_price = round(total_price, -1)  # Округляем до десятков
        rounded_price = int(rounded_price)  # Преобразуем в целое число

        # Формируем сообщение
        message_text = (
            f"Итоговая стоимость товара без учета доставки: {rounded_price} ₽\n\n"
            f"В стоимость товара уже включены:\n\n"
            f"- Страховка товара 3%\n"
            f"- Комиссия сервиса {service_fee}₽\n\n"
            f"Доставка оплачивается после получения товара на складе в Китае по тарифу 1190₽ / кг ✈️\n\n"
            f"Сроки экспресс доставки 9 - 13 дней до Москвы после получения товара на складе."
        )

        # Отправляем результат
        bot.send_message(message.chat.id, message_text)

    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: введите корректную стоимость товара в числовом формате.")



while True:
    try:
        bot.polling(none_stop=True)

    except Exception as e:
        print(f"Ошибка: {e}. Перезапуск через 15 секунд...")
        time.sleep(15)

