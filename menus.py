from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
from scripts import *

# Загрузка локализации из JSON файла
with open('localization.json', 'r', encoding='utf-8') as file:
    locale = json.load(file)

def create_buttons(data, prefix):
    buttons = []
    for text, callback in data.items():
        if not isinstance(text, str):
            text = str(text)
        if callback == "":
            callback = text
        button = types.InlineKeyboardButton(text, callback_data=f'{prefix}:{callback}')
        buttons.append(button)
    return buttons

def main(call, message=None):
    if message is not None: user_id = message.chat.id
    else: user_id = call.message.chat.id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    text = markdown(locale["menu"]["main"])
    btn_stat = InlineKeyboardButton(locale["button"]["stat"], callback_data="stat")
    keyboard = InlineKeyboardMarkup(row_width=2)
    data = json.loads(user[4]) if user[4] else {}
    buttons = {}
    i=0
    if data != {}:
        for book in data:
            book_data = data[book]
            buttons[book_data["name"]] = i
            i+=1
        books = create_buttons(buttons, "open_book")
        keyboard.add(*books)
    keyboard.add(btn_stat)
    return text, keyboard

def get_book(error=False):
    text = markdown(locale["menu"]["get_book"])
    if error == True: text = markdown(locale["menu"]["get_book_error"])
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data="return:main")
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(btn_return)
    return text, keyboard

def open_book(call, book_id):
    user_id = call.message.chat.id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    books = json.loads(user[4])
    books_list = list(books.items())
    book_data = books_list[0]
    file_name, book_info = book_data
    name = book_info['name']
    pages = book_info['pages']
    save_page = book_info['save_page']
    status = book_info['status']

    text = markdown(locale["menu"]["open_book"].format(name=name,pages=pages,save_page=save_page, status=status))
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data="return:main")
    btn_read = InlineKeyboardButton(locale["button"]["read"], callback_data=f"read:{book_id}")
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(btn_read)
    keyboard.add(btn_return)
    return text, keyboard
