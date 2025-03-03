import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def init_database():
    """Initialize database with necessary tables"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # Create conversation history table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        sql_query TEXT NOT NULL,
        results TEXT NOT NULL,
        explanation TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL
    )
    ''')
    
    # Create data table (for CSV data)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS data (
        id INTEGER PRIMARY KEY AUTOINCREMENT
    )
    ''')
    
    conn.commit()
    conn.close()

def create_table_from_file(df, table_name):
    """Create a new table in SQLite database from DataFrame"""
    try:
        conn = sqlite3.connect('data.db')
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"Created table {table_name} with {len(df)} rows")  # Debug print
        
        # Verify the table was created
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Verified table {table_name} has {count} rows")  # Debug print
        
        conn.close()
    except Exception as e:
        print(f"Error creating table {table_name}: {str(e)}")
        raise

def remove_table(table_name):
    """Remove a table from the database"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    conn.close()

def get_all_tables():
    """Get list of all tables and their schemas"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'conversation_history';")
    tables = cursor.fetchall()
    
    # Get schema for each table
    schemas = {}
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schemas[table_name] = {col[1]: col[2] for col in columns}
    
    conn.close()
    return schemas

def execute_query(query):
    """Execute SQL query and return results as DataFrame"""
    try:
        conn = sqlite3.connect('data.db')
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        raise e

def save_conversation(question, sql_query, results, explanation):
    """Save conversation to history with 24-hour expiration"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    current_time = datetime.now()
    expires_at = current_time + timedelta(hours=24)
    
    cursor.execute('''
    INSERT INTO conversation_history 
    (question, sql_query, results, explanation, timestamp, expires_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (question, sql_query, str(results), explanation, current_time, expires_at))
    
    conn.commit()
    conn.close()

def get_recent_conversations():
    """Get conversations from last 24 hours"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # Clean up expired conversations
    cleanup_expired_conversations()
    
    # Get valid conversations
    cursor.execute('''
    SELECT question, sql_query, results, explanation, timestamp
    FROM conversation_history
    WHERE expires_at > CURRENT_TIMESTAMP
    ORDER BY timestamp DESC
    ''')
    
    conversations = cursor.fetchall()
    conn.close()
    
    return [
        {
            'question': conv[0],
            'sql_query': conv[1],
            'results': conv[2],
            'explanation': conv[3],
            'timestamp': conv[4]
        }
        for conv in conversations
    ]

def cleanup_expired_conversations():
    """Delete conversations older than 24 hours"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    DELETE FROM conversation_history
    WHERE expires_at <= CURRENT_TIMESTAMP
    ''')
    
    conn.commit()
    conn.close() 