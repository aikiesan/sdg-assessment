import sqlite3

DB_PATH = 'sdg_assessment.db'  # Adjust if your DB is elsewhere

def manual_cleanup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Drop temp table if it exists
        cursor.execute('DROP TABLE IF EXISTS _alembic_tmp_sdg_relationships;')
        print('Temporary table _alembic_tmp_sdg_relationships dropped.')
        
        # Try to drop the strength column (works only in SQLite 3.35+)
        try:
            cursor.execute('ALTER TABLE sdg_relationships DROP COLUMN strength;')
            print('Column strength dropped from sdg_relationships.')
        except Exception as inner:
            print('Could not drop column strength (likely unsupported in this SQLite version):', inner)
            print('If you need to drop this column in older SQLite, the table must be recreated. Let me know if you need this!')
        
        conn.commit()
    except Exception as e:
        print('Database cleanup error:', e)
    finally:
        conn.close()
        print('Connection closed.')

if __name__ == '__main__':
    manual_cleanup()
