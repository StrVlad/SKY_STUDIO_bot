import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from os import environ
from routers import mistakes, book, admin_panel, notifications
from modules import keyboards
from configs.config import admins

bot = Bot(token=environ["TOKEN"])
dp = Dispatcher(storage=MemoryStorage())


@dp.message(Text(["отмена", "отменить"], ignore_case=True))
@dp.message(Command("cancel"))
@dp.message(Text(["начало", "старт"], ignore_case=True))
@dp.message(Command('start'))
async def start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.reply("Добро пожаловать в SKY STUDIO!",
                        reply_markup=keyboards.start_keyboard(is_admin=message.from_user.id in admins))


@dp.message(Text(["инфо"], ignore_case=True))
async def info(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.reply("Заглушка",
                        reply_markup=keyboards.start_keyboard(is_admin=message.from_user.id in admins))


if __name__ == '__main__':
    dp.include_router(admin_panel.router)
    dp.include_router(book.router)
    dp.include_router(mistakes.router)
    loop = asyncio.new_event_loop()
    loop.create_task(notifications.loop(bot))
    loop.create_task(dp.start_polling(bot))
    loop.run_forever()
