"""Resolve multiple heads by merging

Revision ID: 2792a61b1b90
Revises: 1939fe9a67d8, xxxx
Create Date: 2025-06-23 11:38:18.049397

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2792a61b1b90'
down_revision = ('1939fe9a67d8', 'xxxx')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
