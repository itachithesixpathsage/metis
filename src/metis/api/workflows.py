"""Mock-backed market, analytics, portfolio, risk, and workflow endpoints."""

import asyncio
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["market data", "analytics", "simulations", "portfolio", "risk", "decisions", "backtesting", "reports"])


class PricePoint(BaseModel):
    timestamp: datetime
    price: float = Field(gt=0)


class MarketDataResponse(BaseModel):
    symbol: str
    provider: str
    frequency: str
    data: list[PricePoint]


class MarketDataQuery(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=50)
    start: datetime
    end: datetime
    frequency: Literal["5min", "15min", "1h"] = "15min"


class ReturnsRequest(BaseModel):
    prices: list[float] = Field(min_length=2, max_length=100_000)
    method: Literal["simple", "log"] = "simple"


class ReturnsResponse(BaseModel):
    method: str
    returns: list[float]
    mean: float
    volatility: float


class VolatilityRequest(BaseModel):
    returns: list[float] = Field(min_length=2, max_length=100_000)
    annualization_factor: float = Field(default=252.0, gt=0, le=100_000)


class VolatilityResponse(BaseModel):
    volatility: float
    annualized_volatility: float
    observations: int


class SimulationRequest(BaseModel):
    symbol: str = "EURUSD"
    initial_price: float = Field(default=1.085, gt=0)
    drift: float = Field(default=0.0, ge=-2, le=2)
    volatility: float = Field(default=0.1, ge=0, le=5)
    paths: int = Field(default=10_000, ge=100, le=1_000_000)
    steps: int = Field(default=16, ge=1, le=10_000)
    seed: int = 42


class PortfolioPosition(BaseModel):
    symbol: str = Field(pattern=r"^[A-Z]{6}$")
    side: Literal["long", "short"]
    notional: float = Field(gt=0)
    entry_price: float = Field(gt=0)


class PortfolioCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    positions: list[PortfolioPosition] = Field(default_factory=list, max_length=500)


class PortfolioResponse(BaseModel):
    portfolio_id: UUID
    name: str
    base_currency: str
    positions: list[PortfolioPosition]
    created_at: datetime


class RiskRequest(BaseModel):
    returns: list[float] = Field(min_length=2, max_length=100_000)
    confidence: float = Field(default=0.95, gt=0.5, lt=1)


class RiskResponse(BaseModel):
    confidence: float
    var: float
    expected_shortfall: float
    max_drawdown: float


class DecisionRequest(BaseModel):
    symbol: str = Field(pattern=r"^[A-Z]{6}$")
    current_risk: float = Field(ge=0)
    risk_limit: float = Field(gt=0)
    proposed_action: Literal["hold", "increase", "reduce", "close"] = "hold"


class DecisionResponse(BaseModel):
    approved: bool
    action: str
    reason: str
    evaluated_at: datetime


class BacktestRequest(BaseModel):
    symbol: str = Field(default="EURUSD", pattern=r"^[A-Z]{6}$")
    start: datetime
    end: datetime
    strategy: str = Field(default="momentum", min_length=1, max_length=80)
    initial_capital: float = Field(default=100_000, gt=0)


