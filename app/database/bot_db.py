import os
from datetime import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from app.database.base import Base

class BotDB:
    def __init__(self):
        self.db = Base()
        self.database = os.environ.get("PG_DATABASE")

    def create_database(self):
        self.db.connect()
        self.db.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = self.db.conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{self.database}';")
        exists = cursor.fetchone()
        if exists:
            print(f"Database {self.database} already exists.")
            return
        
        cursor.execute(f"CREATE DATABASE {self.database};")
        print(f"Database {self.database} created successfully.")
        cursor.close()
        self.db.close()

    def create_tables(self):
        self.db.connect(self.database)

        query_path = os.path.join(os.path.dirname(__file__), 'queries/create_tables.sql')

        with open(query_path, 'r') as file:
            query = file.read()

        self.db.execute_query(query)
        print("Tables created successfully.")
        self.db.close()

    def insert_chat(self, chat_id: str, username: str = None, first_name: str = None):
        self.db.connect(self.database)
        query = "INSERT INTO chats (id, username, first_name, ts) VALUES (%s, %s, %s, %s);"
        self.db.execute_query(query, (chat_id, username, first_name, datetime.now()))
        print(f"Chat {chat_id} inserted successfully.")
        self.db.close()

    def check_if_chat_exists(self, chat_id: str):
        self.db.connect(self.database)
        query = "SELECT * FROM chats WHERE id = %s;"
        result = self.db.fetch_one(query, (str(chat_id),))
        if result:
            print(f"Chat {chat_id} already exists.")
            self.db.close()
            return True
        else:
            print(f"Chat {chat_id} does not exist.")
            self.db.close()
            return False

    def insert_class(self, class_id: str, name: str, semester: str = None):
        self.db.connect(self.database)

        query = "SELECT * FROM classes WHERE class_id = %s;"
        result = self.db.fetch_one(query, (class_id,))
        if result:
            print(f"Class {class_id} already exists.")
            self.db.close()
            return
        
        query = "INSERT INTO classes (id, name, semester) VALUES (%s, %s, %s);"
        self.db.execute_query(query, (class_id, name, semester))
        print(f"Class {class_id} inserted successfully.")
        self.db.close()
