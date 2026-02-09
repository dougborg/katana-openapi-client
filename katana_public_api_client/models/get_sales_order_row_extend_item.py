from enum import StrEnum


class GetSalesOrderRowExtendItem(StrEnum):
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
