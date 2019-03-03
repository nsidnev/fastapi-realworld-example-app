"""changing favorites table

Revision ID: 72f74c64751b
Revises: 4e62e0d755a8
Create Date: 2019-01-31 22:56:41.565151

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "72f74c64751b"
down_revision = "4e62e0d755a8"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        """
        ALTER TABLE favourites
        RENAME TO favorites;
        """
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        """
        ALTER TABLE favorites
        RENAME TO favourites;
        """
    )
