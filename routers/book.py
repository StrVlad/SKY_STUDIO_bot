from aiogram import Router, types, F
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from modules.states import Book
from modules.database import DB
import datetime
import aiogram
from modules import keyboards

from configs.config import admins

router = Router()

db = DB()

calendar = keyboards.InlineCalendar()


@router.message(Text("запись", ignore_case=True))
async def ask_visit_date(message: types.Message, state: FSMContext) -> None:
    if db.check_book(message.from_user.id):
        await message.answer(text="Вы уже зарегистрировались", reply_markup=keyboards.start_keyboard())
        return
    if db.check_banned(message.from_user.id):
        await message.answer(text="Вы забанены", reply_markup=keyboards.start_keyboard())
        return

    await message.answer(text="Выберите дату посещения",
                         reply_markup=await calendar.create_keyboard(
                             datetime.date.today(), datetime.date.today() + datetime.timedelta(days=5)))
    await state.set_state(Book.date)


@router.callback_query(StateFilter(Book.date))
async def date_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await calendar.update_keyboard(callback.data, callback.message.reply_markup)
    if isinstance(data, types.InlineKeyboardMarkup):
        await callback.message.edit_reply_markup(reply_markup=data)
        return
    await state.update_data(date=data)
    await state.set_state(Book.time)
    await callback.message.answer("Выберите время посещения (5 макс)",
                                  reply_markup=keyboards.hours_keyboard(datetime.time(hour=12),
                                                                        datetime.time(hour=23),
                                                                        datetime.datetime.strptime(data, "%Y-%m-%d")))


@router.callback_query(StateFilter(Book.time))
async def time_handler(callback: types.CallbackQuery, state: FSMContext, bot: aiogram.Bot):
    await state.update_data(time=callback.data)
    data = await state.get_data()
    try:
        date = datetime.datetime.strptime(data["date"] + data["time"], "%Y-%m-%d%H")
    except ValueError:
        return
    result = db.book_time_slot(date, callback.from_user.id, callback.from_user.username)
    if result:
        await callback.message.answer(f"Вы зарегистрированы на {date.strftime('%d.%m')} на {data['time']}:00",
                                      reply_markup=keyboards.start_keyboard())
        for admin in admins:
            await bot.send_message(admin,
                                   f"Забронировано на {data['time']}:00, {date.strftime('%d.%m')}, {callback.from_user.username}")
        await state.clear()
    else:
        await callback.message.answer(f"Время {data['time']} в этот день уже занято, попробуйте другое")


@router.message(Text("отменить бронь", ignore_case=True))
async def unbook(message: types.Message, state: FSMContext):
    books = db.get_books_by_id(message.from_user.id)
    books_message = ""
    i = 0
    await state.update_data(books=books)
    for book in books:
        i += 1
        books_message += f"{i}: {book[2]}\n"
    await message.answer(f"Ваши брони:\n{books_message}Отправьте номер которой хотите отменить")
    await state.set_state(Book.unbook)


@router.message(F.text.regexp(r'[1-5]'), StateFilter(Book.unbook))
async def unbook_unbook(message: types.Message, state: FSMContext):
    books = (await state.get_data())["books"]
    try:
        book = books[int(message.text) - 1]
    except IndexError:
        await message.answer("Брони под таким номером нет, попробуйте ещё раз")
        return
    db.delete_book(book[2])
    await state.set_state(None)
    await message.answer("Успешно отменено!", reply_markup=keyboards.start_keyboard())
