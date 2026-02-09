from enum import StrEnum


class SalesOrderFulfillmentInvoiceStatus(StrEnum):
    INVOICED = "INVOICED"
    NOT_INVOICED = "NOT_INVOICED"
    PARTIALLY_INVOICED = "PARTIALLY_INVOICED"

    def __str__(self) -> str:
        return str(self.value)
