from enum import Enum


class GetAllSalesOrderRowsExtendItem(str, Enum):
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
