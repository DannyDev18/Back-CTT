"""add sponsors activo column

Revision ID: 98ea811add01
Revises: 5b10776f8ef0
Create Date: 2026-07-16 14:59:59.929496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # requerido: SQLModel usa sqlmodel.sql.sqltypes.AutoString en columnas de texto

# revision identifiers, used by Alembic.
revision: str = '98ea811add01'
down_revision: Union[str, Sequence[str], None] = '5b10776f8ef0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default puebla las filas existentes; se retira después para que
    # el default a nivel de aplicación (Sponsor.activo = True) sea la única
    # fuente de verdad hacia adelante.
    op.add_column(
        'sponsors',
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.alter_column('sponsors', 'activo', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('sponsors', 'activo')
