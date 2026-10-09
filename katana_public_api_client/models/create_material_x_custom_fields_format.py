from enum import StrEnum


class CreateMaterialXCustomFieldsFormat(StrEnum):
    DEFAULT = "default"
    LEGACY = "legacy"

    def __str__(self) -> str:
        return str(self.value)
