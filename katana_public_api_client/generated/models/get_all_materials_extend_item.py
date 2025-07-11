from enum import Enum


class GetAllMaterialsExtendItem(str, Enum):
    LOCATION = "location"
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
