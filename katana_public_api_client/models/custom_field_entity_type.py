from enum import StrEnum


class CustomFieldEntityType(StrEnum):
    SALESORDER = "SalesOrder"
    SALESORDERROW = "SalesOrderRow"

    def __str__(self) -> str:
        return str(self.value)
