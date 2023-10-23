import telebot
from telebot import types
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot('6432599280:AAGtVe1czZYj5wFfDo4SqeNWjJpwhvvfoKc')

admin_user_ids = [487545908, 5876436640]

conn = sqlite3.connect("db.db", check_same_thread=False)

cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS contracts (
                    contract_id TEXT,
                    message_id INT,
                    chat_id INT,
                    message TEXT
                )''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS admin_votes (
                    admin_id TEXT,
                    contract_id TEXT,
                    voted INT
                )''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS executors (
                    contract_id TEXT,
                    pretendents TEXT,
                    executor INT
                )''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS pretendents (
                    contract_id TEXT,
                    pretendent_id INT,
                    votes INT
                )''')
conn.commit()

def admin_only(func):
    def wrapper(message):
        if message.from_user.id in admin_user_ids:
            return func(message)
        else:
            bot.reply_to(message, "У вас нет прав администратора.")

    return wrapper

def check_for_pretender(chat_id, contract_id):
    lst = []
    try:
        cursor.execute("SELECT * FROM pretendents WHERE contract_id = ?", (contract_id,))
        rows1 = cursor.fetchall()

    except IndexError:
        cursor.execute("INSERT INTO pretendents (contract_id, pretendent_id, votes) VALUES (?, ?, ?)",
                       (contract_id, chat_id, 0))
        conn.commit()
        cursor.execute("SELECT * FROM pretendents WHERE contract_id = ?", (contract_id,))
        rows1 = cursor.fetchall()
    for row in rows1:
        lst.append(row[1])

    if chat_id not in lst:
        cursor.execute("INSERT INTO pretendents (contract_id, pretendent_id, votes) VALUES (?, ?, ?)",
                       (contract_id, chat_id, 0))
        conn.commit()

def get_z1blo_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    text_button = types.InlineKeyboardButton('Отправить chat id разработчику', url='t.me/z4eb4lo')
    keyboard.add(text_button)
    return keyboard


def get_contract_keyboard(message_id, user_id):
    h = 'Хэштеги'
    ty = 'Тип контракта'
    tz = 'ТЗ'
    sr = 'Срок'
    st = 'Стоимость'
    d = 'Доп. условия'
    if user_id in user_data and user_data[user_id].get("hash_status") == True:
        h = 'Хэштеги✅'
    if user_id in user_data and user_data[user_id].get("type_status") == True:
        ty = 'Тип контракта✅'
    if user_id in user_data and user_data[user_id].get("tz_status") == True:
        tz = 'ТЗ✅'
    if user_id in user_data and user_data[user_id].get("srok_status") == True:
        sr = 'Срок✅'
    if user_id in user_data and user_data[user_id].get("cost_status") == True:
        st = 'Стоимость✅'
    if user_id in user_data and user_data[user_id].get("dop_status") == True:
        d = 'Доп. условия✅'
    if user_id in user_data and user_data[user_id].get("button_status") == False:
        bu = 'Кнопка "Подписать"❌'
    if user_id in user_data and user_data[user_id].get("button_status") == True:
        bu = 'Кнопка "Подписать"✅'

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    button1 = types.InlineKeyboardButton(f'{h}', callback_data=f'hashtags_{message_id}')
    button2 = types.InlineKeyboardButton(f'{ty}', callback_data=f'type_{message_id}')
    button3 = types.InlineKeyboardButton(f'{tz}', callback_data=f'tz_{message_id}')
    button4 = types.InlineKeyboardButton(f'{sr}', callback_data=f'srok_{message_id}')
    button5 = types.InlineKeyboardButton(f'{st}', callback_data=f'cost_{message_id}')
    button6 = types.InlineKeyboardButton(f'{d}', callback_data=f'dop_{message_id}')
    button_sign = types.InlineKeyboardButton(f'{bu}', callback_data=f'button_status')
    button_cancel = types.InlineKeyboardButton('Отмена', callback_data=f'cancel')
    done = types.InlineKeyboardButton('Отправить контракт', callback_data=f'done')
    keyboard.add(button1, button2, button3, button4, button5, button6, button_sign)
    keyboard.add(done)
    keyboard.add(button_cancel)
    return keyboard


channel_id_filename = "channel_id.txt"
group_id_filename = "group_id.txt"


def save_channel_id(channel_id):
    with open(channel_id_filename, "w") as file:
        file.write(str(channel_id))


def load_channel_id():
    try:
        with open(channel_id_filename, "r") as file:
            return int(file.read())
    except FileNotFoundError:
        return None


def contract_start_message(chat_id, message_id):
    keyboard = get_contract_keyboard(message_id, chat_id)
    bot.edit_message_text(
        "Давайте создадим новый контракт. Введите все параметры:\nесли хотите применить форматирование, то используйте HTML",
        chat_id, message_id, reply_markup=keyboard)


def contract_start_message1(chat_id):
    keyboard = get_contract_keyboard(123231, chat_id)
    bot.send_message(chat_id,
                     "Продолжим. Введите все параметры:\nесли хотите применить форматирование, то используйте HTML",
                     reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help(message):
    msg = (
        '<code>/start</code> - начать создание контракта. Чтобы отменить создание, нажмите "Отмена" в меню или напишите <code>/start</code> '
        'для того, чтобы начать создание контракта заново\n\n')
    msg += (
        '<code>/change_channel</code> - сменить канал, в который будут отправляться все созданные контракты. После вызова '
        'команды, вы должны переслать любое сообщение из канала, в который вы хотите отправлять контракты.\nЕсли '
        'не хотите менять канал - просто отправьте любое сообщение')
    bot.send_message(message.from_user.id, msg, parse_mode='html')


@bot.message_handler(commands=['change_channel'])
@admin_only
def change_channel(message):
    user_id = message.from_user.id
    bot.send_message(user_id,
                     "Пожалуйста, перешлите любое сообщение из канала, в который вы хотите отправлять "
                     "контракты.\n\n<b>После этого, добавьте в этот канал бота как администратора</b>\n\nЕсли вы не "
                     "хотите"
                     "менять канал, просто напишите любое сообщение", parse_mode='html')
    bot.register_next_step_handler(message, get_channel_id)


def get_group_id(message):
    user_id = message.from_user.id
    if message.forward_from_chat is not None:
        global group
        group_id = message.forward_from_chat.id
        if load_group_id() == group_id:
            bot.send_message(user_id, 'Эта группа уже выбран как целевая')
        else:
            save_group_id(group_id)
            bot.send_message(user_id, f"Идентификатор группы успешно изменен на {group_id}")
    else:
        bot.send_message(user_id, "Ошибка! Пожалуйста, перешлите сообщение из группы.")


def get_channel_id(message):
    user_id = message.from_user.id
    if message.forward_from_chat is not None and message.forward_from_chat.type == 'channel':
        global channel_id
        channel_id = message.forward_from_chat.id
        if load_channel_id() == channel_id:
            bot.send_message(user_id, 'Этот канал уже выбран как целевой')
        else:
            save_channel_id(channel_id)
            bot.send_message(user_id, f"Идентификатор канала успешно изменен на {channel_id}")
    else:
        bot.send_message(user_id, "Ошибка! Пожалуйста, перешлите сообщение из канала.")


@bot.message_handler(commands=['chat_id'])
def print_chat_id(message):
    user_id = message.from_user.id
    keyboard = get_z1blo_keyboard()
    bot.send_message(user_id, f'Ваш chat id : <code>{user_id}</code>\nПеред отправкой разработчику скопируйте chat id',
                     parse_mode='html', reply_markup=keyboard)


user_data = {}

def make_contract_message_signed(contract_id):
    cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
    rows = cursor.fetchall()
    contract_id, message_id, chat_id, messagecon = rows[0]
    cursor.execute("SELECT executor FROM executors WHERE contract_id = ?", (contract_id,))
    executor_id = cursor.fetchone()
    username = bot.get_chat(executor_id).username
    messagecon = messagecon.replace('😴Ожидает своего исполнителя', f'✍️@{username} выполняет контракт', 1)
    bot.edit_message_text(messagecon, chat_id, message_id, parse_mode='html')

def make_onetime_contract_message_signed(contract_id, username):
    cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
    rows = cursor.fetchall()
    contract_id, message_id, chat_id, messagecon = rows[0]
    messagecon = messagecon.replace('😴Ожидает своего исполнителя', f'✍️@{username} выполняет контракт', 1)
    bot.edit_message_text(messagecon, chat_id, message_id, parse_mode='html')

def admin_accept_keyboard(contract_id, user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    accept = types.InlineKeyboardButton('Принять', url=f't.me/monopolycontractbot?start=adminaccept_{contract_id}_{user_id}')
    keyboard.add(accept)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = bot.get_chat(user_id)
    username = user.username
    if message.text.startswith('/start signonetime'):
        contract_id = message.text.replace('/start signonetime', '', 1)
        cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
        rows = cursor.fetchall()
        contract_id, message_id, chat_id, messagecon = rows[0]
        bot.send_message(user_id, f'Вы подписали контракт {contract_id}')
        make_onetime_contract_message_signed(contract_id, username)
        for admin_id in admin_user_ids:
            bot.send_message(admin_id, f'@{username} подписал одноразовый контракт с номером {contract_id}',
                             parse_mode='html')
    if message.text.startswith('/start signkonkurs'):
        contract_id = message.text.replace('/start signkonkurs', '', 1)

        cursor.execute("SELECT * FROM executors WHERE contract_id = ?", (contract_id,))
        rows = cursor.fetchall()[0]
        if rows[2] == 0:
            check_for_pretender(user_id, contract_id)
            cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
            rows = cursor.fetchall()
            contract_id, message_id, chat_id, messagecon = rows[0]
            accept_keyboard = admin_accept_keyboard(contract_id, user_id)
            bot.send_message(user_id, f'Вы отправили свою заявку на конкурс исполнителей!')
            for admin in admin_user_ids:
                bot.send_message(admin, f'На контракт №{contract_id} подал заявку @{username}, выбирайте его судьбу!', reply_markup=accept_keyboard)
        else:
            bot.send_message(user_id, f'Увы, но контракт уже подписан!')
    if message.text.startswith('/start adminaccept'):
        _, contract_id, executor_id = message.text.split('_', 2)
        group_id = load_group_id()
        executor_id = int(executor_id)

        cursor.execute("SELECT * FROM executors WHERE contract_id = ?", (contract_id,))

        txt = cursor.fetchall()[0][1]
        if txt == None:
            txt = ''
        txt += f',{executor_id}'

        cursor.execute("UPDATE executors SET pretendents = ? WHERE contract_id = ?", (txt, contract_id))

        cursor.execute("SELECT * FROM executors WHERE contract_id = ?", (contract_id,))
        rows = cursor.fetchall()[0]

        cursor.execute("SELECT * FROM pretendents WHERE contract_id = ? AND pretendent_id = ?", (contract_id, executor_id))
        rows1 = cursor.fetchall()
        if rows[2] == 0:

            pretendents = rows[1].split(',')
            pretendents.remove('')
            pretendents = set(pretendents)

            cursor.execute("SELECT * FROM pretendents WHERE contract_id = ? AND pretendent_id = ?",
                           (contract_id, executor_id))

            votes = cursor.fetchall()[0][2]

            cursor.execute('SELECT voted FROM admin_votes WHERE admin_id = ? AND contract_id = ?', (user_id, contract_id))
            voted = cursor.fetchone()[0]

            if voted:
                bot.send_message(user_id, 'Вы уже проголосовали в этом контракте!')
            else:
                votes += 1
                cursor.execute('UPDATE admin_votes SET voted = ? WHERE admin_id = ? AND contract_id = ?', (True, user_id, contract_id))
                bot.send_message(user_id, f'Вы успешно проголосовали в контракте №{contract_id}!')

            cursor.execute("UPDATE pretendents SET votes = ? WHERE pretendent_id = ? AND contract_id = ?",
                           (votes, executor_id, contract_id))
            conn.commit()

            #проверка все ли админы проголосовали
            cursor.execute('SELECT * FROM admin_votes WHERE contract_id = ?', (contract_id,))
            admin_votes = cursor.fetchall()

            voted = []
            for admin_vote in admin_votes:
                voted.append(admin_vote[2])
            if voted.count(False) == 0:
                winner = {}
                for pretendent in pretendents:
                    pretendent_id = int(pretendent)
                    cursor.execute("SELECT * FROM pretendents WHERE contract_id = ? AND pretendent_id = ?", (contract_id, pretendent_id))
                    votes = cursor.fetchall()[0][2]
                    winner[votes] = pretendent_id
                win = max(winner)
                win_id = winner[win]
                cursor.execute("UPDATE executors SET executor = ? WHERE contract_id = ?", (win_id, contract_id))
                conn.commit()
                executor = bot.get_chat(win_id)
                executor_username = executor.username
                make_contract_message_signed(contract_id)
                for admin in admin_user_ids:
                    bot.send_message(admin,
                                     f'#контракт #подписан\nКонтракт №{contract_id} был подписан с @{executor_username}, избранным народным голосованием!')
                bot.send_message(executor,f'Поздравялем!\nКонтракт {contract_id} был подписан с @{executor_username}, тоесть с Вами!!!')


contract_types_list = ['Одноразовый', 'Конкурс']


def types_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for typ in contract_types_list:
        keyboard.add(types.KeyboardButton(typ))
    return keyboard


@bot.message_handler(commands=['create_contract'])
def create_contract(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'step': 2}
        user_data[user_id] = {"button_status": False}
    user_data[user_id]['stage'] = 0
    user_data[user_id]['step'] = 2
    sent_message = bot.send_message(user_id, 'Введите хэштеги(Без символа "#", разделяя запятой, не важно сколько '
                                             'пробелов будет. Хэштег "#контракт" будет автоматически добавлен в самом'
                                             ' начале)')
    print(user_data[user_id])


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 1 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["contract_type"] = message.text
    user_data[message.chat.id]["type_status"] = True
    bot.send_message(user_id, 'Введите ТЗ. (Вручную, просто в сообщении)')
    user_data[user_id]['step'] = 3


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 2 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    messagehash = '#контракт\n\n'
    try:
        hashtags = message.text.split(',')
        for hashtag in hashtags:
            hashtag = hashtag.strip()
            messagehash += f'#{hashtag} '
    except Exception:
        messagehash += f'#{message.text}'
    user_data[message.chat.id]["hashtags"] = messagehash
    user_data[message.chat.id]["hash_status"] = True
    user_data[user_id]['step'] = 1
    keyboard = types_keyboard()
    bot.send_message(message.chat.id,
                     'Выберите один из заготовленных типов контракта, либо просто введите свой в сообщении.',
                     reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 3 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    current_date = datetime.now()

    one_day_later = current_date + timedelta(days=1)
    one_day_later = str(one_day_later.replace(hour=0, minute=0, second=0))

    three_days_later = current_date + timedelta(days=3)
    three_days_later = str(three_days_later.replace(hour=0, minute=0, second=0))

    seven_days_later = current_date + timedelta(days=7)
    seven_days_later = str(seven_days_later.replace(hour=0, minute=0, second=0))

    thirty_days_later = current_date + timedelta(days=30)
    thirty_days_later = str(thirty_days_later.replace(hour=0, minute=0, second=0))
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    tommorow = types.KeyboardButton(f'{one_day_later[:-10]}')
    days3 = types.KeyboardButton(f'{three_days_later[:-10]}')
    week = types.KeyboardButton(f'{seven_days_later[:-10]}')
    month = types.KeyboardButton(f'{thirty_days_later[:-10]}')
    keyboard.add(tommorow, days3, week, month)
    user_id = message.from_user.id
    user_data[message.chat.id]["tz"] = message.text
    user_data[message.chat.id]["tz_status"] = True
    bot.send_message(message.chat.id, 'Введите срок контракта(Заготовленный, либо просто сообщение вручную, оно никак не парсится)', reply_markup=keyboard)
    user_data[user_id]['step'] = 4


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 4 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["srok"] = message.text
    user_data[message.chat.id]["srok_status"] = True
    user_data[user_id]['step'] = 5
    bot.send_message(message.chat.id, 'Введите стоимость(Число, "BMC" будет дописано автоматически)')


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 5 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["cost"] = message.text.strip()
    user_data[message.chat.id]["cost_status"] = True
    user_data[user_id]['step'] = 6
    bot.send_message(message.chat.id,
                     'Введите Дополнительные условия(Просто текст, если условий нет, то отправьте "Н")')


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 6 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton('Перейти', callback_data="done")
    keyboard.add(button)
    if message.text == 'Н':
        user_data[user_id]['step'] = 0
    else:
        user_data[message.chat.id]["dop"] = message.text
        user_data[message.chat.id]["dop_status"] = True
    user_data[user_id]['contract_status'] = '😴Ожидает своего исполнителя'
    bot.send_message(message.chat.id, 'Перейти к виду контракта', reply_markup=keyboard)


##################################################### тут stage 1 ######################################################


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 1 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["contract_type"] = message.text
    user_data[message.chat.id]["type_status"] = True
    contract_start_message1(user_id)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 2 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    messagehash = '#контракт\n\n'
    try:
        hashtags = message.text.split(',')
        for hashtag in hashtags:
            hashtag = hashtag.strip()
            messagehash += f'#{hashtag} '
    except Exception:
        messagehash += f'#{message.text}'
    user_data[message.chat.id]["hashtags"] = messagehash
    user_data[message.chat.id]["hash_status"] = True
    contract_start_message1(message.from_user.id)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 3 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_data[message.chat.id]["tz"] = message.text
    user_data[message.chat.id]["tz_status"] = True
    contract_start_message1(message.from_user.id)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 4 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_data[message.chat.id]["srok"] = message.text
    user_data[message.chat.id]["srok_status"] = True
    contract_start_message1(message.from_user.id)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 5 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_data[message.chat.id]["cost"] = message.text
    user_data[message.chat.id]["cost_status"] = True
    contract_start_message1(message.from_user.id)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 6 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_data[message.chat.id]["dop"] = message.text
    user_data[message.chat.id]["dop_status"] = True
    contract_start_message1(message.from_user.id)


def accept_send_keyboard(message_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    accept = types.InlineKeyboardButton('Принять', callback_data=f'accept_{message_id}')
    decline = types.InlineKeyboardButton('Внести правки', callback_data=f'decline_{message_id}')
    keyboard.add(accept, decline)
    return keyboard


def finish_contract(call):
    user_id = call.from_user.id
    error_message = 'Вам не хватает следующих парметров:\n'
    if user_id in user_data:
        if user_data[user_id].get("hash_status") and user_data[user_id].get("type_status") and user_data[user_id].get(
                "tz_status") and user_data[user_id].get("srok_status") and user_data[user_id].get("cost_status"):
            contract_message = f"{user_data[user_id]['hashtags']}\n\n"
            contract_message += f"Статус контракта: {user_data[user_id].get('contract_status')}\n\n"
            contract_message += f"<b>Тип:</b>\n{user_data[user_id]['contract_type']}\n\n"
            contract_message += f"<b>ТЗ:</b>\n{user_data[user_id]['tz']}\n\n"
            contract_message += f"<b>Срок выполнения:</b>\n{user_data[user_id]['srok']}\n\n"
            contract_message += f"<b>Стоимость:</b>\n{user_data[user_id]['cost']} BMC\n\n"
            if user_data[user_id].get("dop_status"):
                contract_message += f"<b>Дополнительные условия:</b>\n{user_data[user_id]['dop']}\n\n"
            user_data[user_id]["message"] = contract_message
            sent_message = bot.send_message(user_id, '...')
            keyboard = accept_send_keyboard(sent_message.message_id)
            if user_data[user_id].get('contract_type') in contract_types_list:
                user_data[user_id]['button_status'] = True
                button_status = True
            if user_data[user_id].get("button_status"):
                button_status = True
            else:
                button_status = False
            bot.edit_message_text(
                f"Ваш контракт выглядит так: (Кнопка 'Подписать': {button_status})\n\n{contract_message}\n\nПодтвердите отправку",
                user_id,
                sent_message.message_id, reply_markup=keyboard, parse_mode='html')
        else:
            if user_data[user_id].get("hash_status") is not True:
                error_message += 'Хештеги\n'
            if user_data[user_id].get("type_status") is not True:
                error_message += 'Тип контракта\n'
            if user_data[user_id].get("tz_status") is not True:
                error_message += 'ТЗ\n'
            if user_data[user_id].get("srok_status") is not True:
                error_message += 'Срок\n'
            if user_data[user_id].get("cost_status") is not True:
                error_message += 'Стоимость\n'
            bot.send_message(user_id, error_message)
            contract_start_message1(user_id)
    else:
        bot.send_message(user_id,
                         "Вы не завершили процесс создания контракта. Пожалуйста, следуйте инструкциям.")


def one_sign_keyboard(uid):
    sign_keyboard = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton('Подписать контракт',
                                        url=f't.me/monopolycontractbot?start=signonetime{uid}')
    sign_keyboard.add(button)
    return sign_keyboard


def konkurs_sign_keyboard(uid):
    sign_keyboard = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton('Подписать контракт',
                                        url=f't.me/monopolycontractbot?start=signkonkurs{uid}')
    sign_keyboard.add(button)
    return sign_keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    callback = call.data
    if callback.startswith('type_'):
        user_data[user_id]["step"] = 1
        bot.send_message(user_id, 'Введите тип контракта')
    if callback.startswith('hashtags_'):
        user_data[user_id]["step"] = 2
        bot.send_message(user_id, 'Введите хэштеги через запятую(без #)')
    if callback.startswith('tz_'):
        user_data[user_id]["step"] = 3
        bot.send_message(user_id, 'Введите ТЗ')
    if callback.startswith('srok_'):
        user_data[user_id]["step"] = 4
        bot.send_message(user_id, 'Введите срок')
    if callback.startswith('cost_'):
        user_data[user_id]["step"] = 5
        bot.send_message(user_id, 'Введите стоимость(просто число)')
    if callback.startswith('dop_'):
        user_data[user_id]["step"] = 6
        bot.send_message(user_id, 'Введите дополнительные условия')
    if callback == 'cancel':
        del user_data[user_id]
        bot.send_message(user_id, 'Создание отменено! Если хотите начать снова - напишите /start')
    if callback == 'done':
        finish_contract(call)
    if callback.startswith('accept_'):
        uid = str(uuid.uuid4().hex)[22:]
        message = user_data[user_id].get("message")
        sent_message = bot.send_message(load_channel_id(), message, parse_mode='html')
        print(user_data[user_id].get('contract_type'))
        if user_data[user_id].get('button_status'):
            if user_data[user_id].get('contract_type') == 'Одноразовый':
                # если одноразовый, то генерируем ссылку на одноразовое
                sign_keyboard = one_sign_keyboard(uid)
                # обновляем сообщение, добавляя туда кнопку для подписания
                bot.edit_message_text(message, load_channel_id(), sent_message.message_id, reply_markup=sign_keyboard,
                                      parse_mode='html')
            if user_data[user_id].get('contract_type') == 'Конкурс':
                # конкурс
                sign_keyboard = konkurs_sign_keyboard(uid)
                bot.edit_message_text(message, load_channel_id(), sent_message.message_id, reply_markup=sign_keyboard,
                                      parse_mode='html')
                for admin_id in admin_user_ids:
                    cursor.execute('INSERT INTO admin_votes (admin_id, contract_id, voted) VALUES (?, ?, ?)',
                                   (admin_id, uid, False))
                    conn.commit()
        else:
            bot.edit_message_text(message, load_channel_id(), sent_message.message_id, parse_mode='html')

        cursor.execute("INSERT INTO contracts (contract_id, message_id, chat_id, message) VALUES (?, ?, ?, ?)",
                       (uid, sent_message.message_id, load_channel_id(), message))
        conn.commit()

        cursor.execute("INSERT INTO executors (contract_id, executor) VALUES (?,?)",
                       (uid, 0))
        conn.commit()

        del user_data[user_id]
        bot.send_message(user_id, 'Действие выполнено!')
    if callback.startswith('decline_'):
        message_id = int(callback.replace('decline_', '', 1))
        bot.delete_message(user_id, message_id)
        bot.send_message(user_id, 'Отправка отменена! Можете править контракт, либо создать новый с помощью /create_contract')
        user_data[user_id]['stage'] = 1
        contract_start_message1(user_id)
    if callback == 'button_status':
        user_data[user_id]['button_status'] = not (user_data[user_id]['button_status'])
        contract_start_message1(user_id)

# bot.polling()

while True:
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        print(f'{e}. Рестарт')
        continue
