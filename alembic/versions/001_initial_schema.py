"""
Initial migration for Project Métis - Core schema creation.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema with all core tables."""
    # Create schemas
    op.execute('CREATE SCHEMA IF NOT EXISTS market_data')
    op.execute('CREATE SCHEMA IF NOT EXISTS portfolio')
    op.execute('CREATE SCHEMA IF NOT EXISTS analytics')
    op.execute('CREATE SCHEMA IF NOT EXISTS simulation')
    op.execute('CREATE SCHEMA IF NOT EXISTS risk')
    op.execute('CREATE SCHEMA IF NOT EXISTS decision')
    op.execute('CREATE SCHEMA IF NOT EXISTS validation')

    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE')

    # ============================================================
    # MARKET DATA TABLES
    # ============================================================

    # Instruments table
    op.create_table(
        'instruments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('symbol', sa.String(20), nullable=False, unique=True),
        sa.Column('base_currency', sa.String(3), nullable=False),
        sa.Column('quote_currency', sa.String(3), nullable=False),
        sa.Column('name', sa.String(100)),
        sa.Column('pip_size', sa.Numeric(10, 8), nullable=False, server_default='0.0001'),
        sa.Column('contract_size', sa.Numeric(20, 2), nullable=False, server_default='100000'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='market_data',
    )
    op.create_index('ix_instruments_symbol', 'instruments', ['symbol'], schema='market_data')
    op.create_index('ix_instruments_base_quote', 'instruments', ['base_currency', 'quote_currency'], schema='market_data')

    # Market observations (TimescaleDB hypertable)
    op.create_table(
        'observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('frequency', sa.String(10), nullable=False),
        sa.Column('open_price', sa.Numeric(20, 10), nullable=False),
        sa.Column('high_price', sa.Numeric(20, 10), nullable=False),
        sa.Column('low_price', sa.Numeric(20, 10), nullable=False),
        sa.Column('close_price', sa.Numeric(20, 10), nullable=False),
        sa.Column('bid_price', sa.Numeric(20, 10)),
        sa.Column('ask_price', sa.Numeric(20, 10)),
        sa.Column('mid_price', sa.Numeric(20, 10)),
        sa.Column('volume', sa.Numeric(30, 2)),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('spread_bps', sa.Integer),
        sa.Column('is_valid', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('validation_errors', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='market_data',
    )
    op.create_index('ix_observations_instrument_timestamp', 'observations', ['instrument_id', 'timestamp'], schema='market_data')
    op.create_index('ix_observations_timestamp', 'observations', ['timestamp'], schema='market_data')
    op.create_index('ix_observations_provider', 'observations', ['provider'], schema='market_data')
    op.create_index('ix_observations_frequency', 'observations', ['frequency'], schema='market_data')

    # Convert to hypertable
    op.execute("SELECT create_hypertable('market_data.observations', 'timestamp', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE)")

    # Data quality issues table
    op.create_table(
        'data_quality_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('frequency', sa.String(10), nullable=False),
        sa.Column('issue_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('expected_value', sa.Numeric(20, 10)),
        sa.Column('actual_value', sa.Numeric(20, 10)),
        sa.Column('resolved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='market_data',
    )
    op.create_index('ix_dqi_instrument_timestamp', 'data_quality_issues', ['instrument_id', 'timestamp'], schema='market_data')
    op.create_index('ix_dqi_issue_type', 'data_quality_issues', ['issue_type'], schema='market_data')
    op.create_index('ix_dqi_resolved', 'data_quality_issues', ['resolved'], schema='market_data')

    # ============================================================
    # PORTFOLIO TABLES
    # ============================================================

    # Portfolios
    op.create_table(
        'portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('reporting_currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('base_currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='portfolio',
    )
    op.create_index('ix_portfolios_name', 'portfolios', ['name'], schema='portfolio')

    # Portfolio positions
    op.create_table(
        'positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio.portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),  # 'LONG' or 'SHORT'
        sa.Column('notional_amount', sa.Numeric(30, 2), nullable=False),
        sa.Column('notional_currency', sa.String(3), nullable=False),
        sa.Column('entry_price', sa.Numeric(20, 10), nullable=False),
        sa.Column('entry_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('current_price', sa.Numeric(20, 10)),
        sa.Column('current_timestamp', sa.DateTime(timezone=True)),
        sa.Column('leverage', sa.Numeric(5, 2), nullable=False, server_default='1.0'),
        sa.Column('transaction_cost_bps', sa.Integer, nullable=False, server_default='0'),
        sa.Column('financing_rate', sa.Numeric(10, 8)),
        sa.Column('is_open', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('closed_price', sa.Numeric(20, 10)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='portfolio',
    )
    op.create_index('ix_positions_portfolio', 'positions', ['portfolio_id'], schema='portfolio')
    op.create_index('ix_positions_instrument', 'positions', ['instrument_id'], schema='portfolio')
    op.create_index('ix_positions_is_open', 'positions', ['is_open'], schema='portfolio')

    # Portfolio snapshots (for P&L tracking)
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio.portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_value', sa.Numeric(30, 2), nullable=False),
        sa.Column('unrealized_pnl', sa.Numeric(30, 2), nullable=False, server_default='0'),
        sa.Column('realized_pnl', sa.Numeric(30, 2), nullable=False, server_default='0'),
        sa.Column('gross_exposure', sa.Numeric(30, 2), nullable=False, server_default='0'),
        sa.Column('net_exposure', sa.Numeric(30, 2), nullable=False, server_default='0'),
        sa.Column('currency_exposures', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='portfolio',
    )
    op.create_index('ix_ps_portfolio_timestamp', 'portfolio_snapshots', ['portfolio_id', 'timestamp'], schema='portfolio')

    # Convert to hypertable
    op.execute("SELECT create_hypertable('portfolio.portfolio_snapshots', 'timestamp', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE)")

    # ============================================================
    # ANALYTICS TABLES
    # ============================================================

    # Returns series
    op.create_table(
        'returns_series',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('frequency', sa.String(10), nullable=False),
        sa.Column('simple_return', sa.Numeric(20, 10)),
        sa.Column('log_return', sa.Numeric(20, 10)),
        sa.Column('price', sa.Numeric(20, 10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='analytics',
    )
    op.create_index('ix_returns_instrument_timestamp', 'returns_series', ['instrument_id', 'timestamp'], schema='analytics')
    op.create_index('ix_returns_frequency', 'returns_series', ['frequency'], schema='analytics')

    # Convert to hypertable
    op.execute("SELECT create_hypertable('analytics.returns_series', 'timestamp', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE)")

    # Volatility estimates
    op.create_table(
        'volatility_estimates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('frequency', sa.String(10), nullable=False),
        sa.Column('window_size', sa.Integer, nullable=False),
        sa.Column('volatility', sa.Numeric(20, 10), nullable=False),
        sa.Column('annualised_volatility', sa.Numeric(20, 10)),
        sa.Column('method', sa.String(50), nullable=False),  # 'historical', 'ewma', 'garch'
        sa.Column('parameters', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='analytics',
    )
    op.create_index('ix_vol_instrument_timestamp', 'volatility_estimates', ['instrument_id', 'timestamp'], schema='analytics')
    op.create_index('ix_vol_method', 'volatility_estimates', ['method'], schema='analytics')

    # Correlation matrices
    op.create_table(
        'correlation_matrices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('frequency', sa.String(10), nullable=False),
        sa.Column('window_size', sa.Integer, nullable=False),
        sa.Column('instruments', postgresql.JSONB, nullable=False),  # List of instrument IDs
        sa.Column('matrix', postgresql.JSONB, nullable=False),  # 2D array as JSON
        sa.Column('method', sa.String(50), nullable=False, server_default='pearson'),
        sa.Column('is_valid', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('validation_errors', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='analytics',
    )
    op.create_index('ix_corr_timestamp', 'correlation_matrices', ['timestamp'], schema='analytics')

    # ============================================================
    # SIMULATION TABLES
    # ============================================================

    # Simulation jobs
    op.create_table(
        'simulation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(200)),
        sa.Column('model_type', sa.String(50), nullable=False),  # 'GBM', 'BOOTSTRAP', 'GARCH'
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),  # 'PENDING', 'RUNNING', 'COMPLETED', 'FAILED'
        sa.Column('instruments', postgresql.JSONB, nullable=False),  # List of instrument IDs
        sa.Column('parameters', postgresql.JSONB, nullable=False),
        sa.Column('num_paths', sa.Integer, nullable=False),
        sa.Column('horizon_bars', sa.Integer, nullable=False),
        sa.Column('confidence_levels', postgresql.JSONB, nullable=False),
        sa.Column('random_seed', sa.Integer),
        sa.Column('start_time', sa.DateTime(timezone=True)),
        sa.Column('end_time', sa.DateTime(timezone=True)),
        sa.Column('progress', sa.Integer, nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text),
        sa.Column('result_summary', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='simulation',
    )
    op.create_index('ix_sim_job_status', 'simulation_jobs', ['status'], schema='simulation')
    op.create_index('ix_sim_job_created', 'simulation_jobs', ['created_at'], schema='simulation')

    # Simulation paths (sample of paths for visualization)
    op.create_table(
        'simulation_paths',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('simulation.simulation_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('path_index', sa.Integer, nullable=False),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('timestamps', postgresql.JSONB, nullable=False),  # Array of timestamps
        sa.Column('prices', postgresql.JSONB, nullable=False),  # Array of prices
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='simulation',
    )
    op.create_index('ix_sim_paths_job', 'simulation_paths', ['job_id'], schema='simulation')
    op.create_index('ix_sim_paths_job_instrument', 'simulation_paths', ['job_id', 'instrument_id'], schema='simulation')

    # Terminal price distributions
    op.create_table(
        'terminal_distributions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('simulation.simulation_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('percentiles', postgresql.JSONB, nullable=False),  # {p1, p5, p10, ..., p99}
        sa.Column('mean', sa.Numeric(20, 10)),
        sa.Column('std', sa.Numeric(20, 10)),
        sa.Column('skewness', sa.Numeric(20, 10)),
        sa.Column('excess_kurtosis', sa.Numeric(20, 10)),
        sa.Column('var_95', sa.Numeric(20, 10)),
        sa.Column('var_99', sa.Numeric(20, 10)),
        sa.Column('es_95', sa.Numeric(20, 10)),
        sa.Column('es_99', sa.Numeric(20, 10)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='simulation',
    )
    op.create_index('ix_td_job', 'terminal_distributions', ['job_id'], schema='simulation')

    # ============================================================
    # RISK TABLES
    # ============================================================

    # Risk measurements
    op.create_table(
        'risk_measurements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio.portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('var_95', sa.Numeric(30, 2)),
        sa.Column('var_99', sa.Numeric(30, 2)),
        sa.Column('es_95', sa.Numeric(30, 2)),
        sa.Column('es_99', sa.Numeric(30, 2)),
        sa.Column('portfolio_volatility', sa.Numeric(20, 10)),
        sa.Column('max_drawdown', sa.Numeric(10, 6)),
        sa.Column('current_drawdown', sa.Numeric(10, 6)),
        sa.Column('gross_exposure', sa.Numeric(30, 2)),
        sa.Column('net_exposure', sa.Numeric(30, 2)),
        sa.Column('currency_concentration', postgresql.JSONB),
        sa.Column('component_var', postgresql.JSONB),  # Per-position component VaR
        sa.Column('marginal_var', postgresql.JSONB),  # Per-position marginal VaR
        sa.Column('method', sa.String(50), nullable=False),  # 'historical', 'parametric', 'monte_carlo'
        sa.Column('parameters', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='risk',
    )
    op.create_index('ix_rm_portfolio_timestamp', 'risk_measurements', ['portfolio_id', 'timestamp'], schema='risk')
    op.create_index('ix_rm_method', 'risk_measurements', ['method'], schema='risk')

    # Stress test scenarios
    op.create_table(
        'stress_scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('scenario_type', sa.String(50), nullable=False),  # 'historical', 'hypothetical', 'factor_shock'
        sa.Column('parameters', postgresql.JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='risk',
    )

    # Stress test results
    op.create_table(
        'stress_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio.portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('risk.stress_scenarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('portfolio_loss', sa.Numeric(30, 2)),
        sa.Column('portfolio_loss_pct', sa.Numeric(10, 6)),
        sa.Column('position_losses', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='risk',
    )
    op.create_index('ix_sr_portfolio_timestamp', 'stress_results', ['portfolio_id', 'timestamp'], schema='risk')

    # ============================================================
    # DECISION TABLES
    # ============================================================

    # Risk policies
    op.create_table(
        'risk_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio.portfolios.id', ondelete='CASCADE')),
        sa.Column('rules', postgresql.JSONB, nullable=False),  # Array of rule configurations
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='decision',
    )
    op.create_index('ix_rp_portfolio', 'risk_policies', ['portfolio_id'], schema='decision')
    op.create_index('ix_rp_is_default', 'risk_policies', ['is_default'], schema='decision')

    # Decision records
    op.create_table(
        'decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolio.portfolios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('decision.risk_policies.id', ondelete='SET NULL')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recommendation', sa.String(20), nullable=False),  # 'HOLD', 'REDUCE', 'EXIT', 'INSUFFICIENT_DATA'
        sa.Column('triggered_rules', postgresql.JSONB),  # Array of triggered rule IDs
        sa.Column('explanations', postgresql.JSONB),  # Human-readable explanations
        sa.Column('risk_metrics', postgresql.JSONB),  # Snapshot of risk metrics at decision time
        sa.Column('position_recommendations', postgresql.JSONB),  # Per-position recommendations
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='decision',
    )
    op.create_index('ix_dec_portfolio_timestamp', 'decisions', ['portfolio_id', 'timestamp'], schema='decision')
    op.create_index('ix_dec_recommendation', 'decisions', ['recommendation'], schema='decision')

    # ============================================================
    # VALIDATION TABLES
    # ============================================================

    # Model configurations
    op.create_table(
        'model_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),  # 'GBM', 'BOOTSTRAP', 'GARCH', 'CORRELATION'
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('parameters', postgresql.JSONB, nullable=False),
        sa.Column('training_window', sa.String(50)),  # e.g., '252d', '504d'
        sa.Column('validation_window', sa.String(50)),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='validation',
    )
    op.create_index('ix_mc_model_type', 'model_configurations', ['model_type'], schema='validation')
    op.create_index('ix_mc_is_active', 'model_configurations', ['is_active'], schema='validation')

    # Backtest results
    op.create_table(
        'backtest_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('model_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('validation.model_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('instrument_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('market_data.instruments.id'), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metrics', postgresql.JSONB, nullable=False),  # All validation metrics
        sa.Column('var_coverage_95', sa.Numeric(6, 4)),
        sa.Column('var_coverage_99', sa.Numeric(6, 4)),
        sa.Column('kupiec_p_value_95', sa.Numeric(10, 8)),
        sa.Column('kupiec_p_value_99', sa.Numeric(10, 8)),
        sa.Column('christoffersen_p_value_95', sa.Numeric(10, 8)),
        sa.Column('christoffersen_p_value_99', sa.Numeric(10, 8)),
        sa.Column('es_backtest_p_value', sa.Numeric(10, 8)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='validation',
    )
    op.create_index('ix_btr_model_config', 'backtest_results', ['model_config_id'], schema='validation')
    op.create_index('ix_btr_instrument', 'backtest_results', ['instrument_id'], schema='validation')

    # Walk-forward validation
    op.create_table(
        'walkforward_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('model_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('validation.model_configurations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fold_number', sa.Integer, nullable=False),
        sa.Column('train_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('train_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('test_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('test_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metrics', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='validation',
    )
    op.create_index('ix_wfr_model_config', 'walkforward_results', ['model_config_id'], schema='validation')


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # Drop validation tables
    op.drop_table('walkforward_results', schema='validation')
    op.drop_table('backtest_results', schema='validation')
    op.drop_table('model_configurations', schema='validation')

    # Drop decision tables
    op.drop_table('decisions', schema='decision')
    op.drop_table('risk_policies', schema='decision')

    # Drop risk tables
    op.drop_table('stress_results', schema='risk')
    op.drop_table('stress_scenarios', schema='risk')
    op.drop_table('risk_measurements', schema='risk')

    # Drop simulation tables
    op.drop_table('terminal_distributions', schema='simulation')
    op.drop_table('simulation_paths', schema='simulation')
    op.drop_table('simulation_jobs', schema='simulation')

    # Drop analytics tables
    op.drop_table('correlation_matrices', schema='analytics')
    op.drop_table('volatility_estimates', schema='analytics')
    op.drop_table('returns_series', schema='analytics')

    # Drop portfolio tables
    op.drop_table('portfolio_snapshots', schema='portfolio')
    op.drop_table('positions', schema='portfolio')
    op.drop_table('portfolios', schema='portfolio')

    # Drop market data tables
    op.drop_table('data_quality_issues', schema='market_data')
    op.drop_table('observations', schema='market_data')
    op.drop_table('instruments', schema='market_data')

    # Drop schemas
    op.execute('DROP SCHEMA IF EXISTS validation CASCADE')
    op.execute('DROP SCHEMA IF EXISTS decision CASCADE')
    op.execute('DROP SCHEMA IF EXISTS risk CASCADE')
    op.drop_table('simulation_paths', schema='simulation')
    op.execute('DROP SCHEMA IF EXISTS simulation CASCADE')
    op.execute('DROP SCHEMA IF EXISTS analytics CASCADE')
    op.execute('DROP SCHEMA IF EXISTS portfolio CASCADE')
    op.execute('DROP SCHEMA IF EXISTS market_data CASCADE')