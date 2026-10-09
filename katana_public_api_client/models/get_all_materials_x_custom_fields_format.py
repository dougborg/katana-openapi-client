from enum import StrEnum


class GetAllMaterialsXCustomFieldsFormat(StrEnum):
    DEFAULT = "default"
    LEGACY = "legacy"

    def __str__(self) -> str:
        return str(self.value)
