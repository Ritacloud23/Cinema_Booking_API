"""add price rules

Revision ID: 0589e5bd7d89
Revises: d3dde6e37100
Create Date: 2026-09-22 10:06:27.823267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0589e5bd7d89'
down_revision: Union[str, Sequence[str], None] = 'd3dde6e37100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "price_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("film_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["film_id"], ["films.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_price_rules_film_id"),
        "price_rules",
        ["film_id"],
        unique=False,
    )

    op.add_column(
        "films",
        sa.Column(
            "base_price",
            sa.Float(),
            nullable=False,
            server_default=sa.text("5000"),
        ),
    )

    op.alter_column(
        "films",
        "base_price",
        server_default=None,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("films", "base_price")
    op.drop_index(
        op.f("ix_price_rules_film_id"),
        table_name="price_rules",
    )
    op.drop_table("price_rules")
