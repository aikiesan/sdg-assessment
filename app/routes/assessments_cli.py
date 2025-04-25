import click
from flask.cli import with_appcontext
from app.utils.db_utils import populate_goals, populate_questions

def register_cli_commands(app):
    @app.cli.command('populate-questions')
    @with_appcontext
    def populate_questions_command():
        """Populates the sdg_questions table with questions 1-31."""
        print("Attempting to populate sdg_questions table via CLI...")
        if populate_questions():
            print("CLI: sdg_questions table populated successfully or was already up-to-date.")
        else:
            print("CLI: Failed to populate sdg_questions table. Check logs for errors.")

    @app.cli.command('populate-goals')
    @with_appcontext
    def populate_goals_command():
        """Populates the sdg_goals table with goals 1-17."""
        print("Attempting to populate sdg_goals table via CLI...")
        if populate_goals():
            print("CLI: sdg_goals table populated successfully or was already up-to-date.")
        else:
            print("CLI: Failed to populate sdg_goals table. Check logs for errors.")
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM sdg_questions;")
                conn.commit()
                print(f"Deleted {cur.rowcount} rows from sdg_questions.")
            except Exception as e:
                conn.rollback()
                print(f"Error clearing sdg_questions: {e}")

    @app.cli.command('clear-and-populate-questions')
    @with_appcontext
    def clear_and_populate_questions_command():
        """Clears sdg_questions table and repopulates it with questions 1-31."""
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM sdg_questions;")
            conn.commit()
            print(f"Deleted {cur.rowcount} rows from sdg_questions.")
        except Exception as e:
            conn.rollback()
            print(f"Error clearing sdg_questions: {e}")
            return
        # Now repopulate
        print("Attempting to repopulate sdg_questions table...")
        if populate_questions():
            print("sdg_questions table populated successfully (or was already up-to-date).")
        else:
            print("Failed to populate sdg_questions table. Check logs for errors.")
