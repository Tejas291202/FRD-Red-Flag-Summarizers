from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================
# ENUMS
# ============================================================

class SourceType(str, Enum):
    BLOOMBERG = "bloomberg"
    SCREENER = "screener"


class DataCategory(str, Enum):
    PROFITABILITY = "profitability"
    GROWTH = "growth"
    LEVERAGE = "leverage"
    LIQUIDITY = "liquidity"
    CASH_FLOW = "cash_flow"
    VALUATION = "valuation"
    WORKING_CAPITAL = "working_capital"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RedFlagStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    RED_FLAG = "red_flag"
    NOT_AVAILABLE = "not_available"


# ============================================================
# SOURCE FILE SCHEMA
# ============================================================

class SourceFile(BaseModel):
    """
    Represents an input Excel file.

    Supported sources:
    - Bloomberg Excel
    - Screener Excel
    """

    model_config = ConfigDict(use_enum_values=True)

    file_name: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)
    source_type: SourceType
    uploaded_at: Optional[datetime] = None

    @field_validator("file_name")
    @classmethod
    def validate_excel_file(cls, value: str) -> str:
        if not value.lower().endswith((".xlsx", ".xls")):
            raise ValueError(
                "Only Excel files (.xlsx, .xls) are supported."
            )
        return value


# ============================================================
# COMPANY / SECURITY INFORMATION
# ============================================================

class CompanyInfo(BaseModel):
    """
    Basic company identification information extracted from
    Bloomberg or Screener.
    """

    model_config = ConfigDict(use_enum_values=True)

    company_name: str = Field(..., min_length=1)
    ticker: Optional[str] = None
    isin: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None


# ============================================================
# FINANCIAL PERIOD
# ============================================================

