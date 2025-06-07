from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
import sqlite3
import bcrypt

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

def initialize_database():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            address TEXT NOT NULL,
            secret TEXT NOT NULL,
            funded INTEGER DEFAULT 1
        )
    """)

    # Trustlines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trustlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            currency TEXT NOT NULL,
            issuer_address TEXT NOT NULL,
            trust_limit REAL NOT NULL,
            status TEXT DEFAULT 'active',  -- 'active' or 'deleted'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)


    conn.commit()
    conn.close()

def insert_user(full_name, username, password, address, secret):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (full_name, username, password, address, secret, funded)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (full_name, username, password, address, secret))
    conn.commit()
    conn.close()

def user_exists(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def create_and_store_user(full_name, username, hashed_password):
    if user_exists(username):
        raise Exception("User already exists")

    wallet = generate_faucet_wallet(client, debug=True)

    insert_user(
        full_name,
        username,
        hashed_password,
        wallet.classic_address,
        wallet.seed
    )

    return wallet.classic_address, wallet.seed

def validate_user_login(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        stored_hashed_pw = result[0]
        return bcrypt.checkpw(password.encode(), stored_hashed_pw)
    return False

def get_user_data_by_username(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, address, secret FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "full_name": row[0],
            "address": row[1],
            "secret": row[2]  
        }
    else:
        raise ValueError("User not found.")
    
def get_all_usernames(exclude_username=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    if exclude_username:
        cursor.execute("SELECT username FROM users WHERE username != ?", (exclude_username,))
    else:
        cursor.execute("SELECT username FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def insert_trustline(username, currency, issuer_address, trust_limit):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Get user_id from username
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise ValueError("User not found")
    
    user_id = result[0]

    cursor.execute("""
        INSERT INTO trustlines (user_id, currency, issuer_address, trust_limit)
        VALUES (?, ?, ?, ?)
    """, (user_id, currency, issuer_address, trust_limit))

    conn.commit()
    conn.close()
    