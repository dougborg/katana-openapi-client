from enum import Enum


class CustomFieldsCollectionResourceType(str, Enum):
    CUSTOMER = "customer"
    MATERIAL = "material"
    PRODUCT = "product"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    STOCKTAKE = "stocktake"
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