class JobResponse(BaseModel):
    job_id: UUID
    status: Literal["queued", "running", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    result: dict | None = None
    error: str | None = None
    report_id: UUID | None = None


class ReportResponse(BaseModel):
    report_id: UUID
    title: str
    generated_at: datetime
    summary: str
    metrics: dict[str, float | str]


_portfolios: dict[UUID, PortfolioResponse] = {}
_reports: dict[UUID, ReportResponse] = {}
_jobs: dict[UUID, JobResponse] = {}
_FX = {"EURUSD": 1.085, "GBPUSD": 1.271, "USDJPY": 149.8, "AUDUSD": 0.658, "USDCHF": 0.882, "USDCAD": 1.36, "NZDUSD": 0.612}


def _market_series(symbol: str, count: int, frequency: str = "15min") -> list[PricePoint]:
    if symbol not in _FX:
        raise HTTPException(status_code=404, detail={"code": "unknown_symbol", "message": f"Unsupported symbol: {symbol}"})
    interval = {"5min": 5, "15min": 15, "1h": 60}[frequency]
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    price = _FX[symbol]
    return [PricePoint(timestamp=now - timedelta(minutes=interval * (count - i - 1)), price=price * (1 + 0.0002 * math.sin(i / 4))) for i in range(count)]


@router.get("/market-data/{symbol}", response_model=MarketDataResponse, summary="Get mock FX market data")
async def get_market_data(symbol: str) -> MarketDataResponse:
    normalized = symbol.upper()
    return MarketDataResponse(symbol=normalized, provider="synthetic", frequency="15min", data=_market_series(normalized, 96))


@router.post("/market-data/query", response_model=dict[str, MarketDataResponse], summary="Query mock FX market data")
async def query_market_data(request: MarketDataQuery) -> dict[str, MarketDataResponse]:
    if request.start >= request.end:
        raise HTTPException(status_code=422, detail={"code": "invalid_date_range", "message": "start must be earlier than end"})
    seconds_per_bar = {"5min": 300, "15min": 900, "1h": 3600}[request.frequency]
    count = min(500, max(2, int((request.end - request.start).total_seconds() / seconds_per_bar)))
    return {
        symbol.upper(): MarketDataResponse(
            symbol=symbol.upper(),
            provider="synthetic",
            frequency=request.frequency,
            data=_market_series(symbol.upper(), count, request.frequency),
        )
        for symbol in request.symbols
    }


@router.post("/analytics/returns", response_model=ReturnsResponse, summary="Calculate returns from prices")
async def calculate_returns(request: ReturnsRequest) -> ReturnsResponse:
    if any(price <= 0 for price in request.prices):
        raise HTTPException(status_code=422, detail={"code": "invalid_price", "message": "Prices must be greater than zero"})
    values = [(math.log(b / a) if request.method == "log" else b / a - 1) for a, b in zip(request.prices, request.prices[1:])]
    mean = sum(values) / len(values)
    vol = math.sqrt(sum((x - mean) ** 2 for x in values) / max(1, len(values) - 1))
    return ReturnsResponse(method=request.method, returns=values, mean=mean, volatility=vol)


@router.post("/analytics/volatility", response_model=VolatilityResponse, summary="Estimate realized volatility")
async def calculate_volatility(request: VolatilityRequest) -> VolatilityResponse:
    mean = sum(request.returns) / len(request.returns)
    vol = math.sqrt(sum((x - mean) ** 2 for x in request.returns) / (len(request.returns) - 1))
    return VolatilityResponse(volatility=vol, annualized_volatility=vol * math.sqrt(request.annualization_factor), observations=len(request.returns))


async def _run_job(job_id: UUID, kind: str, parameters: dict) -> None:
    _jobs[job_id] = JobResponse(job_id=job_id, status="running", progress=0)
    try:
        rng = random.Random(parameters.get("seed", 42))
        for progress in (10, 25, 45, 65, 85):
            await asyncio.sleep(0.05)
            _jobs[job_id] = JobResponse(job_id=job_id, status="running", progress=progress)
        result = ({"paths": parameters["paths"], "steps": parameters["steps"], "terminal_price_mean": parameters["initial_price"] * math.exp(parameters["drift"] * parameters["steps"] / 252), "sample_seed": rng.randrange(1_000_000)} if kind == "simulation" else {"symbol": parameters["symbol"], "strategy": parameters["strategy"], "total_return": round(rng.uniform(-0.08, 0.18), 4), "initial_capital": parameters["initial_capital"]})
        report_id = uuid4()
        _reports[report_id] = ReportResponse(report_id=report_id, title=f"{kind.title()} report", generated_at=datetime.now(timezone.utc), summary="Generated from deterministic mock inputs.", metrics={k: v for k, v in result.items() if isinstance(v, (int, float, str))})
        _jobs[job_id] = JobResponse(job_id=job_id, status="completed", progress=100, result=result, report_id=report_id)
    except Exception as exc:
        _jobs[job_id] = JobResponse(job_id=job_id, status="failed", progress=100, error=str(exc))


@router.post("/simulations", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, summary="Submit an asynchronous simulation")
async def submit_simulation(request: SimulationRequest, background_tasks: BackgroundTasks) -> JobResponse:
    job_id = uuid4()
    _jobs[job_id] = JobResponse(job_id=job_id, status="queued", progress=0)
    background_tasks.add_task(_run_job, job_id, "simulation", request.model_dump())
    return _jobs[job_id]


@router.post("/backtesting/run", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, summary="Submit an asynchronous backtest")
async def submit_backtest(request: BacktestRequest, background_tasks: BackgroundTasks) -> JobResponse:
    if request.start >= request.end:
        raise HTTPException(status_code=422, detail={"code": "invalid_date_range", "message": "start must be earlier than end"})
    job_id = uuid4()
    _jobs[job_id] = JobResponse(job_id=job_id, status="queued", progress=0)
    background_tasks.add_task(_run_job, job_id, "backtest", request.model_dump())
    return _jobs[job_id]


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get asynchronous job progress")
async def get_job(job_id: UUID) -> JobResponse:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail={"code": "job_not_found", "message": "Job not found"})
    return job


@router.post("/portfolio", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED, summary="Create an in-memory mock portfolio")
async def create_portfolio(request: PortfolioCreateRequest) -> PortfolioResponse:
    portfolio_id = uuid4()
    portfolio = PortfolioResponse(portfolio_id=portfolio_id, name=request.name, base_currency=request.base_currency, positions=request.positions, created_at=datetime.now(timezone.utc))
    _portfolios[portfolio_id] = portfolio
    return portfolio


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioResponse, summary="Get a mock portfolio")
async def get_portfolio(portfolio_id: UUID) -> PortfolioResponse:
    portfolio = _portfolios.get(portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail={"code": "portfolio_not_found", "message": "Portfolio not found"})
    return portfolio


@router.post("/risk/analyze", response_model=RiskResponse, summary="Calculate mock historical portfolio risk")
async def analyze_risk(request: RiskRequest) -> RiskResponse:
    values = sorted(request.returns)
    index = max(0, min(len(values) - 1, math.floor((1 - request.confidence) * len(values))))
    tail = values[:index + 1]
    peak = 1.0
    equity = 1.0
    drawdown = 0.0
    for value in request.returns:
        equity *= 1 + value
        peak = max(peak, equity)
        drawdown = max(drawdown, (peak - equity) / peak)
    return RiskResponse(confidence=request.confidence, var=max(0.0, -values[index]), expected_shortfall=max(0.0, -sum(tail) / len(tail)), max_drawdown=drawdown)


@router.post("/decisions/evaluate", response_model=DecisionResponse, summary="Evaluate a risk-limit decision")
async def evaluate_decision(request: DecisionRequest) -> DecisionResponse:
    breach = request.current_risk >= request.risk_limit
    action = "reduce" if breach and request.proposed_action in ("hold", "increase") else request.proposed_action
    return DecisionResponse(approved=not (breach and request.proposed_action == "increase"), action=action, reason="Risk limit reached; reduce exposure" if breach else "Risk remains within configured limit", evaluated_at=datetime.now(timezone.utc))


@router.get("/report/{report_id}", response_model=ReportResponse, summary="Get a completed workflow report")
async def get_report(report_id: UUID) -> ReportResponse:
    report = _reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail={"code": "report_not_found", "message": "Report not found"})
    return report
