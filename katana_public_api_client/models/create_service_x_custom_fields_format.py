from enum import StrEnum


class CreateServiceXCustomFieldsFormat(StrEnum):
    DEFAULT = "default"
    LEGACY = "legacy"

    def __str__(self) -> str:
        return str(self.value)
