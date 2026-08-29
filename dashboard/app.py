"""Dash application for the MediciMess branch manager dashboard."""

from calendar import monthrange
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dash import Dash, Input, Output, State, ctx, dcc, html
import plotly.graph_objects as go

from .client import DashboardAPIClient, DashboardAPIError


ASSETS_DIRECTORY = Path(__file__).with_name("assets")

app = Dash(
    __name__,
    assets_folder=str(ASSETS_DIRECTORY),
    title="Medici Bank Branch Operations",
)
server = app.server
api_client = DashboardAPIClient.from_environment()

app.layout = html.Div(
    id="dashboard-shell",
    children=[
        html.Header(
            className="top-bar",
            children=[
                html.Div(
                    children=[
                        html.P("MEDICI BANK", className="eyebrow"),
                        html.H1("Branch Operations Dashboard"),
                    ]
                ),
                html.Div(
                    "Phase 6B",
                    className="phase-badge",
                ),
            ],
        ),
        html.Main(
            className="dashboard-content",
            children=[
                dcc.Location(id="dashboard-url", refresh=False),
                html.Section(
                    id="global-filters",
                    className="panel filter-panel",
                    children=[
                        html.H2("Branch and reporting period"),
                        html.Div(
                            className="filter-grid",
                            children=[
                                html.Div(
                                    children=[
                                        html.Label(
                                            "Branch",
                                            htmlFor="branch-selector",
                                        ),
                                        dcc.Dropdown(
                                            id="branch-selector",
                                            options=[],
                                            placeholder="Select a branch",
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label(
                                            "Start period",
                                            htmlFor="start-period-selector",
                                        ),
                                        dcc.Dropdown(
                                            id="start-period-selector",
                                            options=[],
                                            placeholder="Start month",
                                            clearable=False,
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label(
                                            "End period",
                                            htmlFor="end-period-selector",
                                        ),
                                        dcc.Dropdown(
                                            id="end-period-selector",
                                            options=[],
                                            placeholder="End month",
                                            clearable=False,
                                        ),
                                    ]
                                ),
                            ],
                        ),
                        html.Div(id="branch-load-error", className="error-message"),
                        html.Div(id="period-load-error", className="error-message"),
                    ],
                ),
                html.Section(
                    id="kpi-panel",
                    children=[
                        html.Div(
                            className="section-heading",
                            children=[
                                html.P("FINANCIAL POSITION", className="eyebrow"),
                                html.H2("Key performance indicators"),
                            ],
                        ),
                        html.P(
                            "Modeled cash position is cumulative observed cash "
                            "movement from a zero opening balance; the source does "
                            "not provide historical opening cash-on-hand.",
                            className="panel-note",
                        ),
                        html.Div(
                            id="kpi-card-grid",
                            className="kpi-card-grid",
                            children=[
                                html.Div(
                                    "Select a branch and reporting period.",
                                    className="panel",
                                )
                            ],
                        ),
                    ],
                ),
                html.Section(
                    id="dashboard-panels",
                    className="panel",
                    children=[
                        html.Div(
                            className="section-heading",
                            children=[
                                html.P("LIQUIDITY", className="eyebrow"),
                                html.H2("Cash-flow trends"),
                            ],
                        ),
                        html.Div(id="cashflow-error", className="error-message"),
                        html.Div(
                            className="chart-grid",
                            children=[
                                dcc.Graph(
                                    id="cash-balance-chart",
                                    config={"displaylogo": False, "responsive": True},
                                ),
                                dcc.Graph(
                                    id="cash-movement-chart",
                                    config={"displaylogo": False, "responsive": True},
                                ),
                            ],
                        ),
                        html.Div(
                            children=[
                                html.H3("Cash-flow data table"),
                                html.Div(id="cashflow-table"),
                            ],
                        ),
                    ],
                ),
                html.Section(
                    id="expense-panel",
                    className="panel",
                    children=[
                        html.Div(
                            className="section-heading",
                            children=[
                                html.P("OPERATING COSTS", className="eyebrow"),
                                html.H2("Expense breakdown"),
                            ],
                        ),
                        html.Div(id="expense-error", className="error-message"),
                        html.Div(
                            className="chart-grid",
                            children=[
                                dcc.Graph(
                                    id="expense-category-chart",
                                    config={"displaylogo": False, "responsive": True},
                                ),
                                html.Div(
                                    children=[
                                        html.H3("Top expense counterparties"),
                                        html.Div(id="expense-counterparty-table"),
                                    ]
                                ),
                            ],
                        ),
                    ],
                ),
                html.Section(
                    id="loan-panel",
                    className="panel",
                    children=[
                        html.Div(
                            className="section-heading",
                            children=[
                                html.P("CREDIT ACTIVITY", className="eyebrow"),
                                html.H2("Loan issuance and repayment"),
                            ],
                        ),
                        html.P(
                            "This panel shows observable monthly activity, not "
                            "individual open-loan status or outstanding balances.",
                            className="panel-note",
                        ),
                        html.Div(id="loan-error", className="error-message"),
                        html.Div(
                            className="chart-grid",
                            children=[
                                dcc.Graph(
                                    id="loan-activity-chart",
                                    config={"displaylogo": False, "responsive": True},
                                    className="dashboard-chart",
                                ),
                                dcc.Graph(
                                    id="loan-counterparty-chart",
                                    config={"displaylogo": False, "responsive": True},
                                    className="dashboard-chart",
                                ),
                            ],
                        ),
                        html.Div(
                            children=[
                                html.H3("Counterparty loan activity"),
                                html.Div(id="loan-activity-table"),
                            ]
                        ),
                    ],
                ),
                html.Section(
                    id="bill-panel",
                    className="panel",
                    children=[
                        html.Div(
                            className="section-heading bill-heading",
                            children=[
                                html.Div(
                                    children=[
                                        html.P("CORRESPONDENT BANKING", className="eyebrow"),
                                        html.H2("Bills of exchange activity"),
                                    ]
                                ),
                                dcc.Input(
                                    id="bill-page",
                                    type="number",
                                    min=1,
                                    step=1,
                                    value=1,
                                    className="page-input",
                                ),
                            ],
                        ),
                        html.P(
                            "Observable ledger entries only. The source does not "
                            "provide expected settlement dates, settlement status, "
                            "or overdue days.",
                            className="panel-note",
                        ),
                        html.Div(id="bill-error", className="error-message"),
                        html.P(id="bill-page-summary", className="panel-note"),
                        html.Div(id="bill-table"),
                    ],
                ),
                html.Section(
                    id="alert-panel",
                    className="panel",
                    children=[
                        html.Div(
                            className="section-heading alert-heading",
                            children=[
                                html.Div(
                                    children=[
                                        html.P("RISK REVIEW", className="eyebrow"),
                                        html.H2("Anomaly alerts"),
                                    ]
                                ),
                                dcc.Dropdown(
                                    id="alert-severity-selector",
                                    options=[
                                        {"label": "All severities", "value": "ALL"},
                                        {"label": "High", "value": "HIGH"},
                                        {"label": "Medium", "value": "MEDIUM"},
                                        {"label": "Low", "value": "LOW"},
                                    ],
                                    value="ALL",
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.P(
                            "Alerts are read-only in Phase 6; review status comes "
                            "from the precomputed Phase 4 artifact.",
                            className="panel-note",
                        ),
                        html.Div(id="alert-error", className="error-message"),
                        html.Div(id="alert-summary", className="alert-summary-grid"),
                        html.Div(id="alert-table"),
                    ],
                ),
                html.Section(
                    id="transaction-panel",
                    className="panel",
                    children=[
                        html.Div(
                            className="section-heading",
                            children=[
                                html.P("VALIDATED LEDGER", className="eyebrow"),
                                html.H2("Transaction review"),
                            ],
                        ),
                        html.Div(
                            className="transaction-controls",
                            children=[
                                dcc.Input(
                                    id="transaction-search",
                                    type="search",
                                    placeholder="Search counterparty or description",
                                    debounce=True,
                                ),
                                dcc.Dropdown(
                                    id="transaction-type-selector",
                                    options=[
                                        {"label": value.replace("_", " ").title(), "value": value}
                                        for value in (
                                            "deposit", "withdrawal", "loan_issuance",
                                            "loan_repayment", "operating_expense",
                                            "bill_of_exchange", "trading", "alum_trade",
                                            "war_financing", "ransom_payment",
                                        )
                                    ],
                                    placeholder="All transaction types",
                                    clearable=True,
                                ),
                                dcc.Dropdown(
                                    id="transaction-sort-selector",
                                    options=[
                                        {"label": "Date", "value": "date"},
                                        {"label": "ID", "value": "id"},
                                        {"label": "Type", "value": "type"},
                                        {"label": "Counterparty", "value": "counterparty"},
                                        {"label": "Debit amount", "value": "debit_amount"},
                                        {"label": "Credit amount", "value": "credit_amount"},
                                    ],
                                    value="date",
                                    clearable=False,
                                ),
                                dcc.Dropdown(
                                    id="transaction-order-selector",
                                    options=[
                                        {"label": "Ascending", "value": "asc"},
                                        {"label": "Descending", "value": "desc"},
                                    ],
                                    value="asc",
                                    clearable=False,
                                ),
                                html.Div(
                                    className="pagination-controls",
                                    children=[
                                        html.Button(
                                            "Previous",
                                            id="transaction-previous-page",
                                            n_clicks=0,
                                            type="button",
                                        ),
                                        dcc.Input(
                                            id="transaction-page",
                                            type="number",
                                            min=1,
                                            step=1,
                                            value=1,
                                        ),
                                        html.Button(
                                            "Next",
                                            id="transaction-next-page",
                                            n_clicks=0,
                                            type="button",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        dcc.Store(
                            id="transaction-pagination-metadata",
                            data={"total_pages": 1},
                        ),
                        html.Div(id="transaction-error", className="error-message"),
                        html.P(id="transaction-page-summary", className="panel-note"),
                        html.Div(id="transaction-table"),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("branch-selector", "options"),
    Output("branch-selector", "value"),
    Output("branch-load-error", "children"),
    Input("dashboard-url", "pathname"),
)
def load_branch_controls(_pathname):
    """Populate the branch selector from Phase 6A data."""
    try:
        branches = api_client.get_branches()
    except DashboardAPIError as error:
        return [], None, str(error)

    options = [{"label": branch, "value": branch} for branch in branches]
    value = "Florence" if "Florence" in branches else (branches[0] if branches else None)
    message = "" if branches else "No branches are available."
    return options, value, message


@app.callback(
    Output("start-period-selector", "options"),
    Output("start-period-selector", "value"),
    Output("end-period-selector", "options"),
    Output("end-period-selector", "value"),
    Output("period-load-error", "children"),
    Input("branch-selector", "value"),
)
def load_period_controls(branch):
    """Populate the reporting-period range for the selected branch."""
    if not branch:
        return [], None, [], None, ""

    try:
        records = api_client.get_kpis(branch)
    except DashboardAPIError as error:
        return [], None, [], None, str(error)

    periods = sorted({record["period"] for record in records})
    options = [{"label": period, "value": period} for period in periods]
    if not periods:
        return [], None, [], None, "No reporting periods are available."
    default_start = periods[max(0, len(periods) - 12)]
    return options, default_start, options, periods[-1], ""


def format_florins(value) -> str:
    """Format a serialized financial value for dashboard display."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return "N/A"
    return f"{amount:,.2f} florins"


def prior_year_period(period: str) -> str:
    """Shift a YYYY-MM reporting period back by one year."""
    year, month = period.split("-")
    return f"{int(year) - 1:04d}-{month}"


def format_delta(current, previous, *, financial: bool = True) -> tuple[str, str]:
    """Return a factual prior-year delta label and CSS state."""
    if previous is None:
        return "Prior-year data unavailable", "delta-unavailable"
    difference = Decimal(str(current)) - Decimal(str(previous))
    if difference > 0:
        symbol, state = "▲", "delta-up"
    elif difference < 0:
        symbol, state = "▼", "delta-down"
    else:
        symbol, state = "—", "delta-flat"
    magnitude = abs(difference)
    value = format_florins(magnitude) if financial else f"{int(magnitude):,}"
    return f"{symbol} {value} vs prior year", state


def create_kpi_card(
    label: str,
    value: str,
    *,
    delta: tuple[str, str] | None = None,
    alert: bool = False,
):
    """Create one consistently styled KPI card."""
    class_name = "kpi-card kpi-card-alert" if alert else "kpi-card"
    delta_text, delta_class = delta or (
        "Prior-year data unavailable",
        "delta-unavailable",
    )
    return html.Article(
        className=class_name,
        children=[
            html.H3(label),
            html.P(value, className="kpi-value"),
            html.P(delta_text, className=f"kpi-delta {delta_class}"),
        ],
    )


@app.callback(
    Output("kpi-card-grid", "children"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
)
def load_kpi_cards(branch, start, end):
    """Build KPI cards for the selected branch and reporting range."""
    if not branch or not start or not end:
        return [html.Div("Select a branch and reporting period.", className="panel")]

    try:
        records = api_client.get_kpis(branch, start=start, end=end)
        alerts = api_client.get_alerts(branch, start=start, end=end)
    except DashboardAPIError as error:
        return [html.Div(str(error), className="panel error-message")]

    if not records:
        return [html.Div("No KPI data is available for this range.", className="panel")]

    prior_start = prior_year_period(start)
    prior_end = prior_year_period(end)
    try:
        prior_records = api_client.get_kpis(
            branch, start=prior_start, end=prior_end
        )
        prior_alerts = api_client.get_alerts(
            branch, start=prior_start, end=prior_end
        )
        if not prior_records:
            prior_alerts = None
    except DashboardAPIError:
        prior_records, prior_alerts = [], None

    latest = max(records, key=lambda record: record["period"])
    prior_latest = (
        max(prior_records, key=lambda record: record["period"])
        if prior_records
        else None
    )

    def total(source, field):
        return sum((Decimal(str(record[field])) for record in source), Decimal("0"))

    def financial_delta(current, field, *, snapshot=False):
        if not prior_records:
            return format_delta(current, None)
        previous = (
            Decimal(str(prior_latest[field]))
            if snapshot
            else total(prior_records, field)
        )
        return format_delta(current, previous)

    deposits = total(records, "total_deposits")
    withdrawals = total(records, "total_withdrawals")
    income = total(records, "net_income")

    return [
        create_kpi_card(
            "Modeled Cash Position",
            format_florins(latest["closing_cash_balance"]),
            delta=financial_delta(
                Decimal(str(latest["closing_cash_balance"])),
                "closing_cash_balance",
                snapshot=True,
            ),
        ),
        create_kpi_card(
            "Total Deposits",
            format_florins(deposits),
            delta=financial_delta(deposits, "total_deposits"),
        ),
        create_kpi_card(
            "Total Withdrawals",
            format_florins(withdrawals),
            delta=financial_delta(withdrawals, "total_withdrawals"),
        ),
        create_kpi_card(
            "Loan Portfolio Balance",
            format_florins(latest["loan_portfolio_balance"]),
            delta=financial_delta(
                Decimal(str(latest["loan_portfolio_balance"])),
                "loan_portfolio_balance",
                snapshot=True,
            ),
        ),
        create_kpi_card(
            "Net Income",
            format_florins(income),
            delta=financial_delta(income, "net_income"),
        ),
        create_kpi_card(
            "Flagged Transactions",
            f"{len(alerts):,}",
            delta=format_delta(
                len(alerts),
                len(prior_alerts) if prior_alerts is not None else None,
                financial=False,
            ),
            alert=bool(alerts),
        ),
    ]


def empty_chart(message: str) -> go.Figure:
    """Return a themed empty chart with a readable status message."""
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
    )
    figure.update_layout(
        paper_bgcolor="#fffdf8",
        plot_bgcolor="#fffdf8",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figure


def create_cashflow_table(records):
    """Create a text alternative for the cash-flow charts."""
    headers = ["Period", "Inflows", "Outflows", "Net movement", "Closing balance"]
    return html.Table(
        className="data-table",
        children=[
            html.Thead(html.Tr([html.Th(header) for header in headers])),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(record["period"]),
                            html.Td(format_florins(record["total_cash_inflows"])),
                            html.Td(format_florins(record["total_cash_outflows"])),
                            html.Td(format_florins(record["net_cash_movement"])),
                            html.Td(format_florins(record["closing_cash_balance"])),
                        ]
                    )
                    for record in records
                ]
            ),
        ],
    )


@app.callback(
    Output("cash-balance-chart", "figure"),
    Output("cash-movement-chart", "figure"),
    Output("cashflow-table", "children"),
    Output("cashflow-error", "children"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
)
def load_cashflow_panel(branch, start, end):
    """Build cash-flow charts and their text fallback table."""
    if not branch or not start or not end:
        message = "Select a branch and reporting period."
        return empty_chart(""), empty_chart(""), [], ""

    try:
        records = api_client.get_cashflow(branch, start=start, end=end)
    except DashboardAPIError as error:
        message = str(error)
        return empty_chart(""), empty_chart(""), [], message

    if not records:
        message = "No cash-flow data is available for this range."
        return empty_chart(message), empty_chart(message), [], message

    periods = [record["period"] for record in records]
    closing_balances = [
        float(Decimal(str(record["closing_cash_balance"]))) for record in records
    ]
    inflows = [
        float(Decimal(str(record["total_cash_inflows"]))) for record in records
    ]
    outflows = [
        float(Decimal(str(record["total_cash_outflows"]))) for record in records
    ]

    balance_figure = go.Figure(
        go.Scatter(
            x=periods,
            y=closing_balances,
            mode="lines+markers",
            name="Closing balance",
            line={"color": "#8b1a1a", "width": 3},
            marker={"color": "#b8860b", "size": 7},
            hovertemplate="%{x}<br>%{y:,.2f} florins<extra></extra>",
        )
    )
    balance_figure.update_layout(
        title="Closing cash balance",
        paper_bgcolor="#fffdf8",
        plot_bgcolor="#fffdf8",
        yaxis_title="Florins",
        margin={"l": 55, "r": 20, "t": 55, "b": 45},
    )

    movement_figure = go.Figure()
    movement_figure.add_bar(
        x=periods,
        y=inflows,
        name="Inflows",
        marker_color="#2e7d32",
        hovertemplate="%{x}<br>%{y:,.2f} florins<extra>Inflows</extra>",
    )
    movement_figure.add_bar(
        x=periods,
        y=outflows,
        name="Outflows",
        marker_color="#c62828",
        hovertemplate="%{x}<br>%{y:,.2f} florins<extra>Outflows</extra>",
    )
    movement_figure.update_layout(
        title="Cash inflows and outflows",
        barmode="group",
        paper_bgcolor="#fffdf8",
        plot_bgcolor="#fffdf8",
        yaxis_title="Florins",
        legend={"orientation": "h", "y": 0.98, "yanchor": "top"},
        margin={"l": 55, "r": 20, "t": 55, "b": 45},
    )

    return balance_figure, movement_figure, create_cashflow_table(records), ""


def create_expense_table(records):
    """Create the ranked expense counterparty table."""
    ranked = sorted(
        records,
        key=lambda record: Decimal(str(record["amount"])),
        reverse=True,
    )[:20]
    headers = ["Category", "Counterparty", "Transactions", "Amount"]
    return html.Table(
        className="data-table",
        children=[
            html.Thead(html.Tr([html.Th(header) for header in headers])),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(record["category"]),
                            html.Td(record["counterparty"]),
                            html.Td(record["transaction_count"]),
                            html.Td(format_florins(record["amount"])),
                        ]
                    )
                    for record in ranked
                ]
            ),
        ],
    )


@app.callback(
    Output("expense-category-chart", "figure"),
    Output("expense-counterparty-table", "children"),
    Output("expense-error", "children"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
)
def load_expense_panel(branch, start, end):
    """Build the monthly category chart and ranked counterparty table."""
    if not branch or not start or not end:
        message = "Select a branch and reporting period."
        return empty_chart(message), [], ""

    try:
        records = api_client.get_expenses(branch, start=start, end=end)
    except DashboardAPIError as error:
        message = str(error)
        return empty_chart(message), [], message

    if not records:
        message = "No operating expenses are available for this range."
        return empty_chart(message), [], message

    periods = sorted({record["period"] for record in records})
    categories = sorted({record["category"] for record in records})
    totals = {
        (period, category): sum(
            (
                Decimal(str(record["amount"]))
                for record in records
                if record["period"] == period and record["category"] == category
            ),
            Decimal("0"),
        )
        for period in periods
        for category in categories
    }

    colors = ["#8b1a1a", "#b8860b", "#2e7d32", "#f57c00", "#6d4c41", "#5d4037"]
    figure = go.Figure()
    for index, category in enumerate(categories):
        figure.add_bar(
            x=periods,
            y=[float(totals[(period, category)]) for period in periods],
            name=category,
            marker_color=colors[index % len(colors)],
            hovertemplate=(
                "%{x}<br>%{y:,.2f} florins"
                f"<extra>{category}</extra>"
            ),
        )
    figure.update_layout(
        barmode="stack",
        paper_bgcolor="#fffdf8",
        plot_bgcolor="#fffdf8",
        yaxis_title="Florins",
        legend={
            "orientation": "h",
            "x": 0,
            "xanchor": "left",
            "y": 1.08,
            "yanchor": "bottom",
        },
        margin={"l": 55, "r": 20, "t": 100, "b": 45},
    )

    return figure, create_expense_table(records), ""


def create_loan_table(records):
    """Create a table of the largest observable loan issuances."""
    ranked = sorted(
        records,
        key=lambda record: Decimal(str(record["loans_issued"])),
        reverse=True,
    )[:20]
    headers = [
        "Period",
        "Counterparty",
        "Issued",
        "Repaid",
        "Interest",
        "Net movement",
    ]
    return html.Table(
        className="data-table",
        children=[
            html.Thead(html.Tr([html.Th(header) for header in headers])),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(record["period"]),
                            html.Td(record["counterparty"]),
                            html.Td(format_florins(record["loans_issued"])),
                            html.Td(format_florins(record["loans_repaid"])),
                            html.Td(format_florins(record["interest_earned"])),
                            html.Td(format_florins(record["net_loan_movement"])),
                        ]
                    )
                    for record in ranked
                ]
            ),
        ],
    )


@app.callback(
    Output("loan-activity-chart", "figure"),
    Output("loan-counterparty-chart", "figure"),
    Output("loan-activity-table", "children"),
    Output("loan-error", "children"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
)
def load_loan_panel(branch, start, end):
    """Build the monthly loan-activity chart and counterparty table."""
    if not branch or not start or not end:
        message = "Select a branch and reporting period."
        return empty_chart(message), empty_chart(message), [], ""

    try:
        records = api_client.get_loans(branch, start=start, end=end)
    except DashboardAPIError as error:
        message = str(error)
        return empty_chart(message), empty_chart(message), [], message

    if not records:
        message = "No loan activity is available for this range."
        return empty_chart(""), empty_chart(""), [], message

    periods = sorted({record["period"] for record in records})
    totals = {
        period: {
            field: sum(
                (
                    Decimal(str(record[field]))
                    for record in records
                    if record["period"] == period
                ),
                Decimal("0"),
            )
            for field in ("loans_issued", "loans_repaid", "interest_earned")
        }
        for period in periods
    }

    figure = go.Figure()
    for field, label, color in (
        ("loans_issued", "Loans issued", "#8b1a1a"),
        ("loans_repaid", "Loans repaid", "#2e7d32"),
        ("interest_earned", "Interest earned", "#b8860b"),
    ):
        figure.add_bar(
            x=periods,
            y=[float(totals[period][field]) for period in periods],
            name=label,
            marker_color=color,
            hovertemplate="%{x}<br>%{y:,.2f} florins<extra>" + label + "</extra>",
        )
    figure.update_layout(
        title="Monthly observable loan activity",
        barmode="group",
        paper_bgcolor="#fffdf8",
        plot_bgcolor="#fffdf8",
        yaxis_title="Florins",
        legend={"orientation": "h", "y": 0.98, "yanchor": "top"},
        margin={"l": 55, "r": 20, "t": 60, "b": 45},
    )

    counterparty_totals = {}
    for record in records:
        counterparty = record["counterparty"] or "Unknown"
        counterparty_totals.setdefault(counterparty, Decimal("0"))
        counterparty_totals[counterparty] += Decimal(str(record["loans_issued"]))

    ranked_counterparties = sorted(
        counterparty_totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    positive_counterparties = [
        (counterparty, amount)
        for counterparty, amount in ranked_counterparties
        if amount > 0
    ]
    if positive_counterparties:
        donut = go.Figure(
            go.Pie(
                labels=[item[0] for item in positive_counterparties],
                values=[float(item[1]) for item in positive_counterparties],
                hole=0.55,
                sort=False,
                hovertemplate="%{label}<br>%{value:,.2f} florins<extra></extra>",
            )
        )
        donut.update_layout(
            title="Share of observed issuance by counterparty",
            paper_bgcolor="#fffdf8",
            plot_bgcolor="#fffdf8",
            margin={"l": 20, "r": 20, "t": 60, "b": 20},
        )
    else:
        donut = empty_chart("No loan issuances are available for this range.")

    return figure, donut, create_loan_table(records), ""


def create_alert_table(records):
    """Create a severity-ranked table from precomputed anomaly alerts."""
    severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    ranked = sorted(
        records,
        key=lambda record: (
            severity_rank.get(record["severity"], 3),
            record["period"],
            record["alert_id"],
        ),
    )
    headers = [
        "Severity",
        "Rule",
        "Period",
        "Counterparty",
        "Transaction IDs",
        "Status",
        "Description",
    ]
    return html.Div(
        className="table-scroll",
        children=html.Table(
            className="data-table alert-table",
            children=[
                html.Thead(html.Tr([html.Th(header) for header in headers])),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(
                                    record["severity"],
                                    className=(
                                        "severity-badge severity-"
                                        + record["severity"].lower()
                                    ),
                                ),
                                html.Td(record["rule"]),
                                html.Td(record["period"]),
                                html.Td(record["counterparty"] or "N/A"),
                                html.Td(
                                    ", ".join(
                                        str(identifier)
                                        for identifier in record[
                                            "affected_transaction_ids"
                                        ]
                                    )
                                    or "None"
                                ),
                                html.Td(record["status"]),
                                html.Td(record["description"]),
                            ]
                        )
                        for record in ranked
                    ]
                ),
            ],
        ),
    )


@app.callback(
    Output("alert-summary", "children"),
    Output("alert-table", "children"),
    Output("alert-error", "children"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
    Input("alert-severity-selector", "value"),
)
def load_alert_panel(branch, start, end, severity):
    """Build severity summaries and a read-only anomaly review table."""
    if not branch or not start or not end:
        return [], [], ""

    try:
        records = api_client.get_alerts(branch, start=start, end=end)
    except DashboardAPIError as error:
        return [], [], str(error)

    counts = {
        level: sum(record["severity"] == level for record in records)
        for level in ("HIGH", "MEDIUM", "LOW")
    }
    summary = [
        html.Article(
            className=f"alert-count severity-{level.lower()}",
            children=[html.H3(level.title()), html.P(f"{counts[level]:,}")],
        )
        for level in ("HIGH", "MEDIUM", "LOW")
    ]

    filtered = (
        records
        if severity in (None, "ALL")
        else [record for record in records if record["severity"] == severity]
    )
    if not filtered:
        return summary, [], "No alerts match the selected filters."
    return summary, create_alert_table(filtered), ""


def period_date_bounds(start_period, end_period):
    """Convert dashboard month values into inclusive API date bounds."""
    end_year, end_month = (int(part) for part in end_period.split("-"))
    end_day = monthrange(end_year, end_month)[1]
    return f"{start_period}-01", f"{end_period}-{end_day:02d}"


def create_transaction_table(records):
    """Create a table for one API-managed transaction page."""
    headers = [
        "ID", "Date", "Type", "Counterparty", "Description",
        "Debit account", "Debit amount", "Credit account", "Credit amount",
    ]
    return html.Div(
        className="table-scroll",
        children=html.Table(
            className="data-table transaction-table",
            children=[
                html.Thead(html.Tr([html.Th(header) for header in headers])),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(record["id"]),
                                html.Td(record["date"]),
                                html.Td(record["type"].replace("_", " ").title()),
                                html.Td(record["counterparty"] or "N/A"),
                                html.Td(record["description"]),
                                html.Td(record["debit_account"]),
                                html.Td(format_florins(record["debit_amount"])),
                                html.Td(record["credit_account"]),
                                html.Td(format_florins(record["credit_amount"])),
                            ]
                        )
                        for record in records
                    ]
                ),
            ],
        ),
    )


def create_bill_table(records):
    """Create one page of observable bill-of-exchange ledger entries."""
    headers = [
        "ID",
        "Date",
        "Counterparty",
        "Description",
        "Receivable value",
        "Cash paid",
        "Exchange fee",
    ]
    return html.Div(
        className="table-scroll",
        children=html.Table(
            className="data-table bill-table",
            children=[
                html.Thead(html.Tr([html.Th(header) for header in headers])),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(record["id"]),
                                html.Td(record["date"]),
                                html.Td(record["counterparty"] or "N/A"),
                                html.Td(record["description"]),
                                html.Td(format_florins(record["debit_amount"])),
                                html.Td(format_florins(record["credit_amount"])),
                                html.Td(format_florins(record["credit_amount_2"])),
                            ]
                        )
                        for record in records
                    ]
                ),
            ],
        ),
    )


@app.callback(
    Output("bill-table", "children"),
    Output("bill-page-summary", "children"),
    Output("bill-error", "children"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
    Input("bill-page", "value"),
)
def load_bill_panel(branch, start, end, page):
    """Load one server-managed page of bill-of-exchange activity."""
    if not branch or not start or not end:
        return [], "", ""

    start_date, end_date = period_date_bounds(start, end)
    try:
        payload = api_client.get_transactions(
            branch,
            start=start_date,
            end=end_date,
            type="bill_of_exchange",
            sort_by="date",
            sort_order="desc",
            page=max(1, int(page or 1)),
            per_page=25,
        )
    except DashboardAPIError as error:
        return [], "", str(error)

    records = payload["items"]
    summary = (
        f"Page {payload['page']} of {max(payload['total_pages'], 1)} · "
        f"{payload['total']:,} matching bills"
    )
    if not records:
        return [], summary, "No bills of exchange match the selected range."
    return create_bill_table(records), summary, ""


@app.callback(
    Output("transaction-table", "children"),
    Output("transaction-page-summary", "children"),
    Output("transaction-error", "children"),
    Output("transaction-pagination-metadata", "data"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
    Input("transaction-search", "value"),
    Input("transaction-type-selector", "value"),
    Input("transaction-sort-selector", "value"),
    Input("transaction-order-selector", "value"),
    Input("transaction-page", "value"),
)
def load_transaction_panel(
    branch, start, end, search, transaction_type, sort_by, sort_order, page
):
    """Load one filtered transaction page without transferring the full ledger."""
    if not branch or not start or not end:
        return [], "", "", {"total_pages": 1}

    start_date, end_date = period_date_bounds(start, end)
    try:
        payload = api_client.get_transactions(
            branch,
            start=start_date,
            end=end_date,
            type=transaction_type,
            search=search.strip() if search and search.strip() else None,
            sort_by=sort_by or "date",
            sort_order=sort_order or "asc",
            page=max(1, int(page or 1)),
            per_page=25,
        )
    except DashboardAPIError as error:
        return [], "", str(error), {"total_pages": 1}

    records = payload["items"]
    summary = (
        f"Page {payload['page']} of {max(payload['total_pages'], 1)} · "
        f"{payload['total']:,} matching transactions"
    )
    if not records:
        return (
            [],
            summary,
            "No transactions match the selected filters.",
            {"total_pages": payload["total_pages"]},
        )
    return (
        create_transaction_table(records),
        summary,
        "",
        {"total_pages": payload["total_pages"]},
    )


def calculate_transaction_page(triggered_id, current_page, total_pages):
    """Calculate a bounded page number or reset after a filter change."""
    current = max(1, int(current_page or 1))
    maximum = max(1, int(total_pages or 1))
    if triggered_id == "transaction-previous-page":
        return max(1, current - 1)
    if triggered_id == "transaction-next-page":
        return min(maximum, current + 1)
    return 1


@app.callback(
    Output("transaction-page", "value"),
    Input("transaction-previous-page", "n_clicks"),
    Input("transaction-next-page", "n_clicks"),
    Input("branch-selector", "value"),
    Input("start-period-selector", "value"),
    Input("end-period-selector", "value"),
    Input("transaction-search", "value"),
    Input("transaction-type-selector", "value"),
    Input("transaction-sort-selector", "value"),
    Input("transaction-order-selector", "value"),
    State("transaction-page", "value"),
    State("transaction-pagination-metadata", "data"),
    prevent_initial_call=True,
)
def navigate_transaction_pages(
    _previous_clicks,
    _next_clicks,
    _branch,
    _start,
    _end,
    _search,
    _transaction_type,
    _sort_by,
    _sort_order,
    current_page,
    metadata,
):
    """Navigate pages and reset pagination when any data filter changes."""
    return calculate_transaction_page(
        ctx.triggered_id,
        current_page,
        (metadata or {}).get("total_pages", 1),
    )


if __name__ == "__main__":
    app.run(debug=True)
