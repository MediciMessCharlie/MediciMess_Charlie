"""HTTP client used by the Dash application to call Phase 6A."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .access import can_view_branch, can_view_network
from .auth import current_user


DEFAULT_API_URL = "http://127.0.0.1:8000"


class DashboardAPIError(RuntimeError):
    """Raised when dashboard data cannot be retrieved safely."""


class DashboardAPIClient:
    """Small read-only client for the Phase 6A API."""

    def __init__(
        self,
        base_url: str,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or httpx.Client(timeout=10.0)

    @classmethod
    def from_environment(cls) -> "DashboardAPIClient":
        """Build a client using the configured API URL."""
        return cls(os.environ.get("MEDICIMESS_API_URL", DEFAULT_API_URL))

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        try:
            response = self.http_client.get(
                f"{self.base_url}{path}",
                params=params,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            try:
                message = error.response.json()["error"]["message"]
            except (KeyError, TypeError, ValueError):
                message = f"API returned HTTP {error.response.status_code}"
            raise DashboardAPIError(message) from error
        except httpx.RequestError as error:
            raise DashboardAPIError("The MediciMess API is unavailable.") from error

        payload = response.json()
        if not isinstance(payload, dict):
            raise DashboardAPIError("The API returned an invalid response.")
        return payload

    def _get_items(self, path: str, **params: Any) -> list[Any]:
        payload = self._get(path, **params)
        items = payload.get("items")
        if not isinstance(items, list):
            raise DashboardAPIError("The API returned an invalid item list.")
        return items

    @staticmethod
    def _authorize_branch(branch: str) -> None:
        """Reject a branch request outside the signed-in user's assignment."""
        user = current_user()
        if user is not None and not can_view_branch(user, branch):
            raise DashboardAPIError("You are not authorized to view this branch.")

    def get_branches(self) -> list[str]:
        """Return branches available to the dashboard."""
        branches = self._get_items("/api/branches")
        if not all(
            isinstance(branch, str) for branch in branches
        ):
            raise DashboardAPIError("The API returned an invalid branch list.")
        return branches

    def get_kpis(
        self,
        branch: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return monthly KPI records used to discover available periods."""
        self._authorize_branch(branch)
        params = {"branch": branch}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        records = self._get_items("/api/kpis", **params)
        if not all(isinstance(record, dict) for record in records):
            raise DashboardAPIError("The API returned an invalid KPI list.")
        return records

    def get_alerts(
        self,
        branch: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return alerts used by dashboard summaries and panels."""
        self._authorize_branch(branch)
        params = {"branch": branch}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        records = self._get_items("/api/alerts", **params)
        if not all(isinstance(record, dict) for record in records):
            raise DashboardAPIError("The API returned an invalid alert list.")
        return records

    def get_network_summary(
        self,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> dict[str, Any]:
        """Return cross-branch comparisons, totals, and outlier details."""
        user = current_user()
        if user is not None and not can_view_network(user):
            raise DashboardAPIError("You are not authorized to view the network.")
        params = {}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        payload = self._get("/api/network/summary", **params)
        branches = payload.get("branches")
        totals = payload.get("totals")
        outliers = payload.get("outliers")
        if (
            not isinstance(branches, list)
            or not all(isinstance(row, dict) for row in branches)
            or not isinstance(totals, dict)
            or not isinstance(outliers, list)
            or not all(isinstance(outlier, dict) for outlier in outliers)
        ):
            raise DashboardAPIError("The API returned an invalid network summary.")
        return payload

    def get_cashflow(
        self,
        branch: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return monthly cash-flow records for dashboard charts."""
        self._authorize_branch(branch)
        params = {"branch": branch, "granularity": "monthly"}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        records = self._get_items("/api/cashflow", **params)
        if not all(isinstance(record, dict) for record in records):
            raise DashboardAPIError("The API returned an invalid cash-flow list.")
        return records

    def get_expenses(
        self,
        branch: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return expense-detail records for dashboard analysis."""
        self._authorize_branch(branch)
        params = {"branch": branch}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        records = self._get_items("/api/expenses", **params)
        if not all(isinstance(record, dict) for record in records):
            raise DashboardAPIError("The API returned an invalid expense list.")
        return records

    def get_loans(
        self,
        branch: str,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return observable monthly loan-activity records."""
        self._authorize_branch(branch)
        params = {"branch": branch}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        records = self._get_items("/api/loans", **params)
        if not all(isinstance(record, dict) for record in records):
            raise DashboardAPIError("The API returned an invalid loan list.")
        return records

    def get_transactions(self, branch: str, **filters: Any) -> dict[str, Any]:
        """Return one validated, paginated transaction response."""
        self._authorize_branch(branch)
        params = {"branch": branch}
        params.update(
            {key: value for key, value in filters.items() if value is not None}
        )
        payload = self._get("/api/transactions", **params)
        items = payload.get("items")
        metadata = ("page", "per_page", "total", "total_pages")
        if (
            not isinstance(items, list)
            or not all(isinstance(record, dict) for record in items)
            or not all(isinstance(payload.get(field), int) for field in metadata)
        ):
            raise DashboardAPIError("The API returned an invalid transaction page.")
        return payload
