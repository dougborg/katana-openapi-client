from enum import Enum


class SalesOrderFulfillmentInvoiceStatus(str, Enum):
    INVOICED = "INVOICED"
    NOT_INVOICED = "NOT_INVOICED"
    PARTIALLY_INVOICED = "PARTIALLY_INVOICED"

    def __str__(self) -> str:
        return str(self.value)
