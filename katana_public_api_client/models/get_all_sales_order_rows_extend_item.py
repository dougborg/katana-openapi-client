from enum import StrEnum


class GetAllSalesOrderRowsExtendItem(StrEnum):
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
