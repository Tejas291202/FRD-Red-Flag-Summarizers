from backend.financial.schema import FinancialMetric


class FinancialNormalizer:
    """
    Converts Bloomberg and Screener metrics into
    consistent internal units.

    Internal standard:
        Monetary financial statement values -> INR crore

    Non-monetary metrics retain their natural units.
    """

    MONETARY_UNITS = {
        "million",
        "crore",
    }

    @staticmethod
    def normalize_monetary_value(
        value: float | None,
        source_unit: str | None,
    ) -> float | None:

        if value is None:
            return None

        if source_unit == "crore":
            return float(value)

        # 10 million INR = 1 crore INR
        if source_unit == "million":
            return float(value) / 10

        raise ValueError(
            f"Unsupported monetary unit: {source_unit}"
        )

    @classmethod
    def normalize_metric(
        cls,
        metric: FinancialMetric,
    ) -> FinancialMetric:

        # Monetary values
        if metric.unit in cls.MONETARY_UNITS:

            normalized_value = cls.normalize_monetary_value(
                metric.value,
                metric.unit,
            )

            normalized_unit = "crore"

        # Ratios / per-share / multiples etc.
        else:

            normalized_value = metric.value
            normalized_unit = metric.unit

        return FinancialMetric(
            name=metric.name,
            value=normalized_value,
            period=metric.period,
            currency=metric.currency,
            unit=normalized_unit,
            source=metric.source,
            source_field=metric.source_field,
            source_sheet=metric.source_sheet,
            source_row=metric.source_row,
        )

    @classmethod
    def normalize_metrics(
        cls,
        metrics: list[FinancialMetric],
    ) -> list[FinancialMetric]:

        return [
            cls.normalize_metric(metric)
            for metric in metrics
        ]