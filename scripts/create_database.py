from app.database.bot_db import BotDB

if __name__ == "__main__":
    db = BotDB()
    db.create_database()
    db.create_tables()
