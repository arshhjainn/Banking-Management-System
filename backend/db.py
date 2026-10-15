import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "banking_management"), user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    try:
        yield conn
    finally:
        conn.close()


def query(sql, params=(), one=False):
    with connection() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            rows = cur.fetchone() if one else cur.fetchall()
            conn.commit()
            return rows
        finally:
            cur.close()
