import sqlite3
import os

DB_PATH = os.path.join("data", "logs", "safesight.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check current columns
    c.execute("PRAGMA table_info(violations)")
    columns = [row[1] for row in c.fetchall()]
    
    print(f"Current columns: {columns}")
    
    try:
        if 'x' not in columns:
            print("Adding column 'x'...")
            c.execute("ALTER TABLE violations ADD COLUMN x INTEGER")
        if 'y' not in columns:
            print("Adding column 'y'...")
            c.execute("ALTER TABLE violations ADD COLUMN y INTEGER")
        
        conn.commit()
        print("Migration successful: Database schema matches the new feature requirements.")
    except sqlite3.OperationalError as e:
        print(f"Migration error (might already be migrated): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
