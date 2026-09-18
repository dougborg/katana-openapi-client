from enum import StrEnum


class InventorySignalLeadTimeSource(StrEnum):
    FALLBACK = "fallback"
    SKU = "sku"
    SYSTEM_MO = "system_mo"
    SYSTEM_PO = "system_po"

    def __str__(self) -> str:
        return str(self.value)
