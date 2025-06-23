"""create sdg questions view

Revision ID: xxxx
Revises: a67153dd301b
Create Date: 2025-06-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = 'a67153dd301b'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        CREATE OR REPLACE VIEW sdg_questions_view AS
        SELECT q.id, q.text, q.type, q.sdg_id as primary_sdg_id, g.number as sdg_number, g.name as sdg_name, q.max_score
        FROM sdg_questions q
        JOIN sdg_goals g ON q.sdg_id = g.id
    """)

def downgrade():
    op.execute("DROP VIEW IF EXISTS sdg_questions_view") 