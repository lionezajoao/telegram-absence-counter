import os
import psycopg2
import logging
import sys

logger = logging.getLogger(__name__)

class Base:
    def __init__(self):
        self.host = os.getenv("PG_HOST")
        self.base_database = os.getenv("PG_BASE_DATABASE")
        self.user = os.getenv("PG_USER")
        self.password = os.getenv("PG_PASSWORD")
        self.port = os.getenv("PG_PORT")
        self.conn = None
        self.cursor = None

    def connect(self, database: str = None):
        """Establishes a persistent connection to the database."""
        try:
            if self.conn is None or self.conn.closed != 0:
                self.conn = psycopg2.connect(
                    host=self.host,
                    database=self.base_database if database is None else database,
                    user=self.user,
                    password=self.password,
                    port=self.port
                )
                self.cursor = self.conn.cursor()
                logger.info("Database connection established successfully.")
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error connecting to the database on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            raise

    def close(self):
        """Closes the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.conn = None
        self.cursor = None
        logger.info("Database connection closed.")

    def execute_query(self, query, params=None):
        """Executes a query with the given parameters."""
        try:
            if self.conn.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                logger.warning("Transaction in error state, rolling back before executing new query.")
                self.conn.rollback()
            logger.debug(f"Executing query: {query} with params: {params}")
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.debug("Query executed successfully.")
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error executing query on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            self.conn.rollback()
            raise

    def fetch_all(self, query, params=None):
        """Executes a query and fetches all results."""
        try:
            logger.debug(f"Fetching all results for query: {query} with params: {params}")
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error fetching data on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            self.conn.rollback()
            raise

    def fetch_one(self, query, params=None):
        """Executes a query and fetches a single result."""
        try:
            if self.conn.get_transaction_status() == psycopg2.extensions.TRANSACTION_STATUS_INERROR:
                logger.warning("Transaction in error state, rolling back before executing new query.")
                self.conn.rollback()
            logger.debug(f"Fetching one result for query: {query} with params: {params}")
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            logger.error(f"Error fetching data on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            self.conn.rollback()
            raise
