import telebot
import threading
import traceback

import config
from scripts import *
import menus


VERSION="0.0.1"
print(VERSION)
bot = telebot.TeleBot(config.API)
ALLOWED_EXTENSIONS = {'.txt'}


SAVE_FOLDER = 'books'


# ОБРАБОТКА КОМАНД
@bot.message_handler(commands=['start'])  # обработка команды start
def start(message):
    menu_id = registration(message)
    text, keyboard = menus.main()
    bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode="MarkdownV2")
    bot.delete_message(message.chat.id, message.id)
    if menu_id:
        try:
            bot.delete_message(message.chat.id, menu_id)
        except:
            pass


# ОБРАБОТКА ВЫЗОВОВ
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):  # работа с вызовами inline кнопок
    user_id = call.message.chat.id
    username = call.from_user.username
    bot.clear_step_handler_by_chat_id(chat_id=user_id)
    menu_id = call.message.message_id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))
    SQL_request("UPDATE users SET username = ?, message = ? WHERE id = ?", (username, menu_id, user_id))
    print(f"{user_id}: {call.data}")

    if (call.data).split(":")[0] == "return":
        menu_name = (call.data).split(":")[1]
        open_menu = getattr(menus, menu_name)
        text, keyboard = open_menu()
        bot.edit_message_text(chat_id=user_id, message_id=menu_id, text=text, reply_markup=keyboard, parse_mode="MarkdownV2")


print(f"бот запущен...")
def start_polling():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Перезапуск...")


@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.chat.id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))
    bot.edit_message_text(chat_id=user_id, message_id=user[2], text="Обработка файла\.\.\.", parse_mode="MarkdownV2")
    file_name = message.document.file_name
    file_extension = os.path.splitext(file_name)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        text, keyboard = menus.get_book(True)
        print("Неверный формат книги")
    else:
        try:
            create_folder(SAVE_FOLDER)
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            unique_file_name = get_unique_filename(SAVE_FOLDER, file_name)
            save_path = os.path.join(SAVE_FOLDER, unique_file_name)       
            with open(save_path, 'wb') as new_file:
                new_file.write(downloaded_file)
    
            add_book(user_id, unique_file_name)
            text, keyboard = menus.get_book()
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            text, keyboard = menus.get_book(True)
    
    bot.delete_message(message.chat.id, message.id)
    bot.edit_message_text(chat_id=user_id, message_id=user[2], text=text, reply_markup=keyboard, parse_mode="MarkdownV2")

if __name__ == "__main__":
    # start_polling()
    bot.polling()