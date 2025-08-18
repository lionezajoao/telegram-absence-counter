import os
import uuid
import sys
import logging
from datetime import datetime

from app.database.base import Base

logger = logging.getLogger(__name__)

class BotDB:
    """Manages all database operations for the bot."""

    def __init__(self):
        """Initializes the database connection."""
        self.db = Base()
        self.database = os.environ.get("PG_DATABASE")
        self.db.connect(self.database)
        logger.info("BotDB initialized and connected to database.")

    def close(self):
        """Closes the database connection."""
        self.db.close()
        logger.info("BotDB database connection closed.")

    def insert_chat(self, chat_id: str, username: str = None, first_name: str = None):
        """Inserts a new chat into the database."""
        try:
            query = "INSERT INTO chats (id, username, first_name, ts) VALUES (%s, %s, %s, %s);"
            now = datetime.now().time()
            self.db.execute_query(query, (chat_id, username, first_name, now))
            logger.info(f"Chat {chat_id} inserted successfully.")
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error inserting chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def check_if_chat_exists(self, chat_id: str) -> bool:
        """Checks if a chat already exists in the database."""
        try:
            query = "SELECT id FROM chats WHERE id = %s;"
            result = self.db.fetch_one(query, (str(chat_id),))
            exists = result is not None
            logger.debug(f"Checking if chat {chat_id} exists: {exists}")
            return exists
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error checking if chat {chat_id} exists on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def insert_class(self, class_id: str, name: str, semester: str = None):
        """Inserts a new class, avoiding duplicates."""
        try:
            exists_query = "SELECT id FROM classes WHERE class_id = %s;"
            logger.info(f"Checking if class {class_id} already exists.")
            if self.db.fetch_one(exists_query, (class_id,)):
                logger.info(f"Class {class_id} already exists, skipping insertion.")
                return

            insert_query = "INSERT INTO classes (id, class_id, name, semester) VALUES (%s, %s, %s, %s);"
            generated_uuid = str(uuid.uuid4())
            self.db.execute_query(insert_query, (generated_uuid, class_id, name, semester))
            logger.info(f"Class '{name}' ({class_id}) inserted successfully with UUID {generated_uuid}.")
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error inserting class {class_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def insert_absence(self, chat_id: str, class_id: str):
        """Increments absence counter for a chat and class, or creates a new entry."""
        try:
            class_exists_query = "SELECT id FROM classes WHERE class_id = %s;"
            class_uuid_result = self.db.fetch_one(class_exists_query, (class_id,))
            if not class_uuid_result:
                logger.warning(f"Attempted to add absence for non-existent class_id: {class_id}")
                return False
            class_uuid = class_uuid_result[0]

            absence_query = "SELECT counter FROM absences WHERE chat_id = %s AND class_id = %s;"
            current_absence = self.db.fetch_one(absence_query, (chat_id, class_uuid))

            if current_absence:
                new_counter = current_absence[0] + 1
                update_query = "UPDATE absences SET counter = %s WHERE chat_id = %s AND class_id = %s;"
                self.db.execute_query(update_query, (new_counter, chat_id, class_uuid))
                logger.info(f"Absence count for chat {chat_id} in class {class_id} updated to {new_counter}.")
            else:
                insert_query = "INSERT INTO absences (chat_id, class_id, counter) VALUES (%s, %s, %s);"
                self.db.execute_query(insert_query, (chat_id, class_uuid, 1))
                logger.info(f"New absence entry created for chat {chat_id} in class {class_id} with count 1.")
            return True
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error inserting absence for chat {chat_id}, class {class_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def get_absence_count(self, chat_id: str, class_id: str) -> int:
        """Returns the absence count for a specific chat and class."""
        try:
            class_exists_query = "SELECT id FROM classes WHERE class_id = %s;"
            class_uuid_result = self.db.fetch_one(class_exists_query, (class_id,))
            if not class_uuid_result:
                logger.debug(f"Class {class_id} not found when getting absence count for chat {chat_id}.")
                return 0
            class_uuid = class_uuid_result[0]

            query = "SELECT counter FROM absences WHERE chat_id = %s AND class_id = %s;"
            result = self.db.fetch_one(query, (chat_id, class_uuid))
            count = result[0] if result else 0
            logger.debug(f"Retrieved absence count {count} for chat {chat_id} in class {class_id}.")
            return count
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error getting absence count for chat {chat_id}, class {class_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def get_total_absences(self, chat_id: str) -> int:
        """Returns the total absence count for a specific chat across all classes."""
        try:
            query = "SELECT SUM(counter) FROM absences WHERE chat_id = %s;"
            result = self.db.fetch_one(query, (chat_id,))
            total_count = result[0] if result and result[0] is not None else 0
            logger.debug(f"Retrieved total absence count {total_count} for chat {chat_id}.")
            return total_count
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error getting total absences for chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def get_all_classes(self, chat_id: str) -> list:
        """Returns all registered classes."""
        try:
            query = "SELECT class_id, name, semester FROM classes WHERE chat_id = %s;"
            classes = self.db.fetch_all(query, (chat_id,))
            logger.debug(f"Retrieved {len(classes) if classes else 0} classes.")
            return classes
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error getting all classes on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise
