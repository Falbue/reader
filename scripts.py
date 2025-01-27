import json
from datetime import datetime
import pytz
import sqlite3
import os
import re


DB_NAME = 'reader.db'
DB_PATH = f"{DB_NAME}"
if not os.path.exists(DB_PATH):
    import create_db
SAVE_FOLDER = 'books'


def now_time():  # Получение текущего времени по МСК
    now = datetime.now()
    tz = pytz.timezone('Europe/Moscow')
    now_moscow = now.astimezone(tz)
    current_time = now_moscow.strftime("%H:%M:%S")
    current_date = now_moscow.strftime("%Y.%m.%d")
    return current_date, current_time


def SQL_request(request, params=(), all_data=None):  # Выполнение SQL-запросов
    connect = sqlite3.connect(DB_PATH)
    cursor = connect.cursor()
    if request.strip().lower().startswith('select'):
        cursor.execute(request, params)
        if all_data == None: result = cursor.fetchone()
        else: result = cursor.fetchall()
        connect.close()
        return result
    else:
        cursor.execute(request, params)
        connect.commit()
        connect.close()

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_file(document, bot):
    create_folder(SAVE_FOLDER)
    file_info = bot.get_file(document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    unique_file_name = get_unique_filename(SAVE_FOLDER, document.file_name)
    save_path = os.path.join(SAVE_FOLDER, unique_file_name)
    
    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    
    return unique_file_name

def get_unique_filename(base_path, filename):
    name, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(base_path, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1
    return new_filename

def markdown(text, full=False):  # экранирование
    if full == True: special_characters = r'*|~[]()>#+-=|{}._!'
    else: special_characters = r'>#+-={}.!'
    escaped_text = ''
    for char in text:
        if char in special_characters:
            escaped_text += f'\\{char}'
        else:
            escaped_text += char
    return escaped_text

def registration(message):
    user_id = message.chat.id
    message_id = message.message_id

    date, time  = now_time()
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    if user is None:
        SQL_request("""INSERT INTO users (id, message, time_registration)
                          VALUES (?, ?, ?)""", (user_id, message_id+1, date))
        print(f"Зарегистрирован новый пользователь")
    else:
        menu_id = SQL_request("SELECT message FROM users WHERE id = ?", (user_id,))
        SQL_request("""UPDATE users SET message = ? WHERE id = ?""", (message_id+1, user_id))  # добавление telegram_id нового меню
        return menu_id

def get_book_content(file_path, page=None, user_id=None):
    encodings = ['utf-8', 'windows-1251', 'koi8-r', 'iso-8859-5']
    text = ""
    for encoding in encodings:
        try:
            with open(f"books/{file_path}", 'r', encoding=encoding) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise Exception("Не удалось определить кодировку файла.")

    def split_text_into_pages(text, page_size):
        pages = []
        start = 0
        while start < len(text):
            end = start + page_size
            if end >= len(text):
                pages.append(text[start:])
                break
            while end > start and text[end] not in (' ', '\n', '\t', '\r'):
                end -= 1
            if end == start:
                end = start + page_size
            pages.append(text[start:end])
            start = end
        return pages
    
    pages = split_text_into_pages(text, int(config_data(user_id, "tg_pages")))
    
    if page is not None:
        if page < 0 or page >= len(pages):
            return "Книга прочитана!"
        return pages[page]
    else:
        return len(pages)

def add_book(user_id, file_name):
    date, time = now_time()
    date = f"{date} {time}"
    SQL_request("""INSERT INTO books (filename, time_add, user_id) VALUES (?, ?, ?)""", (file_name, date, user_id))
    pages = get_book_content(file_name)
    update_book_data(user_id, file_name, name=file_name.rsplit('.', 1)[0], pages=pages, save_page=0)

def update_book_data(user_id, book_name, name=None, author=None, pages=None, save_page=None, status=None):
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    data = json.loads(user[4]) if user[4] else {}
    if book_name in data:
        if name is not None:
            data[book_name]['name'] = name
        if author is not None:
            data[book_name]['author'] = author
        if pages is not None:
            data[book_name]['pages'] = pages
        if save_page is not None:
            data[book_name]['save_page'] = save_page
        if status is not None:
            data[book_name]['status'] = status
    else:
        data[book_name] = {
            'name': name if name is not None else book_name,
            'author': author if author is not None else "Не указан",
            'pages': pages if pages is not None else 0,
            'save_page': save_page if save_page is not None else 0,
            'status': status if status is not None else 'close'
        }
    SQL_request("""UPDATE users SET read = ? WHERE id = ?""", (json.dumps(data), user_id))

def update_config(user_id, tg_pages=None):
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    data = json.loads(user[5]) if user[5] else {}
    if tg_pages is not None: data["tg_pages"] = tg_pages
    SQL_request("""UPDATE users SET config = ? WHERE id = ?""", (json.dumps(data), user_id))

def book_data(user_id, book_id):
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    books = json.loads(user[4])
    books_list = list(books.items())
    book_data = books_list[int(book_id)]
    return book_data

def config_data(user_id, config_type=None):
    user = SQL_request("SELECT * FROM users WHERE id = ?", (user_id,))
    config = json.loads(user[5])
    if config_type is not None:
        config = config[config_type]
    return config

def rename_book_data(message, call, data):
    try:
        text = message.text
        user_id = message.chat.id
        book_id = data[1]
        file_name, book_info = book_data(user_id, book_id)
        if data[0] == "name":
            update_book_data(user_id, file_name, name=text)
        elif data[0] == "author":
            update_book_data(user_id, file_name, author=text)
        return True
    except: return False