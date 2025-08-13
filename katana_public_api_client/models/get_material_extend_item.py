from enum import Enum


class GetMaterialExtendItem(str, Enum):
    LOCATION = "location"
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
