from enum import StrEnum


class AbcClassification(StrEnum):
    A = "A"
    B = "B"
    C = "C"

    def __str__(self) -> str:
        return str(self.value)
