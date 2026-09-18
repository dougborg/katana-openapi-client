from enum import StrEnum


class VariantSearchRequestIncludeItem(StrEnum):
    ARCHIVED = "archived"
    DELETED = "deleted"
    ITEM = "item"

    def __str__(self) -> str:
        return str(self.value)
