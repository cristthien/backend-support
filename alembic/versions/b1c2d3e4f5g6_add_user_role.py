"""Add user role column

Revision ID: b1c2d3e4f5g6
Revises: a33119df602d
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, Sequence[str], None] = 'a33119df602d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column to users table."""
    # Create the enum type first
    userrole = sa.Enum('USER', 'MANAGER', 'ADMIN', name='userrole')
    userrole.create(op.get_bind(), checkfirst=True)
    
    # Add the role column with default value
    op.add_column('users', sa.Column('role', userrole, nullable=False, server_default='USER'))


def downgrade() -> None:
    """Remove role column from users table."""
    op.drop_column('users', 'role')
    
    # Drop the enum type
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
