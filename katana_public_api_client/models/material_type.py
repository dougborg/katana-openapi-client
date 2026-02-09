from enum import StrEnum


class MaterialType(StrEnum):
    MATERIAL = "material"

    def __str__(self) -> str:
        return str(self.value)
