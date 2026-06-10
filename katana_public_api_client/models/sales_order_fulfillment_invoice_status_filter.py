from enum import StrEnum


class SalesOrderFulfillmentInvoiceStatusFilter(StrEnum):
    INVOICED = "INVOICED"
    NOT_INVOICED = "NOT_INVOICED"

    def __str__(self) -> str:
        return str(self.value)
