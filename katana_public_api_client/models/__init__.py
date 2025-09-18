"""Contains all the data models used in inputs/outputs"""

from .additional_cost import AdditionalCost
from .additional_cost_list_response import AdditionalCostListResponse
from .archivable_deletable_entity import ArchivableDeletableEntity
from .archivable_entity import ArchivableEntity
from .assigned_operator import AssignedOperator
from .base_entity import BaseEntity
from .batch import Batch
from .batch_create_bom_rows_request import BatchCreateBomRowsRequest
from .batch_response import BatchResponse
from .batch_stock import BatchStock
from .batch_stock_list_response import BatchStockListResponse
from .batch_stock_update import BatchStockUpdate
from .batch_transaction import BatchTransaction
from .bom_row import BomRow
from .bom_row_list_response import BomRowListResponse
from .coded_error_response import CodedErrorResponse
from .create_bom_row_request import CreateBomRowRequest
from .create_customer_address_request import CreateCustomerAddressRequest
from .create_customer_address_request_entity_type import (
    CreateCustomerAddressRequestEntityType,
)
from .create_customer_request import CreateCustomerRequest
from .create_inventory_reorder_point_body import CreateInventoryReorderPointBody
from .create_manufacturing_order_operation_row_request import (
    CreateManufacturingOrderOperationRowRequest,
)
from .create_manufacturing_order_production_request import (
    CreateManufacturingOrderProductionRequest,
)
from .create_manufacturing_order_recipe_row_request import (
    CreateManufacturingOrderRecipeRowRequest,
)
from .create_manufacturing_order_recipe_row_request_batch_transactions_item import (
    CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
)
from .create_manufacturing_order_request import CreateManufacturingOrderRequest
from .create_material_request import CreateMaterialRequest
from .create_outsourced_purchase_order_recipe_row_body import (
    CreateOutsourcedPurchaseOrderRecipeRowBody,
)
from .create_price_list_customer_request import CreatePriceListCustomerRequest
from .create_price_list_request import CreatePriceListRequest
from .create_price_list_row_request import CreatePriceListRowRequest
from .create_product_operation_rows_body import CreateProductOperationRowsBody
from .create_product_operation_rows_body_rows_item import (
    CreateProductOperationRowsBodyRowsItem,
)
from .create_product_operation_rows_body_rows_item_type import (
    CreateProductOperationRowsBodyRowsItemType,
)
from .create_product_request import CreateProductRequest
from .create_product_request_configs_item import CreateProductRequestConfigsItem
from .create_purchase_order_additional_cost_row_request import (
    CreatePurchaseOrderAdditionalCostRowRequest,
)
from .create_purchase_order_additional_cost_row_request_distribution_method import (
    CreatePurchaseOrderAdditionalCostRowRequestDistributionMethod,
)
from .create_purchase_order_request import CreatePurchaseOrderRequest
from .create_purchase_order_request_entity_type import (
    CreatePurchaseOrderRequestEntityType,
)
from .create_purchase_order_request_status import CreatePurchaseOrderRequestStatus
from .create_purchase_order_row_request import CreatePurchaseOrderRowRequest
from .create_recipes_request import CreateRecipesRequest
from .create_recipes_request_rows_item import CreateRecipesRequestRowsItem
from .create_sales_order_address_request import CreateSalesOrderAddressRequest
from .create_sales_order_address_request_entity_type import (
    CreateSalesOrderAddressRequestEntityType,
)
from .create_sales_order_fulfillment_body import CreateSalesOrderFulfillmentBody
from .create_sales_order_request import CreateSalesOrderRequest
from .create_sales_order_request_sales_order_rows_item import (
    CreateSalesOrderRequestSalesOrderRowsItem,
)
from .create_sales_order_request_sales_order_rows_item_attributes_item import (
    CreateSalesOrderRequestSalesOrderRowsItemAttributesItem,
)
from .create_sales_order_request_status import CreateSalesOrderRequestStatus
from .create_sales_order_row_request import CreateSalesOrderRowRequest
from .create_sales_order_shipping_fee_request import CreateSalesOrderShippingFeeRequest
from .create_sales_return_request import CreateSalesReturnRequest
from .create_sales_return_row_body import CreateSalesReturnRowBody
from .create_sales_return_row_request import CreateSalesReturnRowRequest
from .create_serial_numbers_body import CreateSerialNumbersBody
from .create_serial_numbers_body_resource_type import (
    CreateSerialNumbersBodyResourceType,
)
from .create_service_request import CreateServiceRequest
from .create_service_variant_request import CreateServiceVariantRequest
from .create_service_variant_request_custom_fields_item import (
    CreateServiceVariantRequestCustomFieldsItem,
)
from .create_stock_adjustment_request import CreateStockAdjustmentRequest
from .create_stock_adjustment_request_status import CreateStockAdjustmentRequestStatus
from .create_stock_transfer_body import CreateStockTransferBody
from .create_stocktake_request import CreateStocktakeRequest
from .create_stocktake_request_status import CreateStocktakeRequestStatus
from .create_stocktake_row_request import CreateStocktakeRowRequest
from .create_supplier_address_request import CreateSupplierAddressRequest
from .create_supplier_request import CreateSupplierRequest
from .create_tax_rate_request import CreateTaxRateRequest
from .create_variant_request import CreateVariantRequest
from .create_variant_request_config_attributes_item import (
    CreateVariantRequestConfigAttributesItem,
)
from .create_variant_request_custom_fields_item import (
    CreateVariantRequestCustomFieldsItem,
)
from .create_webhook_request import CreateWebhookRequest
from .custom_field import CustomField
from .custom_fields_collection import CustomFieldsCollection
from .custom_fields_collection_list_response import CustomFieldsCollectionListResponse
from .custom_fields_collection_resource_type import CustomFieldsCollectionResourceType
from .customer import Customer
from .customer_address import CustomerAddress
from .customer_address_entity_type import CustomerAddressEntityType
from .customer_address_list_response import CustomerAddressListResponse
from .customer_list_response import CustomerListResponse
from .deletable_entity import DeletableEntity
from .detailed_error_response import DetailedErrorResponse
from .error_response import ErrorResponse
from .factory import Factory
from .factory_legal_address import FactoryLegalAddress
from .find_purchase_orders_billing_status import FindPurchaseOrdersBillingStatus
from .find_purchase_orders_entity_type import FindPurchaseOrdersEntityType
from .find_purchase_orders_extend_item import FindPurchaseOrdersExtendItem
from .find_purchase_orders_status import FindPurchaseOrdersStatus
from .get_all_customer_addresses_entity_type import GetAllCustomerAddressesEntityType
from .get_all_inventory_movements_resource_type import (
    GetAllInventoryMovementsResourceType,
)
from .get_all_inventory_point_extend_item import GetAllInventoryPointExtendItem
from .get_all_locations_response_200 import GetAllLocationsResponse200
from .get_all_manufacturing_order_operation_rows_status import (
    GetAllManufacturingOrderOperationRowsStatus,
)
from .get_all_manufacturing_order_recipe_rows_ingredient_availability import (
    GetAllManufacturingOrderRecipeRowsIngredientAvailability,
)
from .get_all_manufacturing_orders_status import GetAllManufacturingOrdersStatus
from .get_all_materials_extend_item import GetAllMaterialsExtendItem
from .get_all_product_operation_rows_response_200 import (
    GetAllProductOperationRowsResponse200,
)
from .get_all_product_operation_rows_response_200_data_item import (
    GetAllProductOperationRowsResponse200DataItem,
)
from .get_all_products_extend_item import GetAllProductsExtendItem
from .get_all_sales_order_addresses_entity_type import (
    GetAllSalesOrderAddressesEntityType,
)
from .get_all_sales_order_rows_extend_item import GetAllSalesOrderRowsExtendItem
from .get_all_sales_order_rows_product_availability import (
    GetAllSalesOrderRowsProductAvailability,
)
from .get_all_sales_orders_ingredient_availability import (
    GetAllSalesOrdersIngredientAvailability,
)
from .get_all_sales_orders_product_availability import (
    GetAllSalesOrdersProductAvailability,
)
from .get_all_sales_returns_refund_status import GetAllSalesReturnsRefundStatus
from .get_all_serial_numbers_resource_type import GetAllSerialNumbersResourceType
from .get_all_variants_extend_item import GetAllVariantsExtendItem
from .get_material_extend_item import GetMaterialExtendItem
from .get_product_extend_item import GetProductExtendItem
from .get_purchase_order_additional_cost_rows_distribution_method import (
    GetPurchaseOrderAdditionalCostRowsDistributionMethod,
)
from .get_purchase_order_extend_item import GetPurchaseOrderExtendItem
from .get_sales_order_returnable_items_response_200_item import (
    GetSalesOrderReturnableItemsResponse200Item,
)
from .get_sales_order_row_extend_item import GetSalesOrderRowExtendItem
from .get_sales_return_reasons_response_200_item import (
    GetSalesReturnReasonsResponse200Item,
)
from .get_sales_return_row_unassigned_batch_transactions_response_200 import (
    GetSalesReturnRowUnassignedBatchTransactionsResponse200,
)
from .get_sales_return_row_unassigned_batch_transactions_response_200_data_item import (
    GetSalesReturnRowUnassignedBatchTransactionsResponse200DataItem,
)
from .get_variant_extend_item import GetVariantExtendItem
from .inventory import Inventory
from .inventory_item import InventoryItem
from .inventory_item_type import InventoryItemType
from .inventory_list_response import InventoryListResponse
from .inventory_movement import InventoryMovement
from .inventory_movement_list_response import InventoryMovementListResponse
from .inventory_movement_resource_type import InventoryMovementResourceType
from .inventory_reorder_point import InventoryReorderPoint
from .inventory_reorder_point_response import InventoryReorderPointResponse
from .inventory_safety_stock_level import InventorySafetyStockLevel
from .inventory_safety_stock_level_response import InventorySafetyStockLevelResponse
from .item_config import ItemConfig
from .location_address import LocationAddress
from .location_type_0 import LocationType0
from .make_to_order_manufacturing_order_request import (
    MakeToOrderManufacturingOrderRequest,
)
from .manufacturing_order import ManufacturingOrder
from .manufacturing_order_ingredient_availability_type_0 import (
    ManufacturingOrderIngredientAvailabilityType0,
)
from .manufacturing_order_list_response import ManufacturingOrderListResponse
from .manufacturing_order_operation_production import (
    ManufacturingOrderOperationProduction,
)
from .manufacturing_order_operation_row import ManufacturingOrderOperationRow
from .manufacturing_order_operation_row_list_response import (
    ManufacturingOrderOperationRowListResponse,
)
from .manufacturing_order_operation_row_status import (
    ManufacturingOrderOperationRowStatus,
)
from .manufacturing_order_production import ManufacturingOrderProduction
from .manufacturing_order_production_ingredient import (
    ManufacturingOrderProductionIngredient,
)
from .manufacturing_order_production_ingredient_response import (
    ManufacturingOrderProductionIngredientResponse,
)
from .manufacturing_order_production_list_response import (
    ManufacturingOrderProductionListResponse,
)
from .manufacturing_order_recipe_row import ManufacturingOrderRecipeRow
from .manufacturing_order_recipe_row_batch_transactions_item import (
    ManufacturingOrderRecipeRowBatchTransactionsItem,
)
from .manufacturing_order_recipe_row_list_response import (
    ManufacturingOrderRecipeRowListResponse,
)
from .manufacturing_order_status import ManufacturingOrderStatus
from .material import Material
from .material_config import MaterialConfig
from .material_list_response import MaterialListResponse
from .material_type import MaterialType
from .negative_stock import NegativeStock
from .negative_stock_list_response import NegativeStockListResponse
from .operator import Operator
from .outsourced_purchase_order import OutsourcedPurchaseOrder
from .outsourced_purchase_order_entity_type import OutsourcedPurchaseOrderEntityType
from .outsourced_purchase_order_ingredient_availability import (
    OutsourcedPurchaseOrderIngredientAvailability,
)
from .outsourced_purchase_order_recipe_row import OutsourcedPurchaseOrderRecipeRow
from .outsourced_purchase_order_recipe_row_batch_transactions_item import (
    OutsourcedPurchaseOrderRecipeRowBatchTransactionsItem,
)
from .outsourced_purchase_order_recipe_row_ingredient_availability import (
    OutsourcedPurchaseOrderRecipeRowIngredientAvailability,
)
from .outsourced_purchase_order_recipe_row_list_response import (
    OutsourcedPurchaseOrderRecipeRowListResponse,
)
from .price_list import PriceList
from .price_list_customer import PriceListCustomer
from .price_list_customer_list_response import PriceListCustomerListResponse
from .price_list_list_response import PriceListListResponse
from .price_list_row import PriceListRow
from .price_list_row_adjustment_method import PriceListRowAdjustmentMethod
from .price_list_row_list_response import PriceListRowListResponse
from .product import Product
from .product_list_response import ProductListResponse
from .product_operation_rerank import ProductOperationRerank
from .product_operation_rerank_request import ProductOperationRerankRequest
from .product_type import ProductType
from .purchase_order_accounting_metadata import PurchaseOrderAccountingMetadata
from .purchase_order_accounting_metadata_list_response import (
    PurchaseOrderAccountingMetadataListResponse,
)
from .purchase_order_additional_cost_row import PurchaseOrderAdditionalCostRow
from .purchase_order_additional_cost_row_list_response import (
    PurchaseOrderAdditionalCostRowListResponse,
)
from .purchase_order_base import PurchaseOrderBase
from .purchase_order_base_billing_status import PurchaseOrderBaseBillingStatus
from .purchase_order_base_entity_type import PurchaseOrderBaseEntityType
from .purchase_order_base_last_document_status import (
    PurchaseOrderBaseLastDocumentStatus,
)
from .purchase_order_base_status import PurchaseOrderBaseStatus
from .purchase_order_list_response import PurchaseOrderListResponse
from .purchase_order_receive_row import PurchaseOrderReceiveRow
from .purchase_order_receive_row_batch_transactions_item import (
    PurchaseOrderReceiveRowBatchTransactionsItem,
)
from .purchase_order_row import PurchaseOrderRow
from .purchase_order_row_batch_transactions_item import (
    PurchaseOrderRowBatchTransactionsItem,
)
from .purchase_order_row_list_response import PurchaseOrderRowListResponse
from .purchase_order_row_request import PurchaseOrderRowRequest
from .recipe import Recipe
from .recipe_list_response import RecipeListResponse
from .regular_purchase_order import RegularPurchaseOrder
from .regular_purchase_order_entity_type import RegularPurchaseOrderEntityType
from .sales_order import SalesOrder
from .sales_order_accounting_metadata import SalesOrderAccountingMetadata
from .sales_order_accounting_metadata_integration_type import (
    SalesOrderAccountingMetadataIntegrationType,
)
from .sales_order_accounting_metadata_list_response import (
    SalesOrderAccountingMetadataListResponse,
)
from .sales_order_address import SalesOrderAddress
from .sales_order_address_entity_type import SalesOrderAddressEntityType
from .sales_order_address_list_response import SalesOrderAddressListResponse
from .sales_order_fulfillment import SalesOrderFulfillment
from .sales_order_fulfillment_list_response import SalesOrderFulfillmentListResponse
from .sales_order_ingredient_availability_type_0 import (
    SalesOrderIngredientAvailabilityType0,
)
from .sales_order_list_response import SalesOrderListResponse
from .sales_order_product_availability_type_0 import SalesOrderProductAvailabilityType0
from .sales_order_production_status_type_0 import SalesOrderProductionStatusType0
from .sales_order_row import SalesOrderRow
from .sales_order_row_attributes_item import SalesOrderRowAttributesItem
from .sales_order_row_batch_transactions_item import SalesOrderRowBatchTransactionsItem
from .sales_order_row_list_response import SalesOrderRowListResponse
from .sales_order_row_product_availability_type_0 import (
    SalesOrderRowProductAvailabilityType0,
)
from .sales_order_shipping_fee import SalesOrderShippingFee
from .sales_order_shipping_fee_list_response import SalesOrderShippingFeeListResponse
from .sales_order_status import SalesOrderStatus
from .sales_return import SalesReturn
from .sales_return_list_response import SalesReturnListResponse
from .sales_return_row import SalesReturnRow
from .sales_return_row_list_response import SalesReturnRowListResponse
from .sales_return_status import SalesReturnStatus
from .serial_number import SerialNumber
from .serial_number_list_response import SerialNumberListResponse
from .serial_number_resource_type import SerialNumberResourceType
from .serial_number_stock import SerialNumberStock
from .serial_number_stock_transactions_item import SerialNumberStockTransactionsItem
from .service import Service
from .service_list_response import ServiceListResponse
from .service_type import ServiceType
from .service_variant import ServiceVariant
from .service_variant_custom_fields_item import ServiceVariantCustomFieldsItem
from .service_variant_type import ServiceVariantType
from .stock_adjustment import StockAdjustment
from .stock_adjustment_list_response import StockAdjustmentListResponse
from .stock_adjustment_status import StockAdjustmentStatus
from .stock_transfer import StockTransfer
from .stock_transfer_list_response import StockTransferListResponse
from .stock_transfer_row import StockTransferRow
from .stock_transfer_row_batch_transactions_item import (
    StockTransferRowBatchTransactionsItem,
)
from .stock_transfer_status import StockTransferStatus
from .stocktake import Stocktake
from .stocktake_list_response import StocktakeListResponse
from .stocktake_row import StocktakeRow
from .stocktake_row_list_response import StocktakeRowListResponse
from .stocktake_status import StocktakeStatus
from .storage_bin import StorageBin
from .storage_bin_list_response import StorageBinListResponse
from .storage_bin_response import StorageBinResponse
from .storage_bin_update import StorageBinUpdate
from .supplier import Supplier
from .supplier_address import SupplierAddress
from .supplier_address_list_response import SupplierAddressListResponse
from .supplier_address_request import SupplierAddressRequest
from .supplier_list_response import SupplierListResponse
from .tax_rate import TaxRate
from .tax_rate_list_response import TaxRateListResponse
from .unlink_manufacturing_order_request import UnlinkManufacturingOrderRequest
from .unlink_variant_bin_location_request import UnlinkVariantBinLocationRequest
from .updatable_entity import UpdatableEntity
from .update_bom_row_request import UpdateBomRowRequest
from .update_customer_address_body import UpdateCustomerAddressBody
from .update_customer_address_body_entity_type import (
    UpdateCustomerAddressBodyEntityType,
)
from .update_customer_request import UpdateCustomerRequest
from .update_manufacturing_order_operation_row_request import (
    UpdateManufacturingOrderOperationRowRequest,
)
from .update_manufacturing_order_production_ingredient_request import (
    UpdateManufacturingOrderProductionIngredientRequest,
)
from .update_manufacturing_order_production_request import (
    UpdateManufacturingOrderProductionRequest,
)
from .update_manufacturing_order_recipe_row_request import (
    UpdateManufacturingOrderRecipeRowRequest,
)
from .update_manufacturing_order_recipe_row_request_batch_transactions_item import (
    UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem,
)
from .update_manufacturing_order_request import UpdateManufacturingOrderRequest
from .update_material_request import UpdateMaterialRequest
from .update_material_request_configs_item import UpdateMaterialRequestConfigsItem
from .update_outsourced_purchase_order_recipe_row_body import (
    UpdateOutsourcedPurchaseOrderRecipeRowBody,
)
from .update_price_list_customer_request import UpdatePriceListCustomerRequest
from .update_price_list_request import UpdatePriceListRequest
from .update_price_list_row_request import UpdatePriceListRowRequest
from .update_product_operation_row_body import UpdateProductOperationRowBody
from .update_product_operation_row_response_200 import (
    UpdateProductOperationRowResponse200,
)
from .update_product_request import UpdateProductRequest
from .update_product_request_configs_item import UpdateProductRequestConfigsItem
from .update_purchase_order_additional_cost_row_request import (
    UpdatePurchaseOrderAdditionalCostRowRequest,
)
from .update_purchase_order_additional_cost_row_request_distribution_method import (
    UpdatePurchaseOrderAdditionalCostRowRequestDistributionMethod,
)
from .update_purchase_order_request import UpdatePurchaseOrderRequest
from .update_purchase_order_request_status import UpdatePurchaseOrderRequestStatus
from .update_purchase_order_row_request import UpdatePurchaseOrderRowRequest
from .update_recipe_row_body import UpdateRecipeRowBody
from .update_sales_order_address_request import UpdateSalesOrderAddressRequest
from .update_sales_order_address_request_entity_type import (
    UpdateSalesOrderAddressRequestEntityType,
)
from .update_sales_order_body import UpdateSalesOrderBody
from .update_sales_order_body_status import UpdateSalesOrderBodyStatus
from .update_sales_order_fulfillment_body import UpdateSalesOrderFulfillmentBody
from .update_sales_order_row_request import UpdateSalesOrderRowRequest
from .update_sales_order_shipping_fee_body import UpdateSalesOrderShippingFeeBody
from .update_sales_return_request import UpdateSalesReturnRequest
from .update_sales_return_request_status import UpdateSalesReturnRequestStatus
from .update_sales_return_row_body import UpdateSalesReturnRowBody
from .update_service_request import UpdateServiceRequest
from .update_stock_adjustment_request import UpdateStockAdjustmentRequest
from .update_stock_adjustment_request_status import UpdateStockAdjustmentRequestStatus
from .update_stock_transfer_body import UpdateStockTransferBody
from .update_stock_transfer_status_body import UpdateStockTransferStatusBody
from .update_stock_transfer_status_body_status import (
    UpdateStockTransferStatusBodyStatus,
)
from .update_stocktake_request import UpdateStocktakeRequest
from .update_stocktake_request_status import UpdateStocktakeRequestStatus
from .update_stocktake_row_request import UpdateStocktakeRowRequest
from .update_supplier_address_request import UpdateSupplierAddressRequest
from .update_supplier_request import UpdateSupplierRequest
from .update_variant_request import UpdateVariantRequest
from .update_variant_request_config_attributes_item import (
    UpdateVariantRequestConfigAttributesItem,
)
from .update_variant_request_custom_fields_item import (
    UpdateVariantRequestCustomFieldsItem,
)
from .update_webhook_request import UpdateWebhookRequest
from .user import User
from .user_list_response import UserListResponse
from .validation_error_detail import ValidationErrorDetail
from .validation_error_detail_info import ValidationErrorDetailInfo
from .variant import Variant
from .variant_config_attributes_item import VariantConfigAttributesItem
from .variant_custom_fields_item import VariantCustomFieldsItem
from .variant_default_storage_bin_link import VariantDefaultStorageBinLink
from .variant_default_storage_bin_link_response import (
    VariantDefaultStorageBinLinkResponse,
)
from .variant_list_response import VariantListResponse
from .variant_response import VariantResponse
from .variant_response_config_attributes_item import VariantResponseConfigAttributesItem
from .variant_response_custom_fields_item import VariantResponseCustomFieldsItem
from .variant_response_type import VariantResponseType
from .variant_type import VariantType
from .webhook import Webhook
from .webhook_event import WebhookEvent
from .webhook_event_payload import WebhookEventPayload
from .webhook_event_payload_object import WebhookEventPayloadObject
from .webhook_list_response import WebhookListResponse
from .webhook_logs_export import WebhookLogsExport
from .webhook_logs_export_request import WebhookLogsExportRequest
from .webhook_logs_export_request_format import WebhookLogsExportRequestFormat
from .webhook_logs_export_request_status_filter_item import (
    WebhookLogsExportRequestStatusFilterItem,
)

