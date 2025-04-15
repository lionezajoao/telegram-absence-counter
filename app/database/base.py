import os
import psycopg2

class Base:
    def __init__(self):
        self.host = os.getenv("PG_HOST")
        self.base_database = os.getenv("PG_BASE_DATABASE")
        self.user = os.getenv("PG_USER")
        self.password = os.getenv("PG_PASSWORD")
        self.port = os.getenv("PG_PORT")

    def connect(self, database: str = None):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                database=self.base_database if database is None else database,
                user=self.user,
                password=self.password,
                port=self.port
            )

            self.cursor = self.conn.cursor()
            print("Database connection established successfully.")
        except Exception as e:
            print(f"Error connecting to the database: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Database connection closed.")

    def execute_query(self, query, params=None):
        try:
            print(f"Executing query: {query} with params: {params}")
            self.cursor.execute(query, params)
            self.conn.commit()
            print("Query executed successfully.")
        except Exception as e:
            print(f"Error executing query: {e}")
            self.conn.rollback()

    def fetch_all(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def fetch_one(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return result
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None    
