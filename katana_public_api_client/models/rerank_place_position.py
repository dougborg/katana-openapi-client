from enum import StrEnum


class RerankPlacePosition(StrEnum):
    BOTTOM = "bottom"
    TOP = "top"

    def __str__(self) -> str:
        return str(self.value)
