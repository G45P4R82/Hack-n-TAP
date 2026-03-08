import sqlite3
import os
from datetime import datetime

DB_FILE = "rfid_system.db"

class SQLiteDatabase:
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.initialize_admin()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                registered_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT,
                name TEXT,
                timestamp TEXT,
                display_date TEXT,
                display_time TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def initialize_admin(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", ("admin",))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "tijolo22"))
            self.conn.commit()

    def check_credentials(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        return cursor.fetchone() is not None

    def get_all_tags(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tags ORDER BY registered_at DESC")
        rows = cursor.fetchall()
        return {row['id']: {'name': row['name'], 'registered_at': row['registered_at']} for row in rows}

    def validate_tag(self, tag_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
        row = cursor.fetchone()
        if row:
            return {'name': row['name'], 'registered_at': row['registered_at']}
        return None

    def add_tag(self, tag_id, name, registered_at=None, skip_check=False):
        if not skip_check and self.validate_tag(tag_id):
            return False, "Tag já cadastrada!"
        if not registered_at:
            registered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO tags (id, name, registered_at) VALUES (?, ?, ?)", (tag_id, name, registered_at))
            self.conn.commit()
            return True, "Tag cadastrada com sucesso!"
        except sqlite3.Error as e:
            return False, f"Erro ao cadastrar: {e}"

    def update_tag(self, tag_id, new_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name, tag_id))
            self.conn.commit()
            if cursor.rowcount > 0:
                return True, "Nome atualizado!"
            return False, "Tag não encontrada!"
        except sqlite3.Error as e:
            return False, str(e)

    def remove_tag(self, tag_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            self.conn.commit()
            return True, "Tag removida!"
        except sqlite3.Error as e:
            return False, str(e)

    def add_history_entry(self, tag_id, name, timestamp=None, display_date=None, display_time=None):
        now = datetime.now()
        if not timestamp: timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if not display_date: display_date = now.strftime("%d/%m/%Y")
        if not display_time: display_time = now.strftime("%H:%M:%S")
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO history (tag_id, name, timestamp, display_date, display_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (tag_id, name, timestamp, display_date, display_time))
        self.conn.commit()

    def get_history_entries(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM history ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]
