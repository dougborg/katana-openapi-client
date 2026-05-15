from enum import StrEnum


class CustomFieldType(StrEnum):
    BOOLEAN = "boolean"
    DATE = "date"
    NUMBER = "number"
    SHORTTEXT = "shortText"
    SINGLESELECT = "singleSelect"
    URL = "url"

    def __str__(self) -> str:
        return str(self.value)
