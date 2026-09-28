import os
import pymysql
import logging
import threading
from contextlib import contextmanager
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class MySQLManager:
    """
    Manages MySQL database connections, typically via an SSH tunnel.
    """
    def __init__(self, port=3306):
        load_dotenv()
        self.host = "127.0.0.1"  # Local end of the tunnel
        self.port = port
        self.user = (os.getenv("DB_USER") or "").strip()
        self.password = (os.getenv("DB_PASSWORD") or "").strip()
        self.database = (os.getenv("DB_NAME") or "").strip()
        
        self.connection = None
        self.lock = threading.RLock()

    def connect(self):
        """
        Establishes a connection to the MySQL database. Thread-safe.
        """
        with self.lock:
            try:
                # If there's an existing connection, try to close it first
                if self.connection and self.connection.open:
                    try:
                        self.connection.close()
                    except:
                        pass
                
                logger.info(f"Connecting to MySQL on {self.host}:{self.port}...")
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    cursorclass=DictCursor,
                    connect_timeout=10,
                    autocommit=True
                )
                logger.info("MySQL connection established successfully.")
                return self.connection
            except pymysql.MySQLError as e:
                logger.error(f"MySQL connection failed: {str(e)}")
                self.connection = None
                raise e

    def disconnect(self):
        """
        Closes the database connection. Thread-safe.
        """
        with self.lock:
            if self.connection and self.connection.open:
                logger.info("Closing MySQL connection...")
                try:
                    self.connection.close()
                except Exception as e:
                    logger.warning(f"Error while closing connection: {e}")
                self.connection = None
                logger.info("MySQL connection closed.")

    def test_connection(self):
        """
        Tests the connection by executing a simple query.
        Returns True if successful, False otherwise.
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result:
                    logger.info("Connection test successful.")
                    return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
        finally:
            # We don't disconnect here because we might want to keep the connection open
            # after a successful test, or the caller might handle disconnection.
            pass

    def ensure_connected(self):
        """
        Ensures the connection is alive, reconnecting if necessary.
        """
        with self.lock:
            if not self.connection or not self.connection.open:
                self.connect()
            else:
                try:
                    self.connection.ping(reconnect=True)
                except Exception:
                    logger.info("Connection lost, reconnecting...")
                    self.connect()

    @contextmanager
    def get_cursor(self):
        """
        A thread-safe context manager that yields a cursor.
        The lock is held for the entire duration of the context.
        """
        with self.lock:
            self.ensure_connected()
            cursor = self.connection.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def get_databases(self):
        """
        Fetches all databases from the server.
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                return [row['Database'] for row in cursor.fetchall()]
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching databases: {str(e)}")
            return []

    def get_tables(self, database_name):
        """
        Fetches all tables from a specific database.
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(f"SHOW TABLES FROM `{database_name}`")
                return [list(row.values())[0] for row in cursor.fetchall()]
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching tables for {database_name}: {str(e)}")
            return []

    def get_table_schema(self, database_name, table_name):
        """
        Returns the CREATE TABLE statement for a specific table.
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE `{database_name}`.`{table_name}`")
                result = cursor.fetchone()
                return result['Create Table'] + ";" if result else ""
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching schema for {table_name}: {str(e)}")
            return f"-- Error fetching schema for {table_name}: {str(e)}"

    def get_database_schema(self, database_name):
        """
        Returns the full schema (CREATE TABLE statements) for all tables in a database.
        """
        schema = [f"CREATE DATABASE IF NOT EXISTS `{database_name}`;\nUSE `{database_name}`;\n"]
        tables = self.get_tables(database_name)
        for table in tables:
            schema.append(self.get_table_schema(database_name, table))
        return "\n\n".join(schema)
