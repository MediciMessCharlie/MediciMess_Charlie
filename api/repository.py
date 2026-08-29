"""Read precomputed Phase 5 artifacts for the HTTP API."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from datetime import date
from functools import lru_cache
from glob import escape
from pathlib import Path
from typing import Any

from ingestion.pipeline import run_pipeline


TRANSACTION_SORT_FIELDS = frozenset(
    {"id", "date", "type", "counterparty", "debit_amount", "credit_amount"}
)


class ArtifactRepositoryError(RuntimeError):
    """Raised when Phase 5 artifacts cannot be read safely."""


class TransactionRepositoryError(RuntimeError):
    """Raised when validated source transactions cannot be loaded."""


class TransactionRepository:
    """Load validated transactions once and provide filtered access."""

    def __init__(
        self,
        source_path: str | Path,
        *,
        loader: Callable[[str | Path], Any] = run_pipeline,
    ) -> None:
        self.source_path = Path(source_path)
        self._loader = loader
        self._transactions: list[dict[str, Any]] | None = None

    def _load(self) -> list[dict[str, Any]]:
        if self._transactions is None:
            result = self._loader(self.source_path)
            if result.source_errors:
                raise TransactionRepositoryError("; ".join(result.source_errors))
            self._transactions = list(result.accepted)

        return self._transactions

    def load_transactions(
        self,
        *,
        branch: str | None = None,
        start: date | None = None,
        end: date | None = None,
        transaction_type: str | None = None,
        search: str | None = None,
        sort_by: str = "date",
        sort_order: str = "asc",
    ) -> list[dict[str, Any]]:
        """Return validated transactions matching the requested filters."""
        if start is not None and end is not None and start > end:
            raise TransactionRepositoryError("start date must not be after end date")
        if sort_by not in TRANSACTION_SORT_FIELDS:
            raise TransactionRepositoryError(f"unsupported sort field: {sort_by}")
        if sort_order not in {"asc", "desc"}:
            raise TransactionRepositoryError("sort order must be asc or desc")

        search_text = None
        if search is not None:
            search_text = search.strip().casefold()
            if not search_text:
                raise TransactionRepositoryError("search must contain text")

        records = []
        for transaction in self._load():
            if branch is not None and transaction["branch"] != branch:
                continue
            if start is not None and transaction["date"] < start:
                continue
            if end is not None and transaction["date"] > end:
                continue
            if (
                transaction_type is not None
                and transaction["type"] != transaction_type
            ):
                continue
            if search_text is not None:
                searchable_text = " ".join(
                    (
                        str(transaction.get("counterparty", "")),
                        str(transaction.get("description", "")),
                    )
                ).casefold()
                if search_text not in searchable_text:
                    continue

            records.append(transaction)

        return sorted(
            records,
            key=lambda transaction: (transaction[sort_by], transaction["id"]),
            reverse=sort_order == "desc",
        )


class ArtifactRepository:
    """Provide read-only access to a Phase 5 artifact directory."""

    def __init__(self, artifact_directory: str | Path) -> None:
        self.artifact_directory = Path(artifact_directory)

    @staticmethod
    def _validate_period_range(start: str | None, end: str | None) -> None:
        if start is not None and end is not None and start > end:
            raise ArtifactRepositoryError("start period must not be after end period")

    def list_branches(self) -> list[str]:
        """Return sorted branch names discovered from KPI artifacts."""
        return sorted({record["branch"] for record in self.load_kpis()})

    @lru_cache(maxsize=128)
    def load_kpis(
        self,
        *,
        branch: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Load filtered KPI records in branch and period order."""
        self._validate_period_range(start, end)

        metrics_directory = self.artifact_directory / "metrics"
        if not metrics_directory.is_dir():
            raise ArtifactRepositoryError(
                f"Metrics directory does not exist: {metrics_directory}"
            )

        records = []
        pattern = f"metrics_{escape(branch)}_*.json" if branch else "metrics_*.json"
        paths = list(metrics_directory.glob(pattern))
        if branch and not paths:
            paths = list(metrics_directory.glob("metrics_*.json"))
        for path in paths:
            with path.open(encoding="utf-8") as source:
                record = json.load(source)

            if branch is not None and record["branch"] != branch:
                continue
            if start is not None and record["period"] < start:
                continue
            if end is not None and record["period"] > end:
                continue

            records.append(record)

        return sorted(
            records,
            key=lambda record: (record["branch"], record["period"]),
        )

    @lru_cache(maxsize=128)
    def load_alerts(
        self,
        *,
        branch: str | None = None,
        start: str | None = None,
        end: str | None = None,
        severity: str | None = None,
    ) -> list[dict[str, Any]]:
        """Load filtered alerts in branch, period, and alert-ID order."""
        self._validate_period_range(start, end)

        alerts_directory = self.artifact_directory / "alerts"
        if not alerts_directory.is_dir():
            raise ArtifactRepositoryError(
                f"Alerts directory does not exist: {alerts_directory}"
            )

        records = []
        pattern = f"alerts_{escape(branch)}_*.json" if branch else "alerts_*.json"
        paths = list(alerts_directory.glob(pattern))
        if branch and not paths:
            paths = list(alerts_directory.glob("alerts_*.json"))
        for path in paths:
            with path.open(encoding="utf-8") as source:
                file_records = json.load(source)

            for record in file_records:
                if branch is not None and record["branch"] != branch:
                    continue
                if start is not None and record["period"] < start:
                    continue
                if end is not None and record["period"] > end:
                    continue
                if severity is not None and record["severity"] != severity:
                    continue

                records.append(record)

        return sorted(
            records,
            key=lambda record: (
                record["branch"],
                record["period"],
                record["alert_id"],
            ),
        )

    @lru_cache(maxsize=128)
    def load_expenses(
        self,
        *,
        branch: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, str]]:
        """Load filtered expense details in deterministic order."""
        self._validate_period_range(start, end)

        expenses_directory = self.artifact_directory / "expenses"
        if not expenses_directory.is_dir():
            raise ArtifactRepositoryError(
                f"Expenses directory does not exist: {expenses_directory}"
            )

        records = []
        pattern = (
            f"expense_breakdown_{escape(branch)}_*.csv"
            if branch
            else "expense_breakdown_*.csv"
        )
        paths = list(expenses_directory.glob(pattern))
        if branch and not paths:
            paths = list(expenses_directory.glob("expense_breakdown_*.csv"))
        for path in paths:
            with path.open(newline="", encoding="utf-8") as source:
                file_records = csv.DictReader(source)

                for record in file_records:
                    if branch is not None and record["branch"] != branch:
                        continue
                    if start is not None and record["period"] < start:
                        continue
                    if end is not None and record["period"] > end:
                        continue

                    records.append(record)

        return sorted(
            records,
            key=lambda record: (
                record["branch"],
                record["period"],
                record["category"],
                record["counterparty"],
            ),
        )

    @lru_cache(maxsize=128)
    def load_loans(
        self,
        *,
        branch: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, str]]:
        """Load filtered monthly loan-activity details."""
        self._validate_period_range(start, end)

        loans_directory = self.artifact_directory / "loans"
        if not loans_directory.is_dir():
            raise ArtifactRepositoryError(
                f"Loans directory does not exist: {loans_directory}"
            )

        records = []
        pattern = (
            f"loan_portfolio_{escape(branch)}_*.csv"
            if branch
            else "loan_portfolio_*.csv"
        )
        paths = list(loans_directory.glob(pattern))
        if branch and not paths:
            paths = list(loans_directory.glob("loan_portfolio_*.csv"))
        for path in paths:
            with path.open(newline="", encoding="utf-8") as source:
                file_records = csv.DictReader(source)

                for record in file_records:
                    if branch is not None and record["branch"] != branch:
                        continue
                    if start is not None and record["period"] < start:
                        continue
                    if end is not None and record["period"] > end:
                        continue

                    records.append(record)

        return sorted(
            records,
            key=lambda record: (
                record["branch"],
                record["period"],
                record["counterparty"],
            ),
        )

    @lru_cache(maxsize=128)
    def load_time_series(
        self,
        *,
        branch: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Load filtered monthly KPI time-series records."""
        self._validate_period_range(start, end)

        time_series_directory = self.artifact_directory / "time_series"
        if not time_series_directory.is_dir():
            raise ArtifactRepositoryError(
                f"Time-series directory does not exist: {time_series_directory}"
            )

        records = []
        pattern = (
            f"time_series_{escape(branch)}.json"
            if branch
            else "time_series_*.json"
        )
        paths = list(time_series_directory.glob(pattern))
        if branch and not paths:
            paths = list(time_series_directory.glob("time_series_*.json"))
        for path in paths:
            with path.open(encoding="utf-8") as source:
                file_records = json.load(source)

            for record in file_records:
                if branch is not None and record["branch"] != branch:
                    continue
                if start is not None and record["period"] < start:
                    continue
                if end is not None and record["period"] > end:
                    continue

                records.append(record)

        return sorted(
            records,
            key=lambda record: (record["branch"], record["period"]),
        )
