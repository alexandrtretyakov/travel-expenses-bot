import os
from dotenv import load_dotenv
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from messages import text_messages
from models import *

load_dotenv()

db.connect()
db.create_tables([User, Category, Expense])

bot = telebot.TeleBot(os.environ.get('TOKEN'))

category = ''
user = ''


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


# Расходы

@bot.message_handler(func=lambda msg: msg.text == 'Внести расход' + u'\U0001F4B0')
def send_category(message):
    """Вывод выбора категории"""
    global user

    user = User.get_or_create(telegram_id=message.from_user.id)[0]
    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    categories = Category.select()

    for category in categories:
        markup.add(InlineKeyboardButton(category.name, callback_data=f'category__{category._pk}'))

    bot.send_message(message.chat.id, text_messages['select_category'], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('category'))
def callback_query(call):
    """Получение суммы расхода от пользователя"""
    global category
    category = call.data.split("__")[1]

    msg = bot.send_message(call.message.chat.id, text_messages['enter_amount'])
    bot.register_next_step_handler(msg, make_expense)


def make_expense(message):
    """Занесение расхода в базу"""
    Expense.create(category_id=category, user_id=user, amount=message.text)

    bot.send_message(message.chat.id, text_messages['enter_amount_success'], reply_markup=gen_main_keyboard())


# Статистика

@bot.message_handler(func=lambda msg: msg.text == 'Статистика' + u'\U0000231B')
def send_category(message):
    """Выбор периода для статистики"""
    global user

    user = User.get_or_create(telegram_id=message.from_user.id)[0]

    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton('За сегодня', callback_data='today'))
    markup.add(InlineKeyboardButton('За всю поездку', callback_data='trip'))
    markup.add(InlineKeyboardButton('Удалить данные текущей поездки', callback_data='delete'))

    bot.send_message(message.chat.id, text_messages['select_statistics_period'], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'today')
def callback_query(call):
    """Вывод статистики за день"""
    qs = Expense. \
        select(Category.name, fn.SUM(Expense.amount)). \
        join(Category). \
        where((Expense.created_at > datetime.datetime.today().strftime('%Y-%m-%d')) &
              (Expense.user_id == user)). \
        group_by(Category.name)

    message = u'Расходы сегодня:\n\n'

    for q in qs:
        message += u'{}: {} руб.\n'.format(q.category_id.name, q.amount)

    query = Expense. \
        select(fn.SUM(Expense.amount)). \
        where((Expense.created_at > datetime.datetime.today().strftime('%Y-%m-%d')) &
              (Expense.user_id == user))
    sum = query.scalar()

    if sum is None:
        sum = 0

    message += u'\nВсего израсходовано: {} рублей'.format(sum)

    bot.send_message(call.message.chat.id, message, reply_markup=gen_main_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'trip')
def callback_query(call):
    """Вывод статистики за поездку"""
    qs = Expense. \
        select(Category.name, fn.SUM(Expense.amount)). \
        join(Category). \
        where(Expense.user_id == user). \
        group_by(Category.name)

    message = u'Расходы за весь отпуск:\n\n'

    for q in qs:
        message += u'{}: {} руб.\n'.format(q.category_id.name, q.amount)

    query = Expense. \
        select(fn.SUM(Expense.amount)). \
        where(Expense.user_id == user)
    sum = query.scalar()

    if sum is None:
        sum = 0

    print(sum)

    message += u'\nВсего израсходовано: {} рублей'.format(sum)

    bot.send_message(call.message.chat.id, message, reply_markup=gen_main_keyboard())


@bot.callback_query_handler(func=lambda call: call.data == 'delete')
def callback_query(call):
    """Удаляет все расходы для текущего пользователя"""
    query = Expense.delete().where(Expense.user_id == user)
    query.execute()

    bot.send_message(call.message.chat.id, text_messages['delete_success'], reply_markup=gen_main_keyboard())


bot.polling()
