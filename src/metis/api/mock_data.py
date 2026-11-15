"""Mock portfolio data endpoints used while the data services are being built."""

from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["mock data"])


class DashboardMetric(BaseModel):
    label: str
    value: str
    change: str
    change_type: str


class Position(BaseModel):
    pair: str
    direction: str
    notional: str
    entry: str
    current: str
    pnl: str
    risk_pct: str


class Exposure(BaseModel):
    currency: str
    value: str
    width: str
    direction: str


class VarComponent(BaseModel):
    pair: str
    cvar: str
    pct: str


class RecentDecision(BaseModel):
    time: str
    pair: str
    action: str
    reason: str
    type: str


class DashboardData(BaseModel):
    metrics: list[DashboardMetric]
    positions: list[Position]
    exposures: list[Exposure]
    var_decomposition: list[VarComponent]
    recent_decisions: list[RecentDecision]


@router.get("/dashboard", response_model=DashboardData, summary="Mock portfolio dashboard")
async def get_mock_dashboard() -> DashboardData:
    """Return representative portfolio data until persistence and market feeds are connected."""
    return DashboardData(
        metrics=[
            DashboardMetric(label="Total Portfolio Value", value="$2,847,392", change="+2.34%", change_type="positive"),
            DashboardMetric(label="Portfolio VaR (95%)", value="-$34,218", change="-1.2%", change_type="positive"),
            DashboardMetric(label="Expected Shortfall (95%)", value="-$47,891", change="-0.8%", change_type="positive"),
            DashboardMetric(label="Max Drawdown", value="-4.72%", change="+0.3%", change_type="negative"),
            DashboardMetric(label="Gross Exposure", value="$8,940,000", change="+5.1%", change_type="neutral"),
            DashboardMetric(label="Net Exposure", value="$1,240,000", change="-2.4%", change_type="positive"),
        ],
        positions=[
            Position(pair="EUR/USD", direction="LONG", notional="€2,500,000", entry="1.0845", current="1.0912", pnl="+$15,420", risk_pct="2.1%"),
            Position(pair="GBP/USD", direction="SHORT", notional="£1,800,000", entry="1.2678", current="1.2634", pnl="+$7,920", risk_pct="1.4%"),
            Position(pair="USD/JPY", direction="LONG", notional="$3,000,000", entry="151.45", current="152.18", pnl="+$14,580", risk_pct="1.8%"),
            Position(pair="AUD/USD", direction="SHORT", notional="AUD 2,200,000", entry="0.6589", current="0.6542", pnl="+$10,340", risk_pct="1.2%"),
        ],
        exposures=[
            Exposure(currency="USD", value="+$1,240,000", width="45%", direction="positive"),
            Exposure(currency="EUR", value="+€2,500,000", width="52%", direction="positive"),
            Exposure(currency="GBP", value="-£1,800,000", width="38%", direction="negative"),
            Exposure(currency="JPY", value="+¥456,540,000", width="48%", direction="positive"),
            Exposure(currency="AUD", value="-AUD 2,200,000", width="22%", direction="negative"),
        ],
        var_decomposition=[
            VarComponent(pair="EUR/USD", cvar="$12,840", pct="37.5%"),
            VarComponent(pair="GBP/USD", cvar="$8,210", pct="24.0%"),
            VarComponent(pair="USD/JPY", cvar="$9,150", pct="26.7%"),
            VarComponent(pair="AUD/USD", cvar="$4,018", pct="11.8%"),
        ],
        recent_decisions=[
            RecentDecision(time="14:32", pair="EUR/USD", action="HOLD", reason="All constraints satisfied", type="success"),
            RecentDecision(time="13:45", pair="GBP/USD", action="REDUCE", reason="Soft VaR limit breached (92%)", type="warning"),
            RecentDecision(time="12:18", pair="USD/JPY", action="HOLD", reason="All constraints satisfied", type="success"),
            RecentDecision(time="11:05", pair="AUD/USD", action="HOLD", reason="All constraints satisfied", type="success"),
        ],
    )
