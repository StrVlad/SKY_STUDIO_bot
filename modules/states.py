from aiogram.fsm.state import StatesGroup, State


class Book(StatesGroup):
    unbook = State()
    date = State()
    time = State()


class Admin(StatesGroup):
    unban_start = State()
    start = State()
    bookcheck_date = State()
    bookcheck_time = State()
    ban_start = State()
    block_day = State()
    block_hour = State()
    block_hour_time = State()
