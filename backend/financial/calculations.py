from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional, Tuple

from .schema import (
    DataCategory,
    FinancialData,
    FinancialMetric,
    FinancialPeriod,
    MetricSeries,
)


# ============================================================
# FINANCIAL CALCULATOR
# ============================================================

class FinancialCalculator:
    """
    Calculates derived financial metrics from normalized
    FinancialData.

    Calculations include:
    - Revenue growth
    - EBITDA growth
    - Net income growth
    - EBITDA margin
    - EBIT margin
    - Net profit margin
    - ROE
    - ROA
    - Debt-to-equity
    - Net debt
    - Net debt / EBITDA
    - Current ratio
    - Free cash flow
    """

    def calculate(
        self,
        data: FinancialData,
    ) -> FinancialData:
        """
        Calculate derived metrics and add them to the
        FinancialData object.
        """

        periods = self._get_ordered_periods(data)

        for period_key in periods:

            income = data.income_statement.get(
                period_key
            )

            balance = data.balance_sheet.get(
                period_key
            )

            cash_flow = data.cash_flow_statement.get(
                period_key
            )

            if income is not None:

                self._calculate_income_metrics(
                    data,
                    period_key,
                    income,
                )

            if balance is not None:

                self._calculate_balance_metrics(
                    data,
                    period_key,
                    balance,
                )

            if income is not None and balance is not None:

                self._calculate_return_metrics(
                    data,
                    period_key,
                    income,
                    balance,
                )

            if (
                income is not None
                and balance is not None
            ):

                self._calculate_leverage_metrics(
                    data,
                    period_key,
                    income,
                    balance,
                )

            if balance is not None:

                self._calculate_liquidity_metrics(
                    data,
                    period_key,
                    balance,
                )

            if cash_flow is not None:

                self._calculate_cash_flow_metrics(
                    data,
                    period_key,
                    cash_flow,
                )

        self._calculate_growth_metrics(
            data,
            periods,
        )

        return data

    # ========================================================
    # INCOME STATEMENT CALCULATIONS
    # ========================================================

    def _calculate_income_metrics(
        self,
        data: FinancialData,
        period_key: str,
        income,
    ) -> None:

        # ----------------------------------------------------
        # EBITDA MARGIN
        # ----------------------------------------------------

        ebitda_margin = self._divide(
            income.ebitda,
            income.revenue,
        )

        self._add_metric(
            data=data,
            name="ebitda_margin",
            value=self._percentage(
                ebitda_margin
            ),
            period_key=period_key,
            category=DataCategory.PROFITABILITY,
            is_derived=True,
        )

        # ----------------------------------------------------
        # EBIT MARGIN
        # ----------------------------------------------------

        ebit_margin = self._divide(
            income.ebit,
            income.revenue,
        )

        self._add_metric(
            data=data,
            name="operating_margin",
            value=self._percentage(
                ebit_margin
            ),
            period_key=period_key,
            category=DataCategory.PROFITABILITY,
            is_derived=True,
        )

        # ----------------------------------------------------
        # NET PROFIT MARGIN
        # ----------------------------------------------------

        net_margin = self._divide(
            income.net_income,
            income.revenue,
        )

        self._add_metric(
            data=data,
            name="net_margin",
            value=self._percentage(
                net_margin
            ),
            period_key=period_key,
            category=DataCategory.PROFITABILITY,
            is_derived=True,
        )

    # ========================================================
    # BALANCE SHEET CALCULATIONS
    # ========================================================

    def _calculate_balance_metrics(
        self,
        data: FinancialData,
        period_key: str,
        balance,
    ) -> None:

        # ----------------------------------------------------
        # NET DEBT
        # ----------------------------------------------------

        if (
            balance.total_debt is not None
            and balance.cash_and_equivalents is not None
        ):

            net_debt = (
                balance.total_debt
                - balance.cash_and_equivalents
            )

            self._add_metric(
                data=data,
                name="net_debt",
                value=net_debt,
                period_key=period_key,
                category=DataCategory.LEVERAGE,
                is_derived=True,
            )

        # ----------------------------------------------------
        # DEBT / EQUITY
        # ----------------------------------------------------

        debt_to_equity = self._divide(
            balance.total_debt,
            balance.shareholders_equity,
        )

        self._add_metric(
            data=data,
            name="debt_to_equity",
            value=debt_to_equity,
            period_key=period_key,
            category=DataCategory.LEVERAGE,
            is_derived=True,
        )

        # ----------------------------------------------------
        # CURRENT RATIO
        # ----------------------------------------------------

        current_ratio = self._divide(
            balance.current_assets,
            balance.current_liabilities,
        )

        self._add_metric(
            data=data,
            name="current_ratio",
            value=current_ratio,
            period_key=period_key,
            category=DataCategory.LIQUIDITY,
            is_derived=True,
        )

    # ========================================================
    # RETURN METRICS
    # ========================================================

    def _calculate_return_metrics(
        self,
        data: FinancialData,
        period_key: str,
        income,
        balance,
    ) -> None:

        # ----------------------------------------------------
        # ROE
        # ----------------------------------------------------

        roe = self._divide(
            income.net_income,
            balance.shareholders_equity,
        )

        self._add_metric(
            data=data,
            name="roe",
            value=self._percentage(roe),
            period_key=period_key,
            category=DataCategory.PROFITABILITY,
            is_derived=True,
        )

        # ----------------------------------------------------
        # ROA
        # ----------------------------------------------------

        roa = self._divide(
            income.net_income,
            balance.total_assets,
        )

        self._add_metric(
            data=data,
            name="roa",
            value=self._percentage(roa),
            period_key=period_key,
            category=DataCategory.PROFITABILITY,
            is_derived=True,
        )

        # ----------------------------------------------------
        # ROCE
        #
        # Simplified:
        # EBIT / (Total Assets - Current Liabilities)
        # ----------------------------------------------------

        if (
            income.ebit is not None
            and balance.total_assets is not None
            and balance.current_liabilities is not None
        ):

            capital_employed = (
                balance.total_assets
                - balance.current_liabilities
            )

            roce = self._divide(
                income.ebit,
                capital_employed,
            )

            self._add_metric(
                data=data,
                name="roce",
                value=self._percentage(roce),
                period_key=period_key,
                category=DataCategory.PROFITABILITY,
                is_derived=True,
            )

    # ========================================================
    # LEVERAGE METRICS
    # ========================================================

    def _calculate_leverage_metrics(
        self,
        data: FinancialData,
        period_key: str,
        income,
        balance,
    ) -> None:

        # ----------------------------------------------------
        # NET DEBT / EBITDA
        # ----------------------------------------------------

        if (
            balance.total_debt is not None
            and balance.cash_and_equivalents is not None
            and income.ebitda is not None
        ):

            net_debt = (
                balance.total_debt
                - balance.cash_and_equivalents
            )

            net_debt_to_ebitda = self._divide(
                net_debt,
                income.ebitda,
            )

            self._add_metric(
                data=data,
                name="net_debt_to_ebitda",
                value=net_debt_to_ebitda,
                period_key=period_key,
                category=DataCategory.LEVERAGE,
                is_derived=True,
            )

    # ========================================================
    # LIQUIDITY METRICS
    # ========================================================

    def _calculate_liquidity_metrics(
        self,
        data: FinancialData,
        period_key: str,
        balance,
    ) -> None:

        # ----------------------------------------------------
        # QUICK RATIO
        #
        # (Current Assets - Inventory)
        # / Current Liabilities
        # ----------------------------------------------------

        if (
            balance.current_assets is not None
            and balance.inventory is not None
        ):

            quick_assets = (
                balance.current_assets
                - balance.inventory
            )

            quick_ratio = self._divide(
                quick_assets,
                balance.current_liabilities,
            )

            self._add_metric(
                data=data,
                name="quick_ratio",
                value=quick_ratio,
                period_key=period_key,
                category=DataCategory.LIQUIDITY,
                is_derived=True,
            )

    # ========================================================
    # CASH FLOW METRICS
    # ========================================================

    def _calculate_cash_flow_metrics(
        self,
        data: FinancialData,
        period_key: str,
        cash_flow,
    ) -> None:

        # ----------------------------------------------------
        # FREE CASH FLOW
        #
        # CFO - Capex
        #
        # Capex may already be stored as a negative number
        # depending on the source. We therefore normalize
        # the calculation carefully.
        # ----------------------------------------------------

        if (
            cash_flow.cash_from_operations is not None
            and cash_flow.capital_expenditure is not None
        ):

            cfo = cash_flow.cash_from_operations
            capex = cash_flow.capital_expenditure

            if capex > 0:
                free_cash_flow = cfo - capex
            else:
                free_cash_flow = cfo + capex

            self._add_metric(
                data=data,
                name="free_cash_flow",
                value=free_cash_flow,
                period_key=period_key,
                category=DataCategory.CASH_FLOW,
                is_derived=True,
            )

    # ========================================================
    # GROWTH CALCULATIONS
    # ========================================================

    def _calculate_growth_metrics(
        self,
        data: FinancialData,
        periods: List[str],
    ) -> None:

        growth_metrics = [
            (
                "revenue",
                "revenue_growth",
            ),
            (
                "ebitda",
                "ebitda_growth",
            ),
            (
                "net_income",
                "net_income_growth",
            ),
        ]

        for metric_name, growth_name in growth_metrics:

            values = self._get_metric_series(
                data,
                metric_name,
                periods,
            )

            for index in range(1, len(periods)):

                current_period = periods[index]
                previous_period = periods[index - 1]

                current_value = values.get(
                    current_period
                )

                previous_value = values.get(
                    previous_period
                )

                if (
                    current_value is None
                    or previous_value is None
                ):
                    continue

                growth = self._growth_rate(
                    current_value,
                    previous_value,
                )

                if growth is None:
                    continue

                self._add_metric(
                    data=data,
                    name=growth_name,
                    value=growth,
                    period_key=current_period,
                    category=DataCategory.GROWTH,
                    is_derived=True,
                )

    # ========================================================
    # GET METRIC SERIES
    # ========================================================

    def _get_metric_series(
        self,
        data: FinancialData,
        metric_name: str,
        periods: List[str],
    ) -> Dict[str, Optional[float]]:

        result: Dict[str, Optional[float]] = {}

        for series in data.metric_series:

            if series.metric_name == metric_name:

                result.update(
                    series.values
                )

        # Also look directly in normalized metrics.
        for metric in data.metrics:

            if metric.metric_name != metric_name:
                continue

            if metric.period is None:
                continue

            period_key = (
                metric.period.period_label
                or str(metric.period.period_end)
            )

            result[period_key] = metric.value

        return result

    # ========================================================
    # PERIOD ORDERING
    # ========================================================

    @staticmethod
    def _get_ordered_periods(
        data: FinancialData,
    ) -> List[str]:

        periods: List[
            Tuple[str, date]
        ] = []

        # Primary source: FinancialPeriod objects
        for period in data.periods:

            key = (
                period.period_label
                or str(period.period_end)
            )

            periods.append(
                (
                    key,
                    period.period_end,
                )
            )

        # Fallback: collect periods from metrics
        if not periods:

            seen = set()

            for metric in data.metrics:

                if metric.period is None:
                    continue

                key = (
                    metric.period.period_label
                    or str(metric.period.period_end)
                )

                if key in seen:
                    continue

                seen.add(key)

                periods.append(
                    (
                        key,
                        metric.period.period_end,
                    )
                )

        periods.sort(
            key=lambda item: item[1]
        )

        return [
            item[0]
            for item in periods
        ]

    # ========================================================
    # ADD DERIVED METRIC
    # ========================================================

    def _add_metric(
        self,
        data: FinancialData,
        name: str,
        value: Optional[float],
        period_key: str,
        category: DataCategory,
        is_derived: bool,
    ) -> None:

        if value is None:
            return

        period = self._find_period(
            data,
            period_key,
        )

        metric = FinancialMetric(
            metric_name=name,
            value=value,
            unit="%",
            period=period,
            source_type=self._get_source_type(data),
            source_file=self._get_source_file(data),
            category=category,
            raw_value=value,
            is_derived=is_derived,
        )

        data.metrics.append(metric)

        # Update MetricSeries
        series = self._get_or_create_series(
            data,
            name,
            category,
        )

        series.values[period_key] = value

    # ========================================================
    # FIND PERIOD
    # ========================================================

    @staticmethod
    def _find_period(
        data: FinancialData,
        period_key: str,
    ) -> Optional[FinancialPeriod]:

        for period in data.periods:

            key = (
                period.period_label
                or str(period.period_end)
            )

            if key == period_key:
                return period

        return None

    # ========================================================
    # METRIC SERIES CREATION
    # ========================================================

    @staticmethod
    def _get_or_create_series(
        data: FinancialData,
        metric_name: str,
        category: DataCategory,
    ) -> MetricSeries:

        for series in data.metric_series:

            if series.metric_name == metric_name:
                return series

        source_type = (
            data.source_files[0].source_type
            if data.source_files
            else "bloomberg"
        )

        source_file = (
            data.source_files[0].file_name
            if data.source_files
            else None
        )

        series = MetricSeries(
            metric_name=metric_name,
            values={},
            unit="%",
            source_type=source_type,
            source_file=source_file,
            category=category,
        )

        data.metric_series.append(series)

        return series

    # ========================================================
    # SOURCE HELPERS
    # ========================================================

    @staticmethod
    def _get_source_type(
        data: FinancialData,
    ):

        if data.source_files:
            return data.source_files[0].source_type

        return "bloomberg"

    @staticmethod
    def _get_source_file(
        data: FinancialData,
    ) -> Optional[str]:

        if data.source_files:
            return data.source_files[0].file_name

        return None

    # ========================================================
    # MATHEMATICAL HELPERS
    # ========================================================

    @staticmethod
    def _divide(
        numerator: Optional[float],
        denominator: Optional[float],
    ) -> Optional[float]:

        if numerator is None:
            return None

        if denominator is None:
            return None

        if denominator == 0:
            return None

        return numerator / denominator

    @staticmethod
    def _percentage(
        value: Optional[float],
    ) -> Optional[float]:

        if value is None:
            return None

        return value * 100

    @staticmethod
    def _growth_rate(
        current: Optional[float],
        previous: Optional[float],
    ) -> Optional[float]:

        if current is None or previous is None:
            return None

        if previous == 0:
            return None

        return (
            (current - previous)
            / abs(previous)
        ) * 100


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def calculate_financial_metrics(
    data: FinancialData,
) -> FinancialData:
    """
    Convenience function for calculating all derived
    financial metrics.
    """

    calculator = FinancialCalculator()

    return calculator.calculate(data)