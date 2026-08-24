from __future__ import annotations

from typing import List, Optional

from .schema import (
    DataCategory,
    FinancialData,
    FinancialMetric,
    RedFlagStatus,
    SourceType,
)


# ============================================================
# VALIDATION RESULT
# ============================================================

class ValidationResult:
    """
    Stores the result of financial data validation.
    """

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def __repr__(self) -> str:
        return (
            f"ValidationResult("
            f"valid={self.is_valid}, "
            f"errors={len(self.errors)}, "
            f"warnings={len(self.warnings)})"
        )


# ============================================================
# FINANCIAL DATA VALIDATOR
# ============================================================

class FinancialDataValidator:
    """
    Validates normalized FinancialData before it is passed
    to the red-flag analysis engine.
    """

    def validate(
        self,
        data: FinancialData,
    ) -> ValidationResult:

        result = ValidationResult()

        self._validate_company(data, result)
        self._validate_sources(data, result)
        self._validate_periods(data, result)
        self._validate_metrics(data, result)
        self._validate_metric_series(data, result)
        self._validate_statements(data, result)

        return result

    # ========================================================
    # COMPANY VALIDATION
    # ========================================================

    def _validate_company(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        if not data.company.company_name.strip():
            result.add_error(
                "Company name is missing."
            )

        if (
            data.company.ticker is not None
            and not data.company.ticker.strip()
        ):
            result.add_warning(
                "Ticker is present but empty."
            )

        if (
            data.company.currency is not None
            and not data.company.currency.strip()
        ):
            result.add_warning(
                "Currency is present but empty."
            )

    # ========================================================
    # SOURCE VALIDATION
    # ========================================================

    def _validate_sources(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        if not data.source_files:
            result.add_warning(
                "No source files are attached to the "
                "normalized financial data."
            )
            return

        for source in data.source_files:

            if source.source_type not in {
                SourceType.BLOOMBERG,
                SourceType.SCREENER,
            }:
                result.add_error(
                    f"Unsupported source type: "
                    f"{source.source_type}"
                )

            if not source.file_name:
                result.add_error(
                    "Source file name is missing."
                )

            if not source.file_path:
                result.add_error(
                    f"Source path is missing for "
                    f"{source.file_name}."
                )

            if not source.file_name.lower().endswith(
                (".xlsx", ".xls")
            ):
                result.add_error(
                    f"Unsupported file format: "
                    f"{source.file_name}. "
                    f"Only Excel files are supported."
                )

    # ========================================================
    # PERIOD VALIDATION
    # ========================================================

    def _validate_periods(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        seen_periods = set()

        for period in data.periods:

            period_key = (
                period.period_label
                or str(period.period_end)
            )

            if period_key in seen_periods:
                result.add_warning(
                    f"Duplicate financial period: "
                    f"{period_key}"
                )

            seen_periods.add(period_key)

            if period.fiscal_year is not None:

                if not 1900 <= period.fiscal_year <= 2200:
                    result.add_error(
                        f"Invalid fiscal year: "
                        f"{period.fiscal_year}"
                    )

    # ========================================================
    # METRIC VALIDATION
    # ========================================================

    def _validate_metrics(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        if not data.metrics:
            result.add_warning(
                "No financial metrics were found."
            )
            return

        for metric in data.metrics:

            self._validate_metric(
                metric,
                result,
            )

    def _validate_metric(
        self,
        metric: FinancialMetric,
        result: ValidationResult,
    ) -> None:

        if not metric.metric_name.strip():
            result.add_error(
                "Financial metric has no name."
            )

        # ----------------------------------------------------
        # VALUE VALIDATION
        # ----------------------------------------------------

        if metric.value is None:

            result.add_warning(
                f"Metric '{metric.metric_name}' "
                f"has no numeric value."
            )

        # ----------------------------------------------------
        # SOURCE VALIDATION
        # ----------------------------------------------------

        if metric.source_type not in {
            SourceType.BLOOMBERG,
            SourceType.SCREENER,
        }:
            result.add_error(
                f"Metric '{metric.metric_name}' has "
                f"an unsupported source type."
            )

        # ----------------------------------------------------
        # PERIOD VALIDATION
        # ----------------------------------------------------

        if metric.period is None:

            result.add_warning(
                f"Metric '{metric.metric_name}' "
                f"has no financial period."
            )

        # ----------------------------------------------------
        # CATEGORY VALIDATION
        # ----------------------------------------------------

        if not isinstance(
            metric.category,
            DataCategory,
        ):
            result.add_error(
                f"Metric '{metric.metric_name}' "
                f"has an invalid category."
            )

    # ========================================================
    # METRIC SERIES VALIDATION
    # ========================================================

    def _validate_metric_series(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        metric_names = {
            metric.metric_name
            for metric in data.metrics
        }

        for series in data.metric_series:

            if not series.metric_name.strip():
                result.add_error(
                    "Metric series has no metric name."
                )

            if (
                series.metric_name not in metric_names
                and series.values
            ):
                result.add_warning(
                    f"Metric series "
                    f"'{series.metric_name}' has no "
                    f"corresponding metric record."
                )

            for period, value in series.values.items():

                if value is not None and not isinstance(
                    value,
                    (int, float),
                ):
                    result.add_error(
                        f"Metric series "
                        f"'{series.metric_name}' contains "
                        f"an invalid value for period "
                        f"'{period}'."
                    )

    # ========================================================
    # FINANCIAL STATEMENT VALIDATION
    # ========================================================

    def _validate_statements(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        self._validate_income_statements(
            data,
            result,
        )

        self._validate_balance_sheets(
            data,
            result,
        )

        self._validate_cash_flow_statements(
            data,
            result,
        )

    # ========================================================
    # INCOME STATEMENT
    # ========================================================

    def _validate_income_statements(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        for period, statement in (
            data.income_statement.items()
        ):

            if statement.revenue is None:
                result.add_warning(
                    f"Income statement for {period} "
                    f"has no revenue."
                )

            if statement.net_income is None:
                result.add_warning(
                    f"Income statement for {period} "
                    f"has no net income."
                )

            self._check_negative_revenue(
                statement.revenue,
                period,
                result,
            )

    # ========================================================
    # BALANCE SHEET
    # ========================================================

    def _validate_balance_sheets(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        for period, statement in (
            data.balance_sheet.items()
        ):

            if statement.total_assets is None:
                result.add_warning(
                    f"Balance sheet for {period} "
                    f"has no total assets."
                )

            if statement.shareholders_equity is None:
                result.add_warning(
                    f"Balance sheet for {period} "
                    f"has no shareholders' equity."
                )

            if (
                statement.total_assets is not None
                and statement.total_assets < 0
            ):
                result.add_error(
                    f"Total assets cannot be negative "
                    f"for period {period}."
                )

    # ========================================================
    # CASH FLOW
    # ========================================================

    def _validate_cash_flow_statements(
        self,
        data: FinancialData,
        result: ValidationResult,
    ) -> None:

        for period, statement in (
            data.cash_flow_statement.items()
        ):

            if (
                statement.cash_from_operations is None
                and statement.free_cash_flow is None
            ):
                result.add_warning(
                    f"Cash flow statement for {period} "
                    f"has no operating cash flow or "
                    f"free cash flow."
                )

    # ========================================================
    # BASIC FINANCIAL SANITY CHECKS
    # ========================================================

    @staticmethod
    def _check_negative_revenue(
        revenue: Optional[float],
        period: str,
        result: ValidationResult,
    ) -> None:

        if revenue is not None and revenue < 0:
            result.add_error(
                f"Revenue is negative for period "
                f"{period}: {revenue}"
            )


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def validate_financial_data(
    data: FinancialData,
) -> ValidationResult:
    """
    Convenience function for validating FinancialData.
    """

    validator = FinancialDataValidator()

    return validator.validate(data)


# ============================================================
# STRICT VALIDATION HELPER
# ============================================================

def validate_or_raise(
    data: FinancialData,
) -> FinancialData:
    """
    Validate FinancialData and raise ValueError if
    critical validation errors are found.

    Warnings do not cause failure.
    """

    result = validate_financial_data(data)

    if not result.is_valid:

        error_message = "\n".join(
            f"- {error}"
            for error in result.errors
        )

        raise ValueError(
            "Financial data validation failed:\n"
            + error_message
        )

    return data