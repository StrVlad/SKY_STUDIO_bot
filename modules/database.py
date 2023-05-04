import sqlite3
from datetime import datetime


class DB:
    def __init__(self):
        self._conn = sqlite3.connect('sky_studio_schedule.db', check_same_thread=False)
        self._cursor = self._conn.cursor()

    def book_time_slot(self, date: datetime, client_id: int, client_name: str) -> bool:
        try:
            self._cursor.execute('INSERT INTO `schedule` (client_id, client_name, date) VALUES (?, ?, ?)',
                                 (client_id, client_name, date))
            self._conn.commit()
        except sqlite3.IntegrityError:
            return False
        return True

    def get_ten_books(self, date: datetime):
        rows = self._cursor.execute("SELECT * FROM `schedule` WHERE date >= ? LIMIT 10", (date,))
        return rows.fetchall()

    def check_book(self, client_id):
        rows = self._cursor.execute('SELECT * FROM `schedule` WHERE (client_id = ?)', (client_id,))
        return len(rows.fetchall()) > 4

    def check_banned(self, client_id):
        self._cursor.execute("SELECT * FROM `banned` WHERE (banned_id = ?)", (client_id,))
        return bool(self._cursor.fetchone())

    def get_book_in_time_window(self, start_date: datetime, end_date: datetime):
        rows = self._cursor.execute("SELECT * FROM `schedule` WHERE (date >= ?) AND (date <= ?)",
                                    (start_date, end_date,))
        return rows.fetchall()

    def block_book_in_time_slot(self, date: datetime):
        id = self._cursor.execute("SELECT client_id FROM `schedule` WHERE date = ?", (date,)).fetchone()
        self._cursor.execute("REPLACE INTO `schedule` (date) VALUES (?)", (date,))
        self._conn.commit()
        return id[0] if id else None

    def get_id_by_username(self, username: str):
        self._cursor.execute("SELECT client_id FROM `schedule` WHERE (client_name = ?)", (username,))
        return self._cursor.fetchone()

    def get_id_by_username_from_banned(self, username: str):
        self._cursor.execute("SELECT banned_id FROM `banned` WHERE (banned_name = ?)", (username,))
        return self._cursor.fetchone()

    def add_banned(self, client_id: int, client_name: str):
        self._cursor.execute("INSERT INTO `banned` (banned_id, banned_name) VALUES (?,?)", (client_id, client_name))
        self._cursor.execute("DELETE FROM `schedule` WHERE client_id = ?", (client_id,))
        self._conn.commit()

    def set_mentioned(self, is_mentioned: bool, client_id: int):
        self._cursor.execute("UPDATE `schedule` SET (is_mentioned) = (?) WHERE client_id = ? ",
                             (is_mentioned, client_id))
        self._conn.commit()

    def delete_book(self, date: int):
        self._cursor.execute("DELETE FROM `schedule` WHERE date = ?", (date,))
        self._conn.commit()

    def delete_banned(self, banned_id: int):
        self._cursor.execute("DELETE FROM `banned` WHERE banned_id = ?", (banned_id,))
        self._conn.commit()

    def get_books_by_id(self, client_id: int):
        books = self._cursor.execute("SELECT * FROM `schedule` WHERE client_id = ?", (client_id,)).fetchall()
        return books

    def truncate_database(self):
        self._cursor.execute("DELETE FROM `banned`")
        self._cursor.execute("DELETE FROM `schedule`")
        self._cursor.execute("UPDATE `sqlite_sequence` SET `seq` = 0 WHERE `name` = 'banned'")
        self._cursor.execute("UPDATE `sqlite_sequence` SET `seq` = 0 WHERE `name` = 'schedule'")
        self._conn.commit()
