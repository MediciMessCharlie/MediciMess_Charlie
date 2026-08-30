"""HTTP API for MediciMess serving data."""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from dashboard.network import summarize_network

from .repository import (
    ArtifactRepository,
    ArtifactRepositoryError,
    TransactionRepository,
    TransactionRepositoryError,
)


PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
DEFAULT_ARTIFACT_DIRECTORY = Path(__file__).resolve().parents[1] / "sample_serving_outputs"
DEFAULT_TRANSACTION_SOURCE = Path(__file__).resolve().parents[1] / "medici_transactions.csv"
CASHFLOW_FIELDS = (
    "branch",
    "period",
    "total_cash_inflows",
    "total_cash_outflows",
    "net_cash_movement",
    "closing_cash_balance",
)


app = FastAPI(
    title="MediciMess API",
    description="Read-only access to MediciMess dashboard data.",
    version="0.1.0",
)


@app.exception_handler(HTTPException)
def handle_http_error(_request: Request, error: HTTPException) -> JSONResponse:
    """Return application errors in one predictable JSON envelope."""
    codes = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        503: "DATA_UNAVAILABLE",
    }
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": codes.get(error.status_code, "HTTP_ERROR"),
                "message": str(error.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(
    _request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    """Return query-validation errors in the shared error envelope."""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": jsonable_encoder(error.errors()),
            }
        },
    )


@lru_cache(maxsize=1)
def get_repository() -> ArtifactRepository:
    """Reuse a repository for the configured Phase 5 output directory."""
    artifact_directory = os.environ.get(
        "MEDICIMESS_ARTIFACT_DIRECTORY",
        str(DEFAULT_ARTIFACT_DIRECTORY),
    )
    return ArtifactRepository(artifact_directory)


@lru_cache(maxsize=1)
def get_transaction_repository() -> TransactionRepository:
    """Reuse one validated transaction repository across API requests."""
    source_path = os.environ.get(
        "MEDICIMESS_TRANSACTION_SOURCE",
        str(DEFAULT_TRANSACTION_SOURCE),
    )
    return TransactionRepository(source_path)


def serialize_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    """Convert internal date and Decimal values to stable JSON values."""
    serialized = {}
    for field, value in transaction.items():
        if isinstance(value, date):
            serialized[field] = value.isoformat()
        elif isinstance(value, Decimal):
            serialized[field] = str(value)
        else:
            serialized[field] = value
    return serialized


def serialize_decimals(value: Any) -> Any:
    """Recursively preserve decimal precision in network API responses."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: serialize_decimals(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_decimals(item) for item in value]
    return value


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Confirm that the API process is available."""
    return {
        "status": "ok",
        "service": "medicimess-api",
    }


@app.get("/api/branches", tags=["dashboard"])
def read_branches(
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return branches currently available in Phase 5 KPI artifacts."""
    try:
        branches = repository.list_branches()
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "count": len(branches),
        "items": branches,
    }


@app.get("/api/kpis", tags=["dashboard"])
def read_kpis(
    branch: Annotated[str, Query(min_length=1)],
    start: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    end: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return precomputed monthly KPI records for a branch and period range."""
    try:
        records = repository.load_kpis(branch=branch, start=start, end=end)
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "count": len(records),
        "items": records,
    }


@app.get("/api/alerts", tags=["dashboard"])
def read_alerts(
    branch: Annotated[str, Query(min_length=1)],
    start: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    end: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    severity: Literal["LOW", "MEDIUM", "HIGH"] | None = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return precomputed anomaly alerts for a branch and period range."""
    try:
        records = repository.load_alerts(
            branch=branch,
            start=start,
            end=end,
            severity=severity,
        )
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "count": len(records),
        "items": records,
    }


@app.get("/api/network/summary", tags=["dashboard"])
def read_network_summary(
    start: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    end: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return cross-branch KPI comparisons, totals, and outliers."""
    try:
        kpi_records = repository.load_kpis(start=start, end=end)
        alerts = repository.load_alerts(start=start, end=end)
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return serialize_decimals(summarize_network(kpi_records, alerts))


@app.get("/api/expenses", tags=["dashboard"])
def read_expenses(
    branch: Annotated[str, Query(min_length=1)],
    start: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    end: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return precomputed expense details for a branch and period range."""
    try:
        records = repository.load_expenses(branch=branch, start=start, end=end)
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "count": len(records),
        "items": records,
    }


@app.get("/api/loans", tags=["dashboard"])
def read_loans(
    branch: Annotated[str, Query(min_length=1)],
    start: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    end: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return precomputed monthly loan activity for a branch and period range."""
    try:
        records = repository.load_loans(branch=branch, start=start, end=end)
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "count": len(records),
        "items": records,
    }


@app.get("/api/cashflow", tags=["dashboard"])
def read_cashflow(
    branch: Annotated[str, Query(min_length=1)],
    start: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    end: Annotated[str | None, Query(pattern=PERIOD_PATTERN)] = None,
    granularity: Literal["monthly"] = "monthly",
    repository: ArtifactRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Return chart-ready monthly cash-flow data from precomputed KPIs."""
    try:
        kpi_records = repository.load_time_series(
            branch=branch,
            start=start,
            end=end,
        )
    except ArtifactRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    records = [
        {field: record[field] for field in CASHFLOW_FIELDS}
        for record in kpi_records
    ]
    return {
        "granularity": granularity,
        "count": len(records),
        "items": records,
    }


@app.get("/api/transactions", tags=["dashboard"])
def read_transactions(
    branch: Annotated[str, Query(min_length=1)],
    start: date | None = None,
    end: date | None = None,
    transaction_type: Annotated[str | None, Query(alias="type")] = None,
    search: Annotated[str | None, Query(min_length=1)] = None,
    sort_by: Literal[
        "id", "date", "type", "counterparty", "debit_amount", "credit_amount"
    ] = "date",
    sort_order: Literal["asc", "desc"] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 25,
    repository: TransactionRepository = Depends(get_transaction_repository),
) -> dict[str, Any]:
    """Return a filtered and paginated validated transaction ledger."""
    try:
        records = repository.load_transactions(
            branch=branch,
            start=start,
            end=end,
            transaction_type=transaction_type,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except TransactionRepositoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    total = len(records)
    total_pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    page_records = records[offset:offset + per_page]

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "items": [serialize_transaction(record) for record in page_records],
    }
