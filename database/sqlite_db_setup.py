import sqlite3
import os

def init_database():
    # Create database directory if it doesn't exist
    # os.makedirs('database', exist_ok=True)
    
    # Connect to SQLite database (creates it if it doesn't exist)
    conn = sqlite3.connect('database/kit_readiness.db')
    cursor = conn.cursor()
    
    try:
        # Read and execute schema
        with open('database/schema.sql', 'r') as schema_file:
            cursor.executescript(schema_file.read())
            
        # Read and execute sample data
        with open('database/sample_data.sql', 'r') as data_file:
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
    init_database()
