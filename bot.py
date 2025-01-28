import telebot
import threading
import traceback

import config
from scripts import *
import menus


VERSION="0.3.3"
print(VERSION)
bot = telebot.TeleBot(config.API)
ALLOWED_EXTENSIONS = {'.txt'}

commands = [  # КОМАНДЫ
telebot.types.BotCommand("start", "Перезапуск бота"),
telebot.types.BotCommand("help", "Помощь"),
telebot.types.BotCommand("settings", "Настройки"),
]
bot.set_my_commands(commands)


def step_handler(message, menu_id, call, data, function_name, open_menus, attr=None):
    bot.delete_message(message.chat.id, message.message_id)
    menu_function = globals().get(function_name)
    success = menu_function(message, call, data)
    if success == True: text, keyboard = open_menus[0](*attr)
    elif success == False: text, keyboard = open_menus[1](*attr)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=menu_id, text=text, reply_markup=keyboard, parse_mode="MarkdownV2")


# ОБРАБОТКА КОМАНД
@bot.message_handler()
def command_handler(message):
    bot.delete_message(message.chat.id, message.id)
    user_id = message.chat.id
    user = SQL_request("SELECT * FROM users WHERE id = ?", (int(user_id),))
    text, keyboard = menus.loading()
    if user: bot.edit_message_text(chat_id=user_id, message_id=user[2], text=text, reply_markup=keyboard, parse_mode="MarkdownV2")
    if message.text == "/start":
        menu_id = registration(message)
        if menu_id:
            try: bot.delete_message(message.chat.id, menu_id)
            except: pass
        text, keyboard = menus.main(None, message)
        bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode="MarkdownV2")
    else:
        if message.text == "/settings": text, keyboard = menus.settings()
        elif message.text == "/help": text, keyboard = menus.help()
        bot.edit_message_text(chat_id=user_id, message_id=user[2], text=text, reply_markup=keyboard, parse_mode="MarkdownV2")


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
        text, keyboard = open_menu(call)

    elif (call.data).split(":")[0] == "open_book":
        text, keyboard = menus.open_book(call, (call.data).split(":")[1])

    elif (call.data).split(":")[0] == "read":
        data = call.data.split(':')
        book_id = int(data[1])
        current_page = int(data[2])
        text, keyboard = menus.read_book(call, book_id, current_page)

    elif (call.data).split("-")[0] == "edit":
        type_edit = (call.data).split(":")[0].split("-")[1]
        book_id = (call.data).split(":")[1]
        data = [type_edit, book_id]
        open_menus = [getattr(menus, "open_book"), getattr(menus, "edit_book")]
        attr = [call, book_id]
        text, keyboard = menus.edit_book(call, book_id, type_edit)
        bot.register_next_step_handler(call.message, step_handler, menu_id, call, data, "rename_book_data", open_menus, attr)

    elif (call.data).split(":")[0] == "tg_pages":
        tg_pages = (call.data).split(":")[1]
        update_config(user_id, tg_pages)
        text, keyboard = menus.settings()

    else:
        open_menu = getattr(menus, call.data)
        text, keyboard = open_menu(call)

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
            unique_file_name = save_file(message.document, bot)
            add_book(user_id, unique_file_name)
            text, keyboard = menus.get_book()
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            text, keyboard = menus.get_book(True)
    
    bot.delete_message(message.chat.id, message.id)
    bot.edit_message_text(chat_id=user_id, message_id=user[2], text=text, reply_markup=keyboard, parse_mode="MarkdownV2")

if __name__ == "__main__":
    start_polling()
    # bot.polling()
