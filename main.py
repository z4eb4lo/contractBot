import telebot
from telebot import types
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

bot = telebot.TeleBot('6432599280:AAGtVe1czZYj5wFfDo4SqeNWjJpwhvvfoKc')

admin_user_ids = [487545908, 1262539577, 849106299, 146327272]

conn = sqlite3.connect("db.db", check_same_thread=False)

cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS contracts (
                    contract_id TEXT,
                    message_id INT,
                    chat_id INT,
                    message TEXT,
                    button TEXT,
                    time TIMESTAMP
                )''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS nickname (
                    contract_id TEXT,
                    name TEXT
                )''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS admin_votes (
                    admin_id TEXT,
                    contract_id TEXT,
                    voted INT
                )''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS admin_contract_votes (
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

cursor.execute('''CREATE TABLE IF NOT EXISTS contract_vote (
                    contract_id TEXT,
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

def send_contract_page(messages, page, chat_id, get_keyboard=False):
    global total_pages
    markup = types.InlineKeyboardMarkup(row_width=3)
    next_page_button = types.InlineKeyboardButton(
        text="Следующий", callback_data=f"invnext_{page + 1}"
    )
    page_number_button = types.InlineKeyboardButton(f'{page+1}/{total_pages}', callback_data='123')
    prev_page_button = types.InlineKeyboardButton(
        text="Предыдущий", callback_data=f"invprev_{page - 1}"
    )
    search_button = types.InlineKeyboardButton(
        text="Поиск по названию", callback_data="invsearch_name"
    )
    search_button1 = types.InlineKeyboardButton(
        text="Поиск по содержанию контракта", callback_data="invsearch_by_message"
    )
    markup.add(prev_page_button, page_number_button, next_page_button)
    markup.add(search_button)
    # markup.add(search_button1)

    if get_keyboard == True:
        return markup

    sent_message = bot.send_message(chat_id, messages[page], reply_markup=markup, parse_mode='html')
    sent_message_id = sent_message.message_id
    return sent_message_id

@admin_only
@bot.message_handler(commands=['contracts'])
def contracts_handler(message):
    global current_page, total_pages, msgs
    cursor.execute("SELECT * FROM nickname")
    contracts = cursor.fetchall()

    if contracts:
        messages = []
        contracts_per_page = 5
        for i in range(0, len(contracts), contracts_per_page):
            page_contracts = contracts[i:i + contracts_per_page]
            page_message = ""
            for contract in page_contracts:
                contract_id, name = contract
                contract_info = f"ID контракта: <code>{contract_id}</code>\nИмя контракта: {name}\n\n"
                page_message += contract_info
            page_message += 'Чтобы посмотреть контракт, используйте <code>/showcon</code> {ID}\n' \
            'Чтобы посмотреть лог, используйте   <code>/logcon</code> {ID}'
            messages.append(page_message)

        current_page = 0
        total_pages = len(messages)
        chat_id = message.chat.id

        send_contract_page(messages, current_page, chat_id)
        msgs = messages
    else:
        bot.send_message(chat_id, "Не найдено контрактов.")

def search_name(message):
    global total_pages, msgs
    namee = message.text
    chat_id = message.chat.id
    cursor.execute("SELECT * FROM nickname WHERE name LIKE ?", (f'%{namee}%',))
    filtered_contracts = cursor.fetchall()
    if filtered_contracts:
        messages1 = []
        contracts_per_page = 3
        for i in range(0, len(filtered_contracts), contracts_per_page):
            page_contracts = filtered_contracts[i:i + contracts_per_page]
            page_message = ""
            for contract in page_contracts:
                contract_id, name = contract
                contract_info = f"ID контракта: <code>{contract_id}</code>\nИмя контракта: {name}\n\n"
                page_message += contract_info
            page_message += 'Чтобы посмотреть контракт, используйте <code>/showcon</code> {ID}\n' \
                            'Чтобы посмотреть лог, используйте   <code>/logcon</code> {ID}'
            messages1.append(page_message)

        current_page = 0
        total_pages = len(messages1)

        send_contract_page(messages1, current_page, chat_id)
        msgs = messages1
    else:
        bot.send_message(chat_id, "Контракты с таким названием не найдены.")

def search_by_message(message):
    global total_pages
    msg = message.text
    chat_id = message.chat.id
    cursor.execute("SELECT * FROM contracts WHERE message LIKE ?", (f'%{msg}%',))
    filtered_contracts = cursor.fetchall()
    if filtered_contracts:
        messages1 = []
        contracts_per_page = 1
        for i in range(0, len(filtered_contracts), contracts_per_page):
            page_contracts = filtered_contracts[i:i + contracts_per_page]
            page_message = ""
            for contract in page_contracts:
                contract_id, cmessage_id, cchat_id, cmessage, button, timee = contract
                contract_info = f"ID контракта: <code>{contract_id}</code>\nСодержание контракта:\n\n {cmessage}\n\n"
                page_message += contract_info
            page_message += 'Чтобы посмотреть контракт, используйте <code>/showcon</code> {ID}\n' \
                            'Чтобы посмотреть лог, используйте   <code>/logcon</code> {ID}'
            messages1.append(page_message)

        current_page = 0
        total_pages = len(messages1)

        send_contract_page(messages1, current_page, chat_id)
        msgs = messages1
    else:
        bot.send_message(chat_id, "Контракты с таким содержанием не найдены.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('inv'))
def callback_handler(call):
    chat_id = call.from_user.id
    global current_page, total_pages, msgs
    query = call.data.replace('inv', '', 1)
    messages = msgs

    if query == 'search_name':
        bot.send_message(chat_id, 'Введите имя контракта')
        bot.register_next_step_handler(call.message, search_name)

    if query == 'search_by_message':
        bot.send_message(chat_id, 'Введите фрагмент содержания контракта.\nНапример, вы вводите "Сделать чат-бота" и Вам выдаются все контракты, в сообщении которых(полное описание: хештеги, тз, тип, ...) содержится эта фраза')
        bot.register_next_step_handler(call.message, search_by_message)

    if query.startswith('next') or query.startswith('prev'):
        query = query.split('_')
        action = query[0]
        page = int(query[1])
        if action == 'next' and current_page < total_pages - 1:
            current_page += 1
        elif action == 'prev' and current_page > 0:
            current_page -= 1

        markup = send_contract_page(messages, current_page, chat_id, get_keyboard=True)

        bot.edit_message_text(messages[current_page], chat_id=chat_id,
                              message_id=call.message.message_id, reply_markup=markup,parse_mode='html')
        sent_message_id = send_contract_page(messages, current_page, chat_id)
        bot.delete_message(chat_id, sent_message_id)


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
    name = 'Имя в БД'
    if user_id in user_data and user_data[user_id].get("name_status") == True:
        h = 'Имя в БД✅'
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
    button7 = types.InlineKeyboardButton(f'{name}', callback_data=f'name_{message_id}')
    button1 = types.InlineKeyboardButton(f'{h}', callback_data=f'hashtags_{message_id}')
    button2 = types.InlineKeyboardButton(f'{ty}', callback_data=f'type_{message_id}')
    button3 = types.InlineKeyboardButton(f'{tz}', callback_data=f'tz_{message_id}')
    button4 = types.InlineKeyboardButton(f'{sr}', callback_data=f'srok_{message_id}')
    button5 = types.InlineKeyboardButton(f'{st}', callback_data=f'cost_{message_id}')
    button6 = types.InlineKeyboardButton(f'{d}', callback_data=f'dop_{message_id}')
    button_sign = types.InlineKeyboardButton(f'{bu}', callback_data=f'button_status')
    button_cancel = types.InlineKeyboardButton('Отмена', callback_data=f'cancel')
    done = types.InlineKeyboardButton('Отправить контракт', callback_data=f'done')
    keyboard.add(button7)
    keyboard.add(button1, button2, button3, button4, button5, button6, button_sign)
    keyboard.add(done)
    keyboard.add(button_cancel)
    return keyboard


channel_id_filename = "channel_id.txt"


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
        '<code>/create_contract</code> - начать создание контракта. Чтобы отменить создание, нажмите "Отмена" в меню или напишите <code>/start</code> '
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

def create_show_contract_keyboard(contract_id):
    cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
    contract = cursor.fetchall()[0]
    shit, cmessage_id, cchat_id, cmessage, button, timee = contract

    show_contract_keyboard = types.InlineKeyboardMarkup(row_width=1)
    show_button = types.InlineKeyboardButton(f'Посмотреть контракт {contract_id}',
                                             url=f't.me/monopolycontractbot?start=showcontract_{contract_id}')
    show_contract_keyboard.add(show_button)
    return show_contract_keyboard

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
    contract_id, message_id, chat_id, messagecon, button, timee = rows[0]
    cursor.execute("SELECT executor FROM executors WHERE contract_id = ?", (contract_id,))
    executor_id = cursor.fetchone()
    username = bot.get_chat(executor_id).username
    messagecon = messagecon.replace('😴Ожидает своего исполнителя', f'✍️@{username} выполняет контракт', 1)
    bot.edit_message_text(messagecon, chat_id, message_id, parse_mode='html')
    cursor.execute('UPDATE contracts SET message = ? WHERE contract_id = ?', (messagecon, contract_id))
    conn.commit()

def make_onetime_contract_message_signed(contract_id, username):
    cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
    rows = cursor.fetchall()
    contract_id, message_id, chat_id, messagecon, button, timee = rows[0]
    messagecon = messagecon.replace('😴Ожидает своего исполнителя', f'✍️@{username} выполняет контракт', 1)
    bot.edit_message_text(messagecon, chat_id, message_id, parse_mode='html')
    cursor.execute('UPDATE contracts SET message = ? WHERE contract_id = ?', (messagecon, contract_id))
    conn.commit()

def admin_accept_keyboard(contract_id, user_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    accept = types.InlineKeyboardButton('Принять', url=f't.me/monopolycontractbot?start=adminaccept_{contract_id}_{user_id}')
    show_contract = types.InlineKeyboardButton(f'Посмотреть контракт {contract_id}', url=f't.me/monopolycontractbot?start=showcontract_{contract_id}')
    keyboard.add(accept, show_contract)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user = bot.get_chat(user_id)
    username = user.username
    # подпись одноразового
    if message.text.startswith('/start signonetime'):
        contract_id = message.text.replace('/start signonetime', '', 1)
        cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
        rows = cursor.fetchall()
        contract_id, message_id, chat_id, messagecon, button, timee = rows[0]
        bot.send_photo(user_id, photo=open('design/sign.jpg', 'rb'),
                       caption=f'Вы подписали контракт {contract_id}',
                       parse_mode='html')

        logging.basicConfig(level=logging.INFO, filename=f"log/{contract_id}_log.log", filemode="w",
                            format="%(asctime)s %(levelname)s: %(message)s")
        logging.info(f'{username} подписал контракт {contract_id}')

        make_onetime_contract_message_signed(contract_id, username)
        show_contract_keyboard = create_show_contract_keyboard(contract_id)

        for admin_id in admin_user_ids:
            bot.send_photo(admin_id, photo=open('design/sign.jpg', 'rb'), caption=f'@{username} подписал одноразовый контракт с номером <code>{contract_id}</code>',
                             parse_mode='html', reply_markup=show_contract_keyboard)
    # подпись конкурса
    if message.text.startswith('/start signkonkurs'):
        contract_id = message.text.replace('/start signkonkurs', '', 1)

        cursor.execute("SELECT * FROM executors WHERE contract_id = ?", (contract_id,))
        rows = cursor.fetchall()[0]
        # если у контракта нет исполнителя
        if rows[2] == 0:
            check_for_pretender(user_id, contract_id)
            cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id,))
            rows = cursor.fetchall()
            contract_id, message_id, chat_id, messagecon, button, timee = rows[0]
            accept_keyboard = admin_accept_keyboard(contract_id, user_id)
            bot.send_photo(user_id, photo=open('design/handshake.jpg', 'rb'), caption=f'Вы отправили свою заявку на конкурс исполнителей!')
            for admin in admin_user_ids:
                bot.send_photo(user_id, photo=open('design/newcontract.jpg', 'rb'),
                               caption=f'На контракт <code>{contract_id}</code> подал заявку @{username}, выбирайте его судьбу! (Если вы не хотите голосовать за него, просто выберите другого исполнителя)\n\n<b>Также, это сообщение можно переслать в чат, все кнопки сохранятся</b>', reply_markup=accept_keyboard, parse_mode='html')
                # bot.send_message(admin, f'На контракт <code>{contract_id}</code> подал заявку @{username}, выбирайте его судьбу! (Если вы не хотите голосовать за него, просто выберите другого исполнителя)\n\n<b>Также, это сообщение можно переслать в чат, все кнопки сохранятся</b>', reply_markup=accept_keyboard, parse_mode='html')

            logging.basicConfig(level=logging.INFO, filename=f"log/{contract_id}_log.log", filemode="w",
                                format="%(asctime)s %(levelname)s: %(message)s")
            logging.info(f'{username} подал заявку на контракт {contract_id}')
        else:
            bot.send_message(user_id, f'Увы, но контракт уже подписан!')

    # окончание конкурса
    if message.text.startswith('/start adminaccept'):
        _, contract_id, executor_id = message.text.split('_', 2)
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
        # если нет исполнителя
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
                conn.commit()
                bot.send_photo(user_id, photo=open('design/handshake.jpg', 'rb'), caption=f'Вы успешно проголосовали в контракте №{contract_id}!')

                logging.basicConfig(level=logging.INFO, filename=f"log/{contract_id}_log.log", filemode="w",
                                    format="%(asctime)s %(levelname)s: %(message)s")
                logging.info(f'@{bot.get_chat(user_id).username} успешно проголосовали за @{bot.get_chat(executor_id).username} в контракте {contract_id}')

            cursor.execute("UPDATE pretendents SET votes = ? WHERE pretendent_id = ? AND contract_id = ?",
                           (votes, executor_id, contract_id))
            conn.commit()

            #проверка все ли админы проголосовали
            cursor.execute('SELECT * FROM admin_votes WHERE contract_id = ?', (contract_id,))
            admin_votes = cursor.fetchall()

            voted = []
            for admin_vote in admin_votes:
                voted.append(admin_vote[2])
            # если нет не проголосовавших админов, то
            if voted.count(False) == 0:
                winner = {}
                # подсчет у кого брльше голосов, тот и становится исполнителем
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

                show_contract_keyboard = create_show_contract_keyboard(contract_id)

                for admin in admin_user_ids:
                    bot.send_photo(admin, photo=open('design/sign.jpg', 'rb'),
                                   caption=f'#контракт #подписан\nКонтракт <code>{contract_id}</code> был подписан с @{executor_username}, избранным народным голосованием!', parse_mode='html', reply_markup=show_contract_keyboard)

                bot.send_photo(executor, photo=open('design/sign.jpg', 'rb'), caption=f'Поздравялем!\nКонтракт <code>{contract_id}</code> был подписан с @{executor_username}, тоесть с Вами!!!',parse_mode='html')

                logging.basicConfig(level=logging.INFO, filename=f"log/{contract_id}_log.log", filemode="w",
                                    format="%(asctime)s %(levelname)s: %(message)s")
                logging.info(f'Контракт {contract_id} был подписан с @{executor_username}')
        else:
            bot.send_message(user_id, 'Этот контракт уже подписан!')

    # когда кто-то подтверждает контракт, всем отправляется голосвания выкалдывать его или нет.
    if message.text.startswith('/start votecontract'):
        _, action, contract_id = message.text.split('_', 2)

        cursor.execute("SELECT * FROM contracts WHERE contract_id = ?", (contract_id, ))
        contract = cursor.fetchall()[0]
        shit, cmessage_id, cchat_id, cmessage, button, timee = contract

        cursor.execute('SELECT voted FROM admin_contract_votes WHERE admin_id = ? AND contract_id = ?', (user_id, contract_id))
        voted = cursor.fetchone()[0]

        cursor.execute('SELECT votes FROM contract_vote WHERE contract_id = ?', (contract_id, ))
        votes = cursor.fetchone()[0]

        if not voted:
            if action == 'accept':
                votes += 1
            if action == 'decline':
                votes -= 1

            bot.send_photo(user_id, photo=open('design/handshake.jpg', 'rb'), caption=f'Вы успешно проголосовали в контракте №{contract_id}!')

            cursor.execute('UPDATE admin_contract_votes SET voted = ? WHERE admin_id = ? AND contract_id = ?', (1, user_id, contract_id))
            conn.commit()

            cursor.execute('UPDATE contract_vote SET votes = ? WHERE contract_id = ?', (votes, contract_id))
            conn.commit()

            # подсчет результатов
            if votes >= len(admin_user_ids) // 2:

                for admin in admin_user_ids:
                    bot.send_message(admin, f'Контракт <code>{contract_id}</code> был принят администраторами! Приступаем к выкладыванию', parse_mode='html')

                sent_message = bot.send_message(load_channel_id(), cmessage, parse_mode='html')

                logging.basicConfig(level=logging.INFO, filename=f"log/{contract_id}_log.log", filemode="w",
                                    format="%(asctime)s %(levelname)s: %(message)s")
                logging.info(f'Контракт {contract_id} был принят администраторами')

                if button is not None:

                    if button == 'Одноразовый':
                        # если одноразовый, то генерируем ссылку на одноразовое
                        sign_keyboard = one_sign_keyboard(contract_id)
                        # обновляем сообщение, добавляя туда кнопку для подписания
                        bot.edit_message_text(cmessage, load_channel_id(), sent_message.message_id, reply_markup=sign_keyboard,
                                              parse_mode='html')

                    if button == 'Конкурс':
                        # конкурс
                        sign_keyboard = konkurs_sign_keyboard(contract_id)
                        bot.edit_message_text(cmessage, load_channel_id(), sent_message.message_id, reply_markup=sign_keyboard,
                                              parse_mode='html')

                        for admin_id in admin_user_ids:
                            cursor.execute('INSERT INTO admin_votes (admin_id, contract_id, voted) VALUES (?, ?, ?)',
                                           (admin_id, contract_id, False))
                            conn.commit()

                else:
                    bot.edit_message_text(message, load_channel_id(), sent_message.message_id, parse_mode='html')

                cursor.execute('UPDATE contracts SET message_id = ? WHERE contract_id = ?', (sent_message.message_id, contract_id))
                conn.commit()


        if voted:
            bot.send_message(user_id, 'Вы уже проголосовали в выборе этого контракта')

    if message.text.startswith('/start showcontract_'):
        contract_id = message.text.replace('/start showcontract_', '')

        cursor.execute('SELECT * FROM contracts WHERE contract_id = ?', (contract_id, ))
        contract = cursor.fetchall()[0]
        _, cmessage_id, cchat_id, cmessage, button, timee = contract
        bot.send_message(user_id, f'Номер контракта: <code>{contract_id}</code>\n___________________________\n{cmessage}', parse_mode='html')


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
        user_data[user_id] = {'step': -1}
        user_data[user_id] = {"button_status": False}
    user_data[user_id]['stage'] = 0
    user_data[user_id]['step'] = -1
    bot.send_message(user_id, "Введите название контракта, по которому он будет определяться в БД")


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == -1 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["contract_name"] = message.text
    user_data[message.chat.id]["name_status"] = True
    user_data[user_id]['step'] = 2
    sent_message = bot.send_message(user_id, 'Введите хэштеги(Без символа "#", разделяя запятой, не важно сколько '
                                             'пробелов будет. Хэштег "#контракт" будет автоматически добавлен в самом'
                                             ' начале)')


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

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True) # Клавиатура с заготовленными стоимостями
    c500 =  types.KeyboardButton('500')
    c1000 =  types.KeyboardButton('1000')
    c1500 =  types.KeyboardButton('1500')
    c2000 =  types.KeyboardButton('2000')
    c2500 =  types.KeyboardButton('2500')
    c3000 =  types.KeyboardButton('3000')
    c4000 =  types.KeyboardButton('4000')
    c5000 =  types.KeyboardButton('5000')
    keyboard.add(c500, c1000, c1500, c2000, c2500, c3000, c4000, c5000)

    user_data[message.chat.id]["srok"] = message.text
    user_data[message.chat.id]["srok_status"] = True
    user_data[user_id]['step'] = 5
    bot.send_message(message.chat.id, 'Выбреите заготовленное значение или введите стоимость(Число, "BMC" будет дописано автоматически)', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 5 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = types.KeyboardButton('Без доп.условий')
    keyboard.add(button)

    user_id = message.from_user.id
    user_data[message.chat.id]["cost"] = message.text.strip()
    user_data[message.chat.id]["cost_status"] = True
    user_data[user_id]['step'] = 6
    bot.send_message(message.chat.id,
                     'Введите Дополнительные условия(Просто текст, если условий нет, то выберите соответсвующий вариант на клавиатуре)', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 6 and
                                          user_data[message.chat.id]["stage"] == 0)
def handle_contract_type(message):
    user_id = message.from_user.id
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton('Перейти', callback_data="done")
    keyboard.add(button)
    if message.text == 'Без доп.условий':
        user_data[user_id]['step'] = 0
    else:
        user_data[message.chat.id]["dop"] = message.text
        user_data[message.chat.id]["dop_status"] = True
    user_data[user_id]['contract_status'] = '😴Ожидает своего исполнителя'
    bot.send_message(message.chat.id, 'Перейти к виду контракта', reply_markup=keyboard)


##################################################### тут stage 1 ######################################################
# stage 1 - это когда человек нажал "Править" после ввода контракта (тут та самая обработка большой менюшки)

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == 1 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["contract_type"] = message.text
    user_data[message.chat.id]["type_status"] = True
    contract_start_message1(user_id)


@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id]["step"] == -1 and
                                          user_data[message.chat.id]["stage"] == 1)
def handle_contract_type(message):
    user_id = message.from_user.id
    user_data[message.chat.id]["contract_name"] = message.text
    user_data[message.chat.id]["name_status"] = True
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
            contract_message += f"Статус контракта:\n{user_data[user_id].get('contract_status')}\n\n"
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
                f"Ваш контракт выглядит так: (Кнопка 'Подписать': {button_status})\n\nИмя в БД: <b>{user_data[user_id].get('contract_name')}</b>\n\n{contract_message}\n\nПодтвердите отправку",
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

def start_contract_voting(contract_id, message):
    # клавиатура для голосования за контракты
    vote_keyboard = types.InlineKeyboardMarkup(row_width=2)
    accept = types.InlineKeyboardButton('Принять', url=f't.me/monopolycontractbot?start=votecontract_accept_{contract_id}')
    decline = types.InlineKeyboardButton('Отклонить', url=f't.me/monopolycontractbot?start=votecontract_decline_{contract_id}')
    vote_keyboard.add(accept, decline)

    for admin_id in admin_user_ids:
        cursor.execute("INSERT INTO admin_contract_votes (admin_id, contract_id, voted) VALUES (?, ?, ?)", (admin_id, contract_id, 0))
        conn.commit()
        # bot.send_photo(admin_id, photo=open('design/newcontract.jpg', 'rb'), caption=f'На голосование поступил контракт:\n\n{message}\n\nВершите его судьбой!', reply_markup=vote_keyboard, parse_mode='html')
        bot.send_message(admin_id, f'На голосование поступил контракт:\n\n{message}\n\nВершите его судьбой!', reply_markup=vote_keyboard, parse_mode='html')


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    callback = call.data
    if callback.startswith('name_'):
        user_data[user_id]["step"] = -1
        bot.send_message(user_id, 'Введите имя контракта, которое будет вписано в БД')
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
    # отвечает за выкладывание контракта
    if callback.startswith('accept_'):
        uid = str(uuid.uuid4().hex)[22:]
        message = user_data[user_id].get("message")

        button = 'None'

        if user_data[user_id].get('contract_type') in contract_types_list:
            button = user_data[user_id].get('contract_type')

        # Получение текущей даты и времени
        current_time = datetime.now()

        # Преобразование даты и времени в строку в нужном формате
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("INSERT INTO contracts (contract_id, chat_id, message, button, time) VALUES (?, ?, ?, ?, ?)",
                       (uid, load_channel_id(), message, button, time_str))
        conn.commit()

        cursor.execute("INSERT INTO contract_vote (contract_id, votes) VALUES (?, ?)", (uid, 0))
        conn.commit()

        cursor.execute("INSERT INTO executors (contract_id, executor) VALUES (?,?)",
                       (uid, 0))
        conn.commit()

        # имя контракта в БД
        contract_name = user_data[user_id].get('contract_name')
        print(contract_name)
        cursor.execute("INSERT INTO nickname (contract_id, name) VALUES (?, ?)", (uid, contract_name))

        start_contract_voting(uid, message)

        del user_data[user_id]
        # контракт отправлен на рассмотерние алдминов
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


@bot.message_handler(commands=['developers'])
def show_developers(message):
    user_id = message.chat.id
    z1blo = bot.get_chat(487545908).username
    ma = bot.get_chat(849106299).username
    mi = bot.get_chat(1262539577).username
    msg = f'''Разработчики данного бота:
@{z1blo} - старший разработчик
@{ma} - мл. разработчик
@{mi} - мл. разработчик'''
    bot.send_message(user_id, msg)

@admin_only
@bot.message_handler(commands=['test'])
def test(message):
    user_id = message.chat.id
    cursor.execute("SELECT * FROM contracts ORDER BY time")
    rows = cursor.fetchall()
    bot.reply_to(message, str(rows))

@admin_only
@bot.message_handler(commands=['showcon'])
def showcon(message):
    chat_id = message.chat.id
    _, contract_id = message.text.split(' ', 1)
    markup = create_show_contract_keyboard(contract_id)
    bot.send_message(chat_id, f'Информация о контракте №{contract_id}', reply_markup=markup)

@admin_only
@bot.message_handler(commands=['logcon'])
def logcon(message):
    chat_id = message.chat.id
    _, contract_id = message.text.split(' ', 1)
    log_path = f'log/{contract_id}_log.log'
    try:
        bot.send_document(chat_id, open(log_path, 'r'), caption=f'Лог контракта №{contract_id}')
    except Exception:
        bot.send_message(chat_id, 'Такого лога не существует')

while True:
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        print(f'{e}. Рестарт')
        continue