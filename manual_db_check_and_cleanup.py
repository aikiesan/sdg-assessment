import sqlite3

DB_PATH = 'sdg_assessment.db'  # Adjust if your DB is elsewhere

def check_and_cleanup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check columns in sdg_relationships
        cursor.execute("PRAGMA table_info(sdg_relationships);")
        columns = [row[1] for row in cursor.fetchall()]
        print('Columns in sdg_relationships:', columns)
        if 'strength' in columns:
            try:
                cursor.execute('ALTER TABLE sdg_relationships DROP COLUMN strength;')
                print('Column strength dropped from sdg_relationships.')
            except Exception as drop_err:
                print('Could not drop strength column:', drop_err)
                print('If your SQLite version does not support DROP COLUMN, table recreation is required.')
        else:
            print('strength column does NOT exist in sdg_relationships.')
        # Drop temp table
        cursor.execute('DROP TABLE IF EXISTS _alembic_tmp_sdg_relationships;')
        print('Temporary table _alembic_tmp_sdg_relationships dropped.')
        conn.commit()
    except Exception as e:
        print('Database check/cleanup error:', e)
    finally:
        conn.close()
        print('Connection closed.')

if __name__ == '__main__':
    check_and_cleanup()
