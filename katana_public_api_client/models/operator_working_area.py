from enum import StrEnum


class OperatorWorkingArea(StrEnum):
    SHOPFLOOR = "shopFloor"
    WAREHOUSE = "warehouse"

    def __str__(self) -> str:
        return str(self.value)