__all__ = (
    "AdditionalCost",
    "AdditionalCostListResponse",
    "ArchivableDeletableEntity",
    "ArchivableEntity",
    "AssignedOperator",
    "BaseEntity",
    "Batch",
    "BatchCreateBomRowsRequest",
    "BatchResponse",
    "BatchStock",
    "BatchStockListResponse",
    "BatchStockUpdate",
    "BatchTransaction",
    "BomRow",
    "BomRowListResponse",
    "CodedErrorResponse",
    "CreateBomRowRequest",
    "CreateCustomerAddressRequest",
    "CreateCustomerAddressRequestEntityType",
    "CreateCustomerRequest",
    "CreateInventoryReorderPointBody",
    "CreateManufacturingOrderOperationRowRequest",
    "CreateManufacturingOrderProductionRequest",
    "CreateManufacturingOrderRecipeRowRequest",
    "CreateManufacturingOrderRecipeRowRequestBatchTransactionsItem",
    "CreateManufacturingOrderRequest",
    "CreateMaterialRequest",
    "CreateOutsourcedPurchaseOrderRecipeRowBody",
    "CreatePriceListCustomerRequest",
    "CreatePriceListRequest",
    "CreatePriceListRowRequest",
    "CreateProductOperationRowsBody",
    "CreateProductOperationRowsBodyRowsItem",
    "CreateProductOperationRowsBodyRowsItemType",
    "CreateProductRequest",
    "CreateProductRequestConfigsItem",
    "CreatePurchaseOrderAdditionalCostRowRequest",
    "CreatePurchaseOrderAdditionalCostRowRequestDistributionMethod",
    "CreatePurchaseOrderRequest",
    "CreatePurchaseOrderRequestEntityType",
    "CreatePurchaseOrderRequestStatus",
    "CreatePurchaseOrderRowRequest",
    "CreateRecipesRequest",
    "CreateRecipesRequestRowsItem",
    "CreateSalesOrderAddressRequest",
    "CreateSalesOrderAddressRequestEntityType",
    "CreateSalesOrderFulfillmentBody",
    "CreateSalesOrderRequest",
    "CreateSalesOrderRequestSalesOrderRowsItem",
    "CreateSalesOrderRequestSalesOrderRowsItemAttributesItem",
    "CreateSalesOrderRequestStatus",
    "CreateSalesOrderRowRequest",
    "CreateSalesOrderShippingFeeRequest",
    "CreateSalesReturnRequest",
    "CreateSalesReturnRowBody",
    "CreateSalesReturnRowRequest",
    "CreateSerialNumbersBody",
    "CreateSerialNumbersBodyResourceType",
    "CreateServiceRequest",
    "CreateServiceVariantRequest",
    "CreateServiceVariantRequestCustomFieldsItem",
    "CreateStockAdjustmentRequest",
    "CreateStockAdjustmentRequestStatus",
    "CreateStockTransferBody",
    "CreateStocktakeRequest",
    "CreateStocktakeRequestStatus",
    "CreateStocktakeRowRequest",
    "CreateSupplierAddressRequest",
    "CreateSupplierRequest",
    "CreateTaxRateRequest",
    "CreateVariantRequest",
    "CreateVariantRequestConfigAttributesItem",
    "CreateVariantRequestCustomFieldsItem",
    "CreateWebhookRequest",
    "CustomField",
    "CustomFieldsCollection",
    "CustomFieldsCollectionListResponse",
    "CustomFieldsCollectionResourceType",
    "Customer",
    "CustomerAddress",
    "CustomerAddressEntityType",
    "CustomerAddressListResponse",
    "CustomerListResponse",
    "DeletableEntity",
    "DetailedErrorResponse",
    "ErrorResponse",
    "Factory",
    "FactoryLegalAddress",
    "FindPurchaseOrdersBillingStatus",
    "FindPurchaseOrdersEntityType",
    "FindPurchaseOrdersExtendItem",
    "FindPurchaseOrdersStatus",
    "GetAllCustomerAddressesEntityType",
    "GetAllInventoryMovementsResourceType",
    "GetAllInventoryPointExtendItem",
    "GetAllLocationsResponse200",
    "GetAllManufacturingOrderOperationRowsStatus",
    "GetAllManufacturingOrderRecipeRowsIngredientAvailability",
    "GetAllManufacturingOrdersStatus",
    "GetAllMaterialsExtendItem",
    "GetAllProductOperationRowsResponse200",
    "GetAllProductOperationRowsResponse200DataItem",
    "GetAllProductsExtendItem",
    "GetAllSalesOrderAddressesEntityType",
    "GetAllSalesOrderRowsExtendItem",
    "GetAllSalesOrderRowsProductAvailability",
    "GetAllSalesOrdersIngredientAvailability",
    "GetAllSalesOrdersProductAvailability",
    "GetAllSalesReturnsRefundStatus",
    "GetAllSerialNumbersResourceType",
    "GetAllVariantsExtendItem",
    "GetMaterialExtendItem",
    "GetProductExtendItem",
    "GetPurchaseOrderAdditionalCostRowsDistributionMethod",
    "GetPurchaseOrderExtendItem",
    "GetSalesOrderReturnableItemsResponse200Item",
    "GetSalesOrderRowExtendItem",
    "GetSalesReturnReasonsResponse200Item",
    "GetSalesReturnRowUnassignedBatchTransactionsResponse200",
    "GetSalesReturnRowUnassignedBatchTransactionsResponse200DataItem",
    "GetVariantExtendItem",
    "Inventory",
    "InventoryItem",
    "InventoryItemType",
    "InventoryListResponse",
    "InventoryMovement",
    "InventoryMovementListResponse",
    "InventoryMovementResourceType",
    "InventoryReorderPoint",
    "InventoryReorderPointResponse",
    "InventorySafetyStockLevel",
    "InventorySafetyStockLevelResponse",
    "ItemConfig",
    "LocationAddress",
    "LocationType0",
    "MakeToOrderManufacturingOrderRequest",
    "ManufacturingOrder",
    "ManufacturingOrderIngredientAvailabilityType0",
    "ManufacturingOrderListResponse",
    "ManufacturingOrderOperationProduction",
    "ManufacturingOrderOperationRow",
    "ManufacturingOrderOperationRowListResponse",
    "ManufacturingOrderOperationRowStatus",
    "ManufacturingOrderProduction",
    "ManufacturingOrderProductionIngredient",
    "ManufacturingOrderProductionIngredientResponse",
    "ManufacturingOrderProductionListResponse",
    "ManufacturingOrderRecipeRow",
    "ManufacturingOrderRecipeRowBatchTransactionsItem",
    "ManufacturingOrderRecipeRowListResponse",
    "ManufacturingOrderStatus",
    "Material",
    "MaterialConfig",
    "MaterialListResponse",
    "MaterialType",
    "NegativeStock",
    "NegativeStockListResponse",
    "Operator",
    "OutsourcedPurchaseOrder",
    "OutsourcedPurchaseOrderEntityType",
    "OutsourcedPurchaseOrderIngredientAvailability",
    "OutsourcedPurchaseOrderRecipeRow",
    "OutsourcedPurchaseOrderRecipeRowBatchTransactionsItem",
    "OutsourcedPurchaseOrderRecipeRowIngredientAvailability",
    "OutsourcedPurchaseOrderRecipeRowListResponse",
    "PriceList",
    "PriceListCustomer",
    "PriceListCustomerListResponse",
    "PriceListListResponse",
    "PriceListRow",
    "PriceListRowAdjustmentMethod",
    "PriceListRowListResponse",
    "Product",
    "ProductListResponse",
    "ProductOperationRerank",
    "ProductOperationRerankRequest",
    "ProductType",
    "PurchaseOrderAccountingMetadata",
    "PurchaseOrderAccountingMetadataListResponse",
    "PurchaseOrderAdditionalCostRow",
    "PurchaseOrderAdditionalCostRowListResponse",
    "PurchaseOrderBase",
    "PurchaseOrderBaseBillingStatus",
    "PurchaseOrderBaseEntityType",
    "PurchaseOrderBaseLastDocumentStatus",
    "PurchaseOrderBaseStatus",
    "PurchaseOrderListResponse",
    "PurchaseOrderReceiveRow",
    "PurchaseOrderReceiveRowBatchTransactionsItem",
    "PurchaseOrderRow",
    "PurchaseOrderRowBatchTransactionsItem",
    "PurchaseOrderRowListResponse",
    "PurchaseOrderRowRequest",
    "Recipe",
    "RecipeListResponse",
    "RegularPurchaseOrder",
    "RegularPurchaseOrderEntityType",
    "SalesOrder",
    "SalesOrderAccountingMetadata",
    "SalesOrderAccountingMetadataIntegrationType",
    "SalesOrderAccountingMetadataListResponse",
    "SalesOrderAddress",
    "SalesOrderAddressEntityType",
    "SalesOrderAddressListResponse",
    "SalesOrderFulfillment",
    "SalesOrderFulfillmentListResponse",
    "SalesOrderIngredientAvailabilityType0",
    "SalesOrderListResponse",
    "SalesOrderProductAvailabilityType0",
    "SalesOrderProductionStatusType0",
    "SalesOrderRow",
    "SalesOrderRowAttributesItem",
    "SalesOrderRowBatchTransactionsItem",
    "SalesOrderRowListResponse",
    "SalesOrderRowProductAvailabilityType0",
    "SalesOrderShippingFee",
    "SalesOrderShippingFeeListResponse",
    "SalesOrderStatus",
    "SalesReturn",
    "SalesReturnListResponse",
    "SalesReturnRow",
    "SalesReturnRowListResponse",
    "SalesReturnStatus",
    "SerialNumber",
    "SerialNumberListResponse",
    "SerialNumberResourceType",
    "SerialNumberStock",
    "SerialNumberStockTransactionsItem",
    "Service",
    "ServiceListResponse",
    "ServiceType",
    "ServiceVariant",
    "ServiceVariantCustomFieldsItem",
    "ServiceVariantType",
    "StockAdjustment",
    "StockAdjustmentListResponse",
    "StockAdjustmentStatus",
    "StockTransfer",
    "StockTransferListResponse",
    "StockTransferRow",
    "StockTransferRowBatchTransactionsItem",
    "StockTransferStatus",
    "Stocktake",
    "StocktakeListResponse",
    "StocktakeRow",
    "StocktakeRowListResponse",
    "StocktakeStatus",
    "StorageBin",
    "StorageBinListResponse",
    "StorageBinResponse",
    "StorageBinUpdate",
    "Supplier",
    "SupplierAddress",
    "SupplierAddressListResponse",
    "SupplierAddressRequest",
    "SupplierListResponse",
    "TaxRate",
    "TaxRateListResponse",
    "UnlinkManufacturingOrderRequest",
    "UnlinkVariantBinLocationRequest",
    "UpdatableEntity",
    "UpdateBomRowRequest",
    "UpdateCustomerAddressBody",
    "UpdateCustomerAddressBodyEntityType",
    "UpdateCustomerRequest",
    "UpdateManufacturingOrderOperationRowRequest",
    "UpdateManufacturingOrderProductionIngredientRequest",
    "UpdateManufacturingOrderProductionRequest",
    "UpdateManufacturingOrderRecipeRowRequest",
    "UpdateManufacturingOrderRecipeRowRequestBatchTransactionsItem",
    "UpdateManufacturingOrderRequest",
    "UpdateMaterialRequest",
    "UpdateMaterialRequestConfigsItem",
    "UpdateOutsourcedPurchaseOrderRecipeRowBody",
    "UpdatePriceListCustomerRequest",
    "UpdatePriceListRequest",
    "UpdatePriceListRowRequest",
    "UpdateProductOperationRowBody",
    "UpdateProductOperationRowResponse200",
    "UpdateProductRequest",
    "UpdateProductRequestConfigsItem",
    "UpdatePurchaseOrderAdditionalCostRowRequest",
    "UpdatePurchaseOrderAdditionalCostRowRequestDistributionMethod",
    "UpdatePurchaseOrderRequest",
    "UpdatePurchaseOrderRequestStatus",
    "UpdatePurchaseOrderRowRequest",
    "UpdateRecipeRowBody",
    "UpdateSalesOrderAddressRequest",
    "UpdateSalesOrderAddressRequestEntityType",
    "UpdateSalesOrderBody",
    "UpdateSalesOrderBodyStatus",
    "UpdateSalesOrderFulfillmentBody",
    "UpdateSalesOrderRowRequest",
    "UpdateSalesOrderShippingFeeBody",
    "UpdateSalesReturnRequest",
    "UpdateSalesReturnRequestStatus",
    "UpdateSalesReturnRowBody",
    "UpdateServiceRequest",
    "UpdateStockAdjustmentRequest",
    "UpdateStockAdjustmentRequestStatus",
    "UpdateStockTransferBody",
    "UpdateStockTransferStatusBody",
    "UpdateStockTransferStatusBodyStatus",
    "UpdateStocktakeRequest",
    "UpdateStocktakeRequestStatus",
    "UpdateStocktakeRowRequest",
    "UpdateSupplierAddressRequest",
    "UpdateSupplierRequest",
    "UpdateVariantRequest",
    "UpdateVariantRequestConfigAttributesItem",
    "UpdateVariantRequestCustomFieldsItem",
    "UpdateWebhookRequest",
    "User",
    "UserListResponse",
    "ValidationErrorDetail",
    "ValidationErrorDetailInfo",
    "Variant",
    "VariantConfigAttributesItem",
    "VariantCustomFieldsItem",
    "VariantDefaultStorageBinLink",
    "VariantDefaultStorageBinLinkResponse",
    "VariantListResponse",
    "VariantResponse",
    "VariantResponseConfigAttributesItem",
    "VariantResponseCustomFieldsItem",
    "VariantResponseType",
    "VariantType",
    "Webhook",
    "WebhookEvent",
    "WebhookEventPayload",
    "WebhookEventPayloadObject",
    "WebhookListResponse",
    "WebhookLogsExport",
    "WebhookLogsExportRequest",
    "WebhookLogsExportRequestFormat",
    "WebhookLogsExportRequestStatusFilterItem",
)
