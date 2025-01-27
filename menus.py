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

def loading():
    text = markdown(locale["menu"]["loading"])
    keyboard = None
    return text, keyboard

def main(call, message=None):
    if message is not None: user_id = message.chat.id
    else: user_id = call.message.chat.id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    data = json.loads(user[4])
    text = markdown(locale["menu"]["main"])
    if data == {}:
       text = markdown(locale["menu"]["hello"]) 
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
    file_name, book_info = book_data(user_id, book_id)
    name = markdown(str(book_info['name']), True)
    author = markdown(str(book_info['author']), True)
    pages = markdown(str(book_info['pages']), True)
    save_page = markdown(str(book_info['save_page']), True)
    status = markdown(str(book_info['status']), True)

    text = markdown(locale["menu"]["open_book"].format(name=name, author=author, pages=pages, save_page=save_page))
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data="return:main")
    btn_edit_name = InlineKeyboardButton(locale["button"]["edit_name"], callback_data=f"edit-name:{book_id}")
    btn_edit_author = InlineKeyboardButton(locale["button"]["edit_author"], callback_data=f"edit-author:{book_id}")
    btn_read = InlineKeyboardButton(locale["button"]["read"], callback_data=f"read:{book_id}:{save_page}")
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(btn_read)
    keyboard.add(btn_edit_name, btn_edit_author)
    keyboard.add(btn_return)
    return text, keyboard

def read_book(call, book_id, save_page):
    user_id = call.message.chat.id
    file_name, book_info = book_data(user_id, book_id)
    pages = book_info['pages']
    update_book_data(user_id, file_name, save_page=save_page)
    
    text = markdown(f"{get_book_content(file_name, int(save_page))}", True)

    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = []
    if save_page > 0:
        btn_back = InlineKeyboardButton(locale["button"]["back"], callback_data=f'read:{book_id}:{save_page-1}')
        buttons.append(btn_back)
    if save_page < pages:
        btn_next = InlineKeyboardButton(locale["button"]["next"], callback_data=f'read:{book_id}:{save_page+1}')
        buttons.append(btn_next)
    btn_close = InlineKeyboardButton(locale["button"]["close"], callback_data=f'open_book:{book_id}')
    keyboard.add(*buttons)
    keyboard.add(btn_close)
    return text, keyboard

def edit_book(call, book_id, type_edit=None):
    if type_edit is None: edit = "edit_error"
    elif type_edit == "name": edit = "edit_name"
    elif type_edit == "author": edit = "edit_author"
    text = markdown(locale["menu"][edit])
    keyboard = InlineKeyboardMarkup(row_width=1)
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data=f"open_book:{book_id}")
    keyboard.add(btn_return)
    return text, keyboard

def settings():
    text = markdown(locale["menu"]["settings"])
    keyboard = InlineKeyboardMarkup()
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data="return:main")
    keyboard.add(btn_return)
    return text, keyboard

def help():
    text = markdown(locale["menu"]["help"])
    keyboard = InlineKeyboardMarkup()
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data="return:main")
    keyboard.add(btn_return)
    return text, keyboard