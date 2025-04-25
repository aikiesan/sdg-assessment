import click
from flask.cli import with_appcontext
from app.routes.assessments import populate_questions
from app.utils.db import get_db

def register_cli_commands(app):
    @app.cli.command('populate-questions')
    @with_appcontext
    def populate_questions_command():
        """Populates the sdg_questions table with questions 1-31."""
        print("Attempting to populate sdg_questions table...")
        if populate_questions():
            print("sdg_questions table populated successfully (or was already up-to-date).")
        else:
            print("Failed to populate sdg_questions table. Check logs for errors.")

    @app.cli.command('clear-questions')
    @with_appcontext
    def clear_questions_command():
        """Deletes all rows from the sdg_questions table."""
        conn = get_db()
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
