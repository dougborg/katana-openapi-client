from enum import Enum


class SalesOrderAccountingMetadataIntegrationType(str, Enum):
    CUSTOM = "custom"
    QUICKBOOKS = "quickBooks"
    SAGE = "sage"
    XERO = "xero"

    def __str__(self) -> str:
        return str(self.value)
