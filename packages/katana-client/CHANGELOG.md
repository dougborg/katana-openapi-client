# Changelog

## [0.3.0](https://github.com/dougborg/katana-openapi-client/compare/ts-v0.2.0...ts-v0.3.0) (2026-10-07)


### Features

* **ts:** add response helpers, typecheck tests, and live test-tenant smoke suite ([2ff98f2](https://github.com/dougborg/katana-openapi-client/commit/2ff98f21b57c5b2af9173432e382049585ebc2a5)), closes [#911](https://github.com/dougborg/katana-openapi-client/issues/911)

## [0.2.0](https://github.com/dougborg/katana-openapi-client/compare/ts-v0.1.0...ts-v0.2.0) (2026-10-07)


### Features

* **ts:** bring TS client resilience to parity with the Python client ([42f6efd](https://github.com/dougborg/katana-openapi-client/commit/42f6efd2cc02f3159b515a71917e347e88c879db)), closes [#594](https://github.com/dougborg/katana-openapi-client/issues/594)

## [0.1.0](https://github.com/dougborg/katana-openapi-client/compare/ts-v0.0.1...ts-v0.1.0) (2026-10-05)


### ⚠ BREAKING CHANGES

* **client:** get_all_sales_order_fulfillments.status now requires SalesOrderFulfillmentStatus; get_all_sales_orders.production_status requires SalesOrderProductionStatus; get_all_sales_returns.status requires SalesReturnStatus; get_all_stocktakes.status requires StocktakeStatus. This applies to sync, sync_detailed, asyncio, and asyncio_detailed. Convert raw strings with the matching enum constructor or omit the filter. TypeScript query types narrow from string to the existing status unions.
* CreateMaterialRequest.variants now uses CreateMaterialVariantRequest rather than CreateVariantRequest. Nested sales_price and parent IDs are unsupported by POST /materials. Product and standalone variant creation retain their existing request model.
* **client:** align sales-return filters with verified wire behavior ([#1070](https://github.com/dougborg/katana-openapi-client/issues/1070))
* **client:** Variant/service custom fields accept UUID maps or legacy arrays; legacy update entries now require field_name and field_value and are limited to three. Pydantic-to-attrs conversion preserves explicit nullable values and omitted fields.
* **client:** Remove unsupported manufacturing_order_id from operation PATCH and serial_numbers from MO PATCH; relax operation and serial-create required fields.
* **client:** the search request models change shape. `SalesOrderSearchRequest` / `SalesOrderRowSearchRequest` now take `filter`, `order`, `limit` and `page` at the top level; `order`/`limit`/ `page` are no longer nested inside `filter`, and the `where` level is gone. `SalesOrderSearchWhere` / `SalesOrderRowSearchWhere` are renamed to `SalesOrderSearchFilter` / `SalesOrderRowSearchFilter`, replacing the former envelope schemas of those names. No working call can break — the previous shape was rejected with 422 by the API.
* **client:** generated query-parameter enums changed members. `GetAllManufacturingOrdersStatus` drops `PAUSED`/`COMPLETED` and gains `DONE`/`PARTIALLY_COMPLETED`; the `serial_numbers`/`inventory_movements` `resource_type` enums change values; and the customer/sales-order address `entity_type` filter changes from `PurchaseOrderEntityType` to `AddressEntityType`. Callers using the removed members (which never matched the live API) must update.
* **client:** PurchaseOrderRow.landed_cost narrows from string|number to number across the attrs, pydantic, and TypeScript clients.
* **client:** InventorySafetyStockLevel.value changes number->string across the attrs, pydantic, and TypeScript clients.
* **client:** InventoryReorderPoint.value changes number->string and SalesReturnRow create/update request quantity changes string->number across the attrs, pydantic, and TypeScript clients.
* **client:** InventoryItem.purchase_uom_conversion_rate (and the Material / Product schemas that compose it) changes from number to string in the attrs, pydantic, and TypeScript clients to match the live wire format.
* **client:** ManufacturingOrderOperationRow.cost_per_hour and cost_parameter change from number to string in the attrs, pydantic, and TypeScript clients to match the live wire format.
* **ts-client:** ValidationError.details items changed from { field, message, code, value } to the Ajv shape { path, code, message, info }; the hand-written ValidationErrorDetail interface is removed in favor of the generated union type.
* **client:** regenerate TS client for the spec changes + gate it; use StorageBinResponse for bin_locations items

### Features

* **client:** add inventory-signals and MO production-ingredients list endpoints ([#1039](https://github.com/dougborg/katana-openapi-client/issues/1039)) ([d915ae2](https://github.com/dougborg/katana-openapi-client/commit/d915ae2ac234433849342ab0e0d917ad4acf60df)), closes [#1032](https://github.com/dougborg/katana-openapi-client/issues/1032)
* **client:** add manufacturing-order and sales-order rerank endpoints ([#1037](https://github.com/dougborg/katana-openapi-client/issues/1037)) ([2b0e31c](https://github.com/dougborg/katana-openapi-client/commit/2b0e31ce22dd354c61f07598ffb45b03f40587a2)), closes [#1032](https://github.com/dougborg/katana-openapi-client/issues/1032)
* **client:** add unified traceability input + reconcile spec with upstream ([410beb6](https://github.com/dougborg/katana-openapi-client/commit/410beb6ce8d38fdeb28cd354e3c4779b181b34a4))
* **client:** expose 9 missing query-parameter filters ([a6aaf76](https://github.com/dougborg/katana-openapi-client/commit/a6aaf761a4e464487ca75496ce322ef21c1615fa))
* **client:** fix broken search request shape and add 4 search endpoints ([#1041](https://github.com/dougborg/katana-openapi-client/issues/1041)) ([8964472](https://github.com/dougborg/katana-openapi-client/commit/8964472e90bfa9d6c64384b6160c90cf382dafc2))
* **client:** model traceability on manufacturing-order request DTOs ([#1052](https://github.com/dougborg/katana-openapi-client/issues/1052)) ([8dd7a16](https://github.com/dougborg/katana-openapi-client/commit/8dd7a161170a7b5581bc5b73a5b624b47df50b74))
* **client:** reconcile bin transfers + PO row location_id from 2026-06-09 spec ([72a7693](https://github.com/dougborg/katana-openapi-client/commit/72a76932af6d49356446476d4b6b4ccb6c08cdfa))
* **client:** support endpoint-specific custom field inputs ([#1062](https://github.com/dougborg/katana-openapi-client/issues/1062)) ([150766b](https://github.com/dougborg/katana-openapi-client/commit/150766b477114373973c09efd394f522c591413e))
* **client:** sync spec with 2026-09-18 upstream refresh ([#1034](https://github.com/dougborg/katana-openapi-client/issues/1034)) ([b810da4](https://github.com/dougborg/katana-openapi-client/commit/b810da4856a668b40484dea2f4c2528122956dbd))
* **client:** sync upstream sales-order and custom-field contracts ([6e75661](https://github.com/dougborg/katana-openapi-client/commit/6e75661db62973015ef3967d3a07147ced716296))
* **mcp:** surface per-row location_id in PO row + receive tools ([7b0d044](https://github.com/dougborg/katana-openapi-client/commit/7b0d044b116460e2a745af88b2fb3df851d6cd7b)), closes [#945](https://github.com/dougborg/katana-openapi-client/issues/945)
* **ts-client:** port Ajv-style 422 errors + proactive rate limiting ([91cccdd](https://github.com/dougborg/katana-openapi-client/commit/91cccdde082cf0c1e03c5dacd74fe474bdc9f5a8))


### Bug Fixes

* align material variant creation contract ([#1095](https://github.com/dougborg/katana-openapi-client/issues/1095)) ([382a9e9](https://github.com/dougborg/katana-openapi-client/commit/382a9e9232775040a2c58419007a420620dcfce3))
* align serial attachment semantics ([#1097](https://github.com/dougborg/katana-openapi-client/issues/1097)) ([6d658b5](https://github.com/dougborg/katana-openapi-client/commit/6d658b5700c7ef2799f1fee5a70a5ecbd901161f))
* **client:** align manufacturing request contracts with live API ([#1060](https://github.com/dougborg/katana-openapi-client/issues/1060)) ([d7a830f](https://github.com/dougborg/katana-openapi-client/commit/d7a830fd7c12d2c5e27116c1bc6bfae0afe36cc3))
* **client:** align material config create contract ([#1068](https://github.com/dougborg/katana-openapi-client/issues/1068)) ([973e85f](https://github.com/dougborg/katana-openapi-client/commit/973e85f29858420b1578395ddc13381c200f553f))
* **client:** align reorder-point + sales-return-row quantity with wire types ([f3f7706](https://github.com/dougborg/katana-openapi-client/commit/f3f7706c65a7197233311737b1c7e624e8853725)), closes [#865](https://github.com/dougborg/katana-openapi-client/issues/865)
* **client:** align sales-return filters with verified wire behavior ([#1070](https://github.com/dougborg/katana-openapi-client/issues/1070)) ([836ef4d](https://github.com/dougborg/katana-openapi-client/commit/836ef4d6a2cc21206d1ddae23e0163fff11d00b4))
* **client:** allow omitted sales row batch quantity ([#1058](https://github.com/dougborg/katana-openapi-client/issues/1058)) ([0325e16](https://github.com/dougborg/katana-openapi-client/commit/0325e16f8b05deb71bde77ee0158f7f2f681e89d))
* **client:** complete per-row location_id across purchase order row schemas ([64a6290](https://github.com/dougborg/katana-openapi-client/commit/64a6290f96580b81cab38605e88821f301173c06)), closes [#944](https://github.com/dougborg/katana-openapi-client/issues/944)
* **client:** constrain create price-list adjustment_method to its enum ([d5b852e](https://github.com/dougborg/katana-openapi-client/commit/d5b852e9ff647c71a237070259780408384e8a56)), closes [#735](https://github.com/dougborg/katana-openapi-client/issues/735)
* **client:** correct misleading ecommerce_* field docs + examples ([ff9b769](https://github.com/dougborg/katana-openapi-client/commit/ff9b769115991c45e9c8071be2af1b96dcea18b5)), closes [#913](https://github.com/dougborg/katana-openapi-client/issues/913)
* **client:** correct three drifted query-parameter enums ([9f1e2b2](https://github.com/dougborg/katana-openapi-client/commit/9f1e2b2df04daab442962705e462db3ffa6e5866)), closes [#572](https://github.com/dougborg/katana-openapi-client/issues/572)
* **client:** InventorySafetyStockLevel.value is a decimal string ([1c93010](https://github.com/dougborg/katana-openapi-client/commit/1c9301064dfb411623e749751b02d79f973b044e))
* **client:** item purchase_uom_conversion_rate is a decimal string ([abdaedb](https://github.com/dougborg/katana-openapi-client/commit/abdaedb7110331976f3df349f18acb81b77defea)), closes [#735](https://github.com/dougborg/katana-openapi-client/issues/735)
* **client:** MOOperationRow cost_per_hour/cost_parameter are decimal strings ([6636567](https://github.com/dougborg/katana-openapi-client/commit/6636567446ca1d1df06eb6b66f65f70722517482)), closes [#735](https://github.com/dougborg/katana-openapi-client/issues/735)
* **client:** PurchaseOrderRow.landed_cost is a number, not a string|number union ([31a1b11](https://github.com/dougborg/katana-openapi-client/commit/31a1b11987fb0fb800747c89b911b0676efded1c))
* **client:** regenerate TS client for the spec changes + gate it; use StorageBinResponse for bin_locations items ([495ef8f](https://github.com/dougborg/katana-openapi-client/commit/495ef8f79438979cb9ff320cd8f347c91aef5250))
* **client:** split safety-stock create request so its value stays number ([dedcedc](https://github.com/dougborg/katana-openapi-client/commit/dedcedc3dc42ed738ae03903ded0df733917a366)), closes [#865](https://github.com/dougborg/katana-openapi-client/issues/865)
* **client:** type status filters to match upstream enums ([bcbe822](https://github.com/dougborg/katana-openapi-client/commit/bcbe822ad5b959a62bbd92a470d0b9fe5d51ae36))
* **client:** use batch-id-only allocations for production requests ([#1054](https://github.com/dougborg/katana-openapi-client/issues/1054)) ([153aa7f](https://github.com/dougborg/katana-openapi-client/commit/153aa7f4ff16050dd15265453337c846b90a5b93)), closes [#1042](https://github.com/dougborg/katana-openapi-client/issues/1042)
* correct material variant creation and price updates ([#1089](https://github.com/dougborg/katana-openapi-client/issues/1089)) ([f419e1c](https://github.com/dougborg/katana-openapi-client/commit/f419e1ca7c5b4e7dd8221e0a841cf01179770e0a))
