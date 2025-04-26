import sqlite3

# Path to your SQLite database file
DB_PATH = 'sdg_assessment.db'  # Adjust if your DB is elsewhere

def drop_temp_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('DROP TABLE IF EXISTS _alembic_tmp_sdg_relationships;')
        conn.commit()
        print('Temporary table _alembic_tmp_sdg_relationships dropped successfully.')
    except Exception as e:
        print(f'Error dropping table: {e}')
    finally:
        conn.close()
        print('Connection closed.')

if __name__ == '__main__':
    drop_temp_table()
