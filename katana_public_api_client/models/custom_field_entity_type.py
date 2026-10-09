from enum import StrEnum


class CustomFieldEntityType(StrEnum):
    CUSTOMER = "Customer"
    MATERIALVARIANT = "MaterialVariant"
    OUTSOURCEDPURCHASEORDER = "OutsourcedPurchaseOrder"
    OUTSOURCEDPURCHASEORDERROW = "OutsourcedPurchaseOrderRow"
    PRODUCTIONOPERATION = "ProductionOperation"
    PRODUCTVARIANT = "ProductVariant"
    PURCHASEORDER = "PurchaseOrder"
    PURCHASEORDERROW = "PurchaseOrderRow"
    RECIPEBOM = "RecipeBom"
    SALESORDER = "SalesOrder"
    SALESORDERROW = "SalesOrderRow"
    SERVICEVARIANT = "ServiceVariant"
    SUPPLIER = "Supplier"

    def __str__(self) -> str:
        return str(self.value)
