import sqlite3
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pokemon_api.db")
SYNC_FILE_PATH = os.path.join(BASE_DIR, "trainers.json")
OLD_USERS_FILE = os.path.join(BASE_DIR, "auth", "users.json")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)
    
    # Create teams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pokemon_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    
    # Check if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Try to migrate from auth/users.json
        migrated = False
        if os.path.exists(OLD_USERS_FILE):
            try:
                with open(OLD_USERS_FILE, "r") as f:
                    data = json.load(f)
                    for u in data.get("users", []):
                        username = u.get("username")
                        password = u.get("password")
                        role = "admin" if username == "admin" else "user"
                        name = "Administrator" if username == "admin" else username.capitalize()
                        cursor.execute(
                            "INSERT OR IGNORE INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                            (username, password, role, name)
                        )
                conn.commit()
                migrated = True
                print("Migrated existing users from users.json successfully.")
            except Exception as e:
                print(f"Failed to migrate from old users.json: {e}")
        
        if not migrated:
            # Seed default admin
            cursor.execute(
                "INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                ("admin", "admin", "admin", "Administrator")
            )
            conn.commit()
            print("Seeded default admin account.")
            
    conn.close()
    
    # Sync initial state to JSON file
    sync_db_to_json()

def sync_db_to_json():
    """
    Exports the current state of SQLite database into `trainers.json` in the root folder.
    This fulfills the requirement of 'crea la persistencia en tu archivo de datos, y una base en sqlite'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, name, role FROM users")
    users = cursor.fetchall()
    
    trainers_list = []
    admins_list = []
    
    for u in users:
        user_id = u["id"]
        username = u["username"]
        name = u["name"]
        role = u["role"]
        
        if role == "admin":
            admins_list.append({
                "id": user_id,
                "username": username,
                "name": name,
                "role": role
            })
        else:
            # Get user's team
            cursor.execute("SELECT pokemon_id FROM teams WHERE user_id = ?", (user_id,))
            team_rows = cursor.fetchall()
            team_ids = [row["pokemon_id"] for row in team_rows]
            
            trainers_list.append({
                "id": user_id,
                "username": username,
                "name": name,
                "role": role,
                "team": team_ids
            })
            
    conn.close()
    
    sync_data = {
        "trainers": trainers_list,
        "admins": admins_list
    }
    
    with open(SYNC_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, indent=2, ensure_ascii=False)
    
    print(f"Synchronized database state to {SYNC_FILE_PATH}")

if __name__ == "__main__":
    init_db()
