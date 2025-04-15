from app.database.bot_db import BotDB

class BotHandler:
    def __init__(self):
        self.db = BotDB()

    def insert_new_chat(self, chat_id: str, username: str = None, first_name: str = None) -> None:
        """
        Inserts a new chat into the database.
        :param chat_id: The ID of the chat.
        :param username: The username of the chat.
        :param first_name: The first name of the chat.
        :return: None
        """

        if self.db.check_if_chat_exists(chat_id):
            print(f"Chat {chat_id} already exists in the database.")
            return
        
        self.db.insert_chat(chat_id, username, first_name)
        print(f"Chat {chat_id} inserted into the database.")
