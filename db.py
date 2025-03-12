import sqlite3
from typing import Dict, Optional

class Database:
    def __init__(self, db_path: str = 'config.db'):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_channels (
                    server_id INTEGER PRIMARY KEY,
                    channel_id INTEGER NOT NULL
                )
            ''')
            conn.commit()

    def add_notification_channel(self, server_id: int, channel_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO notification_channels (server_id, channel_id)
                VALUES (?, ?)
            ''', (server_id, channel_id))
            conn.commit()

    def remove_notification_channel(self, server_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM notification_channels
                WHERE server_id = ?
            ''', (server_id,))
            conn.commit()

    def get_notification_channels(self) -> Dict[int, int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT server_id, channel_id FROM notification_channels')
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_channel_id(self, server_id: int) -> Optional[int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT channel_id FROM notification_channels
                WHERE server_id = ?
            ''', (server_id,))
            result = cursor.fetchone()
            return result[0] if result else None
