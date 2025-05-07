"""Add expert assessment columns

Revision ID: add_expert_assessment_cols
Revises: # Leave this empty, it will be filled by Flask-Migrate
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_expert_assessment_cols'
down_revision = None  # This will be updated by Flask-Migrate
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to assessments table
    op.add_column('assessments',
        sa.Column('raw_expert_data', sa.JSON(), nullable=True)
    )
    op.add_column('assessments',
        sa.Column('assessment_type', sa.String(length=50), server_default='standard', nullable=False)
    )

def downgrade():
    # Remove the columns if we need to roll back
    op.drop_column('assessments', 'assessment_type')
    op.drop_column('assessments', 'raw_expert_data') 