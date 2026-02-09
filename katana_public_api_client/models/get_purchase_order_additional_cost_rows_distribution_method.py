from enum import StrEnum


class GetPurchaseOrderAdditionalCostRowsDistributionMethod(StrEnum):
    BY_VALUE = "BY_VALUE"
    NON_DISTRIBUTED = "NON_DISTRIBUTED"

    def __str__(self) -> str:
        return str(self.value)
