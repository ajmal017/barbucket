import sqlite3
import os
from datetime import datetime
import configparser


class DataBase():
    __config = configparser.ConfigParser()
    __config.read('barbucket/config.ini')
    __DB_PATH = __config.get('database', 'db_path')

    def __init__(self):
        # If database file does not exist, initialize it
        if not os.path.isfile(DataBase.__DB_PATH):
            self.init_database()


    def connect(self):
        conn = sqlite3.connect(DataBase.__DB_PATH)
        conn.execute("""
            PRAGMA foreign_keys = 1;
        """)
        return conn


    def disconnect(self, conn):
        conn.close()


    def init_database(self):
        # backup old database
        if os.path.isfile(DataBase.__DB_PATH):
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")
            new_name = DataBase.__DB_PATH.split('.')[0] + '_backup_' + timestamp + '.db'
            os.rename(DataBase.__DB_PATH, new_name)

        # create new database and connect to
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE contracts (
                contract_id INTEGER NOT NULL PRIMARY KEY,
                type TEXT,
                exchange_symbol TEXT, 
                broker_symbol TEXT, 
                name TEXT, 
                currency TEXT, 
                exchange TEXT, 
                status_code INTEGER,
                status_text TEXT);""")

        cur.execute("""
            CREATE TABLE quotes (
                contract_id INTEGER,
                date TEXT,
                open REAL,
                high REAL, 
                low REAL, 
                close REAL,
                volume REAL,
                FOREIGN KEY (contract_id)
                    REFERENCES contracts (contract_id)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE,
                UNIQUE (contract_id, date));""")

        cur.execute("""
            CREATE TABLE universe_memberships (
                membership_id INTEGER NOT NULL PRIMARY KEY,
                contract_id INTEGER,
                universe TEXT);""")

        conn.commit()
        cur.close()
        self.disconnect(conn)


    @staticmethod
    def remove_special_chars(input_string):
        special_chars = ["'"]
        result = input_string
        for char in special_chars:
            result = result.replace(char, '')
        return result
