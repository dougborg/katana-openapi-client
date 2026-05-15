from enum import StrEnum


class SalesOrderInvoicingStatus(StrEnum):
    INVOICED = "invoiced"
    NOTINVOICED = "notInvoiced"
    PARTIALLYINVOICED = "partiallyInvoiced"

    def __str__(self) -> str:
        return str(self.value)
