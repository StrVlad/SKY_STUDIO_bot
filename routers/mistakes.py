from aiogram import Router, types
from aiogram.filters import StateFilter

router = Router()


@router.message(StateFilter(None))
async def mistake_none(message: types.Message):
    await message.answer("Не совсем понял вас")


@router.message()
async def mistake(message: types.Message):
    await message.answer("Не совсем понял вас, если хотите отменить напишите /cancel")
