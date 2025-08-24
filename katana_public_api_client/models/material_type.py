from enum import Enum


class MaterialType(str, Enum):
    MATERIAL = "material"

    def __str__(self) -> str:
        return str(self.value)
