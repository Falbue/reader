from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot import types
from scripts import *

# Загрузка локализации из JSON файла
with open('localization.json', 'r', encoding='utf-8') as file:
    locale = json.load(file)

def main():
    text = markdown(locale["menu"]["main"])
    btn_stat = InlineKeyboardButton(locale["button"]["stat"], callback_data="stat")
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(btn_stat)
    return text, keyboard

def get_book(error=False):
    text = markdown(locale["menu"]["get_book"])
    if error == True: text = markdown(locale["menu"]["get_book_error"])
    btn_return = InlineKeyboardButton(locale["button"]["return"], callback_data="return:main")
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(btn_return)
    return text, keyboard