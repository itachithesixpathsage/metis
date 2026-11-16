"""Add explicit bid/ask identity to historical bars."""

from alembic import op
import sqlalchemy as sa

revision = "003_historical_price_side"
down_revision = "002_historical_bars"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The server default marks all pre-existing bars without guessing their side.
    op.add_column(
        "historical_bars",
        sa.Column("price_side", sa.String(16), nullable=False, server_default="unspecified"),
        schema="market_data",
    )
    op.drop_constraint("uq_historical_bar", "historical_bars", schema="market_data", type_="unique")
    op.create_unique_constraint(
        "uq_historical_bar_side", "historical_bars",
        ["symbol", "timeframe", "price_side", "timestamp"], schema="market_data",
    )
    op.drop_index("ix_historical_bars_query", table_name="historical_bars", schema="market_data")
    op.create_index(
        "ix_historical_bars_query", "historical_bars",
        ["symbol", "timeframe", "price_side", "timestamp"], schema="market_data",
    )
    # Existing rows have been backfilled; new writes provide the value explicitly.
    op.alter_column("historical_bars", "price_side", server_default=None, schema="market_data")


def downgrade() -> None:
    op.drop_index("ix_historical_bars_query", table_name="historical_bars", schema="market_data")
    op.create_index(
        "ix_historical_bars_query", "historical_bars",
        ["symbol", "timeframe", "timestamp"], schema="market_data",
    )
    op.drop_constraint("uq_historical_bar_side", "historical_bars", schema="market_data", type_="unique")
    op.create_unique_constraint(
        "uq_historical_bar", "historical_bars", ["symbol", "timeframe", "timestamp"], schema="market_data",
    )
    op.drop_column("historical_bars", "price_side", schema="market_data")
