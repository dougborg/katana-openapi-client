from enum import Enum


class GetSalesOrderRowExtendItem(str, Enum):
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
