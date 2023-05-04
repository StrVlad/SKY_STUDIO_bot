from aiogram import Router, types, F, Bot
from aiogram.filters import Text, StateFilter, Command
from aiogram.fsm.context import FSMContext
from configs.config import admins
from modules import keyboards
from modules.database import DB
from modules.states import Admin
import datetime
import requests

router = Router()

DATABASE = DB()

calendar = keyboards.InlineCalendar()


def _hour_range(start_hour, end_hour):
    for n in range(start_hour, end_hour + 1):
        yield n


@router.message(StateFilter(Admin), Text(["вернуться"], ignore_case=True))
@router.message(F.from_user.id.in_(admins), Text(["админ", "админка"], ignore_case=True))
@router.message(F.from_user.id.in_(admins), Command("admin"))
async def admin(message: types.Message, state: FSMContext):
    await state.set_state(Admin.start)
    await message.answer(text="Привет, Хозяин", reply_markup=keyboards.admin_keyboard())


@router.message(StateFilter(Admin.start), Text("😺"))
async def cat(message: types.Message):
    r = requests.get("https://cataas.com/cat")
    if r.status_code == 200:
        with open("cat.png", 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    cat = types.FSInputFile("cat.png")
    await message.answer_photo(photo=cat, reply_markup=keyboards.admin_keyboard())


# Посмотреть ближайшие брони

@router.message(StateFilter(Admin.start), Text("посмотреть ближайшие брони", ignore_case=True))
async def ten_books(message: types.Message):
    books = DATABASE.get_ten_books(date=datetime.datetime.now())
    books_message = ""
    i = 0
    for book in books:
        i += 1
        books_message += f"{i}: {book[1]} на {book[2]}\n"
    if not books:
        await message.answer("Нет броней", reply_markup=keyboards.admin_keyboard())
        return
    await message.answer(f"Ближайшие брони:\n{books_message}", reply_markup=keyboards.admin_keyboard())


@router.message(StateFilter(Admin.start), Text("забанить пользователя", ignore_case=True))
async def ban_start(message: types.Message, state: FSMContext):
    await message.answer(text="Введите ник пользователя для бана (без @)", reply_markup=keyboards.admin_cancel())
    await state.set_state(Admin.ban_start)


@router.message(StateFilter(Admin.unban_start))
async def ban(message: types.Message, state: FSMContext):
    unban_username = message.text
    client_id = DATABASE.get_id_by_username_from_banned(unban_username)
    if not client_id:
        await message.answer("Пользователь не найден, попробуйте ещё раз", reply_markup=keyboards.admin_cancel())
        return
    DATABASE.delete_banned(int(client_id[0]))
    await message.answer("Пользователь разбанен", reply_markup=keyboards.admin_keyboard())
    await state.set_state(Admin.start)


@router.message(StateFilter(Admin.start), Text("разбанить пользователя", ignore_case=True))
async def ban_start(message: types.Message, state: FSMContext):
    await message.answer(text="Введите ник пользователя для разбана (без @)", reply_markup=keyboards.admin_cancel())
    await state.set_state(Admin.unban_start)


@router.message(StateFilter(Admin.ban_start))
async def ban(message: types.Message, state: FSMContext):
    ban_username = message.text
    client_id = DATABASE.get_id_by_username(ban_username)
    if not client_id:
        await message.answer("Пользователь не найден, попробуйте ещё раз", reply_markup=keyboards.admin_cancel())
        return
    DATABASE.add_banned(int(client_id[0]), ban_username)
    await message.answer("Пользователь забанен", reply_markup=keyboards.admin_keyboard())
    await state.set_state(Admin.start)


@router.message(StateFilter(Admin.start), Text("заблокировать час", ignore_case=True))
async def block_day(message: types.Message, state: FSMContext):
    await message.answer("Выберите день", reply_markup=await calendar.create_keyboard(
        datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)))
    await state.set_state(Admin.block_hour)


@router.callback_query(StateFilter(Admin.block_hour))
async def date_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await calendar.update_keyboard(callback.data, callback.message.reply_markup)
    if isinstance(data, types.InlineKeyboardMarkup):
        await callback.message.edit_reply_markup(reply_markup=data)
        return
    await state.update_data(date=data)
    await state.set_state(Admin.block_hour_time)
    await callback.message.answer("Выберите время",
                                  reply_markup=keyboards.hours_keyboard(datetime.time(hour=12),
                                                                        datetime.time(hour=23),
                                                                        datetime.datetime.strptime(data, "%Y-%m-%d")))


@router.callback_query(StateFilter(Admin.block_hour_time))
async def block_hour_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(time=callback.data)
    data = await state.get_data()
    try:
        date = datetime.datetime.strptime(data["date"] + data["time"], "%Y-%m-%d%H")
    except ValueError:
        return
    client_id = DATABASE.block_book_in_time_slot(date)
    if client_id:
        await bot.send_message(str(client_id), f"Извините, ваша бронь на {date.hour}:00 ({date.date()}) отменена.")
    await callback.message.answer("Заблокировано!")


@router.message(StateFilter(Admin.start), Text("заблокировать день", ignore_case=True))
async def block_day(message: types.Message, state: FSMContext):
    await message.answer("Выберите день", reply_markup=await calendar.create_keyboard(
        datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)))
    await state.set_state(Admin.block_day)


@router.callback_query(StateFilter(Admin.block_day))
async def block_day_handler(callback: types.CallbackQuery, bot: Bot):
    data = await calendar.update_keyboard(callback.data, callback.message.reply_markup)
    if isinstance(data, types.InlineKeyboardMarkup):
        await callback.message.edit_reply_markup(reply_markup=data)
        return
    date = datetime.datetime.strptime(data, "%Y-%m-%d")
    for hour in _hour_range(date.hour + 12, date.hour + 23):
        client_id = DATABASE.block_book_in_time_slot(date + datetime.timedelta(hours=hour))
        if client_id:
            await bot.send_message(str(client_id), f"Извините, ваша бронь на {hour}:00 ({date.date()}) отменена.")

    await callback.message.answer("Заблокировано!", reply_markup=keyboards.admin_cancel())


@router.message(StateFilter(Admin.start), Text("просмотреть брони", ignore_case=True))
async def bookcheck(message: types.Message, state: FSMContext):
    await message.answer(text="Выберите день",
                         reply_markup=await calendar.create_keyboard(
                             datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)))
    await state.set_state(Admin.bookcheck_date)


@router.callback_query(StateFilter(Admin.bookcheck_date))
async def date_handler(callback: types.CallbackQuery):
    data = await calendar.update_keyboard(callback.data, callback.message.reply_markup)
    if isinstance(data, types.InlineKeyboardMarkup):
        await callback.message.edit_reply_markup(reply_markup=data)
        return
    date = datetime.datetime.strptime(data, "%Y-%m-%d")
    result = DATABASE.get_book_in_time_window(date, date + datetime.timedelta(hours=23))
    if not result:
        await callback.message.answer(f"Никто не забронировал",
                                      reply_markup=keyboards.admin_cancel())
    else:
        answer = ""
        for row in result:
            answer += f"Забронировал {row[1]}, на {row[2][11:][:5]}\n"
        await callback.message.answer(answer, reply_markup=keyboards.admin_cancel())
