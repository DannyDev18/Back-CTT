"""create session attendance table

Revision ID: c3f81e29a001
Revises: 98ea811add01
Create Date: 2026-11-08 04:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c3f81e29a001'
down_revision: Union[str, Sequence[str], None] = '98ea811add01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    CREATE TABLE IF NOT EXISTS session_attendance (
        id SERIAL PRIMARY KEY,
        id_enrollment INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
        id_sesion INTEGER NOT NULL REFERENCES sesiones_cronograma(id_sesion) ON DELETE CASCADE,
        check_in_time TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
        scanned_by_user_id INTEGER,
        notes VARCHAR(255),
        CONSTRAINT uq_enrollment_session UNIQUE (id_enrollment, id_sesion)
    );
    CREATE INDEX IF NOT EXISTS idx_attendance_session ON session_attendance(id_sesion);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('session_attendance')