class FinancialPeriod(BaseModel):
    """
    Represents a financial reporting period.
    """

    model_config = ConfigDict(use_enum_values=True)

    period_end: date
    fiscal_year: Optional[int] = None
    fiscal_quarter: Optional[str] = None
    period_label: Optional[str] = None

    @field_validator("fiscal_year")
    @classmethod
    def validate_fiscal_year(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and not 1900 <= value <= 2200:
            raise ValueError("Invalid fiscal year.")
        return value


# ============================================================
# FINANCIAL METRIC
# ============================================================

class FinancialMetric(BaseModel):
    """
    Normalized financial metric.

    Examples:
    - Revenue
    - EBITDA
    - EBIT
    - PAT
    - CFO
    - Capex
    - Total Debt
    - Cash
    - Net Debt
    - ROE
    - ROCE
    - EBITDA Margin
    - P/E
    """

    model_config = ConfigDict(use_enum_values=True)

    metric_name: str = Field(..., min_length=1)
    value: Optional[float] = None
    unit: Optional[str] = None
    currency: Optional[str] = None

    period: Optional[FinancialPeriod] = None

    source_type: SourceType
    source_file: Optional[str] = None

    category: DataCategory = DataCategory.OTHER

    raw_value: Optional[Any] = None

    is_derived: bool = False


# ============================================================
# TIME SERIES METRIC
# ============================================================

class MetricSeries(BaseModel):
    """
    Historical values for one financial metric.
    """

    model_config = ConfigDict(use_enum_values=True)

    metric_name: str = Field(..., min_length=1)
    values: Dict[str, Optional[float]] = Field(default_factory=dict)

    unit: Optional[str] = None
    currency: Optional[str] = None

    source_type: SourceType
    source_file: Optional[str] = None

    category: DataCategory = DataCategory.OTHER


# ============================================================
# FINANCIAL STATEMENTS
# ============================================================

class IncomeStatement(BaseModel):
    """
    Normalized income statement data.
    """

    revenue: Optional[float] = None
    cost_of_goods_sold: Optional[float] = None

    gross_profit: Optional[float] = None

    operating_expenses: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None

    interest_expense: Optional[float] = None
    profit_before_tax: Optional[float] = None

    tax_expense: Optional[float] = None
    net_income: Optional[float] = None

    depreciation: Optional[float] = None
    amortization: Optional[float] = None


class BalanceSheet(BaseModel):
    """
    Normalized balance sheet data.
    """

    total_assets: Optional[float] = None
    current_assets: Optional[float] = None
    cash_and_equivalents: Optional[float] = None

    inventory: Optional[float] = None
    accounts_receivable: Optional[float] = None

    total_liabilities: Optional[float] = None
    current_liabilities: Optional[float] = None

    total_debt: Optional[float] = None
    short_term_debt: Optional[float] = None
    long_term_debt: Optional[float] = None

    shareholders_equity: Optional[float] = None


class CashFlowStatement(BaseModel):
    """
    Normalized cash flow statement data.
    """

    cash_from_operations: Optional[float] = None
    capital_expenditure: Optional[float] = None
    cash_from_investing: Optional[float] = None
    cash_from_financing: Optional[float] = None

    free_cash_flow: Optional[float] = None

    dividends_paid: Optional[float] = None


# ============================================================
# NORMALIZED FINANCIAL DATA
# ============================================================

class FinancialData(BaseModel):
    """
    Complete normalized financial dataset for one company.
    """

    model_config = ConfigDict(use_enum_values=True)

    company: CompanyInfo

    periods: List[FinancialPeriod] = Field(default_factory=list)

    income_statement: Dict[str, IncomeStatement] = Field(
        default_factory=dict
    )

    balance_sheet: Dict[str, BalanceSheet] = Field(
        default_factory=dict
    )

    cash_flow_statement: Dict[str, CashFlowStatement] = Field(
        default_factory=dict
    )

    metrics: List[FinancialMetric] = Field(default_factory=list)

    metric_series: List[MetricSeries] = Field(default_factory=list)

    source_files: List[SourceFile] = Field(default_factory=list)


# ============================================================
# RED FLAG RULE
# ============================================================

class RedFlagRule(BaseModel):
    """
    Defines a rule used by the red-flag engine.
    """

    rule_id: str = Field(..., min_length=1)
    rule_name: str = Field(..., min_length=1)

    description: str = Field(..., min_length=1)

    category: DataCategory

    severity: Severity

    metric_name: Optional[str] = None

    threshold: Optional[float] = None

    comparison: Optional[str] = None

    enabled: bool = True


# ============================================================
# RED FLAG
# ============================================================

class RedFlag(BaseModel):
    """
    Result generated when a red-flag rule is evaluated.
    """

    model_config = ConfigDict(use_enum_values=True)

    rule_id: str
    rule_name: str

    category: DataCategory
    severity: Severity

    status: RedFlagStatus

    metric_name: Optional[str] = None

    actual_value: Optional[float] = None
    threshold_value: Optional[float] = None

    message: str = Field(..., min_length=1)

    evidence: Optional[str] = None

    source_type: Optional[SourceType] = None
    source_file: Optional[str] = None


# ============================================================
# COMPANY RED FLAG SUMMARY
# ============================================================

class RedFlagSummary(BaseModel):
    """
    Consolidated red-flag assessment for one company.
    """

    model_config = ConfigDict(use_enum_values=True)

    company: CompanyInfo

    total_flags: int = 0
    critical_flags: int = 0
    high_flags: int = 0
    medium_flags: int = 0
    low_flags: int = 0

    overall_status: RedFlagStatus = RedFlagStatus.PASS

    red_flags: List[RedFlag] = Field(default_factory=list)

    key_observations: List[str] = Field(default_factory=list)

    generated_at: datetime = Field(
        default_factory=datetime.utcnow
    )


# ============================================================
# DUE DILIGENCE OUTPUT
# ============================================================

class DueDiligenceReport(BaseModel):
    """
    Final structured output of the financial due-diligence
    red-flag analysis.
    """

    model_config = ConfigDict(use_enum_values=True)

    company: CompanyInfo

    source_files: List[SourceFile] = Field(default_factory=list)

    financial_data: FinancialData

    red_flag_summary: RedFlagSummary

    generated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    model_version: str = "1.0.0"