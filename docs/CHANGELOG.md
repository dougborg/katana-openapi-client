# CHANGELOG

<!-- version list -->

## v0.54.1 (2026-04-28)

### Bug Fixes

- **client**: Normalize empty dict to None in from_attrs for absent nullable nested
  objects ([#403](https://github.com/dougborg/katana-openapi-client/pull/403),
  [`c5c7d3a`](https://github.com/dougborg/katana-openapi-client/commit/c5c7d3ad6996b83ac10c37843535539775035586))

- **mcp**: Check_inventory preserves input order, skus_or_variant_ids is required
  ([#397](https://github.com/dougborg/katana-openapi-client/pull/397),
  [`f32066f`](https://github.com/dougborg/katana-openapi-client/commit/f32066f65da8d6bf949a2788a087d9f8c55b68fd))

- **mcp**: Correct list_stock_transfers filters, get_variant_details single-card check,
  help cross-refs ([#397](https://github.com/dougborg/katana-openapi-client/pull/397),
  [`f32066f`](https://github.com/dougborg/katana-openapi-client/commit/f32066f65da8d6bf949a2788a087d9f8c55b68fd))

### Chores

- **actions)(deps**: Bump aquasecurity/trivy-action
  ([#381](https://github.com/dougborg/katana-openapi-client/pull/381),
  [`147700d`](https://github.com/dougborg/katana-openapi-client/commit/147700df8194ac0f1d66ca13b7e6a752e61ba77e))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 6 updates
  ([#384](https://github.com/dougborg/katana-openapi-client/pull/384),
  [`b8b7bfc`](https://github.com/dougborg/katana-openapi-client/commit/b8b7bfc7311bd3d23a05924cb13807d6ca644578))

- **mcp**: Audit tool descriptions to surface batchable shapes and standardize style
  ([#397](https://github.com/dougborg/katana-openapi-client/pull/397),
  [`f32066f`](https://github.com/dougborg/katana-openapi-client/commit/f32066f65da8d6bf949a2788a087d9f8c55b68fd))

- **mcp**: Update client dependency to v0.54.0
  ([`7503c1a`](https://github.com/dougborg/katana-openapi-client/commit/7503c1a4b34ae51ed4f891c81513d4cd36c36b7f))

### Documentation

- **harness**: Harvest project-wide rules from local memory
  ([#402](https://github.com/dougborg/katana-openapi-client/pull/402),
  [`79e5f4f`](https://github.com/dougborg/katana-openapi-client/commit/79e5f4fc7d7bd8662b94c9f8861dbf865b25e05d))

### Testing

- **mcp**: Add check_inventory tests for variant_id and mixed-input paths
  ([#397](https://github.com/dougborg/katana-openapi-client/pull/397),
  [`f32066f`](https://github.com/dougborg/katana-openapi-client/commit/f32066f65da8d6bf949a2788a087d9f8c55b68fd))

## v0.54.0 (2026-04-27)

### Bug Fixes

- **client**: Add NOT_APPLICABLE to OutsourcedPurchaseOrderIngredientAvailability
  ([#394](https://github.com/dougborg/katana-openapi-client/pull/394),
  [`70140c5`](https://github.com/dougborg/katana-openapi-client/commit/70140c51ea92e1eb408cfb41bfd733efd515f22a))

### Chores

- Sync uv.lock with workspace version bump
  ([#383](https://github.com/dougborg/katana-openapi-client/pull/383),
  [`3ac564f`](https://github.com/dougborg/katana-openapi-client/commit/3ac564f1504c25ac151c447485aa8ebf5172d94e))

- **client**: Simplify PR #363 generator transforms + tests
  ([#364](https://github.com/dougborg/katana-openapi-client/pull/364),
  [`5a54305`](https://github.com/dougborg/katana-openapi-client/commit/5a54305061601adf934021c545c6e72147b1643f))

- **harness**: Add lock file, restructure open-pr/review-pr, refresh CLAUDE.md
  ([#383](https://github.com/dougborg/katana-openapi-client/pull/383),
  [`3ac564f`](https://github.com/dougborg/katana-openapi-client/commit/3ac564f1504c25ac151c447485aa8ebf5172d94e))

- **harness**: Adopt code-reviewer/verifier agents; add domain-advisor
  ([#383](https://github.com/dougborg/katana-openapi-client/pull/383),
  [`3ac564f`](https://github.com/dougborg/katana-openapi-client/commit/3ac564f1504c25ac151c447485aa8ebf5172d94e))

- **harness**: Migrate legacy commands to skills
  ([#383](https://github.com/dougborg/katana-openapi-client/pull/383),
  [`3ac564f`](https://github.com/dougborg/katana-openapi-client/commit/3ac564f1504c25ac151c447485aa8ebf5172d94e))

- **harness**: Rebuild .claude/ harness from /harness audit findings
  ([#383](https://github.com/dougborg/katana-openapi-client/pull/383),
  [`3ac564f`](https://github.com/dougborg/katana-openapi-client/commit/3ac564f1504c25ac151c447485aa8ebf5172d94e))

- **mcp**: Post-#342 cleanup — sync debounce, query-shape branching, helper extractions
  ([#391](https://github.com/dougborg/katana-openapi-client/pull/391),
  [`e95a128`](https://github.com/dougborg/katana-openapi-client/commit/e95a128d5bd588d4e27adf2db05ff6634b9ed9fd))

- **mcp**: Simplify PR #365 typed-cache sync + engine
  ([#367](https://github.com/dougborg/katana-openapi-client/pull/367),
  [`9fa5f5e`](https://github.com/dougborg/katana-openapi-client/commit/9fa5f5eb3584a7794f0a6e77ffafdf97b1c59749))

- **mcp**: Simplify PR #373 list_sales_orders cache-back
  ([#375](https://github.com/dougborg/katana-openapi-client/pull/375),
  [`dcd1648`](https://github.com/dougborg/katana-openapi-client/commit/dcd1648a763e8295d1ca3f7a769b8983e9df6330))

- **mcp**: Update client dependency to v0.53.0
  ([`438f18b`](https://github.com/dougborg/katana-openapi-client/commit/438f18ba48d35e2b3a96b4bd30e412b38d9bc5c2))

- **release**: Mcp v0.41.0
  ([`3238a2d`](https://github.com/dougborg/katana-openapi-client/commit/3238a2d8956c1c8c0c4db26fc2fa0a890ed21ca7))

- **release**: Mcp v0.42.0
  ([`e209830`](https://github.com/dougborg/katana-openapi-client/commit/e2098300683a91b9a100546578b177d57e55f3c2))

### Features

- **client+mcp**: Cache-back list_manufacturing_orders (#377)
  ([#386](https://github.com/dougborg/katana-openapi-client/pull/386),
  [`3b85b05`](https://github.com/dougborg/katana-openapi-client/commit/3b85b057a3c2a28953190a315d00663db647a13f))

- **client+mcp**: Cache-back list_purchase_orders (#378)
  ([#387](https://github.com/dougborg/katana-openapi-client/pull/387),
  [`037ff60`](https://github.com/dougborg/katana-openapi-client/commit/037ff60cf28eaf812cd4cad18a3a0f67ab8b513f))

- **client+mcp**: Cache-back list_stock_transfers (#379)
  ([#388](https://github.com/dougborg/katana-openapi-client/pull/388),
  [`581e876`](https://github.com/dougborg/katana-openapi-client/commit/581e8769155f404d7bcb72d8c9bdb351eedc7521))

- **client+mcp**: Emit Cached<Name> sibling classes; cache-back list_stock_adjustments
  (#376) ([#385](https://github.com/dougborg/katana-openapi-client/pull/385),
  [`409c45a`](https://github.com/dougborg/katana-openapi-client/commit/409c45a848715867f0d003382843b6fd6d16a67a))

- **mcp**: Migrate list_sales_orders to cache-backed query (#368)
  ([#373](https://github.com/dougborg/katana-openapi-client/pull/373),
  [`31e4199`](https://github.com/dougborg/katana-openapi-client/commit/31e4199aeed976eed32d2ce3a99ea141c6abf337))

- **mcp**: SQLModel-backed typed cache runtime foundation (#342)
  ([#365](https://github.com/dougborg/katana-openapi-client/pull/365),
  [`ddaf4aa`](https://github.com/dougborg/katana-openapi-client/commit/ddaf4aa6127e7c0b52da63497de9b0ba48aa5c40))

### Refactoring

- **mcp**: Consolidate list-tool helpers + enable complexity linting (#347)
  ([#369](https://github.com/dougborg/katana-openapi-client/pull/369),
  [`f13574e`](https://github.com/dougborg/katana-openapi-client/commit/f13574e252339ed4a9790ba96afde74049d5a674))

- **mcp**: Promote typed-cache test helpers
  ([#380](https://github.com/dougborg/katana-openapi-client/pull/380),
  [`71acdaa`](https://github.com/dougborg/katana-openapi-client/commit/71acdaac56119e83ee1dc5ee67ee1c430010045d))

- **mcp**: Promote typed-cache test helpers (#374)
  ([#380](https://github.com/dougborg/katana-openapi-client/pull/380),
  [`71acdaa`](https://github.com/dougborg/katana-openapi-client/commit/71acdaac56119e83ee1dc5ee67ee1c430010045d))

## v0.53.0 (2026-04-23)

### Chores

- **client**: Simplify PR #361 docstrings
  ([#362](https://github.com/dougborg/katana-openapi-client/pull/362),
  [`478ac01`](https://github.com/dougborg/katana-openapi-client/commit/478ac01b8098961e4c0d361a4baf768eb45cdf9b))

- **mcp**: Update client dependency to v0.52.0
  ([`db197b6`](https://github.com/dougborg/katana-openapi-client/commit/db197b621296b9486baa9db240e465bad8beb9ed))

### Features

- **client**: Generator emits SQLModel tables for cache-target entities (#342)
  ([#363](https://github.com/dougborg/katana-openapi-client/pull/363),
  [`2eb65c9`](https://github.com/dougborg/katana-openapi-client/commit/2eb65c9c8025d84a68a99df06c90bc0e91ba14cb))

## v0.52.0 (2026-04-23)

### Bug Fixes

- **ci**: Isolate parallel agent worktrees from pre-commit hooks
  ([#359](https://github.com/dougborg/katana-openapi-client/pull/359),
  [`0953a9b`](https://github.com/dougborg/katana-openapi-client/commit/0953a9baa5875063b7389dc7c22daacb9e21bfdc))

- **ci**: Sync uv.lock after semantic-release version bumps
  ([`911f334`](https://github.com/dougborg/katana-openapi-client/commit/911f33443bbe39b2a2e7b7d876538c841fc0146a))

- **mcp**: Add --no-sources to Docker build for PyPI resolution
  ([`0607437`](https://github.com/dougborg/katana-openapi-client/commit/0607437051199ff0ee8e66c350615ed277ea656b))

- **mcp**: Add tmpfs for cache in read-only Docker container
  ([`b4e6d83`](https://github.com/dougborg/katana-openapi-client/commit/b4e6d839382bc686bd8489562f3f12448e85f8f5))

- **mcp**: Address copilot feedback on get_purchase_order
  ([#357](https://github.com/dougborg/katana-openapi-client/pull/357),
  [`19a3795`](https://github.com/dougborg/katana-openapi-client/commit/19a379594b4b7fddf45be70ec146b2c7533df31b))

- **mcp**: Address Copilot review on reporting tools
  ([#340](https://github.com/dougborg/katana-openapi-client/pull/340),
  [`da22279`](https://github.com/dougborg/katana-openapi-client/commit/da22279e179db6e6640c459d0f5562b993037d6e))

- **mcp**: Address simplify review findings for auth
  ([`fa570e6`](https://github.com/dougborg/katana-openapi-client/commit/fa570e6e06df2957456c54198be529cdbcff75b1))

- **mcp**: Avoid SQL-keyword f-strings in elicitation prompts
  ([#341](https://github.com/dougborg/katana-openapi-client/pull/341),
  [`014942f`](https://github.com/dougborg/katana-openapi-client/commit/014942ff657eb860203342ae538e772ba83c821d))

- **mcp**: Chain Docker build after both packages publish
  ([`aa5657c`](https://github.com/dougborg/katana-openapi-client/commit/aa5657c9715714396a23da48238446b3eaf90692))

- **mcp**: Expose pagination cursor on list_sales_orders
  ([#336](https://github.com/dougborg/katana-openapi-client/pull/336),
  [`5900ee6`](https://github.com/dougborg/katana-openapi-client/commit/5900ee6d7d0835605394737e892a00b521ccff42))

- **mcp**: Guard page=1 short-circuit against non-positive limit
  ([#335](https://github.com/dougborg/katana-openapi-client/pull/335),
  [`21c323a`](https://github.com/dougborg/katana-openapi-client/commit/21c323a080ff49749208d17f347435a01b90a635))

- **mcp**: Prefab UI was built but never rendered in Claude Desktop
  ([#351](https://github.com/dougborg/katana-openapi-client/pull/351),
  [`5b373fc`](https://github.com/dougborg/katana-openapi-client/commit/5b373fca09ef02270259440838bb36eda8e546c8))

- **mcp**: Respect limit param in list_sales_orders
  ([#335](https://github.com/dougborg/katana-openapi-client/pull/335),
  [`21c323a`](https://github.com/dougborg/katana-openapi-client/commit/21c323a080ff49749208d17f347435a01b90a635))

- **mcp**: Surface missed server-side filters on list_stock_adjustments
  ([#341](https://github.com/dougborg/katana-openapi-client/pull/341),
  [`014942f`](https://github.com/dougborg/katana-openapi-client/commit/014942ff657eb860203342ae538e772ba83c821d))

- **mcp**: Three follow-ups from /review-pr pass on #356
  ([#360](https://github.com/dougborg/katana-openapi-client/pull/360),
  [`3b4e1ef`](https://github.com/dougborg/katana-openapi-client/commit/3b4e1ef58fc44caed4a61ab5bd3987cdc6fba711))

- **mcp**: Tighten list_stock_adjustments after Copilot review
  ([#341](https://github.com/dougborg/katana-openapi-client/pull/341),
  [`014942f`](https://github.com/dougborg/katana-openapi-client/commit/014942ff657eb860203342ae538e772ba83c821d))

- **mcp**: Tighten stock_transfers after Copilot review
  ([#339](https://github.com/dougborg/katana-openapi-client/pull/339),
  [`c3295a9`](https://github.com/dougborg/katana-openapi-client/commit/c3295a95926b722dfdde4f627385e91971bd91c3))

- **mcp**: Use int for tracking_location_id/supplier_id in list_purchase_orders
  ([#343](https://github.com/dougborg/katana-openapi-client/pull/343),
  [`42cafe2`](https://github.com/dougborg/katana-openapi-client/commit/42cafe20cfeca8bb2b549a6aec238b9a3a7d52da))

### Chores

- Sync uv.lock with mcp v0.39.0
  ([`84941d9`](https://github.com/dougborg/katana-openapi-client/commit/84941d96ead13655d75d86696d1093425cc0c636))

- **actions)(deps**: Bump actions/upload-pages-artifact
  ([#327](https://github.com/dougborg/katana-openapi-client/pull/327),
  [`82a6258`](https://github.com/dougborg/katana-openapi-client/commit/82a62588e49df5060dceb7ed896860e2e8e68b5f))

- **deps)(deps**: Bump the python-minor-patch group with 6 updates
  ([#328](https://github.com/dougborg/katana-openapi-client/pull/328),
  [`abf3c8d`](https://github.com/dougborg/katana-openapi-client/commit/abf3c8d02d58b0823bb9ccb8187a11499df24a58))

- **mcp**: Post-wave cleanup — correctness drift in list tools
  ([#348](https://github.com/dougborg/katana-openapi-client/pull/348),
  [`2d1fb86`](https://github.com/dougborg/katana-openapi-client/commit/2d1fb863b0cde6eec5b4cde5067f729b99c877d7))

- **mcp**: Post-wave cleanup — fix correctness drift in list tools
  ([#348](https://github.com/dougborg/katana-openapi-client/pull/348),
  [`2d1fb86`](https://github.com/dougborg/katana-openapi-client/commit/2d1fb863b0cde6eec5b4cde5067f729b99c877d7))

- **mcp**: Simplify follow-ups to Prefab UI delivery fix
  ([#351](https://github.com/dougborg/katana-openapi-client/pull/351),
  [`5b373fc`](https://github.com/dougborg/katana-openapi-client/commit/5b373fca09ef02270259440838bb36eda8e546c8))

- **release**: Mcp v0.36.0
  ([`8152185`](https://github.com/dougborg/katana-openapi-client/commit/8152185367b0be6ac2594c3ea49e6dd6621bf663))

- **release**: Mcp v0.37.0
  ([`fe65eca`](https://github.com/dougborg/katana-openapi-client/commit/fe65eca8169ba585baf3949e07b6aa70a7f2e729))

- **release**: Mcp v0.37.1
  ([`6652f0a`](https://github.com/dougborg/katana-openapi-client/commit/6652f0a056b62f338ccdc9b2b2fbec9c1b1122f9))

- **release**: Mcp v0.38.0
  ([`49b712e`](https://github.com/dougborg/katana-openapi-client/commit/49b712efdd29f93efa7f97b1df4c40af776d7dfc))

- **release**: Mcp v0.39.0
  ([`60a2ada`](https://github.com/dougborg/katana-openapi-client/commit/60a2ada75bcb0f2de10159783e9b2b82e50beda7))

- **release**: Mcp v0.39.1
  ([`2af011c`](https://github.com/dougborg/katana-openapi-client/commit/2af011cba74b75b022053543f743b73e620beb92))

- **release**: Mcp v0.40.0
  ([`d41522e`](https://github.com/dougborg/katana-openapi-client/commit/d41522e9aabde2144de12db0cc11a178e83975f8))

### Documentation

- **mcp**: Document format parameter in help resource
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Fix help text for get_variant_details and check_inventory
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Include `id` in list_sales_orders include_rows field list
  ([#344](https://github.com/dougborg/katana-openapi-client/pull/344),
  [`80c5107`](https://github.com/dougborg/katana-openapi-client/commit/80c51071923dc6c7ee912bfeb6e6ded2273497a3))

### Features

- **client**: Base generated pydantic models on SQLModel (#342 foundation)
  ([#361](https://github.com/dougborg/katana-openapi-client/pull/361),
  [`50c951c`](https://github.com/dougborg/katana-openapi-client/commit/50c951cea8a95458a98848a0b070a2ca3c93de14))

- **mcp**: Add aggregation/reporting tools
  ([#340](https://github.com/dougborg/katana-openapi-client/pull/340),
  [`da22279`](https://github.com/dougborg/katana-openapi-client/commit/da22279e179db6e6640c459d0f5562b993037d6e))

- **mcp**: Add endpoint authentication for HTTP transport
  ([`405d5c6`](https://github.com/dougborg/katana-openapi-client/commit/405d5c6fe01058b4093ceec693d7d0957d699ad1))

- **mcp**: Add format=json | markdown to list/get tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to customers tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to items + inventory tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to manufacturing_orders tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to purchase_orders tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to reporting tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to sales_orders tools
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add format=json|markdown to stock_transfers read tool
  ([#345](https://github.com/dougborg/katana-openapi-client/pull/345),
  [`a789450`](https://github.com/dougborg/katana-openapi-client/commit/a7894503de09abb4766fa59c9812a3d612a4f23b))

- **mcp**: Add hot-reload dev tasks and fix Docker health check
  ([`5a996ea`](https://github.com/dougborg/katana-openapi-client/commit/5a996ea0536f4546ff2bc76011867ef6c690800a))

- **mcp**: Add include_rows to list_sales_orders
  ([#344](https://github.com/dougborg/katana-openapi-client/pull/344),
  [`80c5107`](https://github.com/dougborg/katana-openapi-client/commit/80c51071923dc6c7ee912bfeb6e6ded2273497a3))

- **mcp**: Add include_rows to list_sales_orders (#332)
  ([#344](https://github.com/dougborg/katana-openapi-client/pull/344),
  [`80c5107`](https://github.com/dougborg/katana-openapi-client/commit/80c51071923dc6c7ee912bfeb6e6ded2273497a3))

- **mcp**: Add stock-transfer tools
  ([#339](https://github.com/dougborg/katana-openapi-client/pull/339),
  [`c3295a9`](https://github.com/dougborg/katana-openapi-client/commit/c3295a95926b722dfdde4f627385e91971bd91c3))

- **mcp**: Add stock-transfer tools (#338)
  ([#339](https://github.com/dougborg/katana-openapi-client/pull/339),
  [`c3295a9`](https://github.com/dougborg/katana-openapi-client/commit/c3295a95926b722dfdde4f627385e91971bd91c3))

- **mcp**: Complete stock-adjustment CRUD
  ([#341](https://github.com/dougborg/katana-openapi-client/pull/341),
  [`014942f`](https://github.com/dougborg/katana-openapi-client/commit/014942ff657eb860203342ae538e772ba83c821d))

- **mcp**: Date-range filters + list_manufacturing_orders + list_purchase_orders
  ([#343](https://github.com/dougborg/katana-openapi-client/pull/343),
  [`42cafe2`](https://github.com/dougborg/katana-openapi-client/commit/42cafe20cfeca8bb2b549a6aec238b9a3a7d52da))

- **mcp**: Date-range filters on list_sales_orders; add list_manufacturing_orders +
  list_purchase_orders
  ([#343](https://github.com/dougborg/katana-openapi-client/pull/343),
  [`42cafe2`](https://github.com/dougborg/katana-openapi-client/commit/42cafe20cfeca8bb2b549a6aec238b9a3a7d52da))

- **mcp**: Exhaustive get_customer + canonical-name markdown labels (#346)
  ([#352](https://github.com/dougborg/katana-openapi-client/pull/352),
  [`508ec16`](https://github.com/dougborg/katana-openapi-client/commit/508ec16884aea80982d3a287fea48d41b71ed276))

- **mcp**: Exhaustive get_inventory_movements + canonical-name labels (#346)
  ([#353](https://github.com/dougborg/katana-openapi-client/pull/353),
  [`1e7a711`](https://github.com/dougborg/katana-openapi-client/commit/1e7a71152d90419bd92742fc5d251928ab163df3))

- **mcp**: Exhaustive get_manufacturing_order + recipe + canonical-name labels (#346)
  ([#355](https://github.com/dougborg/katana-openapi-client/pull/355),
  [`7a86aa9`](https://github.com/dougborg/katana-openapi-client/commit/7a86aa915ff54a69c8e491aaf1ca4acea8a417e7))

- **mcp**: Exhaustive get_purchase_order + canonical-name labels
  ([#357](https://github.com/dougborg/katana-openapi-client/pull/357),
  [`19a3795`](https://github.com/dougborg/katana-openapi-client/commit/19a379594b4b7fddf45be70ec146b2c7533df31b))

- **mcp**: Exhaustive get_purchase_order + canonical-name labels (#346)
  ([#357](https://github.com/dougborg/katana-openapi-client/pull/357),
  [`19a3795`](https://github.com/dougborg/katana-openapi-client/commit/19a379594b4b7fddf45be70ec146b2c7533df31b))

- **mcp**: Exhaustive get_sales_order + canonical-name markdown labels (#346)
  ([#354](https://github.com/dougborg/katana-openapi-client/pull/354),
  [`03c7967`](https://github.com/dougborg/katana-openapi-client/commit/03c796733e6a5b3181ee29c8ffeb5f1d114d0751))

- **mcp**: Exhaustive get_variant_details + get_item (#346)
  ([#356](https://github.com/dougborg/katana-openapi-client/pull/356),
  [`af394ac`](https://github.com/dougborg/katana-openapi-client/commit/af394ac8291e0e11e0288ac94d95d685ab6dda80))

- **mcp**: HTTP transport support for Docker and Claude.ai co-work
  ([#326](https://github.com/dougborg/katana-openapi-client/pull/326),
  [`39e7c4e`](https://github.com/dougborg/katana-openapi-client/commit/39e7c4e47c67772b10edb60c6d9ea8128444fa7a))

- **mcp**: Improve docker compose with health check and .env.example
  ([#326](https://github.com/dougborg/katana-openapi-client/pull/326),
  [`39e7c4e`](https://github.com/dougborg/katana-openapi-client/commit/39e7c4e47c67772b10edb60c6d9ea8128444fa7a))

- **mcp**: Support HTTP transport in Docker and add co-work docs
  ([#326](https://github.com/dougborg/katana-openapi-client/pull/326),
  [`39e7c4e`](https://github.com/dougborg/katana-openapi-client/commit/39e7c4e47c67772b10edb60c6d9ea8128444fa7a))

- **mcp**: Update client dependency to v0.51.0
  ([`2d433c3`](https://github.com/dougborg/katana-openapi-client/commit/2d433c3bf86ce8725edbcdbf1d6105daf7bb70f6))

### Performance Improvements

- **mcp**: Read category_name from cache instead of live API
  ([#348](https://github.com/dougborg/katana-openapi-client/pull/348),
  [`2d1fb86`](https://github.com/dougborg/katana-openapi-client/commit/2d1fb863b0cde6eec5b4cde5067f729b99c877d7))

- **mcp**: Route category lookup via variant.type — no more probing
  ([#348](https://github.com/dougborg/katana-openapi-client/pull/348),
  [`2d1fb86`](https://github.com/dougborg/katana-openapi-client/commit/2d1fb863b0cde6eec5b4cde5067f729b99c877d7))

## v0.51.0 (2026-04-13)

### Bug Fixes

- Sweep remaining semgrep findings across the repo
  ([`e6c7ec3`](https://github.com/dougborg/katana-openapi-client/commit/e6c7ec39bcb9cdc1e95c2f126ca2dd48716d3996))

- **mcp**: Address Copilot review feedback — remove unused imports and fix version
  ([`a803b3d`](https://github.com/dougborg/katana-openapi-client/commit/a803b3d0b1eb723520c6f402f5ebdf5ba3204189))

- **mcp**: Address second-round review feedback
  ([`349941a`](https://github.com/dougborg/katana-openapi-client/commit/349941a272f62065d7d858aa8f13c00671faa405))

- **mcp**: Address third-round review comments
  ([`5d0ee53`](https://github.com/dougborg/katana-openapi-client/commit/5d0ee532378ba9e519c17bf16fd5d29cf7f310f3))

- **mcp**: Default_factory retry + variant_id on StockInfo
  ([`10d329f`](https://github.com/dougborg/katana-openapi-client/commit/10d329f404e5b26e413936928496ae01275841d4))

- **mcp**: Dodge semgrep Django-SQL false positives
  ([`d6f3b4a`](https://github.com/dougborg/katana-openapi-client/commit/d6f3b4aa116825cb7239cb7308a260368caf5dde))

- **mcp**: Guard variant=None and add API fallback in batch check_inventory
  ([`ff83752`](https://github.com/dougborg/katana-openapi-client/commit/ff83752f5524c6042528575c629b691301582cba))

- **mcp**: Handle 404 cleanly in PO/variant lookups
  ([`7706141`](https://github.com/dougborg/katana-openapi-client/commit/770614157d54e612953ecbc15837f1517134fa21))

- **mcp**: Handle None correctly in inventory_items is\_\* flag coercion
  ([`582fba0`](https://github.com/dougborg/katana-openapi-client/commit/582fba0d3de9ca0463f5f4e6140e516dffdf5afb))

- **mcp**: Import ToolResult from fastmcp.tools package directly
  ([`b82d598`](https://github.com/dougborg/katana-openapi-client/commit/b82d598aa59851495b5373dda58f2ec1d064903d))

- **mcp**: Resolve pyright type errors across server and tools
  ([`aea6889`](https://github.com/dougborg/katana-openapi-client/commit/aea68896b2ba324073b690b559aa6bcadfa39bd9))

- **mcp**: Tighten batch recipe ops, MTO response, and docs
  ([`e175d0b`](https://github.com/dougborg/katana-openapi-client/commit/e175d0bde677db0293a218d99462dc9caefae684))

- **mcp**: Use 'is not None' check when rendering sales order totals
  ([`192c555`](https://github.com/dougborg/katana-openapi-client/commit/192c555f124b87ddab901cc76438e00d3d499d67))

- **scripts**: Update test_mcp_resources to use Services container and handle JSON
  results
  ([`111287b`](https://github.com/dougborg/katana-openapi-client/commit/111287bb9204426109e97b2f228d86aa326c8429))

### Chores

- Add include paths to pyrightconfig
  ([`de6777f`](https://github.com/dougborg/katana-openapi-client/commit/de6777f5f1f417f9a065910282e584c696ebf9d0))

- Exclude .claude/worktrees from yamllint
  ([`27df541`](https://github.com/dougborg/katana-openapi-client/commit/27df5410d241dcc532d89fafe73ccea49d4eecb2))

- **deps**: Bump all dependencies (April 2026)
  ([`45a2e4a`](https://github.com/dougborg/katana-openapi-client/commit/45a2e4a9c88fb72cc72921d5a4236d59924cfb77))

- **release**: Mcp v0.34.0
  ([`31bbdb1`](https://github.com/dougborg/katana-openapi-client/commit/31bbdb1564f80feac2e259334e92269ddb06a6b7))

- **release**: Mcp v0.35.0
  ([`4a0e0c5`](https://github.com/dougborg/katana-openapi-client/commit/4a0e0c544429dbb4807a75373e19255cbf5be459))

### Documentation

- Document LSP usage in CLAUDE.md and relevant commands
  ([`a5a0a75`](https://github.com/dougborg/katana-openapi-client/commit/a5a0a7586e7ba01bfd5a344a5f1af0abbd4a458d))

- **mcp**: Update resource documentation for new structure
  ([`dd2edd4`](https://github.com/dougborg/katana-openapi-client/commit/dd2edd49673ea32c9c955ef1fa5f7b5fcd49479c))

### Features

- **client**: Narrow unwrap_unset return type when default is non-None
  ([`505ca1d`](https://github.com/dougborg/katana-openapi-client/commit/505ca1df8988bbb23bdd4482e6df5d227a215786))

- **mcp**: Accept batch SKUs/variant_ids in check_inventory
  ([`a3c0cac`](https://github.com/dougborg/katana-openapi-client/commit/a3c0cac0d6d7c92d4334aba180b6eb44ab2a3e86))

- **mcp**: Accept variant_id in lookup tools, add batch variant lookup
  ([`9cdbd6f`](https://github.com/dougborg/katana-openapi-client/commit/9cdbd6fe00c943a7930950cbd2b9fbd61bf928a7))

- **mcp**: Add batch_update_manufacturing_order_recipes with Prefab UI
  ([`cfcb800`](https://github.com/dougborg/katana-openapi-client/commit/cfcb8006815a10ed012952fb92e9ee247b9b2009))

- **mcp**: Add list_sales_orders and get_sales_order tools
  ([`abc9ffe`](https://github.com/dougborg/katana-openapi-client/commit/abc9ffe55cb182752fb536f1fd2dd8e86f604310))

- **mcp**: Add PO lookup and manufacturing order recipe editing tools
  ([`b36993f`](https://github.com/dougborg/katana-openapi-client/commit/b36993f84e83d861abcf093e87fa11af7b23d39a))

- **mcp**: Add search_customers and get_customer tools
  ([`f2ebfc6`](https://github.com/dougborg/katana-openapi-client/commit/f2ebfc686ffa4c7a84aeafb968674033a37492f5))

- **mcp**: Restructure resources — reference data only, remove transactional
  ([`0df24d7`](https://github.com/dougborg/katana-openapi-client/commit/0df24d7354be9cd4d8ee7231db420c149ee492aa))

- **mcp**: Support make-to-order MO creation linked to sales order rows
  ([`836a6f4`](https://github.com/dougborg/katana-openapi-client/commit/836a6f4158fb66efb3e13faee27c4ade8d242d8b))

### Refactoring

- **mcp**: Extract shared helpers, use EntityType, parallelize lookups
  ([`3247352`](https://github.com/dougborg/katana-openapi-client/commit/3247352f229d745babd49bf77388d9321d371576))

- **mcp**: Typed OpType enum and memoized recipe fetches in batch planner
  ([`f70dba7`](https://github.com/dougborg/katana-openapi-client/commit/f70dba7e5d6a3f7e5a4087972aca45baf41b817c))

- **mcp**: Use format_md_table helper for all markdown tables
  ([`6c6fff6`](https://github.com/dougborg/katana-openapi-client/commit/6c6fff6f709e21c8c0c9d589c12f39d1e01b3f44))

## v0.50.0 (2026-04-09)

### Bug Fixes

- Address Copilot review feedback on security PR
  ([#310](https://github.com/dougborg/katana-openapi-client/pull/310),
  [`57a55a3`](https://github.com/dougborg/katana-openapi-client/commit/57a55a3e621800a3456b531050826f1983541ea2))

- Remediate critical security findings from codebase audit
  ([#310](https://github.com/dougborg/katana-openapi-client/pull/310),
  [`57a55a3`](https://github.com/dougborg/katana-openapi-client/commit/57a55a3e621800a3456b531050826f1983541ea2))

- Restore ty exclusion for test_generate_tools_json.py, remove unused cast import
  ([#307](https://github.com/dougborg/katana-openapi-client/pull/307),
  [`d0003bc`](https://github.com/dougborg/katana-openapi-client/commit/d0003bcf796e20855c571ab3984d2e81cbc59364))

- **client**: Add DRAFT PO status, fix unwrap_unset and validation error details
  ([`1d8a4e9`](https://github.com/dougborg/katana-openapi-client/commit/1d8a4e9f0c7db8afe3d4f7d2205ccb3db90d9af9))

- **client**: Sanitize sensitive data in transport error logs
  ([#310](https://github.com/dougborg/katana-openapi-client/pull/310),
  [`57a55a3`](https://github.com/dougborg/katana-openapi-client/commit/57a55a3e621800a3456b531050826f1983541ea2))

- **mcp**: Address PR review feedback — UI actions, validation, tests
  ([`bc2e96a`](https://github.com/dougborg/katana-openapi-client/commit/bc2e96a6cfb5ac2c6562693d6f8cd083ea33c9bf))

- **mcp**: Fix cache sync datetime type and prefab UI positional args
  ([`83d07ed`](https://github.com/dougborg/katana-openapi-client/commit/83d07ed0f6fb82d60cc636e04d5fe219fd78ad7d))

- **mcp**: Remove stack trace from initialization error log
  ([#310](https://github.com/dougborg/katana-openapi-client/pull/310),
  [`57a55a3`](https://github.com/dougborg/katana-openapi-client/commit/57a55a3e621800a3456b531050826f1983541ea2))

- **mcp**: Rewrite check_inventory to use inventory API, add movements and stock
  adjustment tools
  ([`f9fe8e6`](https://github.com/dougborg/katana-openapi-client/commit/f9fe8e62a7553dd80735cbc7ad39e07a3d427833))

- **ts**: Patch npm dependency vulnerabilities via pnpm overrides
  ([#310](https://github.com/dougborg/katana-openapi-client/pull/310),
  [`57a55a3`](https://github.com/dougborg/katana-openapi-client/commit/57a55a3e621800a3456b531050826f1983541ea2))

### Chores

- Upgrade all dependencies including FastMCP 2.x → 3.x
  ([#307](https://github.com/dougborg/katana-openapi-client/pull/307),
  [`d0003bc`](https://github.com/dougborg/katana-openapi-client/commit/d0003bcf796e20855c571ab3984d2e81cbc59364))

- Upgrade all dependencies including FastMCP 3.x migration
  ([#307](https://github.com/dougborg/katana-openapi-client/pull/307),
  [`d0003bc`](https://github.com/dougborg/katana-openapi-client/commit/d0003bcf796e20855c571ab3984d2e81cbc59364))

- **deps)(deps**: Bump katana-mcp-server
  ([#308](https://github.com/dougborg/katana-openapi-client/pull/308),
  [`d524e5a`](https://github.com/dougborg/katana-openapi-client/commit/d524e5a233d972cd5fe59a224ed5a1a2f323d415))

- **release**: Mcp v0.32.0
  ([`009c696`](https://github.com/dougborg/katana-openapi-client/commit/009c696e2593753ccbbf0d4ecbc71b70e95c8310))

- **release**: Mcp v0.33.0
  ([`7713c3a`](https://github.com/dougborg/katana-openapi-client/commit/7713c3a4d818091614e700029f55503f5774b1e0))

### Features

- **client**: Improve search with tokenization, fuzzy matching, and scoring
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

- **mcp**: Add cache invalidation to item write operations
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

- **mcp**: Add get_manufacturing_order tool, update_item handles variant fields
  ([`34f3ff6`](https://github.com/dougborg/katana-openapi-client/commit/34f3ff620649bd93eb53a7cd7e4f4d85b0420dd7))

- **mcp**: Add persistent SQLite catalog cache with FTS5 search
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

- **mcp**: Add Prefab UI for interactive tool responses in Claude Desktop
  ([`bcc6ad9`](https://github.com/dougborg/katana-openapi-client/commit/bcc6ad9e559502c7b137ba9192ae9b06f5fae8f8))

- **mcp**: Persistent SQLite catalog cache with FTS5 search
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

- **mcp**: Wire SQLite cache into Services, search, and variant tools
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

### Refactoring

- **client**: Remove VariantCache from client library
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

- **mcp**: Address review — targeted invalidation, EntityType enum, batch sync
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

- **mcp**: Extract cache decorators, remove tool boilerplate
  ([#304](https://github.com/dougborg/katana-openapi-client/pull/304),
  [`a53bf31`](https://github.com/dougborg/katana-openapi-client/commit/a53bf31e7fad64a389e4faa8199d6b7f5fa905c9))

## v0.49.1 (2026-03-26)

### Bug Fixes

- **client**: Allow extra fields in API response models
  ([#296](https://github.com/dougborg/katana-openapi-client/pull/296),
  [`ef918e8`](https://github.com/dougborg/katana-openapi-client/commit/ef918e8933137ac1012f66addb7a6668b71fa2a9))

- **client**: Allow extra fields in API responses, add new endpoints (#295)
  ([#296](https://github.com/dougborg/katana-openapi-client/pull/296),
  [`ef918e8`](https://github.com/dougborg/katana-openapi-client/commit/ef918e8933137ac1012f66addb7a6668b71fa2a9))

- **client**: Harden generation script and add e2e extra-fields test
  ([#296](https://github.com/dougborg/katana-openapi-client/pull/296),
  [`ef918e8`](https://github.com/dougborg/katana-openapi-client/commit/ef918e8933137ac1012f66addb7a6668b71fa2a9))

- **client**: Improve extraction script output quality
  ([#296](https://github.com/dougborg/katana-openapi-client/pull/296),
  [`ef918e8`](https://github.com/dougborg/katana-openapi-client/commit/ef918e8933137ac1012f66addb7a6668b71fa2a9))

- **client**: Update vulnerable dependencies, exclude worktrees from ty
  ([#296](https://github.com/dougborg/katana-openapi-client/pull/296),
  [`ef918e8`](https://github.com/dougborg/katana-openapi-client/commit/ef918e8933137ac1012f66addb7a6668b71fa2a9))

## v0.49.0 (2026-03-26)

### Bug Fixes

- **mcp**: Add katana-mcp-server as dev dependency for CI test discovery
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Address review feedback — method names, subset checks, ValueError
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Fix stale model imports preventing server startup
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Fix stale model imports that prevented server startup
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Override __annotate__ instead of deleting it (Python 3.14)
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Patch __func__.__annotate__ for bound methods (Python 3.14)
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Python 3.14 compatibility and PO status validation
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **mcp**: Validate purchase order initial status before enum conversion
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

### Chores

- Default to Python 3.14 for local development
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

- **release**: Mcp v0.31.1
  ([`a62b929`](https://github.com/dougborg/katana-openapi-client/commit/a62b929ab2ea41abcc717825982e732bb0f61915))

### Features

- Add /review-pr and /open-pr skills from katana-tools
  ([#297](https://github.com/dougborg/katana-openapi-client/pull/297),
  [`45e5ed3`](https://github.com/dougborg/katana-openapi-client/commit/45e5ed3ba30a41725767c11d95564b60ae64f8f7))

- Add Claude Code agents and enhance commands with ChernyCode principles
  ([#297](https://github.com/dougborg/katana-openapi-client/pull/297),
  [`45e5ed3`](https://github.com/dougborg/katana-openapi-client/commit/45e5ed3ba30a41725767c11d95564b60ae64f8f7))

### Refactoring

- Simplify agent and command definitions
  ([#297](https://github.com/dougborg/katana-openapi-client/pull/297),
  [`45e5ed3`](https://github.com/dougborg/katana-openapi-client/commit/45e5ed3ba30a41725767c11d95564b60ae64f8f7))

- **mcp**: Extract \_pin_annotate helper and use Literal for PO status
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

### Testing

- **mcp**: Fix broken tests and include MCP tests in main suite
  ([#294](https://github.com/dougborg/katana-openapi-client/pull/294),
  [`ed7ee8c`](https://github.com/dougborg/katana-openapi-client/commit/ed7ee8c042cb2076a27a27c42920e7207cbf9f64))

## v0.48.0 (2026-03-25)

### Bug Fixes

- **client**: Correct docstring for \_extract_nested_error return type
  ([#293](https://github.com/dougborg/katana-openapi-client/pull/293),
  [`052e0d2`](https://github.com/dougborg/katana-openapi-client/commit/052e0d211046b4188b8e9acea5b6c240baf8665a))

- **client**: Remove unnecessary casts with proper type narrowing
  ([#293](https://github.com/dougborg/katana-openapi-client/pull/293),
  [`052e0d2`](https://github.com/dougborg/katana-openapi-client/commit/052e0d211046b4188b8e9acea5b6c240baf8665a))

- **client**: Use cast for nested dict access to satisfy ty type checker
  ([#289](https://github.com/dougborg/katana-openapi-client/pull/289),
  [`441632b`](https://github.com/dougborg/katana-openapi-client/commit/441632b94761e8e131080f5828c7a13a9c795688))

- **mcp**: Remove noqa suppression and fix to_unset(None) misuse
  ([#290](https://github.com/dougborg/katana-openapi-client/pull/290),
  [`2686aad`](https://github.com/dougborg/katana-openapi-client/commit/2686aadb6df495af372e06c0a75231a72f867f7f))

- **mcp**: Restore getattr for attrs Product model in inventory tools
  ([#290](https://github.com/dougborg/katana-openapi-client/pull/290),
  [`2686aad`](https://github.com/dougborg/katana-openapi-client/commit/2686aadb6df495af372e06c0a75231a72f867f7f))

### Chores

- **actions)(deps**: Bump dorny/paths-filter
  ([#288](https://github.com/dougborg/katana-openapi-client/pull/288),
  [`54798f2`](https://github.com/dougborg/katana-openapi-client/commit/54798f287ae52ed07bd5c359302fda189602d307))

- **actions)(deps**: Bump the github-actions group with 5 updates
  ([#284](https://github.com/dougborg/katana-openapi-client/pull/284),
  [`ff3ad0d`](https://github.com/dougborg/katana-openapi-client/commit/ff3ad0ddb27f4df3614f8d57550b52c21c2a017a))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 9 updates
  ([#289](https://github.com/dougborg/katana-openapi-client/pull/289),
  [`441632b`](https://github.com/dougborg/katana-openapi-client/commit/441632b94761e8e131080f5828c7a13a9c795688))

- **deps)(deps**: Bump types-python-dateutil
  ([#286](https://github.com/dougborg/katana-openapi-client/pull/286),
  [`6c140f1`](https://github.com/dougborg/katana-openapi-client/commit/6c140f1495d6b4ceee0578025dfa25b754f6c96d))

- **release**: Mcp v0.31.0
  ([`15ba095`](https://github.com/dougborg/katana-openapi-client/commit/15ba0956997cafbac01f47a82fa8bb72528df482))

### Documentation

- Add Claude Code slash commands and self-improvement patterns
  ([#287](https://github.com/dougborg/katana-openapi-client/pull/287),
  [`07c905f`](https://github.com/dougborg/katana-openapi-client/commit/07c905f97bc33e0d7e9db2f06ff335c2c0d78141))

### Features

- **mcp**: Add tool annotations, tags, LLM-optimized descriptions, prompts, and caching
  config ([#291](https://github.com/dougborg/katana-openapi-client/pull/291),
  [`efd82d1`](https://github.com/dougborg/katana-openapi-client/commit/efd82d1b5809b1a4ea78e4f6e63f5f4c603dd1f7))

- **mcp**: MCP best practices — annotations, tags, LLM descriptions, prompts
  ([#291](https://github.com/dougborg/katana-openapi-client/pull/291),
  [`efd82d1`](https://github.com/dougborg/katana-openapi-client/commit/efd82d1b5809b1a4ea78e4f6e63f5f4c603dd1f7))

- **mcp**: Standardize all tool returns to ToolResult with markdown + structured content
  ([#291](https://github.com/dougborg/katana-openapi-client/pull/291),
  [`efd82d1`](https://github.com/dougborg/katana-openapi-client/commit/efd82d1b5809b1a4ea78e4f6e63f5f4c603dd1f7))

### Refactoring

- **mcp**: Reduce tech debt with shared helpers, dead code removal, and consistency
  fixes ([#290](https://github.com/dougborg/katana-openapi-client/pull/290),
  [`2686aad`](https://github.com/dougborg/katana-openapi-client/commit/2686aadb6df495af372e06c0a75231a72f867f7f))

- **mcp**: Tech debt cleanup with shared helpers and dead code removal
  ([#290](https://github.com/dougborg/katana-openapi-client/pull/290),
  [`2686aad`](https://github.com/dougborg/katana-openapi-client/commit/2686aadb6df495af372e06c0a75231a72f867f7f))

## v0.47.3 (2026-03-13)

### Bug Fixes

- **client**: Make CodedErrorResponse/DetailedErrorResponse fields optional to prevent
  KeyError crashes
  ([`4371b9f`](https://github.com/dougborg/katana-openapi-client/commit/4371b9fac8a0ecf69ed4475b6524d68beb30ddda))

### Chores

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 11 updates
  ([#282](https://github.com/dougborg/katana-openapi-client/pull/282),
  [`e68aa74`](https://github.com/dougborg/katana-openapi-client/commit/e68aa742817166c4714ddc216656c88376087c16))

## v0.47.2 (2026-03-02)

### Bug Fixes

- **client**: Name all inline enums and fix UP047 lint
  ([#283](https://github.com/dougborg/katana-openapi-client/pull/283),
  [`a4ce370`](https://github.com/dougborg/katana-openapi-client/commit/a4ce3709373800fd1ea702764ed13940e2c4db4b))

- **client**: Name all inline enums to eliminate fragile positional references
  ([#283](https://github.com/dougborg/katana-openapi-client/pull/283),
  [`a4ce370`](https://github.com/dougborg/katana-openapi-client/commit/a4ce3709373800fd1ea702764ed13940e2c4db4b))

- **spec**: Use anyOf for nullable invoice_status enum ref
  ([#283](https://github.com/dougborg/katana-openapi-client/pull/283),
  [`a4ce370`](https://github.com/dougborg/katana-openapi-client/commit/a4ce3709373800fd1ea702764ed13940e2c4db4b))

### Chores

- **actions)(deps**: Bump aquasecurity/trivy-action
  ([#277](https://github.com/dougborg/katana-openapi-client/pull/277),
  [`df9baba`](https://github.com/dougborg/katana-openapi-client/commit/df9babad0c8ab13365ac187c3f8fc6f9c9ad91e9))

- **actions)(deps**: Bump the github-actions group with 3 updates
  ([#281](https://github.com/dougborg/katana-openapi-client/pull/281),
  [`c9d56d3`](https://github.com/dougborg/katana-openapi-client/commit/c9d56d3b25e17025567aa59e06653fa7eaf59a44))

## v0.47.1 (2026-02-26)

### Bug Fixes

- **client**: Consolidate duplicated inline enums into shared schemas
  ([`ed0e510`](https://github.com/dougborg/katana-openapi-client/commit/ed0e5107ab3d780128bf0b23b1b3caeeef965689))

## v0.47.0 (2026-02-11)

### Features

- **client**: Add thin API wrapper layer for all resources via client.api
  ([#275](https://github.com/dougborg/katana-openapi-client/pull/275),
  [`915b3d2`](https://github.com/dougborg/katana-openapi-client/commit/915b3d27841e7a65fe7e97aae45c3b1e7915c726))

## v0.46.0 (2026-02-11)

### Bug Fixes

- **client**: Address review — clarify logger call convention, add end-to-end test
  ([#274](https://github.com/dougborg/katana-openapi-client/pull/274),
  [`a9e3453`](https://github.com/dougborg/katana-openapi-client/commit/a9e3453de9c33c5fd6f8868176702203144e81f8))

### Documentation

- **spec**: Document cost_per_unit constraint on stock adjustment rows
  ([#273](https://github.com/dougborg/katana-openapi-client/pull/273),
  [`35a5a30`](https://github.com/dougborg/katana-openapi-client/commit/35a5a3009b7ed030cd5c9bede2ce1a247f2bbb11))

- **spec**: Document cost_per_unit constraint on stock adjustment rows
  ([#274](https://github.com/dougborg/katana-openapi-client/pull/274),
  [`a9e3453`](https://github.com/dougborg/katana-openapi-client/commit/a9e3453de9c33c5fd6f8868176702203144e81f8))

### Features

- **client**: Accept duck-typed loggers via Logger protocol
  ([#274](https://github.com/dougborg/katana-openapi-client/pull/274),
  [`a9e3453`](https://github.com/dougborg/katana-openapi-client/commit/a9e3453de9c33c5fd6f8868176702203144e81f8))

## v0.45.0 (2026-02-11)

### Bug Fixes

- **client**: Preserve array query params across paginated requests
  ([#272](https://github.com/dougborg/katana-openapi-client/pull/272),
  [`599880f`](https://github.com/dougborg/katana-openapi-client/commit/599880f981579ec5891e18783ba37930f5bdb48d))

### Chores

- **release**: Mcp v0.30.0
  ([`d17976b`](https://github.com/dougborg/katana-openapi-client/commit/d17976bccd35e4470f40521851b2db05cd8776f1))

### Features

- **mcp**: Update client dependency to v0.44.6
  ([`e4559a3`](https://github.com/dougborg/katana-openapi-client/commit/e4559a3c23de1105c170e0c788a82ba3347225d8))

## v0.44.6 (2026-02-09)

### Bug Fixes

- Apply ruff 0.15.0 formatting and lint fixes
  ([`aefc8f7`](https://github.com/dougborg/katana-openapi-client/commit/aefc8f74d32ed6276643e44c13ba0606a2ef07c1))

### Chores

- **deps)(deps**: Bump the python-minor-patch group with 4 updates
  ([`58602a0`](https://github.com/dougborg/katana-openapi-client/commit/58602a0ac5590bb35277c4c604993585600d5e7f))

- **deps)(deps-dev**: Bump types-jsonschema
  ([`4960c8c`](https://github.com/dougborg/katana-openapi-client/commit/4960c8c384b636b4d5c7f7cb331251c6ca9587cc))

## v0.44.5 (2026-02-07)

### Bug Fixes

- Address second round of PR review comments
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Address PR review comments
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Address second round of PR review comments
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Align P4 OpenAPI schemas with Katana official API
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Preserve original response shape in PaginationTransport
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Regenerate TypeScript client for P4 schema alignment
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **mcp**: Update stock adjustment field references after P4 alignment
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

### Documentation

- Add Katana API questions document for P4 alignment follow-up
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- Add live API investigation findings to API questions document
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- Update endpoint and model counts after P4 alignment
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- Update endpoint count in OpenAPI docs page
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

### Refactoring

- **client**: Extract 22 inline schemas to named schemas in OpenAPI spec
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

## v0.44.4 (2026-02-06)

### Bug Fixes

- **client**: Align P3 OpenAPI schemas with Katana official API
  ([#267](https://github.com/dougborg/katana-openapi-client/pull/267),
  [`9cd8ba0`](https://github.com/dougborg/katana-openapi-client/commit/9cd8ba01ff18efddc192b6641ff8f25cd3ed23a4))

### Documentation

- **client**: Add default page size to ADR-003 context
  ([#235](https://github.com/dougborg/katana-openapi-client/pull/235),
  [`ca346ff`](https://github.com/dougborg/katana-openapi-client/commit/ca346ffa61149a81872c186af3216d449334531e))

- **client**: Update ADR-003 to reflect limit=250 default
  ([#235](https://github.com/dougborg/katana-openapi-client/pull/235),
  [`ca346ff`](https://github.com/dougborg/katana-openapi-client/commit/ca346ffa61149a81872c186af3216d449334531e))

## v0.44.3 (2026-02-06)

### Bug Fixes

- **client**: Align P2 OpenAPI schemas with Katana official API
  ([#266](https://github.com/dougborg/katana-openapi-client/pull/266),
  [`af03314`](https://github.com/dougborg/katana-openapi-client/commit/af033145b709c840aadbd74f8fb7f471a28c5a70))

## v0.44.2 (2026-02-06)

### Bug Fixes

- **client**: Add missing is_archived field to UpdateProductRequest
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

- **client**: Align P1 OpenAPI schemas with Katana official API
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

- **client**: Align P1 OpenAPI schemas with Katana official API spec
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

- **scripts**: Remove API key logging to address security warning
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

### Documentation

- Add Katana API comprehensive documentation for spec comparison
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

## v0.44.1 (2026-02-06)

### Bug Fixes

- **client**: Correct pagination defaults for auto-pagination
  ([#234](https://github.com/dougborg/katana-openapi-client/pull/234),
  [`5c97def`](https://github.com/dougborg/katana-openapi-client/commit/5c97deff077316f660278e8c28cadf375762ca34))

### Testing

- **client**: Add missing zero limit edge case test
  ([#234](https://github.com/dougborg/katana-openapi-client/pull/234),
  [`5c97def`](https://github.com/dougborg/katana-openapi-client/commit/5c97deff077316f660278e8c28cadf375762ca34))

## v0.44.0 (2026-02-05)

### Bug Fixes

- **client**: Align stocktake row schema with Katana API
  ([#231](https://github.com/dougborg/katana-openapi-client/pull/231),
  [`2827857`](https://github.com/dougborg/katana-openapi-client/commit/28278571e9a801271d2dcb586e977c5d8705046f))

- **client**: Handle null ingredient_expected_date in ManufacturingOrderRecipeRow
  ([`6ffd928`](https://github.com/dougborg/katana-openapi-client/commit/6ffd928cee225b07d147b98a2181bb05fa0f9dda))

- **client**: Handle null sales_order_delivery_deadline in ManufacturingOrder
  ([`c89b8f4`](https://github.com/dougborg/katana-openapi-client/commit/c89b8f48542bb366ee9be2503fcfc50533682ba4))

- **deps**: Bump urllib3 to 2.6.3 for CVE-2026-21441
  ([#227](https://github.com/dougborg/katana-openapi-client/pull/227),
  [`1124ea8`](https://github.com/dougborg/katana-openapi-client/commit/1124ea828596e6ae3ab8078a353d63feea0942bc))

### Chores

- **deps)(deps**: Bump the python-minor-patch group with 11 updates
  ([#228](https://github.com/dougborg/katana-openapi-client/pull/228),
  [`9b81517`](https://github.com/dougborg/katana-openapi-client/commit/9b8151777e3156ba4b1feaed4cab10299c7f1d6d))

- **deps)(deps**: Bump the python-minor-patch group with 2 updates
  ([#229](https://github.com/dougborg/katana-openapi-client/pull/229),
  [`dcfa11f`](https://github.com/dougborg/katana-openapi-client/commit/dcfa11f47c61dc0a055c2143e458122050ffd773))

- **deps)(deps**: Bump types-python-dateutil
  ([#230](https://github.com/dougborg/katana-openapi-client/pull/230),
  [`5563c70`](https://github.com/dougborg/katana-openapi-client/commit/5563c703ab0227dc2a1ee2eb28f2e0abd231a71d))

- **deps)(deps-dev**: Bump ty in the python-minor-patch group
  ([#232](https://github.com/dougborg/katana-openapi-client/pull/232),
  [`9617414`](https://github.com/dougborg/katana-openapi-client/commit/96174148c049748dc05586142cec3e0e175081bf))

- **release**: Mcp v0.29.0
  ([`deec6f3`](https://github.com/dougborg/katana-openapi-client/commit/deec6f355a83e93e3f8f471e708d6f0d29722fec))

### Documentation

- Remove stale docs and fix placeholder references
  ([#233](https://github.com/dougborg/katana-openapi-client/pull/233),
  [`3f73417`](https://github.com/dougborg/katana-openapi-client/commit/3f734170b1c0e0332acce021a08704d5c79e5aa2))

### Features

- **mcp**: Update client dependency to v0.43.0
  ([#226](https://github.com/dougborg/katana-openapi-client/pull/226),
  [`a6e177c`](https://github.com/dougborg/katana-openapi-client/commit/a6e177ce07a01389585528b1ce967c92f76dca13))

## v0.43.0 (2026-01-16)

### Bug Fixes

- **client**: Address PR review comments from Copilot
  ([#214](https://github.com/dougborg/katana-openapi-client/pull/214),
  [`1d5200b`](https://github.com/dougborg/katana-openapi-client/commit/1d5200b6bb987d3594705d579a6b35cac37a7286))

- **client**: Resolve type errors for ty 0.0.11 compatibility
  ([#224](https://github.com/dougborg/katana-openapi-client/pull/224),
  [`f5ea245`](https://github.com/dougborg/katana-openapi-client/commit/f5ea245094414ba0b9f1fde5260a181a9486ddb1))

- **client**: Resolve type errors for ty 0.0.1a25 compatibility
  ([#225](https://github.com/dougborg/katana-openapi-client/pull/225),
  [`13dbf43`](https://github.com/dougborg/katana-openapi-client/commit/13dbf43cf400c16fedd86a87fe44d239aa46b16d))

- **mcp**: Address review comments on hardcoded values
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

- **mcp**: Fix incomplete template variable check in test
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

- **mcp**: Use explicit if-else for empty list fallbacks
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

### Chores

- **actions)(deps**: Bump the github-actions group with 4 updates
  ([#212](https://github.com/dougborg/katana-openapi-client/pull/212),
  [`792734d`](https://github.com/dougborg/katana-openapi-client/commit/792734dd6008cfe65339508cb247a2cc7a2c832a))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 11 updates
  ([#224](https://github.com/dougborg/katana-openapi-client/pull/224),
  [`f5ea245`](https://github.com/dougborg/katana-openapi-client/commit/f5ea245094414ba0b9f1fde5260a181a9486ddb1))

- **deps)(deps**: Bump the python-minor-patch group with 9 updates
  ([#217](https://github.com/dougborg/katana-openapi-client/pull/217),
  [`a91edbb`](https://github.com/dougborg/katana-openapi-client/commit/a91edbb2ee228aea30b6eb3f8f8ba48d3325794a))

- **deps)(deps**: Bump types-python-dateutil
  ([#218](https://github.com/dougborg/katana-openapi-client/pull/218),
  [`4a9d5b6`](https://github.com/dougborg/katana-openapi-client/commit/4a9d5b61c6163ba314b7ad3f489596172e84f6c3))

- **infra**: Enable Dependabot uv support for Python dependencies
  ([#216](https://github.com/dougborg/katana-openapi-client/pull/216),
  [`b00b0a1`](https://github.com/dougborg/katana-openapi-client/commit/b00b0a1241e44b147c3a079ae129137eab0afe74))

- **release**: Mcp v0.27.0
  ([`38556ce`](https://github.com/dougborg/katana-openapi-client/commit/38556ce6404ae2d3b9f2ae5a3b36e1746a3773bd))

- **release**: Mcp v0.28.0
  ([`45580ed`](https://github.com/dougborg/katana-openapi-client/commit/45580ed4e2f5d8b8b6361c951d7df35972225fb3))

### Documentation

- Fix exception hierarchy documentation in CLAUDE.md
  ([#214](https://github.com/dougborg/katana-openapi-client/pull/214),
  [`1d5200b`](https://github.com/dougborg/katana-openapi-client/commit/1d5200b6bb987d3594705d579a6b35cac37a7286))

### Features

- **client**: Add ProductionIngredient resource type to inventory movements
  ([#225](https://github.com/dougborg/katana-openapi-client/pull/225),
  [`13dbf43`](https://github.com/dougborg/katana-openapi-client/commit/13dbf43cf400c16fedd86a87fe44d239aa46b16d))

- **mcp**: Add token reduction patterns and ToolResult integration
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

- **mcp**: Update client dependency to v0.42.0
  ([#211](https://github.com/dougborg/katana-openapi-client/pull/211),
  [`990dd93`](https://github.com/dougborg/katana-openapi-client/commit/990dd931430b0d2de5e113f675407f51d52f4259))

### Refactoring

- **client,mcp**: Use consistent helper utilities for API response handling
  ([#214](https://github.com/dougborg/katana-openapi-client/pull/214),
  [`1d5200b`](https://github.com/dougborg/katana-openapi-client/commit/1d5200b6bb987d3594705d579a6b35cac37a7286))

- **mcp**: Use shared make_tool_result utility
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

## v0.42.0 (2025-12-12)

### Bug Fixes

- **client**: Handle boolean string pagination fields (first_page, last_page)
  ([#210](https://github.com/dougborg/katana-openapi-client/pull/210),
  [`bb2238d`](https://github.com/dougborg/katana-openapi-client/commit/bb2238d55b0a9639d476e609ff4b70c6e54137cd))

- **docs**: Address PR review comments
  ([#208](https://github.com/dougborg/katana-openapi-client/pull/208),
  [`860be5a`](https://github.com/dougborg/katana-openapi-client/commit/860be5aaebe62bc34afae974b89152f5557cb470))

- **docs**: Correct TypeScript ADR references and MCP tool counts
  ([#208](https://github.com/dougborg/katana-openapi-client/pull/208),
  [`860be5a`](https://github.com/dougborg/katana-openapi-client/commit/860be5aaebe62bc34afae974b89152f5557cb470))

- **mcp**: Address additional PR review comments
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Patch FastMCP for Pydantic 2.12+ compatibility
  ([#204](https://github.com/dougborg/katana-openapi-client/pull/204),
  [`9a651b2`](https://github.com/dougborg/katana-openapi-client/commit/9a651b253a72990363c25a76134cb5e63df7a579))

- **mcp**: Remove dead code and unused fixture params from integration tests
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Use unwrap_data helper for list response extraction
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

### Chores

- **release**: Mcp v0.24.0
  ([`85bdbb4`](https://github.com/dougborg/katana-openapi-client/commit/85bdbb48ff82746bb6763b353d3e17fe5573597b))

- **release**: Mcp v0.25.0
  ([`6748599`](https://github.com/dougborg/katana-openapi-client/commit/6748599d174fe39779d2b0595128739962310b11))

- **release**: Mcp v0.26.0
  ([`d77f3b6`](https://github.com/dougborg/katana-openapi-client/commit/d77f3b65bda9437aa4b5c4837c24537b3d10fcda))

### Code Style

- **mcp**: Move imports to module level per review feedback
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

### Documentation

- Overhaul documentation for multi-package ecosystem
  ([#208](https://github.com/dougborg/katana-openapi-client/pull/208),
  [`860be5a`](https://github.com/dougborg/katana-openapi-client/commit/860be5aaebe62bc34afae974b89152f5557cb470))

### Features

- **mcp**: Add CLI transport options and simplify CLAUDE.md
  ([#209](https://github.com/dougborg/katana-openapi-client/pull/209),
  [`103ea19`](https://github.com/dougborg/katana-openapi-client/commit/103ea19854d55d2dac2b3d0783fcf7e8f6391b67))

- **mcp**: Add integration tests for end-to-end workflows
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Add response caching middleware and migrate pytest to native TOML
  ([#204](https://github.com/dougborg/katana-openapi-client/pull/204),
  [`9a651b2`](https://github.com/dougborg/katana-openapi-client/commit/9a651b253a72990363c25a76134cb5e63df7a579))

- **mcp**: Add test data isolation and cleanup utilities
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Update client dependency to v0.41.0
  ([#203](https://github.com/dougborg/katana-openapi-client/pull/203),
  [`4b3ea94`](https://github.com/dougborg/katana-openapi-client/commit/4b3ea944f15ea5d664720a957f9be744b9b7c2be))

### Testing

- **client**: Add edge case tests for boolean pagination field conversion
  ([#210](https://github.com/dougborg/katana-openapi-client/pull/210),
  [`bb2238d`](https://github.com/dougborg/katana-openapi-client/commit/bb2238d55b0a9639d476e609ff4b70c6e54137cd))

- **client**: Improve test coverage per review feedback
  ([#210](https://github.com/dougborg/katana-openapi-client/pull/210),
  [`bb2238d`](https://github.com/dougborg/katana-openapi-client/commit/bb2238d55b0a9639d476e609ff4b70c6e54137cd))

## v0.41.0 (2025-12-10)

### Bug Fixes

- **client**: Update dependencies to address urllib3 security vulnerabilities
  ([#202](https://github.com/dougborg/katana-openapi-client/pull/202),
  [`d4d1fb1`](https://github.com/dougborg/katana-openapi-client/commit/d4d1fb1481e5039cbdf79c35c39465450c647b53))

### Chores

- **release**: Mcp v0.23.0
  ([`5ade79f`](https://github.com/dougborg/katana-openapi-client/commit/5ade79fb9d863d4a96aa0c7377bf957036b8d7a7))

### Features

- **mcp**: Add create_sales_order tool
  ([#201](https://github.com/dougborg/katana-openapi-client/pull/201),
  [`055352c`](https://github.com/dougborg/katana-openapi-client/commit/055352cb8c66a734ff1f7bbafe6d3055fd65061f))

## v0.40.0 (2025-12-10)

### Bug Fixes

- Address self-review feedback and exclude integration tests
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

- **client**: Address PR review feedback - remove unused code
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **client**: Align domain model types and constraints with OpenAPI spec
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Use AwareDatetime for all timestamp fields in domain models
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Use datetime for archived_at and deleted_at fields
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

### Chores

- **client**: Update dependencies to latest versions
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **release**: Mcp v0.22.0
  ([`72cd376`](https://github.com/dougborg/katana-openapi-client/commit/72cd3766338e71a30a22164e370c7f91e74fac6a))

### Documentation

- **client**: Add comprehensive TypeScript client documentation
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

### Features

- **client**: Add auto-generated Pydantic models from OpenAPI
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Add auto-generated Pydantic v2 models from OpenAPI
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **mcp**: Update client dependency to v0.39.0
  ([#196](https://github.com/dougborg/katana-openapi-client/pull/196),
  [`95cda20`](https://github.com/dougborg/katana-openapi-client/commit/95cda20ab5c0381755bd813a36ac56da1f53b5d0))

- **ts-client**: Add TypeScript client with resilient transport
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **ts-client**: Add TypeScript client with retry and pagination transport
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **ts-client**: Integrate KatanaClient with generated SDK and add tests
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

### Refactoring

- **client**: Improve pydantic models code quality
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Modernize dependencies for 2025
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

- **client**: Modernize TypeScript client dependencies for 2025
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

- **client**: Use composition pattern for domain models
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

### Testing

- **client**: Add comprehensive tests for domain model factory methods
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

## v0.39.0 (2025-12-05)

### Bug Fixes

- **client**: Address Copilot review feedback for pagination normalization
  ([#195](https://github.com/dougborg/katana-openapi-client/pull/195),
  [`5665061`](https://github.com/dougborg/katana-openapi-client/commit/5665061e87fc77fddc610e1009e4e3ec6a0dccf7))

- **client**: Convert pagination string values to integers for correct comparison
  ([#195](https://github.com/dougborg/katana-openapi-client/pull/195),
  [`5665061`](https://github.com/dougborg/katana-openapi-client/commit/5665061e87fc77fddc610e1009e4e3ec6a0dccf7))

- **client**: Improve pagination value normalization edge case handling
  ([#195](https://github.com/dougborg/katana-openapi-client/pull/195),
  [`5665061`](https://github.com/dougborg/katana-openapi-client/commit/5665061e87fc77fddc610e1009e4e3ec6a0dccf7))

### Chores

- **release**: Mcp v0.21.0
  ([`86c11de`](https://github.com/dougborg/katana-openapi-client/commit/86c11de0e981296408a8fe4be42315983959f8c7))

### Features

- **mcp**: Update client dependency to v0.38.0
  ([#194](https://github.com/dougborg/katana-openapi-client/pull/194),
  [`9d9a4f3`](https://github.com/dougborg/katana-openapi-client/commit/9d9a4f324c8d9e988bac9251f764104aa8a7a24e))

## v0.38.0 (2025-12-05)

### Bug Fixes

- **client**: Address code review feedback on auto-pagination
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **client**: Enable auto-pagination by default in generated code
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **client**: Improve auto-pagination defaults and explicit controls
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **client**: Make regex pattern more robust for page defaults
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **mcp**: Consolidate test fixtures to resolve conftest plugin conflict
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

### Chores

- Add .cursor/ to .gitignore
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **release**: Mcp v0.20.0
  ([`ce3a2a6`](https://github.com/dougborg/katana-openapi-client/commit/ce3a2a6cf5ee911b9247d30ab52a6d9453864446))

### Features

- **client**: Improve auto-pagination with explicit controls
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **mcp**: Update client dependency to v0.37.0
  ([#192](https://github.com/dougborg/katana-openapi-client/pull/192),
  [`c8c62c4`](https://github.com/dougborg/katana-openapi-client/commit/c8c62c4c35765e32aec8d30e10f45ed14954cc3f))

## v0.37.0 (2025-12-05)

### Bug Fixes

- **client**: Address code review feedback on auto-pagination
  ([#191](https://github.com/dougborg/katana-openapi-client/pull/191),
  [`8dc3cfc`](https://github.com/dougborg/katana-openapi-client/commit/8dc3cfcb1e9751b2c204a709846bee9dd1cc9eea))

- **mcp**: Consolidate test fixtures to resolve conftest plugin conflict
  ([#191](https://github.com/dougborg/katana-openapi-client/pull/191),
  [`8dc3cfc`](https://github.com/dougborg/katana-openapi-client/commit/8dc3cfcb1e9751b2c204a709846bee9dd1cc9eea))

### Chores

- **actions)(deps**: Bump actions/checkout in the github-actions group
  ([#190](https://github.com/dougborg/katana-openapi-client/pull/190),
  [`76ad170`](https://github.com/dougborg/katana-openapi-client/commit/76ad170e6855db06ac464e69729fb4a34267d581))

- **release**: Mcp v0.19.0
  ([`33b13f6`](https://github.com/dougborg/katana-openapi-client/commit/33b13f640bcdfbad0cc1395ef114158e6d79dec2))

### Documentation

- Add strict quality standards - no ignoring pre-existing issues
  ([#188](https://github.com/dougborg/katana-openapi-client/pull/188),
  [`c7424a2`](https://github.com/dougborg/katana-openapi-client/commit/c7424a290477dffff0f9a1f18c046764c3654b91))

### Features

- **client**: Improve auto-pagination with explicit controls
  ([#191](https://github.com/dougborg/katana-openapi-client/pull/191),
  [`8dc3cfc`](https://github.com/dougborg/katana-openapi-client/commit/8dc3cfcb1e9751b2c204a709846bee9dd1cc9eea))

- **mcp**: Update client dependency to v0.36.0
  ([`e31ddb5`](https://github.com/dougborg/katana-openapi-client/commit/e31ddb52bacb9c9a0c62eaad19239c4f241d4d15))

## v0.36.0 (2025-11-22)

### Bug Fixes

- Address Copilot review comments in .cursorrules
  ([`f1007f4`](https://github.com/dougborg/katana-openapi-client/commit/f1007f4d9e476c725e13d71629aeeca39eb1faf0))

### Chores

- **release**: Mcp v0.18.0
  ([`7cdd30c`](https://github.com/dougborg/katana-openapi-client/commit/7cdd30c781b64aec24b14f3ea31ae0f686ca813c))

### Features

- Add Cursor rules for better AI assistance
  ([`65851d4`](https://github.com/dougborg/katana-openapi-client/commit/65851d4a9880589c62a664dd2b192d62cb5ff0bc))

## v0.35.0 (2025-11-21)

### Bug Fixes

- **client**: Add SalesOrderFulfillmentRow to SerialNumberResourceType enum
  ([`701580e`](https://github.com/dougborg/katana-openapi-client/commit/701580eadd9acb56cf03a83138f6d257d1b21bb0))

### Features

- **mcp**: Update client dependency to v0.34.0
  ([`42be36e`](https://github.com/dougborg/katana-openapi-client/commit/42be36e94d75b521970de8e231f9166fb9897457))

## v0.34.0 (2025-11-18)

### Bug Fixes

- **ci**: Ignore site/ directory in yamllint config
  ([`2aed19f`](https://github.com/dougborg/katana-openapi-client/commit/2aed19f7b422f1451bd617671fa439fc1ddbe25b))

- **ci**: Ignore site/ directory in yamllint config
  ([`6aa1e54`](https://github.com/dougborg/katana-openapi-client/commit/6aa1e542dee736107db1eef8c0c0d46bfbaf836e))

### Chores

- **actions)(deps**: Bump python-semantic-release/python-semantic-release
  ([#176](https://github.com/dougborg/katana-openapi-client/pull/176),
  [`c8b3a7d`](https://github.com/dougborg/katana-openapi-client/commit/c8b3a7ded982974ac54b9658a12c9a1587ac3f86))

- **release**: Mcp v0.17.0
  ([`a995d0b`](https://github.com/dougborg/katana-openapi-client/commit/a995d0b0a2d42afbfb937323a637febff5909cda))

### Documentation

- **mcp**: Add ADRs for tool interface pattern and automated documentation
  ([`4f5425f`](https://github.com/dougborg/katana-openapi-client/commit/4f5425f8686b3685e1779762c1559cb09948daac))

### Features

- **client**: Enhance invalid_type validation error messages
  ([`5df0d0f`](https://github.com/dougborg/katana-openapi-client/commit/5df0d0f6d0789251e31011db5b587a91c8ca58fb))

- **client**: Enhance min/max validation error messages
  ([`574cd44`](https://github.com/dougborg/katana-openapi-client/commit/574cd44d75c18c76faa2177ac68d01fba2051c52))

- **client**: Enhance pattern validation error messages
  ([`491cf3c`](https://github.com/dougborg/katana-openapi-client/commit/491cf3c791c8788795bdcd105ec887e05c42c0b8))

- **client**: Enhance required field validation error messages
  ([`f41e25f`](https://github.com/dougborg/katana-openapi-client/commit/f41e25fb30539d0fb735ed61e5ddc3805ebddddc))

- **client**: Enhance too_small/too_big validation error messages
  ([`85a4543`](https://github.com/dougborg/katana-openapi-client/commit/85a45433e1ed2863d068e7f6b6fa28f93d8e3caa))

- **client**: Enhance unrecognized_keys validation error messages
  ([`9a64a55`](https://github.com/dougborg/katana-openapi-client/commit/9a64a55f25533c50b0ae00bb889c465c334fbd6a))

- **client**: Improve enum validation error messages
  ([`f86c5ff`](https://github.com/dougborg/katana-openapi-client/commit/f86c5ff095993dd19be78678a64c7028cf0f20af))

- **mcp**: Update client dependency to v0.33.0
  ([#181](https://github.com/dougborg/katana-openapi-client/pull/181),
  [`5aa64dc`](https://github.com/dougborg/katana-openapi-client/commit/5aa64dc5e58a4b05c2953f99a018a7af212d4422))

### Refactoring

- **client**: Use discriminated unions for validation errors
  ([`ce67506`](https://github.com/dougborg/katana-openapi-client/commit/ce67506e90625dd5cc16afba117c03e64b795b13))

## v0.33.0 (2025-11-14)

### Chores

- Configure yamllint with 120 char line length
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

- Consolidate config and cleanup documentation
  ([`36a2b0f`](https://github.com/dougborg/katana-openapi-client/commit/36a2b0f87151eb6c2d74c733a57226a411a6d0b5))

- **actions)(deps**: Bump the github-actions group with 2 updates
  ([`7ca453a`](https://github.com/dougborg/katana-openapi-client/commit/7ca453ac54954b0ea8a45279749356ae83e7d98a))

- **release**: Mcp v0.10.0
  ([`14f1835`](https://github.com/dougborg/katana-openapi-client/commit/14f183557e2dc172ed952e8da1a7e016934e12a6))

- **release**: Mcp v0.11.0
  ([`74d0dd2`](https://github.com/dougborg/katana-openapi-client/commit/74d0dd2e7cd882606cce67f2460dceb8507fa352))

- **release**: Mcp v0.12.0
  ([`1e54f96`](https://github.com/dougborg/katana-openapi-client/commit/1e54f96a9790e272265a67d41aa5f3d99c4e40bf))

- **release**: Mcp v0.13.0
  ([`911b0ef`](https://github.com/dougborg/katana-openapi-client/commit/911b0efdd5e22d5ddde46781576f8ab28d62a82d))

- **release**: Mcp v0.14.0
  ([`8f33a95`](https://github.com/dougborg/katana-openapi-client/commit/8f33a959b011eaa037f10b9323ebed51827a292f))

- **release**: Mcp v0.15.0
  ([`5310d08`](https://github.com/dougborg/katana-openapi-client/commit/5310d08626e8fad4572e139f95566381c4cf45dd))

- **release**: Mcp v0.16.0
  ([`65b09a0`](https://github.com/dougborg/katana-openapi-client/commit/65b09a0d0c39c81505581e42f1fded9ad426c34a))

- **release**: Mcp v0.9.0
  ([`2ec7337`](https://github.com/dougborg/katana-openapi-client/commit/2ec73379b775646bad3bd4adc2bd39b5cbfeb4fc))

### Documentation

- **client**: Add pending changelog entry for stock adjustment rows
  ([#178](https://github.com/dougborg/katana-openapi-client/pull/178),
  [`6ef834e`](https://github.com/dougborg/katana-openapi-client/commit/6ef834ebfd765e0ad982a5db6561fa7a68823b16))

- **mcp**: Add comprehensive documentation for observability decorators to LOGGING.md
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Add tools.json generator documentation to docker.md
  ([#175](https://github.com/dougborg/katana-openapi-client/pull/175),
  [`9c2c6f2`](https://github.com/dougborg/katana-openapi-client/commit/9c2c6f27e55424c67e1920df06902f29c5957a7d))

### Features

- **client**: Add stock adjustment rows, reason field, and regen script improvements
  (#178) ([#179](https://github.com/dougborg/katana-openapi-client/pull/179),
  [`c57c5f3`](https://github.com/dougborg/katana-openapi-client/commit/c57c5f39682fe4d2a19af227070565c2c978452c))

- **mcp**: Add @observe_tool and @observe_service decorators with tests
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Add FastMCP elicitation pattern to destructive operations
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

- **mcp**: Add observability decorators for automatic tool instrumentation
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Add resources foundation and first inventory/items resource
  ([`c0b5459`](https://github.com/dougborg/katana-openapi-client/commit/c0b54593e54c268cd9e170af2b6cfdb0cd56c2d2))

- **mcp**: Add tools.json generator for Docker MCP Registry submission
  ([#175](https://github.com/dougborg/katana-openapi-client/pull/175),
  [`9c2c6f2`](https://github.com/dougborg/katana-openapi-client/commit/9c2c6f27e55424c67e1920df06902f29c5957a7d))

- **mcp**: Add tools.json generator script with comprehensive tests
  ([#175](https://github.com/dougborg/katana-openapi-client/pull/175),
  [`9c2c6f2`](https://github.com/dougborg/katana-openapi-client/commit/9c2c6f27e55424c67e1920df06902f29c5957a7d))

- **mcp**: Apply @observe_tool decorator to all foundation tools
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Apply Unpack decorator to all remaining MCP tools
  ([`ef59809`](https://github.com/dougborg/katana-openapi-client/commit/ef5980912bb2afa40b1b2d41a7c45639a33ba237))

- **mcp**: Implement FastMCP elicitation pattern for destructive operations
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

- **mcp**: Implement remaining MCP resources for inventory and orders
  ([`062fedd`](https://github.com/dougborg/katana-openapi-client/commit/062feddcd2a2fc789e35b8c5ba1cc0d1c836cfb3))

- **mcp**: Implement Unpack decorator for flat tool parameters
  ([`862ce79`](https://github.com/dougborg/katana-openapi-client/commit/862ce79f10c244c3b711487cccbed7ccf744d27f))

- **mcp**: Implement Unpack decorator for flat tool parameters
  ([`a025ca9`](https://github.com/dougborg/katana-openapi-client/commit/a025ca98e0f8d279da03471800b7ebeb8da20ec7))

- **mcp**: Update client dependency to v0.32.0
  ([#158](https://github.com/dougborg/katana-openapi-client/pull/158),
  [`ff8f2be`](https://github.com/dougborg/katana-openapi-client/commit/ff8f2be1ab84d5cabeffa41b32e425a7ad0dc41f))

### Refactoring

- **mcp**: Extract ConfirmationSchema to shared module
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

### Testing

- **mcp**: Add test reproducing Claude Code parameter passing issue
  ([`05f643e`](https://github.com/dougborg/katana-openapi-client/commit/05f643eabf2880c3577259baf4b81a9e4433ce4f))

- **mcp**: Fix integration tests with pytest-asyncio fixture decorator
  ([`36db39d`](https://github.com/dougborg/katana-openapi-client/commit/36db39d548f4573a1714d56a99dff3355b5f0a96))

- **mcp**: Fix wrapper test to call implementation directly
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

## v0.32.0 (2025-11-08)

### Bug Fixes

- **client**: Allow empty SKUs and support service variant type
  ([`1baae73`](https://github.com/dougborg/katana-openapi-client/commit/1baae73535c8db1b95547ff4a43fce12992a23a2))

- **copilot**: Repair YAML frontmatter in agent definition files
  ([`1c6fc85`](https://github.com/dougborg/katana-openapi-client/commit/1c6fc85abad148235639fc2e1c95920f4948c642))

- **mcp**: Add .client attribute to mock context in test_orders
  ([#157](https://github.com/dougborg/katana-openapi-client/pull/157),
  [`621925c`](https://github.com/dougborg/katana-openapi-client/commit/621925c23baa0194b94f8bc06c14160a09032394))

- **mcp**: Remove unnecessary @pytest.mark.asyncio decorators from sync validation tests
  ([#153](https://github.com/dougborg/katana-openapi-client/pull/153),
  [`80da12c`](https://github.com/dougborg/katana-openapi-client/commit/80da12cd1129e2d571acde48f9055343003acb29))

- **mcp**: Remove unused ManufacturingOrderStatus import
  ([#157](https://github.com/dougborg/katana-openapi-client/pull/157),
  [`621925c`](https://github.com/dougborg/katana-openapi-client/commit/621925c23baa0194b94f8bc06c14160a09032394))

### Chores

- Migrate from mypy to ty for type checking
  ([#137](https://github.com/dougborg/katana-openapi-client/pull/137),
  [`87ad793`](https://github.com/dougborg/katana-openapi-client/commit/87ad7936bd31116d8326c2ea9de4b412e48b3d6e))

- Update Python version support to 3.12, 3.13, and 3.14
  ([#147](https://github.com/dougborg/katana-openapi-client/pull/147),
  [`7183e55`](https://github.com/dougborg/katana-openapi-client/commit/7183e550f8efa0b2defc862fe8cf3494fb0493b6))

- **copilot**: Remove duplicate agent files with .md extension
  ([`a0e27e1`](https://github.com/dougborg/katana-openapi-client/commit/a0e27e197c191bed55aafdf5a67b48205dc16b61))

- **release**: Mcp v0.7.0
  ([`c5e5dc2`](https://github.com/dougborg/katana-openapi-client/commit/c5e5dc2a5ff92d17fc2987d35b87817c45839c26))

- **release**: Mcp v0.8.0
  ([`e7a3c31`](https://github.com/dougborg/katana-openapi-client/commit/e7a3c31c3b777bd06cbf1917aee2777eb9824910))

### Continuous Integration

- Fix required status checks for docs-only PRs
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- Fix required status checks for docs-only PRs
  ([#148](https://github.com/dougborg/katana-openapi-client/pull/148),
  [`902b62a`](https://github.com/dougborg/katana-openapi-client/commit/902b62aa739bec456d1570b447a74673db1d703e))

### Documentation

- Add ADR-014 for GitHub Copilot custom agents architecture
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- Add ADR-014 for GitHub Copilot custom agents architecture
  ([#148](https://github.com/dougborg/katana-openapi-client/pull/148),
  [`902b62a`](https://github.com/dougborg/katana-openapi-client/commit/902b62aa739bec456d1570b447a74673db1d703e))

- Reorganize to module-local structure
  ([#143](https://github.com/dougborg/katana-openapi-client/pull/143),
  [`5646bee`](https://github.com/dougborg/katana-openapi-client/commit/5646bee800eb6bc945804ab4476a14cb325fbb0f))

- **mcp**: Add ADR-014 and MCP v0.1.0 release checklist
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- **mcp**: Create comprehensive v0.1.0 release checklist
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- **mcp**: Fix tool name in README (search_items not search_products)
  ([#151](https://github.com/dougborg/katana-openapi-client/pull/151),
  [`01b410e`](https://github.com/dougborg/katana-openapi-client/commit/01b410e8b845468511a2c313ae08ab6aa863adf8))

- **mcp**: Include stock_level field in search_items response example
  ([#151](https://github.com/dougborg/katana-openapi-client/pull/151),
  [`01b410e`](https://github.com/dougborg/katana-openapi-client/commit/01b410e8b845468511a2c313ae08ab6aa863adf8))

### Features

- **mcp**: Add create_product and create_material catalog tools
  ([#153](https://github.com/dougborg/katana-openapi-client/pull/153),
  [`80da12c`](https://github.com/dougborg/katana-openapi-client/commit/80da12cd1129e2d571acde48f9055343003acb29))

- **mcp**: Add dedicated create_product and create_material catalog management tools
  ([#153](https://github.com/dougborg/katana-openapi-client/pull/153),
  [`80da12c`](https://github.com/dougborg/katana-openapi-client/commit/80da12cd1129e2d571acde48f9055343003acb29))

- **mcp**: Add get_variant_details tool for fetching variant info by SKU
  ([#152](https://github.com/dougborg/katana-openapi-client/pull/152),
  [`8246b95`](https://github.com/dougborg/katana-openapi-client/commit/8246b955d7f389628f09bbbf6ff052b5bb4d998b))

- **mcp**: Implement create_manufacturing_order tool
  ([#156](https://github.com/dougborg/katana-openapi-client/pull/156),
  [`bc78244`](https://github.com/dougborg/katana-openapi-client/commit/bc782442b00cf6ae35512009e5f0c3b4bd6ec04d))

- **mcp**: Implement create_manufacturing_order tool for issue #44
  ([#156](https://github.com/dougborg/katana-openapi-client/pull/156),
  [`bc78244`](https://github.com/dougborg/katana-openapi-client/commit/bc782442b00cf6ae35512009e5f0c3b4bd6ec04d))

- **mcp**: Implement fulfill_order tool for manufacturing and sales orders
  ([#157](https://github.com/dougborg/katana-openapi-client/pull/157),
  [`621925c`](https://github.com/dougborg/katana-openapi-client/commit/621925c23baa0194b94f8bc06c14160a09032394))

- **mcp**: Implement verify_order_document tool with comprehensive tests for #86
  ([#154](https://github.com/dougborg/katana-openapi-client/pull/154),
  [`a1671b5`](https://github.com/dougborg/katana-openapi-client/commit/a1671b569485515604e68fa2bbd5316a80b48903))

- **mcp**: Implement verify_order_document tool with structured response models
  ([#154](https://github.com/dougborg/katana-openapi-client/pull/154),
  [`a1671b5`](https://github.com/dougborg/katana-openapi-client/commit/a1671b569485515604e68fa2bbd5316a80b48903))

- **mcp**: Update client dependency to v0.31.0
  ([#141](https://github.com/dougborg/katana-openapi-client/pull/141),
  [`7bf1c59`](https://github.com/dougborg/katana-openapi-client/commit/7bf1c591abc1fc26200f5878a1ae8e73463596b7))

### Refactoring

- **copilot**: Adopt official GitHub Copilot agent structure
  ([#146](https://github.com/dougborg/katana-openapi-client/pull/146),
  [`0523a50`](https://github.com/dougborg/katana-openapi-client/commit/0523a5019616f8c8de42598cd46e73fc2f33a896))

- **copilot**: Adopt official GitHub Copilot agent structure
  ([#145](https://github.com/dougborg/katana-openapi-client/pull/145),
  [`e0311c5`](https://github.com/dougborg/katana-openapi-client/commit/e0311c5e7178858b0017b829d0694f5abaf98b7e))

- **copilot**: Migrate agents to awesome-copilot three-tier architecture
  ([#145](https://github.com/dougborg/katana-openapi-client/pull/145),
  [`e0311c5`](https://github.com/dougborg/katana-openapi-client/commit/e0311c5e7178858b0017b829d0694f5abaf98b7e))

- **mcp**: Address code review feedback for verify_order_document
  ([#154](https://github.com/dougborg/katana-openapi-client/pull/154),
  [`a1671b5`](https://github.com/dougborg/katana-openapi-client/commit/a1671b569485515604e68fa2bbd5316a80b48903))

- **mcp**: Address PR review feedback for manufacturing orders
  ([#156](https://github.com/dougborg/katana-openapi-client/pull/156),
  [`bc78244`](https://github.com/dougborg/katana-openapi-client/commit/bc782442b00cf6ae35512009e5f0c3b4bd6ec04d))

- **mcp**: Move create_mock_context to shared conftest
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

### Testing

- **mcp**: Add API payload and response structure validation tests
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Add comprehensive edge case tests for receive_purchase_order
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Add comprehensive integration tests for inventory tools
  ([#150](https://github.com/dougborg/katana-openapi-client/pull/150),
  [`b84b05b`](https://github.com/dougborg/katana-openapi-client/commit/b84b05b7a225faa7dc21933eb6ddb5b8994cec1b))

- **mcp**: Add comprehensive test coverage for receive_purchase_order tool
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Add comprehensive unit tests for receive_purchase_order tool
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Address PR review feedback for integration tests
  ([#150](https://github.com/dougborg/katana-openapi-client/pull/150),
  [`b84b05b`](https://github.com/dougborg/katana-openapi-client/commit/b84b05b7a225faa7dc21933eb6ddb5b8994cec1b))

## v0.31.0 (2025-11-05)

### Bug Fixes

- **ci**: Convert pre-commit to local hooks via uv
  ([#135](https://github.com/dougborg/katana-openapi-client/pull/135),
  [`12d86d6`](https://github.com/dougborg/katana-openapi-client/commit/12d86d6e3b14d1251822f4c6bf96545dde8c8240))

- **copilot**: Address review comments on custom agent definitions
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- **mcp**: Address PR review comments on purchase order tools
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **test**: Use .test TLD for mock URLs to avoid DNS lookups
  ([#140](https://github.com/dougborg/katana-openapi-client/pull/140),
  [`5e78ef8`](https://github.com/dougborg/katana-openapi-client/commit/5e78ef890a79c44756093d1ea357335f2df95290))

### Chores

- **actions)(deps**: Bump the github-actions group with 6 updates
  ([#130](https://github.com/dougborg/katana-openapi-client/pull/130),
  [`4da0481`](https://github.com/dougborg/katana-openapi-client/commit/4da0481da939e9d277a187ce3dd207d2c1ed8d67))

- **docker)(deps**: Bump python in /katana_mcp_server
  ([#129](https://github.com/dougborg/katana-openapi-client/pull/129),
  [`286b536`](https://github.com/dougborg/katana-openapi-client/commit/286b536efa6f1a49d44e6e8643a54c504804e4b0))

- **release**: Mcp v0.6.0
  ([`ec773ed`](https://github.com/dougborg/katana-openapi-client/commit/ec773ed50e0fab2104b476d3819b9ac93b5a3216))

### Documentation

- Initial plan for custom GitHub Copilot agents
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- Update workflows README with automated dependency management
  ([#122](https://github.com/dougborg/katana-openapi-client/pull/122),
  [`30510f5`](https://github.com/dougborg/katana-openapi-client/commit/30510f597e14d89b10c951af28de12963aed3976))

### Features

- Add automated MCP dependency update workflow
  ([#122](https://github.com/dougborg/katana-openapi-client/pull/122),
  [`30510f5`](https://github.com/dougborg/katana-openapi-client/commit/30510f597e14d89b10c951af28de12963aed3976))

- Add custom GitHub Copilot agents for specialized tasks
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- Define custom GitHub Copilot agents for specialized development tasks
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- **mcp**: Add structured logging with performance metrics
  ([`dbba41e`](https://github.com/dougborg/katana-openapi-client/commit/dbba41eb3712c83b9d1540f64b1fd416227f317d))

- **mcp**: Add stub purchase order foundation tools
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Automate MCP dependency updates on client releases
  ([#122](https://github.com/dougborg/katana-openapi-client/pull/122),
  [`30510f5`](https://github.com/dougborg/katana-openapi-client/commit/30510f597e14d89b10c951af28de12963aed3976))

- **mcp**: Implement create_purchase_order with real API integration
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Implement purchase order foundation tools
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Implement receive_purchase_order with real API integration
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Implement verify_order_document tool
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

### Performance Improvements

- **mcp**: Optimize variant fetching with API-level ID filtering
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

### Testing

- **mcp**: Add comprehensive logging tests and documentation
  ([`dbba41e`](https://github.com/dougborg/katana-openapi-client/commit/dbba41eb3712c83b9d1540f64b1fd416227f317d))

## v0.30.0 (2025-11-05)

### Chores

- Clean up trigger file
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- Trigger push of README badge changes
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- **infra**: Add Dependabot configuration for GitHub Actions and Docker updates
  ([#119](https://github.com/dougborg/katana-openapi-client/pull/119),
  [`555122b`](https://github.com/dougborg/katana-openapi-client/commit/555122bbbf45675c0aef0acba6c26872c1b4670b))

- **infra**: Add Dependabot configuration for weekly dependency updates
  ([#119](https://github.com/dougborg/katana-openapi-client/pull/119),
  [`555122b`](https://github.com/dougborg/katana-openapi-client/commit/555122bbbf45675c0aef0acba6c26872c1b4670b))

- **infra**: Remove Python pip config from Dependabot (uv incompatibility)
  ([#119](https://github.com/dougborg/katana-openapi-client/pull/119),
  [`555122b`](https://github.com/dougborg/katana-openapi-client/commit/555122bbbf45675c0aef0acba6c26872c1b4670b))

### Continuous Integration

- Add path filters to skip CI for docs-only changes
  ([#123](https://github.com/dougborg/katana-openapi-client/pull/123),
  [`722a6f8`](https://github.com/dougborg/katana-openapi-client/commit/722a6f869df737857261c936990a1f5b76ae5b2a))

- Add path filters to skip unnecessary CI runs
  ([#123](https://github.com/dougborg/katana-openapi-client/pull/123),
  [`722a6f8`](https://github.com/dougborg/katana-openapi-client/commit/722a6f869df737857261c936990a1f5b76ae5b2a))

### Documentation

- Add CI, coverage, and docs status badges to README
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- Add CI, coverage, docs, and security status badges to README
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- **client**: Fix inline comment to reflect actual priority order
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

### Features

- **client**: Add netrc support for API authentication
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

- **client**: Add ~/.netrc support for API authentication
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

### Refactoring

- **client**: Address code review feedback
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

- **client**: Improve hostname extraction robustness and type safety
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

- **client**: Improve netrc hostname extraction robustness
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

## v0.29.0 (2025-11-05)

### Bug Fixes

- **client**: Correct BatchCreateBomRowsRequest field name from bom_rows to data
  ([#115](https://github.com/dougborg/katana-openapi-client/pull/115),
  [`5bb9918`](https://github.com/dougborg/katana-openapi-client/commit/5bb9918095c33f06b2502f944b7ae1df708c9dcc))

### Chores

- **release**: Mcp v0.4.0
  ([`c3594e4`](https://github.com/dougborg/katana-openapi-client/commit/c3594e404b660ccd6e06b16dcc133ccae91d5866))

- **release**: Mcp v0.5.0
  ([`0c67647`](https://github.com/dougborg/katana-openapi-client/commit/0c67647906e83400e8df2767547892ba1a6a9736))

### Documentation

- Fix 66 OpenAPI spec example warnings
  ([#116](https://github.com/dougborg/katana-openapi-client/pull/116),
  [`d20997c`](https://github.com/dougborg/katana-openapi-client/commit/d20997c6a8287659ca1ccc7ed4f487e4bd1816fb))

### Features

- **mcp**: Complete unified item CRUD interface
  ([`9c123e3`](https://github.com/dougborg/katana-openapi-client/commit/9c123e3619b9e872d4ce8aa360d11ec6779002f1))

- **mcp**: Migrate to StockTrim architecture with unified item creation
  ([`8645d9d`](https://github.com/dougborg/katana-openapi-client/commit/8645d9dd15dc302b2f64938d8b6f61ce390e13d4))

## v0.28.0 (2025-11-05)

### Bug Fixes

- Address additional review feedback on PR #78
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Address code review feedback from PR #78
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Correct Product converter to use archived_at instead of deleted_at
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Remove reference to non-existent variant.product_or_material_name field
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Update devcontainer and deployment docs with corrected MCP doc references
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Update MCP issue creation scripts to reference new documentation paths
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

### Chores

- **client**: Regenerate client after removing product_or_material_name field
  ([`fa53c7c`](https://github.com/dougborg/katana-openapi-client/commit/fa53c7cedacabe3934c950291acd5fc104fbc898))

### Continuous Integration

- Prevent race conditions in release workflow with proper concurrency control
  ([#109](https://github.com/dougborg/katana-openapi-client/pull/109),
  [`4fc496f`](https://github.com/dougborg/katana-openapi-client/commit/4fc496f06403bc09e094b94513974986b1abb3b9))

### Documentation

- Create AGENT_WORKFLOW.md for AI agent development guide
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Enhance agent coordination guidelines with detailed patterns
  ([#110](https://github.com/dougborg/katana-openapi-client/pull/110),
  [`9478f42`](https://github.com/dougborg/katana-openapi-client/commit/9478f4238b77b79305337393fb1d638577e1e7fd))

- Update copilot-instructions.md and CLAUDE.md with uv and validation tiers
  ([#107](https://github.com/dougborg/katana-openapi-client/pull/107),
  [`9d3c383`](https://github.com/dougborg/katana-openapi-client/commit/9d3c3838ce815d53993e3b39b1ee01c567da7531))

- **mcp**: Add StockTrim architecture migration plan
  ([#112](https://github.com/dougborg/katana-openapi-client/pull/112),
  [`8d081e4`](https://github.com/dougborg/katana-openapi-client/commit/8d081e45cae909543e7cd6a1e754a5c9aca0cd60))

- **mcp**: Reorganize MCP documentation and align issues with v0.1.0 plan
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

### Features

- **client**: Add Product, Material, Service domain models with helper integration
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- **client**: Add Pydantic domain models for ETL and data processing
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- **client**: Add pytest-xdist for parallel test execution
  ([#111](https://github.com/dougborg/katana-openapi-client/pull/111),
  [`c96bee1`](https://github.com/dougborg/katana-openapi-client/commit/c96bee1e83c214097711d622d74b6add2b1854f3))

- **client+mcp**: Add Pydantic domain models for catalog entities
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

## v0.27.0 (2025-10-28)

### Bug Fixes

- Correct incomplete sentence in import comment
  ([#72](https://github.com/dougborg/katana-openapi-client/pull/72),
  [`6d046f2`](https://github.com/dougborg/katana-openapi-client/commit/6d046f239df54d750f8b8a8148e1bbe259e3dd8e))

- **client**: Implement client-side fuzzy search for products
  ([`4fa5907`](https://github.com/dougborg/katana-openapi-client/commit/4fa5907e10a1b3fccc09e33d1bd9f8e7df36a679))

- **client**: Use enum for extend parameter in variant search
  ([`ad36ea9`](https://github.com/dougborg/katana-openapi-client/commit/ad36ea940d06f768cae679b196896c538637ceea))

- **client+mcp**: Handle nested product_or_material object in variant responses
  ([`9dd0251`](https://github.com/dougborg/katana-openapi-client/commit/9dd0251dff9ded3ac05391273c6e4592abda0e23))

- **mcp**: Configure semantic-release to update __init__.py version
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Correct context access pattern to use request_context.lifespan_context
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Correct semantic-release paths for subdirectory execution
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Correct semantic-release paths for subdirectory execution
  ([#74](https://github.com/dougborg/katana-openapi-client/pull/74),
  [`804beee`](https://github.com/dougborg/katana-openapi-client/commit/804beee0843a633a9c6524fd4637fa24b7e4dbd7))

- **mcp**: Extract SKU from first product variant in search results
  ([`d4c8594`](https://github.com/dougborg/katana-openapi-client/commit/d4c8594c3f080ca3795d384f93e35a417a74b9ae))

- **mcp**: Implement proper FastMCP tool registration pattern
  ([`b6aee3c`](https://github.com/dougborg/katana-openapi-client/commit/b6aee3c3ddda9f1998d56d6c60c6865763eb33b4))

- **mcp**: Import tools/resources/prompts modules to register decorators
  ([#70](https://github.com/dougborg/katana-openapi-client/pull/70),
  [`de4eaa2`](https://github.com/dougborg/katana-openapi-client/commit/de4eaa23fe6bc990fff45d2ac92e73ce5211ebe0))

- **mcp**: Register tools with MCP server and release v0.1.0
  ([#70](https://github.com/dougborg/katana-openapi-client/pull/70),
  [`de4eaa2`](https://github.com/dougborg/katana-openapi-client/commit/de4eaa23fe6bc990fff45d2ac92e73ce5211ebe0))

- **mcp**: Use context.server_context instead of context.state
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Use full path to uv and add prerequisites documentation
  ([`a95feb3`](https://github.com/dougborg/katana-openapi-client/commit/a95feb36242b14704e9be222a8eccc394311cd1b))

- **spec**: Remove non-existent product_or_material_name field from Variant schema
  ([`b04fa35`](https://github.com/dougborg/katana-openapi-client/commit/b04fa3539f42dbfc057d77f9a65032fed3557fb1))

### Chores

- Add pytest to pre-commit hooks
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- Remove CLIENT_README.md with Poetry references
  ([#72](https://github.com/dougborg/katana-openapi-client/pull/72),
  [`6d046f2`](https://github.com/dougborg/katana-openapi-client/commit/6d046f239df54d750f8b8a8148e1bbe259e3dd8e))

- Remove generated CLIENT_README.md and stop generating it
  ([#72](https://github.com/dougborg/katana-openapi-client/pull/72),
  [`6d046f2`](https://github.com/dougborg/katana-openapi-client/commit/6d046f239df54d750f8b8a8148e1bbe259e3dd8e))

- Update uv.lock after rebase
  ([`d72fb38`](https://github.com/dougborg/katana-openapi-client/commit/d72fb38ce9a9ee830a2628efef150c9a28a340c3))

- **mcp**: Remove alpha version specifier for v0.1.0 release
  ([#70](https://github.com/dougborg/katana-openapi-client/pull/70),
  [`de4eaa2`](https://github.com/dougborg/katana-openapi-client/commit/de4eaa23fe6bc990fff45d2ac92e73ce5211ebe0))

- **mcp**: Sync version to 0.2.0 in __init__.py
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **release**: Mcp v0.2.0
  ([`59989e8`](https://github.com/dougborg/katana-openapi-client/commit/59989e8c4fdb6e421930907eab3e13b29c36068b))

- **release**: Mcp v0.2.1
  ([`f3ce21e`](https://github.com/dougborg/katana-openapi-client/commit/f3ce21e1ad34fd588ebd6f67d2d2647fde74b63e))

- **release**: Mcp v0.3.0
  ([`70d5546`](https://github.com/dougborg/katana-openapi-client/commit/70d554601285edd00802010b4da537a447f0b1ca))

### Documentation

- **mcp**: Improve comment explaining side-effect imports
  ([#71](https://github.com/dougborg/katana-openapi-client/pull/71),
  [`0910a93`](https://github.com/dougborg/katana-openapi-client/commit/0910a93a5f3b10dbb05d912cb5c14184797309fd))

### Features

- **client**: Add variant search caching with relevance ranking
  ([`754a3c8`](https://github.com/dougborg/katana-openapi-client/commit/754a3c89f22b59da2dbcc546089ea6a6135ad5af))

- **client+mcp**: Format variant names to match Katana UI
  ([`78922b9`](https://github.com/dougborg/katana-openapi-client/commit/78922b9d82f054ac16eda8defb0611df5779f9d9))

- **mcp**: Add Docker support and MCP registry submission materials
  ([#73](https://github.com/dougborg/katana-openapi-client/pull/73),
  [`01f1671`](https://github.com/dougborg/katana-openapi-client/commit/01f1671339eb099ea41e60b1bd17ceef4ec1cfb5))

- **mcp**: Add hot-reload development workflow with mcp-hmr
  ([`0bcc707`](https://github.com/dougborg/katana-openapi-client/commit/0bcc707e80651f9313feb5d6a163d287bd7817c6))

### Refactoring

- Address code review feedback
  ([`5112abb`](https://github.com/dougborg/katana-openapi-client/commit/5112abb66327d3f0c893a5a8487b25eebfe4422f))

- Extract variant display name logic to shared utility
  ([`ed33fc8`](https://github.com/dougborg/katana-openapi-client/commit/ed33fc8cf7671983303da9656cc9ee21d04cf7a4))

- Use generated API models instead of dicts in client helpers
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **client+mcp**: Search variants instead of products
  ([`d22ac02`](https://github.com/dougborg/katana-openapi-client/commit/d22ac0242553b6d94c1a13bd9db55902784029ba))

- **mcp**: Add error handling, logging, and validation to tools
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Use importlib.metadata for version instead of hardcoded string
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

### Testing

- **mcp**: Update inventory tool tests for new interfaces
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

## v0.26.5 (2025-10-27)

### Bug Fixes

- Add Production enum option for InventoryMovement resource_type
  ([#69](https://github.com/dougborg/katana-openapi-client/pull/69),
  [`1962398`](https://github.com/dougborg/katana-openapi-client/commit/196239878edf28e4dd6bc4c75f14f3f2aca45990))

### Chores

- Remove and ignore claude settings file
  ([#69](https://github.com/dougborg/katana-openapi-client/pull/69),
  [`1962398`](https://github.com/dougborg/katana-openapi-client/commit/196239878edf28e4dd6bc4c75f14f3f2aca45990))

## v0.26.4 (2025-10-27)

### Bug Fixes

- Correct MCP artifact upload path
  ([`336fe14`](https://github.com/dougborg/katana-openapi-client/commit/336fe1497c8490e7cefae2d37b5aa9af0968fef4))

## v0.26.3 (2025-10-27)

### Bug Fixes

- Use inputs context instead of github.event.inputs
  ([`78924e5`](https://github.com/dougborg/katana-openapi-client/commit/78924e56e6a6917259992d89129adadaed4ec8f7))

## v0.26.2 (2025-10-27)

### Bug Fixes

- Handle skipped release steps in build conditions
  ([`f565b7a`](https://github.com/dougborg/katana-openapi-client/commit/f565b7ad0a69dd827065985b1f5c1cdad904444d))

## v0.26.1 (2025-10-27)

### Bug Fixes

- Correct boolean comparison in workflow_dispatch conditions
  ([`a4d3c54`](https://github.com/dougborg/katana-openapi-client/commit/a4d3c548a5c5a783ed2e754f09cd4bd67f3df79a))

## v0.26.0 (2025-10-26)

### Bug Fixes

- **mcp**: Correct semantic-release paths for subdirectory execution
  ([`7b4119e`](https://github.com/dougborg/katana-openapi-client/commit/7b4119e2a1ae79ecbc966318ea6d0576d74ac796))

- **mcp**: Use python -m build instead of uv build in semantic-release
  ([`c7071c2`](https://github.com/dougborg/katana-openapi-client/commit/c7071c2d62abe6fb23fad9d4965912501b320419))

- **mcp**: Use same build_command pattern as client - format changelog only
  ([`7603014`](https://github.com/dougborg/katana-openapi-client/commit/760301487546c0e5e4b41fc8d3e97a4519407f0a))

### Chores

- Remove duplicate Release MCP Server workflow
  ([`314c591`](https://github.com/dougborg/katana-openapi-client/commit/314c5917c0dddc5b4a13b77422658ab60c5b0c94))

- **release**: Mcp v0.1.0
  ([`93e2583`](https://github.com/dougborg/katana-openapi-client/commit/93e2583498913d256ded067afab7bc60ebe3c29a))

### Documentation

- Add comprehensive monorepo semantic-release guide
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- Add MCP deployment summary
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- Update all documentation for monorepo semantic-release
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- Update deployment docs and fix release workflow
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- **mcp**: Update DEPLOYMENT.md for automated semantic-release
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

### Features

- Add manual publish triggers for both packages
  ([`29c1377`](https://github.com/dougborg/katana-openapi-client/commit/29c1377db6d7212e7e069cf35112f9165021f180))

- Prepare MCP server v0.1.0a1 for PyPI deployment
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- **mcp**: Configure monorepo semantic-release for independent versioning
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

## v0.25.0 (2025-10-24)

### Bug Fixes

- **client**: Remove invalid root_options parameter from workflow
  ([`8e313f3`](https://github.com/dougborg/katana-openapi-client/commit/8e313f37714af9d7814e088f3e0286c64ca61da9))

### Features

- **mcp**: Add package README for better documentation
  ([`9f9cebf`](https://github.com/dougborg/katana-openapi-client/commit/9f9cebfe86a739993b147b775cfc87439feb4e0b))

## v0.24.0 (2025-10-24)

### Documentation

- Add comprehensive monorepo semantic-release guide
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

- Add MCP deployment summary
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

- Update all documentation for monorepo semantic-release
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

### Features

- Prepare MCP server v0.1.0a1 for PyPI deployment
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

- **mcp**: Configure monorepo semantic-release for independent versioning
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

## v0.23.0 (2025-10-24)

- Initial Release
