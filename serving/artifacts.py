"""Generate stable Phase 5 artifacts from precomputed Phase 3/4 outputs."""

from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from .contracts import (
    EXPENSE_FIELDS,
    LOAN_FIELDS,
    ServingContractError,
    validate_alert,
    validate_expense_detail,
    validate_kpi,
    validate_loan_detail,
)


Partition = tuple[str, str]


@dataclass(frozen=True)
class ServingManifest:
    """Paths written during one serving-layer run."""

    metric_files: tuple[Path, ...]
    time_series_files: tuple[Path, ...]
    alert_files: tuple[Path, ...]
    expense_files: tuple[Path, ...]
    loan_files: tuple[Path, ...]

    @property
    def all_files(self) -> tuple[Path, ...]:
        return (
            self.metric_files
            + self.time_series_files
            + self.alert_files
            + self.expense_files
            + self.loan_files
        )


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _safe_component(value: str) -> str:
    component = re.sub(r"[^A-Za-z0-9.-]+", "_", value.strip()).strip("._")
    if not component:
        raise ServingContractError("branch cannot form a safe filename")
    return component


def _atomic_text_write(path: Path, writer: Callable[[Any], None], *, newline: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline=newline,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            writer(temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _write_json(path: Path, payload: Any) -> Path:
    def write(output: Any) -> None:
        json.dump(_json_value(payload), output, indent=2, sort_keys=True)
        output.write("\n")

    _atomic_text_write(path, write)
    return path


def _write_csv(path: Path, records: list[Mapping[str, Any]], fields: tuple[str, ...]) -> Path:
    def write(output: Any) -> None:
        writer = csv.DictWriter(
            output,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for record in records:
            writer.writerow({field: _json_value(record[field]) for field in fields})

    _atomic_text_write(path, write, newline="")
    return path


def _partition(record: Mapping[str, Any]) -> Partition:
    return record["branch"], record["period"]


def _group_by_partition(records: Iterable[Mapping[str, Any]]) -> dict[Partition, list[Mapping[str, Any]]]:
    grouped: dict[Partition, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[_partition(record)].append(record)
    return dict(grouped)


def write_serving_artifacts(
    *,
    kpi_records: Iterable[Mapping[str, Any]],
    alert_records: Iterable[Mapping[str, Any]],
    expense_details: Iterable[Mapping[str, Any]],
    loan_details: Iterable[Mapping[str, Any]],
    output_directory: str | Path,
) -> ServingManifest:
    """Validate, partition, and write all required Phase 5 artifacts."""
    kpis = [validate_kpi(record) for record in kpi_records]
    alerts = [validate_alert(record) for record in alert_records]
    expenses = [validate_expense_detail(record) for record in expense_details]
    loans = [validate_loan_detail(record) for record in loan_details]

    kpi_by_partition: dict[Partition, Mapping[str, Any]] = {}
    for record in kpis:
        partition = _partition(record)
        if partition in kpi_by_partition:
            raise ServingContractError(
                f"duplicate KPI record for {partition[0]} {partition[1]}"
            )
        kpi_by_partition[partition] = record

    known_partitions = set(kpi_by_partition)
    for name, records in (
        ("alert", alerts), ("expense", expenses), ("loan", loans)
    ):
        unknown = sorted({_partition(record) for record in records} - known_partitions)
        if unknown:
            branch, period = unknown[0]
            raise ServingContractError(
                f"{name} record has no matching KPI partition: {branch} {period}"
            )

    alerts_by_partition = _group_by_partition(alerts)
    expenses_by_partition = _group_by_partition(expenses)
    loans_by_partition = _group_by_partition(loans)
    kpis_by_branch: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in kpis:
        kpis_by_branch[record["branch"]].append(record)

    root = Path(output_directory)
    metric_paths = []
    alert_paths = []
    expense_paths = []
    loan_paths = []

    for branch, period in sorted(known_partitions):
        safe_branch = _safe_component(branch)
        partition = (branch, period)
        metric_paths.append(
            _write_json(
                root / "metrics" / f"metrics_{safe_branch}_{period}.json",
                kpi_by_partition[partition],
            )
        )
        alert_paths.append(
            _write_json(
                root / "alerts" / f"alerts_{safe_branch}_{period}.json",
                sorted(
                    alerts_by_partition.get(partition, []),
                    key=lambda record: record["alert_id"],
                ),
            )
        )
        expense_paths.append(
            _write_csv(
                root / "expenses" / f"expense_breakdown_{safe_branch}_{period}.csv",
                sorted(
                    expenses_by_partition.get(partition, []),
                    key=lambda record: (record["category"], record["counterparty"]),
                ),
                EXPENSE_FIELDS,
            )
        )
        loan_paths.append(
            _write_csv(
                root / "loans" / f"loan_portfolio_{safe_branch}_{period}.csv",
                sorted(
                    loans_by_partition.get(partition, []),
                    key=lambda record: record["counterparty"],
                ),
                LOAN_FIELDS,
            )
        )

    time_series_paths = []
    for branch in sorted(kpis_by_branch):
        safe_branch = _safe_component(branch)
        time_series_paths.append(
            _write_json(
                root / "time_series" / f"time_series_{safe_branch}.json",
                sorted(kpis_by_branch[branch], key=lambda record: record["period"]),
            )
        )

    return ServingManifest(
        metric_files=tuple(metric_paths),
        time_series_files=tuple(time_series_paths),
        alert_files=tuple(alert_paths),
        expense_files=tuple(expense_paths),
        loan_files=tuple(loan_paths),
    )
