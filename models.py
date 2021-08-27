import os
import datetime
from peewee import *
from dotenv import load_dotenv

load_dotenv()

db = SqliteDatabase(os.environ.get('DATABASE_NAME'))


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    telegram_id = IntegerField(unique=True)


class Category(BaseModel):
    name = CharField(max_length=150)


class Expense(BaseModel):
    category_id = ForeignKeyField(Category)
    user_id = ForeignKeyField(User, related_name='expenses')
    amount = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
