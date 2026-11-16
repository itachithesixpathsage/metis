"""Add indexed historical OHLC storage."""

from alembic import op
import sqlalchemy as sa

revision = "002_historical_bars"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "historical_bars",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("symbol", sa.String(6), nullable=False),
        sa.Column("timeframe", sa.String(3), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float(), nullable=False), sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False), sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float()), sa.Column("volume_type", sa.String(30)),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("quality_status", sa.String(16), nullable=False, server_default="valid"),
        sa.UniqueConstraint("symbol", "timeframe", "timestamp", name="uq_historical_bar"),
        schema="market_data",
    )
    op.create_index("ix_historical_bars_query", "historical_bars",
                    ["symbol", "timeframe", "timestamp"], schema="market_data")


def downgrade() -> None:
    op.drop_index("ix_historical_bars_query", table_name="historical_bars", schema="market_data")
    op.drop_table("historical_bars", schema="market_data")
