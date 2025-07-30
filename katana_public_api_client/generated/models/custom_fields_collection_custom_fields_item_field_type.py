from enum import Enum


class CustomFieldsCollectionCustomFieldsItemFieldType(str, Enum):
    BOOLEAN = "boolean"
    DATE = "date"
    NUMBER = "number"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
