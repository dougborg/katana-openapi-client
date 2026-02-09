from enum import StrEnum


class SalesOrderAccountingMetadataIntegrationType(StrEnum):
    CUSTOM = "custom"
    QUICKBOOKS = "quickBooks"
    SAGE = "sage"
    XERO = "xero"

    def __str__(self) -> str:
        return str(self.value)
