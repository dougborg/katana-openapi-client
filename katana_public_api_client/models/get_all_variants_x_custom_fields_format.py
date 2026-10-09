from enum import StrEnum


class GetAllVariantsXCustomFieldsFormat(StrEnum):
    DEFAULT = "default"
    LEGACY = "legacy"

    def __str__(self) -> str:
        return str(self.value)
