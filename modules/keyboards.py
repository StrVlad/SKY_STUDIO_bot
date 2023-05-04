import datetime

from aiogram.types import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from datetime import timedelta, date, time


def _date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def _hour_range(start_hour, end_hour):
    for n in range(start_hour, end_hour + 1):
        yield n


def start_keyboard(*, is_admin=False):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text='Инфо'))
    keyboard.add(KeyboardButton(text='Запись'))
    keyboard.add(KeyboardButton(text="Отменить бронь"))
    if is_admin:
        keyboard.add(KeyboardButton(text="Админ"))
    keyboard = keyboard.as_markup()
    keyboard.resize_keyboard = True
    keyboard.one_time_keyboard = True
    return keyboard


def hours_keyboard(start_hour: time, end_hour: time, date_: datetime.datetime):
    keyboard = InlineKeyboardBuilder()
    buttons = []
    start_hour = start_hour.hour
    end_hour = end_hour.hour
    if date_.date() == datetime.date.today():
        if start_hour < datetime.datetime.now().time().hour + 1 \
                if datetime.datetime.now().time().minute > 0 else 0:
            start_hour = datetime.datetime.now().time().hour + 1 \
                if datetime.datetime.now().time().minute > 0 else 0
    for hour in _hour_range(start_hour, end_hour):
        buttons.append(InlineKeyboardButton(text=f"{hour}:00", callback_data=hour))
    keyboard.row(*buttons[:len(buttons) // 3])
    keyboard.row(*buttons[len(buttons) // 3:len(buttons) // 3 * 2])
    keyboard.row(*buttons[len(buttons) // 3 * 2:])
    return keyboard.as_markup()


def admin_keyboard():
    keyboard = ReplyKeyboardBuilder()
    row = [
        KeyboardButton(text="Посмотреть ближайшие брони"),
    ]
    keyboard.row(*row)
    row = [
        KeyboardButton(text="Просмотреть брони"),
        KeyboardButton(text="😺")
    ]
    keyboard.row(*row)
    row = [
        KeyboardButton(text="Забанить пользователя"),
        KeyboardButton(text="Разбанить пользователя")
    ]
    keyboard.row(*row)
    row = [
        KeyboardButton(text="Заблокировать день"),
        KeyboardButton(text="Заблокировать час"),
    ]
    keyboard.row(*row)
    keyboard = keyboard.as_markup()
    keyboard.resize_keyboard = True
    keyboard.one_time_keyboard = True
    return keyboard


def admin_cancel():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Вернуться"))
    keyboard = keyboard.as_markup()
    keyboard.resize_keyboard = True
    return keyboard


class InlineCalendar:
    @staticmethod
    async def _get_days(markup: InlineKeyboardMarkup):
        number_of_days = len(markup.inline_keyboard[0] + markup.inline_keyboard[1]) - 1
        date_ = None
        for button in markup.inline_keyboard[0] + markup.inline_keyboard[1]:
            try:
                date_ = datetime.datetime.strptime(button.callback_data, "%Y-%m-%d")
                break
            except ValueError:
                number_of_days -= 1
                pass

        return date_.date(), number_of_days

    @staticmethod
    async def create_keyboard(from_day: date, to_day: date):
        keyboard = InlineKeyboardBuilder()
        buttons = []
        if not (from_day <= datetime.date.today()):
            buttons.append(InlineKeyboardButton(text="<<", callback_data="left"))
        else:
            from_day = datetime.date.today()
        for date_ in _date_range(from_day, to_day):
            buttons.append(InlineKeyboardButton(text=date_.strftime("%d.%m"), callback_data=date_.strftime("%Y-%m-%d")))
        keyboard.row(*buttons[:len(buttons) // 2 + 1], InlineKeyboardButton(text=">>", callback_data="right"))
        keyboard.row(*buttons[len(buttons) // 2 + 1:])
        return keyboard.as_markup()

    @staticmethod
    async def update_keyboard(callback_data, keyboard):
        match callback_data:
            case "left":
                first_day, number_of_days = await InlineCalendar._get_days(keyboard)
                return await InlineCalendar.create_keyboard(first_day - timedelta(days=number_of_days),
                                                            first_day - timedelta(days=1))
            case "right":
                first_day, number_of_days = await InlineCalendar._get_days(keyboard)
                return await InlineCalendar.create_keyboard(first_day + timedelta(days=number_of_days),
                                                            first_day + timedelta(days=number_of_days * 2 - 1))
            case _:
                return callback_data
