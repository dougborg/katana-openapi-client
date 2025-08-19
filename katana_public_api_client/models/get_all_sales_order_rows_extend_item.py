from enum import Enum


class GetAllSalesOrderRowsExtendItem(str, Enum):
    LOCATION = "location"
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
