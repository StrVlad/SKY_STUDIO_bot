import asyncio
import datetime

import aiogram

from configs.config import admins

from modules.database import DB

db = DB()


async def loop(bot: aiogram.Bot):
    while True:
        start_date = datetime.datetime.now() - datetime.timedelta(hours=1, minutes=30)
        end_date = datetime.datetime.now() + datetime.timedelta(hours=1, minutes=30)
        books = db.get_book_in_time_window(start_date, end_date)
        for book in books:
            book_date = datetime.datetime.strptime(book[2], "%Y-%m-%d %H:%M:%S")
            if book_date < datetime.datetime.now():
                db.delete_book(book[2])
                continue

            if book[4] or not book[3]:
                continue

            await bot.send_message(book[3],
                                   f"У вас бронь на {book_date.time().hour}:00. Пожалуйста, приходите вовремя")
            for admin in admins:
                await bot.send_message(admin, f"Забронировано на {book_date.time().hour}:00, {book[1]}")

            db.set_mentioned(True, book[3])
        await asyncio.sleep(5)
