import sqlite3
import os
import argparse


def init_database(overwrite=False):
    # Create database directory if it doesn't exist
    os.makedirs('database', exist_ok=True)

    db_path = "database/kit_readiness.db"

    if os.path.exists(db_path):
        if overwrite:
            os.remove(db_path)
            print(f"Database '{db_path}' has been deleted.")
        else:
            print(f"Database '{db_path}' already exists. Use --overwrite to overwrite it.")
            return

    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Read and execute schema
        with open("database/schema.sql", "r") as schema_file:
            cursor.executescript(schema_file.read())

        # Read and execute sample data
        with open("database/sample_data.sql", "r") as data_file:
            cursor.executescript(data_file.read())

        # Commit the changes
        conn.commit()
        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the Kit Readiness database.")
    parser.add_argument('--overwrite', action='store_true', help="Overwrite the existing database if it exists.")
    args = parser.parse_args()

    init_database(overwrite=args.overwrite)
