import os
from dotenv import load_dotenv
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

from messages import text_messages
from models import *

load_dotenv()

db.connect()
db.create_tables([User, Category, Expense])

bot = telebot.TeleBot(os.environ.get('TOKEN'))


def gen_main_keyboard():
    """Создание основной клавиатуры"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton('Внести расход' + u'\U0001F4B0'))
    markup.add(KeyboardButton('Статистика' + u'\U0000231B'))

    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Отправляем приветственное сообщение и помощь по работе с ботом"""
    name = message.from_user.first_name
    bot.send_message(message.chat.id, text_messages['welcome'].format(name=name), reply_markup=gen_main_keyboard())


bot.polling()
