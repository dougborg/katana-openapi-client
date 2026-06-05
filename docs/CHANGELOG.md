# CHANGELOG

<!-- version list -->

## v0.79.0 (2026-06-05)

### Bug Fixes

- **client**: Correct misleading ecommerce\_\* field docs + examples
  ([`ff9b769`](https://github.com/dougborg/katana-openapi-client/commit/ff9b769115991c45e9c8071be2af1b96dcea18b5))

### Chores

- Sync uv.lock after release
  ([`257e42d`](https://github.com/dougborg/katana-openapi-client/commit/257e42d6326e539d726b30a6dfb3ff795e7ffb1f))

- Sync uv.lock after release
  ([`683a3ad`](https://github.com/dougborg/katana-openapi-client/commit/683a3ad84f57d5a8fce30a95a1376c0a19c1e441))

- **mcp**: Update client dependency to v0.78.0
  ([`cae9b78`](https://github.com/dougborg/katana-openapi-client/commit/cae9b78d1083059d697cd069b457b177de1570a4))

- **release**: Mcp v0.113.0
  ([`a28bea7`](https://github.com/dougborg/katana-openapi-client/commit/a28bea7b38b3b80ba610a03b2754cb335b47ec3c))

### Features

- **mcp**: Add get_sales_order detail card
  ([`84b6a9b`](https://github.com/dougborg/katana-openapi-client/commit/84b6a9b83d155fb8535333330f002dc77d8a9cae))

### Testing

- **mcp**: Cover get_sales_order detail card + name enrichment
  ([`c39c9ad`](https://github.com/dougborg/katana-openapi-client/commit/c39c9addaedfff50e59737819aab215f93f969c2))

## v0.78.0 (2026-06-05)

### Bug Fixes

- **ci**: Re-lock uv.lock against post-release main so the lock never lags (closes #901)
  ([`26e9272`](https://github.com/dougborg/katana-openapi-client/commit/26e92725d98f515eab1e949ef4b7462dccd55ae4))

- **client**: Constrain create price-list adjustment_method to its enum
  ([`d5b852e`](https://github.com/dougborg/katana-openapi-client/commit/d5b852e9ff647c71a237070259780408384e8a56))

- **client**: Item purchase_uom_conversion_rate is a decimal string
  ([`abdaedb`](https://github.com/dougborg/katana-openapi-client/commit/abdaedb7110331976f3df349f18acb81b77defea))

- **client**: MOOperationRow cost_per_hour/cost_parameter are decimal strings
  ([`6636567`](https://github.com/dougborg/katana-openapi-client/commit/6636567446ca1d1df06eb6b66f65f70722517482))

- **client**: String-quote MOOperationRow cost examples in path responses
  ([`543b065`](https://github.com/dougborg/katana-openapi-client/commit/543b06568114b169e2c7a78c22d7ffb82dbae696))

- **mcp**: Cut modify_manufacturing_order post-apply latency from rate-limit gate
  ([`a21d52d`](https://github.com/dougborg/katana-openapi-client/commit/a21d52d4919407e338fbe4ae62ec03b7853202b4))

- **mcp**: Pin ecommerce template/label key sets at import
  ([`adb80d3`](https://github.com/dougborg/katana-openapi-client/commit/adb80d383e6c8a156178544dba2cccb10840905c))

### Chores

- Sync uv.lock after release
  ([`0c92318`](https://github.com/dougborg/katana-openapi-client/commit/0c92318df3ff6ac1f652aba754dd27f719a14ca2))

- Sync uv.lock after release
  ([`66edc0a`](https://github.com/dougborg/katana-openapi-client/commit/66edc0a03c25d07125e98db897789cb564f51555))

- Sync uv.lock after release
  ([`0b99051`](https://github.com/dougborg/katana-openapi-client/commit/0b990512e7537cd5b403cbd56392b62213e98e41))

- Sync uv.lock after release
  ([`63314d3`](https://github.com/dougborg/katana-openapi-client/commit/63314d325be55b5bc9ad5ac7bd01b8c2ae55dee2))

- **mcp**: Update client dependency to v0.77.0
  ([`aaf41fa`](https://github.com/dougborg/katana-openapi-client/commit/aaf41faa3116f6ce4c16b30bc726592299e48cc6))

- **release**: Mcp v0.110.0
  ([`aef30f9`](https://github.com/dougborg/katana-openapi-client/commit/aef30f94403e5677b849c4da84aeb58a580575fa))

- **release**: Mcp v0.111.0
  ([`fae17a0`](https://github.com/dougborg/katana-openapi-client/commit/fae17a0435dc04be26b254cfee09a9591ae38873))

- **release**: Mcp v0.111.1
  ([`c0bae4a`](https://github.com/dougborg/katana-openapi-client/commit/c0bae4a78296f7fb945b2c3624945a77f3f32a28))

- **release**: Mcp v0.112.0
  ([`da9f25f`](https://github.com/dougborg/katana-openapi-client/commit/da9f25f9e4648ce3b3ff4e0c8c32695fd1ce177c))

### Documentation

- Record Katana's 2026-06-04 response on the serial-fulfillment gap
  ([`24e91e1`](https://github.com/dougborg/katana-openapi-client/commit/24e91e16618301bd5546a1df39182aec93ac0cb2))

- **scripts**: Clarify probe_money_fields scope + portable run example
  ([`8b692f3`](https://github.com/dougborg/katana-openapi-client/commit/8b692f342904927e8db1bf76100e842ac7ca0ec0))

- **scripts**: Correct money-probe coverage + seed wording
  ([`3a3ad3a`](https://github.com/dougborg/katana-openapi-client/commit/3a3ad3a55d2eb610b0ae7ce35c3d4a97ba4c3fef))

### Features

- **mcp**: Create_sales_order accepts status + picked_date
  ([#907](https://github.com/dougborg/katana-openapi-client/pull/907),
  [`222bdb3`](https://github.com/dougborg/katana-openapi-client/commit/222bdb3b9ef0fbe01f2f9097a16dfbde17aa26c1))

- **mcp**: Derive ecommerce storefront deep-links for sales orders
  ([`9fdcd52`](https://github.com/dougborg/katana-openapi-client/commit/9fdcd520ccdb60f105ce8b1c2ec988b8786c0f0e))

- **ts-client**: Port Ajv-style 422 errors + proactive rate limiting
  ([`91cccdd`](https://github.com/dougborg/katana-openapi-client/commit/91cccdde082cf0c1e03c5dacd74fe474bdc9f5a8))

### Performance Improvements

- **mcp**: Extend parent_from_outcome to modify_item + header-only modify_sales_order
  ([`2ca96ac`](https://github.com/dougborg/katana-openapi-client/commit/2ca96acecfcdd9ef0fa5a2bbe02e436b063fb0b0))

### Refactoring

- Address review — int in coalesce signature, read-side seed samples
  ([`ed365be`](https://github.com/dougborg/katana-openapi-client/commit/ed365be05d473f6689d9e317bf5f1018d0e86d2d))

- Empty-string guard in coalesce + env-overridable seed fixtures
  ([`944c0eb`](https://github.com/dougborg/katana-openapi-client/commit/944c0ebe10d35fb8af6b2fcb1d7516d3dae59e8f))

- **client**: Consolidate duplicate price-list adjustment-method enums
  ([`2451c34`](https://github.com/dougborg/katana-openapi-client/commit/2451c34f83ce25e593a140c03bda10eb58729c16))

- **scripts**: Make seed cleanup resilient to malformed ledger lines
  ([`530946d`](https://github.com/dougborg/katana-openapi-client/commit/530946db35c4a7fa480a12a1b716c4bedd415634))

- **scripts**: Route money-field probes through make_test_client
  ([`2c571e2`](https://github.com/dougborg/katana-openapi-client/commit/2c571e2bf3165ac9f0c08a9fc047bfc3954e801c))

## v0.77.0 (2026-06-03)

### Bug Fixes

- **client**: Align POST /bom_rows + GET /bin_locations response shapes with live API
  ([`4932cb7`](https://github.com/dougborg/katana-openapi-client/commit/4932cb70ddcf66f03cfa4a6fe8751ca7db972960))

- **client**: Regenerate TS client for the spec changes + gate it; use
  StorageBinResponse for bin_locations items
  ([`495ef8f`](https://github.com/dougborg/katana-openapi-client/commit/495ef8f79438979cb9ff320cd8f347c91aef5250))

- **mcp**: Verify archival + wire-vs-literal status in make_response_verifier
  ([`a95302b`](https://github.com/dougborg/katana-openapi-client/commit/a95302bb2c85e74a9b95d3c517622aea0657f52b))

### Chores

- Sync root uv.lock to katana-openapi-client 0.76.0
  ([#895](https://github.com/dougborg/katana-openapi-client/pull/895),
  [`0f6784e`](https://github.com/dougborg/katana-openapi-client/commit/0f6784e39a77d4fefda6d96f6f615e8010ada3f3))

- Sync uv.lock to katana_mcp_server 0.109.0
  ([`3881360`](https://github.com/dougborg/katana-openapi-client/commit/38813608f9d2b217d7746e1bc3700920f93a7a34))

- **mcp**: Update client dependency to v0.76.0
  ([`0967896`](https://github.com/dougborg/katana-openapi-client/commit/0967896ab3a6caf6efc2caa5ea7ab0db7a5e04f1))

- **release**: Mcp v0.109.0
  ([`b0c714c`](https://github.com/dougborg/katana-openapi-client/commit/b0c714c27e0663242a122a1ffa39d213630359d2))

### Continuous Integration

- Gate the TypeScript client functionally instead of by byte-diff
  ([`97ae3d9`](https://github.com/dougborg/katana-openapi-client/commit/97ae3d903df59fa3fe525dd5d5e4c1a1ae611d72))

- **integration**: Live-integration.yml workflow (#837 Phase 3)
  ([#895](https://github.com/dougborg/katana-openapi-client/pull/895),
  [`0f6784e`](https://github.com/dougborg/katana-openapi-client/commit/0f6784e39a77d4fefda6d96f6f615e8010ada3f3))

### Documentation

- Correct generate-ts comment — TS codegen is not byte-deterministic across OS
  ([`222b05b`](https://github.com/dougborg/katana-openapi-client/commit/222b05b82870bea455b66e804273d239373d6c22))

- Scope the "don't monkeypatch datetime" warning to code under test (review)
  ([#894](https://github.com/dougborg/katana-openapi-client/pull/894),
  [`b2ef1d2`](https://github.com/dougborg/katana-openapi-client/commit/b2ef1d2b599954c0a372b49233ee02acdf0ee3a5))

- **escalations**: Consolidate serial-fulfillment gap; add minimal-request matrix
  ([#900](https://github.com/dougborg/katana-openapi-client/pull/900),
  [`3a96d35`](https://github.com/dougborg/katana-openapi-client/commit/3a96d35adc2e429d8047c04a076834acd0e3352c))

- **escalations**: Refine serial-fulfillment gap with UI-traced ledger lifecycle
  ([#900](https://github.com/dougborg/katana-openapi-client/pull/900),
  [`3a96d35`](https://github.com/dougborg/katana-openapi-client/commit/3a96d35adc2e429d8047c04a076834acd0e3352c))

- **escalations**: Refine serial-fulfillment gap with UI-traced ledger lifecycle (#784)
  ([#900](https://github.com/dougborg/katana-openapi-client/pull/900),
  [`3a96d35`](https://github.com/dougborg/katana-openapi-client/commit/3a96d35adc2e429d8047c04a076834acd0e3352c))

### Refactoring

- **mcp**: Migrate SO modify sub-entities to columnar DataTables (closes #721)
  ([`7976987`](https://github.com/dougborg/katana-openapi-client/commit/7976987a362506e4edbb56440a1fb16f681cff10))

### Testing

- Address review on the fake-time sweep
  ([#894](https://github.com/dougborg/katana-openapi-client/pull/894),
  [`b2ef1d2`](https://github.com/dougborg/katana-openapi-client/commit/b2ef1d2b599954c0a372b49233ee02acdf0ee3a5))

- Fake time in all time-based tests; never read the real wall clock
  ([#894](https://github.com/dougborg/katana-openapi-client/pull/894),
  [`b2ef1d2`](https://github.com/dougborg/katana-openapi-client/commit/b2ef1d2b599954c0a372b49233ee02acdf0ee3a5))

- Remove hollow never-wired-mock tests from test_performance (closes #897)
  ([#902](https://github.com/dougborg/katana-openapi-client/pull/902),
  [`ca843ac`](https://github.com/dougborg/katana-openapi-client/commit/ca843ac44b901db06688c6d34bc264d408923f93))

- **mcp**: Drop redundant cache syncs in live smoke tests (#837 follow-up)
  ([#899](https://github.com/dougborg/katana-openapi-client/pull/899),
  [`def1adc`](https://github.com/dougborg/katana-openapi-client/commit/def1adca216ae8d922b2fbd26f83d138c037ab72))

- **mcp**: Live MCP-server smoke tests + workflow job (#837 Phase 4)
  ([#898](https://github.com/dougborg/katana-openapi-client/pull/898),
  [`f52cbc9`](https://github.com/dougborg/katana-openapi-client/commit/f52cbc92f4e6938c18f3694273c16b0e59ab9cd2))

## v0.76.0 (2026-06-02)

### Bug Fixes

- **client**: Align custom-fields surface with Katana's live API
  ([#893](https://github.com/dougborg/katana-openapi-client/pull/893),
  [`a8fdc6d`](https://github.com/dougborg/katana-openapi-client/commit/a8fdc6dd9e5d6db0eef112a08d3b3baba9e2ad72))

- **client**: Align custom-fields surface with Katana's live API (#805)
  ([#893](https://github.com/dougborg/katana-openapi-client/pull/893),
  [`a8fdc6d`](https://github.com/dougborg/katana-openapi-client/commit/a8fdc6dd9e5d6db0eef112a08d3b3baba9e2ad72))

- **client**: Regenerate CustomFieldDefinition after merging v0.74.0
  ([#893](https://github.com/dougborg/katana-openapi-client/pull/893),
  [`a8fdc6d`](https://github.com/dougborg/katana-openapi-client/commit/a8fdc6dd9e5d6db0eef112a08d3b3baba9e2ad72))

### Chores

- Sync root uv.lock to katana-mcp-server 0.108.0
  ([`2caf250`](https://github.com/dougborg/katana-openapi-client/commit/2caf250dcd9f3f3a7bb072982d3f39fa256f9a98))

### Testing

- **client**: Address PR #889 review — live marker + typed skip exception
  ([`f306818`](https://github.com/dougborg/katana-openapi-client/commit/f3068184edb80ce2ead426967f2346fb19397e17))

- **client**: Live-tenant integration scaffolding — tests/integration/ (#837 Phase 2)
  ([`728f5cf`](https://github.com/dougborg/katana-openapi-client/commit/728f5cf6406fd3ac1ee8433bf51e4c120dddf4b2))

## v0.75.0 (2026-06-02)

### Bug Fixes

- **client**: Declare ServiceVariant.sku as nullable to match wire contract
  ([#892](https://github.com/dougborg/katana-openapi-client/pull/892),
  [`e1fc86b`](https://github.com/dougborg/katana-openapi-client/commit/e1fc86bb98381dde526c134adb20063aeff82c3c))

### Chores

- **release**: Mcp v0.108.0
  ([`99f4dae`](https://github.com/dougborg/katana-openapi-client/commit/99f4dae104a4fbf2b64c832f835428d43def3adb))

### Documentation

- Clean up null-SKU pitfall test list formatting (review)
  ([#892](https://github.com/dougborg/katana-openapi-client/pull/892),
  [`e1fc86b`](https://github.com/dougborg/katana-openapi-client/commit/e1fc86bb98381dde526c134adb20063aeff82c3c))

- Mark serial-fulfillment escalation submitted + caveat fulfill_order
  ([`92313d9`](https://github.com/dougborg/katana-openapi-client/commit/92313d983ece1cabcc4adf3a1b183a0e4ef6348f))

- **mcp**: Drop internal repo path from fulfill_order serial-gap caveat
  ([`c7d47c9`](https://github.com/dougborg/katana-openapi-client/commit/c7d47c9cc2ceedd8e6d56e4e289eda2a83c0db20))

### Features

- **mcp**: Stock-transfer modify card; retire generic ActionResult cards (refs #721)
  ([`cb643b1`](https://github.com/dougborg/katana-openapi-client/commit/cb643b169c03fbc86db1a10187b351fd8d7e6f1f))

### Breaking Changes

- **mcp**: Build_modification_preview_ui and build_modification_result_ui are removed.
  Any caller rendering a ModificationResponse must route through to_tool_result, which
  dispatches to the per-entity build\_<entity>\_modify_ui.

## v0.74.0 (2026-06-02)

### Bug Fixes

- **client**: Construct model_config as SQLModelConfig for ty 0.0.42
  ([`34ba6ac`](https://github.com/dougborg/katana-openapi-client/commit/34ba6aca88e4ced10ab45b4a623ecaf40644f05a))

- **mcp**: Paginate DataTables only when rows overflow one page
  ([`ce9368c`](https://github.com/dougborg/katana-openapi-client/commit/ce9368ccfaaf4980505f2092ca3158ac82cc6406))

### Chores

- Regenerate client + pydantic models for codegen bump
  ([`f3e537f`](https://github.com/dougborg/katana-openapi-client/commit/f3e537f5c0fbcb11430da969b3b2d87798c8c540))

- **deps**: Drop now-redundant direct python-dateutil dependency
  ([`1993334`](https://github.com/dougborg/katana-openapi-client/commit/199333428bd2511df42b8bd2ce92d88355a0681a))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 9 updates
  ([`190f6c1`](https://github.com/dougborg/katana-openapi-client/commit/190f6c10171f7012a3caa5f386b762a5ec83e7c0))

- **mcp**: Update client dependency to v0.73.0
  ([`a450018`](https://github.com/dougborg/katana-openapi-client/commit/a4500188fefc2cceee5d97066f00ac32a8a1ed53))

- **release**: Mcp v0.107.0
  ([`372a2d7`](https://github.com/dougborg/katana-openapi-client/commit/372a2d79a176c74bbcb3f7169ec1eff51e43ca6e))

- **release**: Mcp v0.107.1
  ([`4dd40a4`](https://github.com/dougborg/katana-openapi-client/commit/4dd40a4a5304a75320a3c0f17ac4739e1d1f211b))

### Documentation

- **escalations**: Public-API gap — serial-tracked make-to-order SO fulfillment
  ([#784](https://github.com/dougborg/katana-openapi-client/pull/784),
  [`40af388`](https://github.com/dougborg/katana-openapi-client/commit/40af3880c35b8fb05dab8c06876dd32a27f3b5ca))

### Features

- **mcp**: Diff-decorated MO modify/delete card (refs #721)
  ([`69e89c2`](https://github.com/dougborg/katana-openapi-client/commit/69e89c2587b22d4ffd15b840bb00e5e48d035b76))

### Testing

- **mcp**: Cover MO modify card + three collection tables
  ([`caf4638`](https://github.com/dougborg/katana-openapi-client/commit/caf46382f04af82aa31853d3a03e275dca055b2c))

## v0.73.0 (2026-06-01)

### Bug Fixes

- **client**: Make ManufacturingOrder.production_deadline_date nullable
  ([`f68e6da`](https://github.com/dougborg/katana-openapi-client/commit/f68e6da2882e6e084a987127e411dc8c8966716b))

- **mcp**: Return parent_id from search_items so item CRUD gets the right id
  ([`01aa81a`](https://github.com/dougborg/katana-openapi-client/commit/01aa81a4c5233ad70cf3bf4e83d8ffe4dd749336))

- **mcp**: Truthful serial-tracked SO block message + close-out discoverability
  ([`a2c5cff`](https://github.com/dougborg/katana-openapi-client/commit/a2c5cff74d35143ce2b033416f2ed872257bdf70))

### Chores

- **mcp**: Update client dependency to v0.72.1
  ([`6b24a4b`](https://github.com/dougborg/katana-openapi-client/commit/6b24a4b552ee040e5314f59a86fe7ca8d59155d3))

- **release**: Mcp v0.100.0
  ([`dadb283`](https://github.com/dougborg/katana-openapi-client/commit/dadb283a886f7b8d117b8f0517c913326dab0d6a))

- **release**: Mcp v0.100.1
  ([`e430344`](https://github.com/dougborg/katana-openapi-client/commit/e430344e27fe2f021d8d24927244809b2367e0d7))

- **release**: Mcp v0.101.0
  ([`52d729b`](https://github.com/dougborg/katana-openapi-client/commit/52d729b4963ab65ad3d7fa93c753235c757652c1))

- **release**: Mcp v0.102.0
  ([`a5f87cd`](https://github.com/dougborg/katana-openapi-client/commit/a5f87cde724ab056f25d467c59cc1f48ae6256ab))

- **release**: Mcp v0.103.0
  ([`9beb3b2`](https://github.com/dougborg/katana-openapi-client/commit/9beb3b2dd74e3f147f3081442bd6a6f791183638))

- **release**: Mcp v0.104.0
  ([`0d9adb4`](https://github.com/dougborg/katana-openapi-client/commit/0d9adb42b4855c4305633d163df2d5be2b7e1fcd))

- **release**: Mcp v0.105.0
  ([`5151de5`](https://github.com/dougborg/katana-openapi-client/commit/5151de5f6ab71cfc9f51fbe4394c31aa0fa7bb48))

- **release**: Mcp v0.105.1
  ([`f15602c`](https://github.com/dougborg/katana-openapi-client/commit/f15602c9ae97b60376c7f7ba31b2d80b2d7bc155))

- **release**: Mcp v0.106.0
  ([`cdb2c19`](https://github.com/dougborg/katana-openapi-client/commit/cdb2c1943df15099e6c9d27e804b14f6cdefb5f2))

### Continuous Integration

- Broaden generated-file freshness check to the whole client package
  ([`06023f4`](https://github.com/dougborg/katana-openapi-client/commit/06023f423fa6bca406fa9033f7856df43f0aa692))

- Pin codegen tools exactly + guard generated-file freshness
  ([`992379f`](https://github.com/dougborg/katana-openapi-client/commit/992379fc2261ce061354f5f94096aad53279c0e3))

### Documentation

- **harness**: Teach card-review the thin-DTO / single-row-table anti-pattern
  ([`10ed2e1`](https://github.com/dougborg/katana-openapi-client/commit/10ed2e1bb7aa200c3a8809ba15d3232c413e80e0))

- **mcp**: Address #882 review round 2 — self-contained, copy-pasteable examples
  ([`6aade0f`](https://github.com/dougborg/katana-openapi-client/commit/6aade0f96545529a53f06241d4974ea5812244ab))

- **mcp**: Address #882 review — accurate group_id guidance, truthful caveat framing
  ([`400654b`](https://github.com/dougborg/katana-openapi-client/commit/400654bd12f903183a20cbf130310dde0eb96ead))

- **mcp**: Reconcile add_serial_numbers transfer contract with the MO-linked limitation
  ([`1163875`](https://github.com/dougborg/katana-openapi-client/commit/11638758bf7f142ea223cc07b2dfda96ed5f7370))

- **typed-cache**: Document the preserve-on-conflict contract
  ([`254658a`](https://github.com/dougborg/katana-openapi-client/commit/254658a41b483122326e172985be7e33500bb4aa))

### Features

- **harness**: Add /card-review skill for prefab UI UX audit
  ([`c787b70`](https://github.com/dougborg/katana-openapi-client/commit/c787b70651d6d5b0fd79b8e641380f0467007567))

- **mcp**: Default create_purchase_order to DRAFT status
  ([`b7d77b0`](https://github.com/dougborg/katana-openapi-client/commit/b7d77b0552fd3131566631ca29c65d6c80ccb154))

- **mcp**: Denormalize service_id onto CachedVariant; drop search_items O(N) scan
  ([`367cc2b`](https://github.com/dougborg/katana-openapi-client/commit/367cc2bad803880cbc31d95d6348e8d5cd38a3fe))

- **mcp**: Diff-decorated item modify/delete card (closes #726)
  ([`3ec8020`](https://github.com/dougborg/katana-openapi-client/commit/3ec8020d4183adaa87e94cbd58d237e18210ac25))

- **mcp**: Make CachedVariant.service_id durable; drop search_items re-read
  ([`2a1a2de`](https://github.com/dougborg/katana-openapi-client/commit/2a1a2de3188701548158875c46298168d8e03cd9))

- **mcp**: Redesign create-item card to four-tier framework
  ([`617a567`](https://github.com/dougborg/katana-openapi-client/commit/617a567e01a8ca3b393761a6679d79b57b3cadd5))

- **mcp**: Render PO line-item diff table in the modify card (refs #721)
  ([`a7d2659`](https://github.com/dougborg/katana-openapi-client/commit/a7d26594bbb238e5f6466f00a108aca39b599fae))

- **mcp**: Thread diff overlay through the item entity view
  ([`e389a61`](https://github.com/dougborg/katana-openapi-client/commit/e389a61cc25d0e92eb76e7e847df8e1dd2392235))

- **mcp**: User-centric content on prefab UI cards (closes #861)
  ([`d06f239`](https://github.com/dougborg/katana-openapi-client/commit/d06f2391d6e7ef9150c308dd2a700962920cea8a))

### Refactoring

- **mcp**: Extract reusable collection-diff element from the BOM modify card
  ([`aa5b909`](https://github.com/dougborg/katana-openapi-client/commit/aa5b90982c6a549941ce6bd3edd873e2c80a05c0))

### Testing

- **mcp**: Cover item modify card + variant diff-table
  ([`19b56dc`](https://github.com/dougborg/katana-openapi-client/commit/19b56dcbd11a2896684b53561afcded4286cf851))

- **mcp**: Cover PO line-item diff table + browser render
  ([`5dc79c8`](https://github.com/dougborg/katana-openapi-client/commit/5dc79c85538e6ed6e803560729a3ac27b4503178))

### Breaking Changes

- **client**: `ManufacturingOrder.production_deadline_date` is now
  `datetime | None | Unset` (was `datetime | Unset`). Consumers that assumed a non-null
  datetime must handle None.

## v0.72.1 (2026-05-28)

### Bug Fixes

- **client**: POST /outsourced_purchase_order_recipe_rows returns 200, not 201
  ([`862d584`](https://github.com/dougborg/katana-openapi-client/commit/862d584db81943237f98b3ea085d250063c8d2b5))

### Chores

- **mcp**: Update client dependency to v0.72.0
  ([`641ce42`](https://github.com/dougborg/katana-openapi-client/commit/641ce424aae059b24bd0b00a315d1a8ac5474bd8))

## v0.72.0 (2026-05-28)

### Bug Fixes

- **client**: Correct POST create status codes — Katana returns 200, not 201
  ([`c766fd8`](https://github.com/dougborg/katana-openapi-client/commit/c766fd85ccb9c89091f9f85b974fc9451e272715))

### Chores

- **release**: Mcp v0.99.0
  ([`0dff9f8`](https://github.com/dougborg/katana-openapi-client/commit/0dff9f8a648a56b2772d18bc16071403e4e1249a))

### Features

- **mcp**: Build_so_modify_ui — diff-decorated SO modify card (closes #723)
  ([`f030742`](https://github.com/dougborg/katana-openapi-client/commit/f030742a671f4b0c34089775f9678f2dfce94c28))

## v0.71.0 (2026-05-27)

### Bug Fixes

- **mcp**: Fulfill_order preview Confirm now propagates completed_at / serials / etc —
  closes #845
  ([`1c306d4`](https://github.com/dougborg/katana-openapi-client/commit/1c306d4e028a1c6b2d3d1a608e04686f6b2b80bb))

### Chores

- **mcp**: Update client dependency to v0.70.0
  ([`e0c8dde`](https://github.com/dougborg/katana-openapi-client/commit/e0c8dde33d98c2898d26efc16ad71b1ad443b31f))

- **release**: Mcp v0.94.0
  ([`448adc7`](https://github.com/dougborg/katana-openapi-client/commit/448adc734d427060d8ef712d43a0db6cf0b4d932))

- **release**: Mcp v0.95.0
  ([`dcb0aee`](https://github.com/dougborg/katana-openapi-client/commit/dcb0aee397b265f322c3bbfd65871664575a30df))

- **release**: Mcp v0.96.0
  ([`bbba231`](https://github.com/dougborg/katana-openapi-client/commit/bbba2317d151ec493e150b0d41c0d4a91cf159b3))

- **release**: Mcp v0.97.0
  ([`760dabe`](https://github.com/dougborg/katana-openapi-client/commit/760dabe048b1c6841091ae355544313049a8ce65))

- **release**: Mcp v0.98.0
  ([`f18054e`](https://github.com/dougborg/katana-openapi-client/commit/f18054e0b3bee57e2c3b52b086d1a448bfdffadb))

### Features

- **client**: Add make_test_client() helper for live-tenant integration testing
  ([`6cde5b4`](https://github.com/dougborg/katana-openapi-client/commit/6cde5b4c002eaacb530376f446c177238243d57d))

- **mcp**: Add sub-step timing to \_modify_manufacturing_order_impl
  ([`880d027`](https://github.com/dougborg/katana-openapi-client/commit/880d02760a439a9497bd6ba223f6af0487f28a81))

- **mcp**: Build_bom_modify_ui — per-row diff-decorated BOM modify card (closes #811)
  ([`170fba6`](https://github.com/dougborg/katana-openapi-client/commit/170fba69b9ab51503d9e5dd3748981d8ff166b6e))

- **mcp**: Consistent soft-state defaults across direct-lookup + list tools
  ([`4fa2eb0`](https://github.com/dougborg/katana-openapi-client/commit/4fa2eb02b21f067a914ddc680bca546033d93dad))

- **mcp**: Create_sales_order accepts shipping fees inline
  ([`70d0575`](https://github.com/dougborg/katana-openapi-client/commit/70d057579c1b9541be200f56ee86d8185c21b358))

### Refactoring

- **mcp**: Extract BOM table-merge helpers into shared bom_table module (closes #850)
  ([`4ac739a`](https://github.com/dougborg/katana-openapi-client/commit/4ac739abc985a4ea47e076d98a89d7a98e26a0f4))

## v0.70.0 (2026-05-26)

### Bug Fixes

- **client**: Align /serial_numbers spec with live wire shape
  ([#791](https://github.com/dougborg/katana-openapi-client/pull/791),
  [`45e01f1`](https://github.com/dougborg/katana-openapi-client/commit/45e01f12703fc776b23a2b93a8769e4190e887a4))

- **client**: ServiceVariant.custom_fields nullable to fix create_item(type=service)
  ([`c2898d8`](https://github.com/dougborg/katana-openapi-client/commit/c2898d8ae0ea74f3d629f06205b9dae8d416d0e7))

- **mcp**: Add identifying context to fulfill-card warning logs
  ([#799](https://github.com/dougborg/katana-openapi-client/pull/799),
  [`bd052bb`](https://github.com/dougborg/katana-openapi-client/commit/bd052bbdcac5ae721661a9a7edde4b953ad545d8))

- **mcp**: Add Prefab UI cards to get_product_bom + get_variant_details batch — closes
  #810
  ([`d077e84`](https://github.com/dougborg/katana-openapi-client/commit/d077e84eb6f59ed9828efe3ccc679306a5fd07c6))

- **mcp**: Address code review on batch recipe diff overlay
  ([#798](https://github.com/dougborg/katana-openapi-client/pull/798),
  [`10c8ca5`](https://github.com/dougborg/katana-openapi-client/commit/10c8ca59d75366a9a3263871a55470d6948b67a2))

- **mcp**: Address code review on fulfill card redesign
  ([#799](https://github.com/dougborg/katana-openapi-client/pull/799),
  [`bd052bb`](https://github.com/dougborg/katana-openapi-client/commit/bd052bbdcac5ae721661a9a7edde4b953ad545d8))

- **mcp**: Address code review on fulfill card redesign (#553)
  ([#799](https://github.com/dougborg/katana-openapi-client/pull/799),
  [`bd052bb`](https://github.com/dougborg/katana-openapi-client/commit/bd052bbdcac5ae721661a9a7edde4b953ad545d8))

- **mcp**: Address Copilot review on recipe diff overlay
  ([#798](https://github.com/dougborg/katana-openapi-client/pull/798),
  [`10c8ca5`](https://github.com/dougborg/katana-openapi-client/commit/10c8ca59d75366a9a3263871a55470d6948b67a2))

- **mcp**: Address review on low_stock metric scope and cache flags
  ([`fe78618`](https://github.com/dougborg/katana-openapi-client/commit/fe78618ed29cba54c8d10b6b28c56548364b181f))

- **mcp**: Cap get_inventory_movements rows via max_items extension
  ([#776](https://github.com/dougborg/katana-openapi-client/pull/776),
  [`ef402a9`](https://github.com/dougborg/katana-openapi-client/commit/ef402a966eb9b2a0d8aabc57120df78191a4328b))

- **mcp**: Clamp inventory_movements per-page limit to Katana's 250 max (#771 follow-up)
  ([#776](https://github.com/dougborg/katana-openapi-client/pull/776),
  [`ef402a9`](https://github.com/dougborg/katana-openapi-client/commit/ef402a966eb9b2a0d8aabc57120df78191a4328b))

- **mcp**: Filter soft-deleted child rows from list\_<entity> reads (refs #803)
  ([`808b03d`](https://github.com/dougborg/katana-openapi-client/commit/808b03d3b76f90d376ec0fc601976cc6956aa145))

- **mcp**: Flip customer-card currency badge to secondary variant
  ([`5b2656e`](https://github.com/dougborg/katana-openapi-client/commit/5b2656e5a03cfe8a58fdc74b08809df7c1b319e3))

- **mcp**: Land MO header status transitions in lock-safe order
  ([#774](https://github.com/dougborg/katana-openapi-client/pull/774),
  [`0a30cc4`](https://github.com/dougborg/katana-openapi-client/commit/0a30cc4116a8e6f2bf78b9e4c2d78c052ccb567b))

- **mcp**: Land MO header status transitions in lock-safe order (#773)
  ([#774](https://github.com/dougborg/katana-openapi-client/pull/774),
  [`0a30cc4`](https://github.com/dougborg/katana-openapi-client/commit/0a30cc4116a8e6f2bf78b9e4c2d78c052ccb567b))

- **mcp**: Manage_product_bom commits every row in batch — close #809
  ([`b0329e7`](https://github.com/dougborg/katana-openapi-client/commit/b0329e74e172d08df1632841882749ec91fb4b8f))

- **mcp**: Narrow MatchResult perfect-status invariant on null prices
  ([`d8a20e4`](https://github.com/dougborg/katana-openapi-client/commit/d8a20e43dc2dd8ba0d3797a009401c7319dd732c))

- **mcp**: Overlay PATCH response on cache merge to defeat read-replica lag
  ([`d20eb06`](https://github.com/dougborg/katana-openapi-client/commit/d20eb065960537a41172ce0e6a84dde8b4bbbae1))

- **mcp**: Preserve None for missing PO values + correct metric docstring
  ([`5d1991b`](https://github.com/dougborg/katana-openapi-client/commit/5d1991b21dcf7277ae7b25e6ee602526c10bdfc3))

- **mcp**: Reconcile child rows on parent sync (closes #803)
  ([`5e70f84`](https://github.com/dougborg/katana-openapi-client/commit/5e70f84f9a0c244ab84532d2340e75c5bd79381a))

- **mcp**: Sync parent + supplier caches for low_stock_items enrichment
  ([`5154ac1`](https://github.com/dougborg/katana-openapi-client/commit/5154ac17d462c32d60c4e232cc6d24216dcd14d0))

- **mcp**: Use OpenLink for View-in-Katana per file convention
  ([`87e320e`](https://github.com/dougborg/katana-openapi-client/commit/87e320e92ab1ac7dedbbf6f5056289097b54b63a))

- **mcp**: Use trendSentiment alias on Metric for type-check parity
  ([`5564295`](https://github.com/dougborg/katana-openapi-client/commit/556429585c877cc9a2f9f1a8dbea0276a6e502fb))

- **scripts**: Address #795 review threads missed at merge time
  ([#800](https://github.com/dougborg/katana-openapi-client/pull/800),
  [`519cdd8`](https://github.com/dougborg/katana-openapi-client/commit/519cdd8275ac6542079fb7382decd36caf97e780))

- **tests**: Type extractable[] via TypedDict to satisfy ty inference
  ([`1555956`](https://github.com/dougborg/katana-openapi-client/commit/15559560443ab13fc4e002c7e3ce940ba5b88eae))

### Chores

- Sync uv.lock after merge of main into review-followup branch
  ([#799](https://github.com/dougborg/katana-openapi-client/pull/799),
  [`bd052bb`](https://github.com/dougborg/katana-openapi-client/commit/bd052bbdcac5ae721661a9a7edde4b953ad545d8))

- Sync uv.lock after rebase onto main
  ([#798](https://github.com/dougborg/katana-openapi-client/pull/798),
  [`10c8ca5`](https://github.com/dougborg/katana-openapi-client/commit/10c8ca59d75366a9a3263871a55470d6948b67a2))

- Sync uv.lock with release-bot v0.86.0 bump
  ([#791](https://github.com/dougborg/katana-openapi-client/pull/791),
  [`45e01f1`](https://github.com/dougborg/katana-openapi-client/commit/45e01f12703fc776b23a2b93a8769e4190e887a4))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 8 updates
  ([`1dadbe3`](https://github.com/dougborg/katana-openapi-client/commit/1dadbe3f12b72e84e2cb384258f3301d44275b13))

- **mcp**: Update client dependency to v0.69.0
  ([`d4b680e`](https://github.com/dougborg/katana-openapi-client/commit/d4b680e2d5adf3f19534ee25b6b94bda6230b239))

- **release**: Mcp v0.82.0
  ([`2d27b44`](https://github.com/dougborg/katana-openapi-client/commit/2d27b4402bd4ee1b83093fca75678955cb52db57))

- **release**: Mcp v0.83.0
  ([`a24a039`](https://github.com/dougborg/katana-openapi-client/commit/a24a039763c2678e8b19128daacaddaed507bfc4))

- **release**: Mcp v0.84.0
  ([`95dfeda`](https://github.com/dougborg/katana-openapi-client/commit/95dfedab6e4ec04fc581c993b97416b395b5a5db))

- **release**: Mcp v0.85.0
  ([`077e1ae`](https://github.com/dougborg/katana-openapi-client/commit/077e1ae4674c2c46e18052526398afb10fe8fe6e))

- **release**: Mcp v0.86.0
  ([`e862d80`](https://github.com/dougborg/katana-openapi-client/commit/e862d80bf1598d2fa984cc30138824636a06eb60))

- **release**: Mcp v0.87.0
  ([`fbadf79`](https://github.com/dougborg/katana-openapi-client/commit/fbadf79286854a8d47e1665581d5b841464fd78f))

- **release**: Mcp v0.87.1
  ([`60862d5`](https://github.com/dougborg/katana-openapi-client/commit/60862d54769a29f1c0f7d7c14d8fda32ba64aaf5))

- **release**: Mcp v0.88.0
  ([`6e7f064`](https://github.com/dougborg/katana-openapi-client/commit/6e7f0647178ee586cd64c559d9f17d6cec1a7cd9))

- **release**: Mcp v0.89.0
  ([`5795ccc`](https://github.com/dougborg/katana-openapi-client/commit/5795ccc4af3a2071caddb1240b535a40dd49ff95))

- **release**: Mcp v0.90.0
  ([`83d2103`](https://github.com/dougborg/katana-openapi-client/commit/83d2103479370d24e498ae768fb5d61f79a72770))

- **release**: Mcp v0.90.1
  ([`3c38895`](https://github.com/dougborg/katana-openapi-client/commit/3c388955f867940827c9d448d45f85d62ab1ef1f))

- **release**: Mcp v0.91.0
  ([`c22da75`](https://github.com/dougborg/katana-openapi-client/commit/c22da75422e8807ba3c79954082fffd8b2e40535))

- **release**: Mcp v0.92.0
  ([`6af1db3`](https://github.com/dougborg/katana-openapi-client/commit/6af1db387096ff8d90a192a75984a1eff474b1ad))

- **release**: Mcp v0.92.1
  ([`202daac`](https://github.com/dougborg/katana-openapi-client/commit/202daace079a1c604c745427cab710854facdbc8))

- **release**: Mcp v0.93.0
  ([`62b778c`](https://github.com/dougborg/katana-openapi-client/commit/62b778c6a352f5b1abd76462cdeb51d4ef9bc1d2))

- **release**: Mcp v0.93.1
  ([`288b1ec`](https://github.com/dougborg/katana-openapi-client/commit/288b1ec1a7bdadd6609518e40963a4b9e8fdefd4))

- **release**: Mcp v0.93.2
  ([`b09f6c9`](https://github.com/dougborg/katana-openapi-client/commit/b09f6c9b34398ee58e4f36aae6a370704d496982))

- **release**: Mcp v0.93.3
  ([`cebf5a7`](https://github.com/dougborg/katana-openapi-client/commit/cebf5a76e4b6a51373dbe9ec739b38f353d4023d))

- **spec-drift**: Live probe for POST /bom_rows response shape
  ([#820](https://github.com/dougborg/katana-openapi-client/pull/820),
  [`6b8e3ca`](https://github.com/dougborg/katana-openapi-client/commit/6b8e3caab3bbaf5119b6fcc644986c453f0681c1))

- **spec-drift**: Refresh upstream specs to 2026-05-26 — custom-fields search shipped
  ([`74ab539`](https://github.com/dougborg/katana-openapi-client/commit/74ab53930098e401fcf60fee3d7aba8474f51865))

### Documentation

- **adr**: Add ADR-0021 unified direct-apply rail; supersede ADR-0015
  ([`2993eed`](https://github.com/dougborg/katana-openapi-client/commit/2993eed2836358d8aae0f798c46ad0fcb5769f04))

- **groom**: Add Custom-fields workstream + schema-mutation guardrail
  ([`20a2769`](https://github.com/dougborg/katana-openapi-client/commit/20a2769191bb8f66da6d50ac8c3b389c5ddf3b45))

- **mcp**: Clarify which step Katana rejects in locked-MO transitions
  ([#774](https://github.com/dougborg/katana-openapi-client/pull/774),
  [`0a30cc4`](https://github.com/dougborg/katana-openapi-client/commit/0a30cc4116a8e6f2bf78b9e4c2d78c052ccb567b))

- **mcp**: Correct misleading SKU example in fulfill enrichment comment
  ([#799](https://github.com/dougborg/katana-openapi-client/pull/799),
  [`bd052bb`](https://github.com/dougborg/katana-openapi-client/commit/bd052bbdcac5ae721661a9a7edde4b953ad545d8))

- **mcp**: Correct stale identifier reference in MO modify planner
  ([#774](https://github.com/dougborg/katana-openapi-client/pull/774),
  [`0a30cc4`](https://github.com/dougborg/katana-openapi-client/commit/0a30cc4116a8e6f2bf78b9e4c2d78c052ccb567b))

- **mcp**: Correct test helper docstring (#771 follow-up)
  ([#776](https://github.com/dougborg/katana-openapi-client/pull/776),
  [`ef402a9`](https://github.com/dougborg/katana-openapi-client/commit/ef402a966eb9b2a0d8aabc57120df78191a4328b))

- **mcp**: Update prefab_ui module docstring for action selection
  ([`3c95158`](https://github.com/dougborg/katana-openapi-client/commit/3c95158439f223974d5d0377847f745cdb87ad34))

- **tests**: Update stale \_build_apply_action_direct docstring refs
  ([`d787806`](https://github.com/dougborg/katana-openapi-client/commit/d787806811471b1d31ddfda98203dffe08390f10))

### Features

- **harness**: Add Katana official MCP server (disabled by default)
  ([`c11adee`](https://github.com/dougborg/katana-openapi-client/commit/c11adee2e612367738baa55a895f07aa840917d1))

- **mcp**: Add create_customer tool with per-entity Prefab card
  ([`c9d5939`](https://github.com/dougborg/katana-openapi-client/commit/c9d5939523892cfebeccf96cb3c33b463d526c1b))

- **mcp**: Add inventory-ordering guard on fulfill_order (#787)
  ([#796](https://github.com/dougborg/katana-openapi-client/pull/796),
  [`2b43fb0`](https://github.com/dougborg/katana-openapi-client/commit/2b43fb08839a29f113a069037df9acdbcdaf7585))

- **mcp**: Add Prefab UI for check_inventory batch path (#562)
  ([#769](https://github.com/dougborg/katana-openapi-client/pull/769),
  [`137ad4c`](https://github.com/dougborg/katana-openapi-client/commit/137ad4c7fba22efb8280c9ab21f30d6d733df99b))

- **mcp**: Add serial_numbers MCP tools (add, list, delete)
  ([#791](https://github.com/dougborg/katana-openapi-client/pull/791),
  [`45e01f1`](https://github.com/dougborg/katana-openapi-client/commit/45e01f12703fc776b23a2b93a8769e4190e887a4))

- **mcp**: Add serial_numbers MCP tools + align spec (#785, #789)
  ([#791](https://github.com/dougborg/katana-openapi-client/pull/791),
  [`45e01f1`](https://github.com/dougborg/katana-openapi-client/commit/45e01f12703fc776b23a2b93a8769e4190e887a4))

- **mcp**: Add Tier 3 per-row breakdown to receive_purchase_order card (#556)
  ([#793](https://github.com/dougborg/katana-openapi-client/pull/793),
  [`c371ea4`](https://github.com/dougborg/katana-openapi-client/commit/c371ea41051faef265d4548beda4b77e59a9ff06))

- **mcp**: Batch recipe update card per-row diff overlay
  ([#798](https://github.com/dougborg/katana-openapi-client/pull/798),
  [`10c8ca5`](https://github.com/dougborg/katana-openapi-client/commit/10c8ca59d75366a9a3263871a55470d6948b67a2))

- **mcp**: Batch recipe update card per-row diff overlay (#557)
  ([#798](https://github.com/dougborg/katana-openapi-client/pull/798),
  [`10c8ca5`](https://github.com/dougborg/katana-openapi-client/commit/10c8ca59d75366a9a3263871a55470d6948b67a2))

- **mcp**: Extend LowStockItem and enrich low_stock_items with parent + supplier
  ([`1837cd1`](https://github.com/dougborg/katana-openapi-client/commit/1837cd1f8312a941f6a89385dcac4f2716f378e8))

- **mcp**: Redesign build_low_stock_ui per #537 four-tier framework
  ([`2465b76`](https://github.com/dougborg/katana-openapi-client/commit/2465b76300093bc3ee6bbb04d433d5076e0d6198))

- **mcp**: Redesign build_verification_ui per #537 four-tier framework
  ([`f2905b4`](https://github.com/dougborg/katana-openapi-client/commit/f2905b40efefc549c93713297e5db541b813857c))

- **mcp**: Redesign fulfill card with Tier 2 metrics + per-row breakdown (#553)
  ([#797](https://github.com/dougborg/katana-openapi-client/pull/797),
  [`b424202`](https://github.com/dougborg/katana-openapi-client/commit/b424202d97cf55b35ba78b487a32efa09c9468b4))

- **mcp**: Refactor MO fulfill to POST /manufacturing_order_productions (#790)
  ([#792](https://github.com/dougborg/katana-openapi-client/pull/792),
  [`decf4bb`](https://github.com/dougborg/katana-openapi-client/commit/decf4bb0d24b54b97c2b77a5a06138c8a8a2ef06))

- **mcp**: Support backdated completion timestamp in fulfill_order (#778)
  ([#779](https://github.com/dougborg/katana-openapi-client/pull/779),
  [`6470b4a`](https://github.com/dougborg/katana-openapi-client/commit/6470b4ae46a211472056182971eab3d03c57e87f))

- **mcp**: Treat DELETE 404 as success + filter tombstones from
  get_manufacturing_order_recipe
  ([#780](https://github.com/dougborg/katana-openapi-client/pull/780),
  [`e26635f`](https://github.com/dougborg/katana-openapi-client/commit/e26635f1e858c676ca48e36a164587bb63a1eb27))

- **scripts**: Add SafeClient guard for probe mutations (#781)
  ([#795](https://github.com/dougborg/katana-openapi-client/pull/795),
  [`bc6b7c1`](https://github.com/dougborg/katana-openapi-client/commit/bc6b7c183a9145767b592f90f450f05110d504d1))

### Refactoring

- **mcp**: Clear apply-rail error state on retry + sync docs
  ([`0220d95`](https://github.com/dougborg/katana-openapi-client/commit/0220d955858476e639af91b5b7207d979e9a44c5))

- **mcp**: Dedupe apply-rail state init per review
  ([`a6cb23a`](https://github.com/dougborg/katana-openapi-client/commit/a6cb23abdbcae4317873592c7cdad3a1f00449f0))

- **mcp**: Drop doubled article in cancel-message per review
  ([`1e5d02f`](https://github.com/dougborg/katana-openapi-client/commit/1e5d02f29e0065af6eaf64b2e9e1b9b4ff994eaf))

- **mcp**: Drop variant footer + coalesce fulfilled handles per review
  ([`778f539`](https://github.com/dougborg/katana-openapi-client/commit/778f5392b7ef0164c94eba27c7dc129c246d9ae5))

- **mcp**: Extract check_inventory + variant_details action helpers
  ([`32e4646`](https://github.com/dougborg/katana-openapi-client/commit/32e46466beacb06aca89e2c3806f55203e5518ca))

- **mcp**: Migrate apply/cancel rail to CallTool + UpdateContext
  ([`0edd135`](https://github.com/dougborg/katana-openapi-client/commit/0edd135ff0f8dd7aeaad1872b88f51374fef2e27))

- **mcp**: Replace remaining SendMessage drill-ins in cards
  ([`181ca3b`](https://github.com/dougborg/katana-openapi-client/commit/181ca3bb9043074dc61baa451fa1b0609d9311da))

- **mcp**: Replace SendMessage drill-ins through low-stock card
  ([`7256805`](https://github.com/dougborg/katana-openapi-client/commit/7256805a7c3adfff485842841f98ecad8d558eb8))

- **mcp**: Simplify low_stock card per review
  ([`a3ccf69`](https://github.com/dougborg/katana-openapi-client/commit/a3ccf691ff94536254029bd3dd79d5a1f22ec3fc))

- **mcp**: Simplify verification card per review
  ([`b4f44d3`](https://github.com/dougborg/katana-openapi-client/commit/b4f44d33ee65a4565a7c1697110f6daed04bb451))

### Testing

- **mcp**: Cover verification card four-tier redesign
  ([#554](https://github.com/dougborg/katana-openapi-client/pull/554),
  [`019cd44`](https://github.com/dougborg/katana-openapi-client/commit/019cd44bfb91a9814a0e2c58d11daa81d733dd7c))

- **mcp**: Pin fulfill-card SKU regression to actual buggy prefix
  ([#799](https://github.com/dougborg/katana-openapi-client/pull/799),
  [`bd052bb`](https://github.com/dougborg/katana-openapi-client/commit/bd052bbdcac5ae721661a9a7edde4b953ad545d8))

- **mcp**: Pin new action types on migrated prefab UI buttons
  ([`e0cc56c`](https://github.com/dougborg/katana-openapi-client/commit/e0cc56c216136a0971a484e91bfe4c349af3124c))

### Breaking Changes

- **client**: The generated type `ServiceVariantCustomFieldsItem` was renamed to
  `ServiceVariantCustomFieldsType0Item` (consequence of the nullable union —
  `openapi-python-client` appends `Type0` to member names of `X | None` unions). No
  callers inside this repo referenced the old name; external callers importing the
  symbol must update the import. The wire format and field name are unchanged.

## v0.69.0 (2026-05-18)

### Bug Fixes

- **client**: Create_sales_order addresses payload (three-layer fix)
  ([#775](https://github.com/dougborg/katana-openapi-client/pull/775),
  [`c450444`](https://github.com/dougborg/katana-openapi-client/commit/c450444674b81855bab16a9cbf8f6d61228cd8e4))

### Chores

- **mcp**: Update client dependency to v0.68.0
  ([`a60b6fa`](https://github.com/dougborg/katana-openapi-client/commit/a60b6fa45bcf7cbeb0564f1149c32f1215d9f332))

### Documentation

- **mcp**: Clarify zip field rename rationale (#772 follow-up)
  ([#775](https://github.com/dougborg/katana-openapi-client/pull/775),
  [`c450444`](https://github.com/dougborg/katana-openapi-client/commit/c450444674b81855bab16a9cbf8f6d61228cd8e4))

### Features

- **client**: Fix create_sales_order addresses payload (three-layer fix)
  ([#775](https://github.com/dougborg/katana-openapi-client/pull/775),
  [`c450444`](https://github.com/dougborg/katana-openapi-client/commit/c450444674b81855bab16a9cbf8f6d61228cd8e4))

## v0.68.0 (2026-05-18)

### Chores

- Sync uv.lock to katana-mcp-server v0.81.0
  ([#770](https://github.com/dougborg/katana-openapi-client/pull/770),
  [`8f2fac0`](https://github.com/dougborg/katana-openapi-client/commit/8f2fac0bb0a3ba023b766c39d94d3b3c30f711a6))

- **deps**: Batch upgrade dev + runtime locks; defensive func.__name__ for ty 0.0.37
  ([#768](https://github.com/dougborg/katana-openapi-client/pull/768),
  [`5c84753`](https://github.com/dougborg/katana-openapi-client/commit/5c84753a582efc1626ef476aa0f0ed9fcb25f7f1))

- **release**: Mcp v0.80.0
  ([`6c8cf33`](https://github.com/dougborg/katana-openapi-client/commit/6c8cf33c1855f470fc4c4f3df37aca36af51fc25))

- **release**: Mcp v0.81.0
  ([`fe54b3a`](https://github.com/dougborg/katana-openapi-client/commit/fe54b3a21f28e4c31fd17882a1fccf67dee8d18a))

### Features

- **client**: Align SalesOrder custom_fields with live API dict shape
  ([#770](https://github.com/dougborg/katana-openapi-client/pull/770),
  [`8f2fac0`](https://github.com/dougborg/katana-openapi-client/commit/8f2fac0bb0a3ba023b766c39d94d3b3c30f711a6))

- **mcp**: Drop derived reporting tools; redesign check_inventory card with native
  Katana fields ([#757](https://github.com/dougborg/katana-openapi-client/pull/757),
  [`94e112f`](https://github.com/dougborg/katana-openapi-client/commit/94e112fde00a4e3a314c8388f7f6be95759d1052))

- **mcp**: Point-in-time inventory via inventory_at + filter pass-through
  ([#762](https://github.com/dougborg/katana-openapi-client/pull/762),
  [`06d1997`](https://github.com/dougborg/katana-openapi-client/commit/06d1997eb19d4b12a9d47a118c05c1d1a5e266e3))

## v0.67.0 (2026-05-18)

### Chores

- **mcp**: Update client dependency to v0.66.0
  ([`8c3c69c`](https://github.com/dougborg/katana-openapi-client/commit/8c3c69c71684ae3d3d60c6da86a9b20dc2e4ba3e))

- **release**: Mcp v0.77.0
  ([`aa79747`](https://github.com/dougborg/katana-openapi-client/commit/aa79747f63c3ea6ecbc0c42ddee0f20861401437))

- **release**: Mcp v0.78.0
  ([`96d467e`](https://github.com/dougborg/katana-openapi-client/commit/96d467ee1e79778c742925bf0006246d1210dd42))

- **release**: Mcp v0.79.0
  ([`f4e9004`](https://github.com/dougborg/katana-openapi-client/commit/f4e9004c40710df3429d6e98ef0973d59fd177b0))

### Features

- **client**: Live-verified spec drift batch + verification harness
  ([#756](https://github.com/dougborg/katana-openapi-client/pull/756),
  [`2f5d5b4`](https://github.com/dougborg/katana-openapi-client/commit/2f5d5b405877867ffa0ccf765f5d7f4d4270ca41))

- **mcp**: Per-entity PO modify card with field-level diff overlay — #722
  ([#755](https://github.com/dougborg/katana-openapi-client/pull/755),
  [`5713459`](https://github.com/dougborg/katana-openapi-client/commit/5713459fce23976d04d925db11a9c1992c5de608))

- **mcp**: Product-level BOM tooling (#747)
  ([#748](https://github.com/dougborg/katana-openapi-client/pull/748),
  [`4b6d23a`](https://github.com/dougborg/katana-openapi-client/commit/4b6d23a544e0a70d921a9a6fb8fab1172792495a))

- **mcp**: Product-level BOM tooling (get_product_bom, manage_product_bom)
  ([#748](https://github.com/dougborg/katana-openapi-client/pull/748),
  [`4b6d23a`](https://github.com/dougborg/katana-openapi-client/commit/4b6d23a544e0a70d921a9a6fb8fab1172792495a))

- **mcp**: Wire Factory.base_currency_code through variant details card
  ([#753](https://github.com/dougborg/katana-openapi-client/pull/753),
  [`0e7127e`](https://github.com/dougborg/katana-openapi-client/commit/0e7127e70bf031a2319193f2ff1d1d6a8cb3eef7))

### Refactoring

- **mcp**: Extract \_format_money helper + standardize currency rendering
  ([#752](https://github.com/dougborg/katana-openapi-client/pull/752),
  [`b5f149d`](https://github.com/dougborg/katana-openapi-client/commit/b5f149d2febb2ca68af6090b26f33b2d8e7ec14e))

### Testing

- **mcp**: Type test_bom fixture defaults as `T | Unset`, not `T | object`
  ([#748](https://github.com/dougborg/katana-openapi-client/pull/748),
  [`4b6d23a`](https://github.com/dougborg/katana-openapi-client/commit/4b6d23a544e0a70d921a9a6fb8fab1172792495a))

### Breaking Changes

- **client**: `CustomFieldDefinition.id` becomes a UUID string (was integer);
  `field_type` / `entity_type` become enums; `CreateServiceVariantRequest.sku` is no
  longer required (callers omitting it will continue to work, but `required` removal is
  a schema-level breaking change); `StockTransferRowRequest.quantity` becomes a string.
  The MCP `stock_transfers` boundary already stringifies the input float so MCP callers
  don't have to.

## v0.66.0 (2026-05-15)

### Chores

- **mcp**: Update client dependency to v0.65.1
  ([`e4b7e62`](https://github.com/dougborg/katana-openapi-client/commit/e4b7e62ee068d1f7253a8091553806ecab85ef1f))

### Features

- **client**: Live-verified spec drift sweep (MO recipe, invoicing, webhook)
  ([`76951db`](https://github.com/dougborg/katana-openapi-client/commit/76951db43ebfdf766212fb9df1093f2e81be3a0a))

### Breaking Changes

- **client**: `ManufacturingOrderRecipeRow.cost` and `total_actual_quantity` change from
  `number` to `string`; the `SalesOrder.invoicing_status` field now references the new
  `SalesOrderInvoicingStatus` enum instead of free-form string.

## v0.65.1 (2026-05-15)

### Bug Fixes

- **client**: Document 412 PreconditionFailedError on DELETE endpoints
  ([`f08bf15`](https://github.com/dougborg/katana-openapi-client/commit/f08bf1573a980333720e9fcd2e031d8b28a6f4a9))

- **client**: Surface undocumented-status response bodies in APIError
  ([`88589e8`](https://github.com/dougborg/katana-openapi-client/commit/88589e813c18fd3fe98ebe896c60b584788608a8))

### Chores

- **mcp**: Update client dependency to v0.65.0
  ([`3a319ba`](https://github.com/dougborg/katana-openapi-client/commit/3a319badd6390f524d0e6076437a518be843b805))

### Documentation

- Note Katana /sales_returns sales_order_id filter is ignored upstream
  ([`64c1538`](https://github.com/dougborg/katana-openapi-client/commit/64c1538efb1258518f7bde52052979762294d4ed))

## v0.65.0 (2026-05-15)

### Chores

- **deps**: Bump gitpython, python-multipart, cryptography for CVE fixes
  ([`70c9ce4`](https://github.com/dougborg/katana-openapi-client/commit/70c9ce47eadf26a84540bc507446ef53e8fe134d))

- **mcp**: Update client dependency to v0.64.0
  ([`d24ed23`](https://github.com/dougborg/katana-openapi-client/commit/d24ed2373a57122a737130a0956d0bfa8117387e))

- **release**: Mcp v0.76.0
  ([`89bee51`](https://github.com/dougborg/katana-openapi-client/commit/89bee511fcc83b88f33697b9c997a2107fa1611a))

### Documentation

- Pull README.io reference markdown corpus via llms.txt
  ([`f87dcbc`](https://github.com/dougborg/katana-openapi-client/commit/f87dcbc703a1c5f50a6846410f713e3c99f1a950))

- **mcp**: Purge stale markdown/format references after #719
  ([`f93c838`](https://github.com/dougborg/katana-openapi-client/commit/f93c83810018ed4076e8acce109fccc11c6d076f))

### Features

- **client**: 2026-05-14 spec drift sweep + CVE bumps
  ([`7f32a2d`](https://github.com/dougborg/katana-openapi-client/commit/7f32a2d0ddaafd0c212c45c3621399e24dae1fcd))

- **mcp**: Per-entity create-order Prefab cards (PO/SO/MO) — #551
  ([`c93e5ca`](https://github.com/dougborg/katana-openapi-client/commit/c93e5caca13a045c44af1f053b41e54586f9566b))

### Refactoring

- **mcp**: Drop hand-written markdown formatters; content is JSON
  ([`93c14cc`](https://github.com/dougborg/katana-openapi-client/commit/93c14cc3dfb5680ccdbe8168e29291c944d3ea84))

### Breaking Changes

- **client**: Multiple field types narrowed from `number` to `string` on read schemas
  (`SalesOrderRow.price_per_unit` / `cogs_value`,
  `ManufacturingOrderRecipeRow.planned_quantity_per_unit`,
  `ManufacturingOrderOperationRow.planned_time_per_unit` / `planned_time_parameter` /
  `total_actual_time` / `planned_cost_per_unit` / `total_actual_cost`). Consumers doing
  arithmetic on these need to parse them (e.g., `float(row.price_per_unit)` or
  `decimal.Decimal(row.price_per_unit)`); pydantic clients in lax mode will continue to
  auto-coerce. The `SalesOrderSearchRequest` / `SalesOrderSearchRequestFilter` classes
  are removed — callers of `POST /sales_orders/search` should switch to
  `SearchFilterRequest`. `SalesOrderRow`'s `attributes.items` request field is renamed
  `name` → `key` on Create / Update DTOs (matches the read shape).

## v0.64.0 (2026-05-14)

### Bug Fixes

- **client**: Guard \_convert_nested_value to_dict fallback with callable()
  ([`4a47e4c`](https://github.com/dougborg/katana-openapi-client/commit/4a47e4cb451d8dc4a5996d04603b7b0ff85a5bc6))

- **client**: Relax non-nullable spec fields to match live Katana wire
  ([#727](https://github.com/dougborg/katana-openapi-client/pull/727),
  [`cfe6fef`](https://github.com/dougborg/katana-openapi-client/commit/cfe6fef86e19662dcd118109bffcbdbf5ce58307))

- **harness**: Address review findings from #689 on /groom (#683 follow-up)
  ([#690](https://github.com/dougborg/katana-openapi-client/pull/690),
  [`4341cce`](https://github.com/dougborg/katana-openapi-client/commit/4341cced2ba0b9e9c0e9e63086247013a3018cf3))

- **mcp**: \_dump_list supports attrs models on API-fallback variant path
  ([`0eb57f6`](https://github.com/dougborg/katana-openapi-client/commit/0eb57f69c86673d6d88a23322cbb0f6ef94b898c))

- **mcp**: Guard variant_lookup against None variant_id lookups
  ([`0ffa191`](https://github.com/dougborg/katana-openapi-client/commit/0ffa19102fb61370a80401ed59c8717ec2e24e89))

- **mcp**: Repair DataTable onRowClick per-row binding + Slot/RESULT envelope
  ([`b4c8bcc`](https://github.com/dougborg/katana-openapi-client/commit/b4c8bcc899d532f8f5b5d027237d01352bfbc3dd))

- **mcp**: Repair modify-tool feedback loop after SRAM PO reconciliation
  ([`9574f24`](https://github.com/dougborg/katana-openapi-client/commit/9574f2410bce1637098b32a188aeea2e974b221f))

- **mcp**: Write modified entity through to typed cache on apply
  ([`52cfbc8`](https://github.com/dougborg/katana-openapi-client/commit/52cfbc894893c1e68b4107e26fd12adcc61a3770))

### Chores

- Bundle uv.lock drift from rebase
  ([`808566f`](https://github.com/dougborg/katana-openapi-client/commit/808566f685f77a54fa58e5b00ed884ffedcb23c2))

- Bundle uv.lock drift from rebase onto main
  ([`6df7ffb`](https://github.com/dougborg/katana-openapi-client/commit/6df7ffb0a4ba27df095c796aef302c338cf971c2))

- Bundle uv.lock drift from rebase onto main
  ([`a5949ce`](https://github.com/dougborg/katana-openapi-client/commit/a5949cec9725665659b6156e0923aabae14383f7))

- Scrub customer-specific data from tests, docs, and help text
  ([`bf43901`](https://github.com/dougborg/katana-openapi-client/commit/bf4390197ecd62641c43b366f014c25bdd2e5d3c))

- Scrub second-pass Spot Bikes leakage (Mayhem, Rocker, Liquid Black, real IDs)
  ([`8b6b45f`](https://github.com/dougborg/katana-openapi-client/commit/8b6b45fa88c0b60dfe9d6c3a88dab6e54e256312))

- **harness**: Require rebased-on-target-branch in /open-pr and /review-pr
  ([#692](https://github.com/dougborg/katana-openapi-client/pull/692),
  [`c5cf718`](https://github.com/dougborg/katana-openapi-client/commit/c5cf7182016818434681867796c5640ab719b12a))

- **mcp**: Update client dependency to v0.63.0
  ([`0c9a2df`](https://github.com/dougborg/katana-openapi-client/commit/0c9a2df1f8753c3f563f588a2a1642158a1c62b6))

- **release**: Mcp v0.71.0
  ([`609fd2d`](https://github.com/dougborg/katana-openapi-client/commit/609fd2d67d215dd162783e3c1a74eb99225d9376))

- **release**: Mcp v0.71.1
  ([`0c6fde7`](https://github.com/dougborg/katana-openapi-client/commit/0c6fde7a0eccb34b12b5824c79798a129426e724))

- **release**: Mcp v0.72.0
  ([`1edb0b6`](https://github.com/dougborg/katana-openapi-client/commit/1edb0b61ddb5347b0e2f465fe1de2cba5a8bbca3))

- **release**: Mcp v0.73.0
  ([`8a1cd56`](https://github.com/dougborg/katana-openapi-client/commit/8a1cd56852f5b564e539fbb3dfa563a3eb7f4603))

- **release**: Mcp v0.74.0
  ([`86d8881`](https://github.com/dougborg/katana-openapi-client/commit/86d8881cf9937dabbf84df667ba75dda65ea72cf))

- **release**: Mcp v0.75.0
  ([`7688267`](https://github.com/dougborg/katana-openapi-client/commit/7688267e2d80ee8ccd703531fface52ebceabf18))

- **release**: Mcp v0.75.1
  ([`421f720`](https://github.com/dougborg/katana-openapi-client/commit/421f7200a312bfd1e90a9c164c9e648ddcdc5db1))

- **release**: Mcp v0.75.2
  ([`d8f2e7d`](https://github.com/dougborg/katana-openapi-client/commit/d8f2e7dca63e764f01fdaaf4e6544b3ad420200c))

### Documentation

- Add npm badge to TS README and cross-refs to new subsystem docs
  ([`e3ceacb`](https://github.com/dougborg/katana-openapi-client/commit/e3ceacb64b60848e562e417042ce42c896412e6d))

- Add subsystem-local docs for progressive-discovery refactor
  ([`2434876`](https://github.com/dougborg/katana-openapi-client/commit/24348769246afbb4ae141d14aadb3dc666420f9e))

- Address Copilot review on #716 — accurate generator pointer + type/scope wording
  ([`0835a80`](https://github.com/dougborg/katana-openapi-client/commit/0835a80b6a27eaba5d94d178d6f985f5138bf61b))

- Address Copilot review on Tier 2-4 PR
  ([#712](https://github.com/dougborg/katana-openapi-client/pull/712),
  [`339b203`](https://github.com/dougborg/katana-openapi-client/commit/339b203f2b2235faeb2905c3b4d07e799a729fd0))

- Address second Copilot review on #716 — __init__.py + accurate git push behavior
  ([`a4669e8`](https://github.com/dougborg/katana-openapi-client/commit/a4669e8b824880c2ff24f59afa616ea9a7d91074))

- Address second Copilot review on #729
  ([`fc7de8b`](https://github.com/dougborg/katana-openapi-client/commit/fc7de8be4ac20288c2b0723a23f172e9b81ef6a6))

- Address second Copilot review on Tier 2-4 PR
  ([#712](https://github.com/dougborg/katana-openapi-client/pull/712),
  [`8c68ba5`](https://github.com/dougborg/katana-openapi-client/commit/8c68ba5a8b23b7450eb8960f8d463a2bd25eb4ed))

- Address third Copilot review on Tier 2-4 PR
  ([#712](https://github.com/dougborg/katana-openapi-client/pull/712),
  [`a7bd305`](https://github.com/dougborg/katana-openapi-client/commit/a7bd305ae53fc5853744ad376909a79f31524944))

- Address three #569 follow-up drifts surfaced during #712 audit
  ([`5fa1fcf`](https://github.com/dougborg/katana-openapi-client/commit/5fa1fcff43f55d4b0f54af448be5e1e45d401ad9))

- Codify the no-hand-maintained-drift-prone-refs rule
  ([`7496b29`](https://github.com/dougborg/katana-openapi-client/commit/7496b29de9e0843972f1f4939c8a3eae49f60d16))

- Make root README drift-resistant
  ([`f759d97`](https://github.com/dougborg/katana-openapi-client/commit/f759d97bddb4a0182221760efbafcc1772e307bc))

- Slim CLAUDE.md to a spine + topical pointer table
  ([`ac858db`](https://github.com/dougborg/katana-openapi-client/commit/ac858dbee88221a27df4caf19c424c6a5922a31b))

- Tier 2 process-doc sweep — CONTRIBUTING + MCP architecture
  ([`a43c015`](https://github.com/dougborg/katana-openapi-client/commit/a43c0158c9f5f995cafea3ec9e3c096e546b2ba6))

- Tier 3 reference/archive cleanup
  ([`31052ba`](https://github.com/dougborg/katana-openapi-client/commit/31052ba6e4a34c1b0a727317af8ee15aa04bb810))

- Trim spec descriptions per code review
  ([`043acd9`](https://github.com/dougborg/katana-openapi-client/commit/043acd99e4b779c297bec6582551a24b5750bdb3))

- **claude**: Document cross-worktree LSP bleed + workaround
  ([`42003b4`](https://github.com/dougborg/katana-openapi-client/commit/42003b41c5d66bc19dce1741a08c0b62e3bd6b41))

- **harness**: Tier 4 shared guides drift sweep + cross-cutting cleanup
  ([`ce92dd2`](https://github.com/dougborg/katana-openapi-client/commit/ce92dd2d5430c59433ac6669aafc9bd15b8dde0a))

- **harness**: Wire the Rolling Backlog board into the daily workflow (#568 Phase 1)
  ([#686](https://github.com/dougborg/katana-openapi-client/pull/686),
  [`81497ea`](https://github.com/dougborg/katana-openapi-client/commit/81497eaa7dd4968cac057e7f5f6e5a0f51308bb7))

- **mcp**: Make MCP server README drift-resistant
  ([`93fdece`](https://github.com/dougborg/katana-openapi-client/commit/93fdece0dad837f5aa5308d6079159d7f3cb0a2f))

- **mcp**: Update \_dump_list comment to reference Type0Item class names
  ([`eb7df9f`](https://github.com/dougborg/katana-openapi-client/commit/eb7df9f4cfcf6611a485f7b1b1d82f541e0eb3e9))

### Features

- **harness**: /groom skill — board hygiene via observed drift, not re-derivation (#683)
  ([#689](https://github.com/dougborg/katana-openapi-client/pull/689),
  [`6b9bb87`](https://github.com/dougborg/katana-openapi-client/commit/6b9bb87d7d8a5152301a5c5ae0e6ba9d568da9ee))

- **mcp**: Expose item-level purchase_uom on catalog create tools
  ([`29de49b`](https://github.com/dougborg/katana-openapi-client/commit/29de49b8ac7f1f3ad4273e5b889ed90908225c53))

- **mcp**: Redesign build_item_detail_ui per #537 four-tier framework
  ([`79d6361`](https://github.com/dougborg/katana-openapi-client/commit/79d63610f0bec49ca59f5d3e6a1e2befc36bd782))

- **mcp**: Rev 2 of variant card + canonical display_name
  ([`151a924`](https://github.com/dougborg/katana-openapi-client/commit/151a9243d5fbff5718a3dc7856d0199237e0a595))

- **mcp**: Surface canonical display_name on ItemVariantSummary
  ([`a4e5563`](https://github.com/dougborg/katana-openapi-client/commit/a4e55639026d714f2f8f391eb38d5e9c6e9a4bef))

- **mcp**: Surface display_name in fulfill_order inventory updates
  ([`293b5a9`](https://github.com/dougborg/katana-openapi-client/commit/293b5a9406ecd3e3fa6add757472bcf40cb20070))

- **mcp**: Surface display_name on list\_\*/MO summary models
  ([`7529ea3`](https://github.com/dougborg/katana-openapi-client/commit/7529ea38ddd21fb21cdefaf9cb8fa1715fa0514a))

- **mcp**: Surface display_name on MO recipe rows + batch update UI
  ([`33b63b0`](https://github.com/dougborg/katana-openapi-client/commit/33b63b09d44b66117e55ec829b347fabf927228b))

- **mcp**: Surface display_name on PO/SO get-row models
  ([`0f24d64`](https://github.com/dougborg/katana-openapi-client/commit/0f24d64052ae775f0910567aae286ccec2687a49))

- **mcp**: Surface display_name on verify_order_document results
  ([`c1f9303`](https://github.com/dougborg/katana-openapi-client/commit/c1f93039a8742d16645e477a91f8c52218deed45))

### Testing

- **mcp**: Parity test for cache-hit vs API-fallback variant details path
  ([`2f1490c`](https://github.com/dougborg/katana-openapi-client/commit/2f1490c85acf1f3f7463178a66ca04339d284979))

## v0.63.0 (2026-05-12)

### Bug Fixes

- **client**: Backfill missing property descriptions on 12 schemas
  (test_schema_comprehensive)
  ([#681](https://github.com/dougborg/katana-openapi-client/pull/681),
  [`7a637b7`](https://github.com/dougborg/katana-openapi-client/commit/7a637b7378cd79825e66c5220f205a9af9d30ce3))

- **mcp**: Auto-rebuild typed cache on schema fingerprint mismatch
  ([`03a714c`](https://github.com/dougborg/katana-openapi-client/commit/03a714c72acbc61430b8e881cc134bb37b43af0a))

- **mcp**: Lead preview coaching with no-iframe fallback
  ([#648](https://github.com/dougborg/katana-openapi-client/pull/648),
  [`b6fb056`](https://github.com/dougborg/katana-openapi-client/commit/b6fb056af3d2171c5f2ac42fbab1cea0e7922aed))

### Chores

- **release**: Mcp v0.69.0
  ([`12062a5`](https://github.com/dougborg/katana-openapi-client/commit/12062a5963ee7640c1de3c4294719e3343e0c5fc))

- **release**: Mcp v0.69.1
  ([`32b8e07`](https://github.com/dougborg/katana-openapi-client/commit/32b8e07ae71f7b7e8d48766d6535bba85770623e))

- **release**: Mcp v0.70.0
  ([`02875aa`](https://github.com/dougborg/katana-openapi-client/commit/02875aae70555a379795c88d407a7e4bb22ed58c))

### Features

- **mcp**: Background cache warm-up at lifespan startup (#593)
  ([#680](https://github.com/dougborg/katana-openapi-client/pull/680),
  [`4f0f7fa`](https://github.com/dougborg/katana-openapi-client/commit/4f0f7fa74408f8ca5f8649c82111c56ec7d1bcd7))

- **mcp**: Extend rebuild_cache to cover catalog entity types
  ([`afa3641`](https://github.com/dougborg/katana-openapi-client/commit/afa36417998f9b23cbd170d50fad46eda81ba002))

### Testing

- **mcp**: Pin MO+datetime regression on typed-cache write path (#632)
  ([#678](https://github.com/dougborg/katana-openapi-client/pull/678),
  [`c329345`](https://github.com/dougborg/katana-openapi-client/commit/c3293451860c64e5bbc038b402e5a8e8cc89135e))

- **mcp**: Suppress webbrowser.open during browser-test fixture
  ([`cd90d5c`](https://github.com/dougborg/katana-openapi-client/commit/cd90d5cadc56a93f5c51b7a9b1a3a249b8923354))

### Breaking Changes

- **client**: Two narrowings in this PR.

## v0.62.0 (2026-05-11)

### Bug Fixes

- **client**: Also relax VariantResponse.sku + migrate pre-existing caches
  ([`b79a478`](https://github.com/dougborg/katana-openapi-client/commit/b79a4780f4fb244422262a65493480aaf9bb56e7))

- **client**: Clarify VariantResponse.sku presence + test setup comment
  ([`2cf54df`](https://github.com/dougborg/katana-openapi-client/commit/2cf54dfe23ff9d1674567779bdd660499ceeb680))

- **client**: Declare Variant.sku as nullable to match wire contract
  ([`a8109c2`](https://github.com/dougborg/katana-openapi-client/commit/a8109c2e0152aaf3077e63a81eeb40045085c592))

### Chores

- Sync uv.lock to mcp v0.68.0
  ([`b56322c`](https://github.com/dougborg/katana-openapi-client/commit/b56322c114ac9f497e6a560e4f3db7f6df37de04))

- **client**: Regen catches stale MO operation row example
  ([`bf4ba61`](https://github.com/dougborg/katana-openapi-client/commit/bf4ba61514299c5fd4ea0d2ae1d3d3e6bdc941b9))

## v0.61.0 (2026-05-11)

### Bug Fixes

- **client**: Drop Location anyOf union and InventoryItem.purchase_uom maxLength
  ([`d554da9`](https://github.com/dougborg/katana-openapi-client/commit/d554da90c463dcb4a8c0c66253e445e9b9cd3441))

- **client**: PydanticJSON serializes nested datetimes in plain dicts/lists
  ([`1174c34`](https://github.com/dougborg/katana-openapi-client/commit/1174c34c4af2a1d19c1506b5efd9bc1a69d18861))

- **mcp**: Coerce numerics in modification helpers to drop verification false-positives
  ([`a667e16`](https://github.com/dougborg/katana-openapi-client/commit/a667e1660d56f71d46de47d28e034fabfb35bd5f))

- **mcp**: Collapse modification cards to one state-bound DataTable + wire live-tick on
  apply ([#629](https://github.com/dougborg/katana-openapi-client/pull/629),
  [`b43ceb3`](https://github.com/dougborg/katana-openapi-client/commit/b43ceb3c987fc31176b9a4f16a4a57a3e3d6a401))

- **mcp**: Drop broken live-tick SetState; pin behavior with production-shape harness
  stub ([#645](https://github.com/dougborg/katana-openapi-client/pull/645),
  [`8c54f18`](https://github.com/dougborg/katana-openapi-client/commit/8c54f18ebf9362ea3d24bb34b1a6d00ecc3c7d30))

- **mcp**: Narrow OperationalError fallback to FTS5 syntax errors only
  ([`c693bb4`](https://github.com/dougborg/katana-openapi-client/commit/c693bb486cb67117853313e04980e781aa0e3ecc))

- **mcp**: Replace FTS5 listeners with SQLite triggers
  ([`2b12f46`](https://github.com/dougborg/katana-openapi-client/commit/2b12f469050a65028f8ae9a89e6a5e7d2bb8550b))

- **mcp**: Replace text() with DDL/exec_driver_sql in typed-cache FTS
  ([`df68488`](https://github.com/dougborg/katana-openapi-client/commit/df684880514ee0fd4514e4f030b417f989321fa3))

- **mcp**: Rollback typed-cache session on bind-param failures so subsequent calls don't
  hang
  ([`d0468d7`](https://github.com/dougborg/katana-openapi-client/commit/d0468d79b22585acc42daa15a70ee195eaf2a38b))

- **mcp**: Use startswith for FTS5 syntax-error matching
  ([`62445b8`](https://github.com/dougborg/katana-openapi-client/commit/62445b885a25c64f36ac2254a12e5117bb6ff3c1))

- **scripts**: Tools.json generator emits clean, non-duplicate descriptions
  ([`b8e0b69`](https://github.com/dougborg/katana-openapi-client/commit/b8e0b6970ec545b3081ee0cadf8c41dd2cf989ec))

### Chores

- Regenerate uv.lock for mcp v0.66.0 workspace bump
  ([`63359e1`](https://github.com/dougborg/katana-openapi-client/commit/63359e166fae006e69b8fcbc2d3b881c6fd2c332))

- **client**: Simplify Phase A generator passes (#472 follow-up)
  ([`4646318`](https://github.com/dougborg/katana-openapi-client/commit/46463183c4ece2caca0cb166e792740883033028))

- **deps**: Bump prefab-ui 0.18.5 → 0.19.1
  ([`86437c7`](https://github.com/dougborg/katana-openapi-client/commit/86437c7412b12da93b16f09479adfb8ad6286272))

- **deps**: Consolidated dependency updates
  ([`2cdaf0b`](https://github.com/dougborg/katana-openapi-client/commit/2cdaf0ba2cb44db13120c35c581e3242c828c2ac))

- **deps)(deps**: Bump openapi-python-client
  ([`13a9478`](https://github.com/dougborg/katana-openapi-client/commit/13a9478a84002e1e0e03a9d288d3503a7543233d))

- **harness**: Teach /open-pr to suggest /rebase when branch is behind main
  ([`d31f886`](https://github.com/dougborg/katana-openapi-client/commit/d31f886769b6e005706cbaeb6f6257027423526d))

- **mcp**: Start typecheck cleanup of katana_mcp_server/tests/ (#480 Phase B, partial)
  ([`9659503`](https://github.com/dougborg/katana-openapi-client/commit/96595039466513a22739e80a334c4bba331193c5))

- **mcp**: Update client dependency to v0.60.0
  ([`a566692`](https://github.com/dougborg/katana-openapi-client/commit/a566692a1786037c5563e020e7ab7d5f86b89247))

- **release**: Mcp v0.63.0
  ([`a17e0cd`](https://github.com/dougborg/katana-openapi-client/commit/a17e0cd7ce8e6865cb068a57abfa4ca66dbf8263))

- **release**: Mcp v0.64.0
  ([`150cc37`](https://github.com/dougborg/katana-openapi-client/commit/150cc37cb94fb6c0e4b8056edc3b27e98857f7fe))

- **release**: Mcp v0.64.1
  ([`a98dda4`](https://github.com/dougborg/katana-openapi-client/commit/a98dda4ee6bfcb5b623fabec7e21ae88342430e7))

- **release**: Mcp v0.65.0
  ([`39c2744`](https://github.com/dougborg/katana-openapi-client/commit/39c274455f01bffcffcc0aa31b61a8eb2e25f96a))

- **release**: Mcp v0.66.0
  ([`94f594e`](https://github.com/dougborg/katana-openapi-client/commit/94f594efa68d03cc8bdd35597b92cf60d28adcb7))

- **release**: Mcp v0.67.0
  ([`318aa42`](https://github.com/dougborg/katana-openapi-client/commit/318aa426d8c3a1c84f680e21a9125d0a318b5e27))

- **release**: Mcp v0.68.0
  ([`1befd80`](https://github.com/dougborg/katana-openapi-client/commit/1befd80ec30efdf6132feb176b8d076fb7723360))

### Continuous Integration

- **mcp**: Wire poe test-browser into CI + pre-install Chromium in devcontainer
  ([`26cbd47`](https://github.com/dougborg/katana-openapi-client/commit/26cbd47f0d6786f3e5136c675a6d63e726487bc7))

### Documentation

- **claude**: Add stub-shape + docstring-promise pitfalls to Known Pitfalls
  ([`3a41c77`](https://github.com/dougborg/katana-openapi-client/commit/3a41c776e8bf60f53f85e2026aa1fcb5b28eb9ba))

- **claude**: Document Prefab DataTable mustache state-binding requirement
  ([`cc231f9`](https://github.com/dougborg/katana-openapi-client/commit/cc231f970c372fa5f50e0c271b5785d149220d7d))

- **mcp**: Address Copilot review comments on cookbook recipe
  ([#665](https://github.com/dougborg/katana-openapi-client/pull/665),
  [`caace27`](https://github.com/dougborg/katana-openapi-client/commit/caace275db5b1915dcf79174fd5f6ef3faf748ca))

- **mcp**: Cookbook recipe for catalog search in the typed cache (#472 Phase E)
  ([`7cf330c`](https://github.com/dougborg/katana-openapi-client/commit/7cf330cc5165118a3d3fe0c377f62d7f43ef7fd5))

- **mcp**: Correct cookbook recipe accuracy issues (#665 round 2)
  ([`04bd48a`](https://github.com/dougborg/katana-openapi-client/commit/04bd48a366681f3b6957d9105db0264dd5b07832))

- **mcp**: Correct populate_fts_from_existing_rows docstring
  ([`b406230`](https://github.com/dougborg/katana-openapi-client/commit/b4062306bbb7e59e1d06b731b01a9396310837d7))

- **mcp**: Fix code-reviewer findings on cookbook recipe (#665 review)
  ([`d51da13`](https://github.com/dougborg/katana-openapi-client/commit/d51da13b9b4911a82bf6189aa848086a1721376a))

### Features

- **mcp**: Migrate catalog call sites to typed cache + decommission CatalogCache (#472
  Phase D)
  ([`42d782e`](https://github.com/dougborg/katana-openapi-client/commit/42d782e49155b3c60cb961f29cb1d3bf0e766fba))

- **mcp**: Prefab UI cards for stock_adjustment family + direct-apply rail (#311, #639)
  ([`52ae702`](https://github.com/dougborg/katana-openapi-client/commit/52ae702217a91c43782ff0fde5303dc2e3adb3d6))

- **mcp**: Rewire @cache_read decorator to Cached\* class keys (#472 Phase C)
  ([`8ef5106`](https://github.com/dougborg/katana-openapi-client/commit/8ef5106cf823bce21d9225e3fdea6233b4e4cccb))

- **mcp**: Wire catalog typed-cache sync + FTS sidecar + CatalogQueries adapter (#472
  Phase B)
  ([`e433980`](https://github.com/dougborg/katana-openapi-client/commit/e4339803cb763ee3a6ac0ff2664313f49737b0b9))

### Refactoring

- **mcp**: Drop unused topo_sort_specs and dedupe archive-column logic
  ([`854550c`](https://github.com/dougborg/katana-openapi-client/commit/854550c43e64ad28584f6fb5df2d7058f14c2951))

### Testing

- **mcp**: Browser render coverage for the other 4 state-bound DataTable cards
  ([`d5d4a30`](https://github.com/dougborg/katana-openapi-client/commit/d5d4a30e18984bc6172f12d52bef2c24dd07a9ad))

- **mcp**: Browser-render tests catch the actual #629 bug + audit-fix all bare-string
  state bindings
  ([`762efe8`](https://github.com/dougborg/katana-openapi-client/commit/762efe8b710cc1a999c0aa6a980ad6ab665ac1e8))

- **scripts**: Regression tests for tools.json generator bugfixes
  ([`6d81e26`](https://github.com/dougborg/katana-openapi-client/commit/6d81e268e5143853aace1e5d10483743c58fe22f))

### Breaking Changes

- **mcp**: `Services.cache` field removed. `katana_mcp.cache` and
  `katana_mcp.cache_sync` modules removed. `EntityType` enum removed. Third-party
  consumers of `katana_mcp_server` that touched any of these will need to migrate to
  `services.typed_cache.catalog` and the `Cached*` SQLModel classes from
  `katana_public_api_client.models_pydantic._generated`.

## v0.60.0 (2026-05-08)

### Chores

- **client**: Emit Mapped[T] field types on Cached\* classes (drop col()/cast()
  ergonomics tax)
  ([`c845c69`](https://github.com/dougborg/katana-openapi-client/commit/c845c6947cd2497f94738e055cbac63a2b4cc48d))

- **release**: Mcp v0.62.0
  ([`b82abdb`](https://github.com/dougborg/katana-openapi-client/commit/b82abdbad7fdaaff8b360ee6dc03eb7ce7e233dc))

### Features

- **client**: Add catalog Cached\* siblings + FTS5 specs (#472 Phase A)
  ([`7133848`](https://github.com/dougborg/katana-openapi-client/commit/7133848e9bb84e83dac2fda054f8a52f405b6bc6))

- **mcp**: Direct-apply rail for create_sales_order + create_manufacturing_order
  ([`9110857`](https://github.com/dougborg/katana-openapi-client/commit/91108575c032cfb69b0b75f4c9eeb90204837834))

### Breaking Changes

- **client**: New public Cached\* classes (CachedVariant, CachedProduct, CachedMaterial,
  CachedService, CachedCustomer, CachedSupplier, CachedLocation, CachedTaxRate,
  CachedOperator, CachedFactory, CachedAdditionalCost) ship in the generated client.
  CachedPurchaseOrder.supplier field type changed from Supplier to CachedSupplier (now
  references the cache sibling, consistent with the typed-cache pattern).

## v0.59.0 (2026-05-08)

### Bug Fixes

- **client**: Align 6 query parameter types with Katana wire contract
  ([`2eafa42`](https://github.com/dougborg/katana-openapi-client/commit/2eafa42f2e3f377e315756285959354b6e45b0ce))

- **client**: Declare 200 response bodies for update_sales_order +
  update_customer_address
  ([`7c64de9`](https://github.com/dougborg/katana-openapi-client/commit/7c64de9d662c4feef1672c2c59f7bab2ce044f50))

- **client**: Rewrite ValidationErrorDetail to match Katana's Ajv-style 422 wire shape
  ([`f2164eb`](https://github.com/dougborg/katana-openapi-client/commit/f2164eb72f09a8e55c5f6d84d22b4b6e48df1d1a))

- **mcp**: Address Copilot review on PR #535 — single-item card by_location + N+1 cache
  fix
  ([`432c712`](https://github.com/dougborg/katana-openapi-client/commit/432c7122a0a8442d28d1363fe11390ce38236dd8))

- **mcp**: Expose configs and config_attributes on modify_item
  ([#581](https://github.com/dougborg/katana-openapi-client/pull/581),
  [`4058791`](https://github.com/dougborg/katana-openapi-client/commit/4058791d8d99f2caa078eb40585c8c64aa575f28))

- **mcp**: Get_variant_details batch returns partial results on misses
  ([`5ce501d`](https://github.com/dougborg/katana-openapi-client/commit/5ce501d52b6328ea55f1e1f869f17e8bd4b2a2ae))

- **mcp**: Make resolve_entity_name resilient to cache failures
  ([`5445c94`](https://github.com/dougborg/katana-openapi-client/commit/5445c94377c936b5bef0d92650a3aa1ccdb69650))

- **mcp**: Make typed cache safe for concurrent MCP server processes
  ([`adbef74`](https://github.com/dougborg/katana-openapi-client/commit/adbef74ea73a7a2a32f35c6e9369685e109f6949))

- **mcp**: Parse list_locations address as nested object
  ([`80b4f22`](https://github.com/dougborg/katana-openapi-client/commit/80b4f22ed8966f3c7027dbfe0745880e0be45256))

- **mcp**: Rail Confirm-button apply through agent loop
  ([`9e02411`](https://github.com/dougborg/katana-openapi-client/commit/9e02411874434f43c3ce062a24d50c27365a9ba9))

- **mcp**: Render apply errors prominently and surface real error string
  ([`dde631e`](https://github.com/dougborg/katana-openapi-client/commit/dde631e553c721345fc14bf5cc1114d5fa443eac))

- **mcp**: Search_items renders proper empty-state UI when 0 results
  ([#470](https://github.com/dougborg/katana-openapi-client/pull/470),
  [`0bd2cd6`](https://github.com/dougborg/katana-openapi-client/commit/0bd2cd695271809b300476a52d200936269f191b))

- **mcp**: Structlog logger + branch-neutral resolve_entity_name warnings
  ([`45c0d96`](https://github.com/dougborg/katana-openapi-client/commit/45c0d9606b718af77335fd9ab497473288c4ec9b))

- **mcp**: Surface cache-miss warnings on direct-apply PO responses
  ([`a612100`](https://github.com/dougborg/katana-openapi-client/commit/a6121003cde068299b8c47e9f8b9da518c0b361e))

- **mcp**: Sync parent caches before lifting default_supplier onto variants
  ([`950dc33`](https://github.com/dougborg/katana-openapi-client/commit/950dc33f50300fef47aaaaae6febefccd7fd61c7))

### Chores

- **client**: #395 spec audit — add recurring drift guardrail + audit report
  ([#585](https://github.com/dougborg/katana-openapi-client/pull/585),
  [`15e505b`](https://github.com/dougborg/katana-openapi-client/commit/15e505b1037a6d1595784653f05607b3d0fec55b))

- **harness**: Bump harness-kit lock 0.4.0 → 0.5.1
  ([`62ce368`](https://github.com/dougborg/katana-openapi-client/commit/62ce368642601f7d6fec6f99b27d7e972b8f668a))

- **harness**: Enable harness-kit plugin in shared project settings
  ([`c0ebb16`](https://github.com/dougborg/katana-openapi-client/commit/c0ebb166161f88bdb4693cffec010301d9147f17))

- **mcp**: Consolidate remaining stdlib loggers on structlog
  ([`b327c98`](https://github.com/dougborg/katana-openapi-client/commit/b327c98de4b848779f2796bc04d3419dd59a1b26))

- **mcp**: Enable ty type-checking on katana_mcp_server/src/ (#480 Phase A)
  ([`a140423`](https://github.com/dougborg/katana-openapi-client/commit/a140423450ef0083d14da532baef4992ddb5566b))

- **release**: Mcp v0.58.0
  ([`746d17d`](https://github.com/dougborg/katana-openapi-client/commit/746d17dc0d3c64fb1bb738a4995a7c95b0dde054))

- **release**: Mcp v0.59.0
  ([`7fbfbe1`](https://github.com/dougborg/katana-openapi-client/commit/7fbfbe1fb217a2f6b69b4c3022bf35b58172624c))

- **release**: Mcp v0.60.0
  ([`2b8f8ca`](https://github.com/dougborg/katana-openapi-client/commit/2b8f8ca8fe511535e47bab99f965f5cc85b21c93))

- **release**: Mcp v0.61.0
  ([`ef631c2`](https://github.com/dougborg/katana-openapi-client/commit/ef631c2e21f50b40269df47d88d1d3efeebd1e5c))

- **scripts**: Add verify_drift.py + 2026-05-06 audit notes (WIP)
  ([`239ad5b`](https://github.com/dougborg/katana-openapi-client/commit/239ad5b2980f9cb9e5a17593f495332399d1e296))

- **scripts**: Simplify verify_drift.py — drop redundant fetches and dead state
  ([`bf22e8a`](https://github.com/dougborg/katana-openapi-client/commit/bf22e8a3874069a1f8573d393b9c26776290e99c))

### Documentation

- Capture 2026-05-05 session retro + cache-IDs pitfall + harness upstream config
  ([`f130037`](https://github.com/dougborg/katana-openapi-client/commit/f130037f691ad1e491f7024122cde07c1efd8a98))

- KATANA_API_QUESTIONS.md sweep — cross-check vs upstream specs, move resolved entries
  ([#603](https://github.com/dougborg/katana-openapi-client/pull/603),
  [`08930fd`](https://github.com/dougborg/katana-openapi-client/commit/08930fd5cffce86599686b492d94da404eae133f))

- KATANA_API_QUESTIONS.md §7 — stock_transfer/stock_adjustment row immutability + DELETE
  open question ([#603](https://github.com/dougborg/katana-openapi-client/pull/603),
  [`08930fd`](https://github.com/dougborg/katana-openapi-client/commit/08930fd5cffce86599686b492d94da404eae133f))

- **claude.md**: Document archive/deleted state conventions
  ([`786c149`](https://github.com/dougborg/katana-openapi-client/commit/786c149b4256bd838359e1c3559edca29788c41f))

- **KATANA_API_QUESTIONS**: Add §7 (stock_transfer/stock_adjustment immutability) +
  sweep stale entries
  ([#603](https://github.com/dougborg/katana-openapi-client/pull/603),
  [`08930fd`](https://github.com/dougborg/katana-openapi-client/commit/08930fd5cffce86599686b492d94da404eae133f))

- **mcp**: Add /correct-shipped-build skill + document closed-record correction
  non-coverage
  ([`5d7c83f`](https://github.com/dougborg/katana-openapi-client/commit/5d7c83f2abf1bdc80f857c0f7f5f3e773cf87ccd))

- **mcp**: Document every Field on the four foundation tool modules
  ([`043f476`](https://github.com/dougborg/katana-openapi-client/commit/043f476df7fd63485afe544870d3d3ace42f6e72))

- **mcp**: Sync help resource and tool docstrings with new reference shape
  ([`b83b644`](https://github.com/dougborg/katana-openapi-client/commit/b83b644a59504cc5dcbba2252ed7c410b83444f6))

### Features

- **client**: Adaptive rate-limit transport with X-Ratelimit-\* awareness
  ([`cc80d06`](https://github.com/dougborg/katana-openapi-client/commit/cc80d06b2e21c5d45b2574977d204ce4772591a4))

- **client**: Add serial_numbers to SalesOrderFulfillmentRowRequest
  ([`a3a3f92`](https://github.com/dougborg/katana-openapi-client/commit/a3a3f92c8e24b106b4f79dde97a4ca009f0ac10b))

- **client**: Add serial_numbers to UpdateManufacturingOrderRequest
  ([#586](https://github.com/dougborg/katana-openapi-client/pull/586),
  [`2cca3a4`](https://github.com/dougborg/katana-openapi-client/commit/2cca3a48e6eccd05cb49d2043a79fb09cc2abc13))

- **mcp**: Add list\_\* tool wrappers for reference resources
  ([#530](https://github.com/dougborg/katana-openapi-client/pull/530),
  [`5adf095`](https://github.com/dougborg/katana-openapi-client/commit/5adf095af6e7fcafffd1adbd523736af03bc5f97))

- **mcp**: Check_inventory exposes per-location breakdown + location_id filter
  ([#529](https://github.com/dougborg/katana-openapi-client/pull/529),
  [`1a5a46e`](https://github.com/dougborg/katana-openapi-client/commit/1a5a46e8cad5cf133dc6526affdc77421de13271))

- **mcp**: Correct_purchase_order — composite closed-record edits on POs
  ([#532](https://github.com/dougborg/katana-openapi-client/pull/532),
  [`f9cf0ce`](https://github.com/dougborg/katana-openapi-client/commit/f9cf0ce3f0e242d641d4ef22cf6df78800957156))

- **mcp**: Direct-apply Confirm-button rail for create_purchase_order
  ([`56a4ea5`](https://github.com/dougborg/katana-openapi-client/commit/56a4ea587379e11c5f70cba23f6789101289c5be))

- **mcp**: Direct-apply preview cards for every modification tool
  ([`6b8fbe4`](https://github.com/dougborg/katana-openapi-client/commit/6b8fbe4a90317214f844d33398ff909251086180))

- **mcp**: Enrich create_purchase_order apply response with notes echo + preview-side
  context
  ([`6ea9c8d`](https://github.com/dougborg/katana-openapi-client/commit/6ea9c8d55755e06dbc5baed05f8fe98014f7c120))

- **mcp**: Expose ecommerce + tracking + custom fields + dates on create_sales_order
  ([`d709d1c`](https://github.com/dougborg/katana-openapi-client/commit/d709d1c55b98c8846b069e66c08988a7479efc10))

- **mcp**: Expose entity_type + dates + tracking_location_id on create_purchase_order
  ([`0d5daa4`](https://github.com/dougborg/katana-openapi-client/commit/0d5daa478e35257a6ac1d2fffb2457d5397b97b1))

- **mcp**: Expose stock_adjustment_number, date override, and batch_transactions on
  create_stock_adjustment
  ([`f11efb7`](https://github.com/dougborg/katana-openapi-client/commit/f11efb756f8a7f1ab15d7aff36a26f6ca3efd843))

- **mcp**: Expose transfer_date and order_created_date on create_stock_transfer
  ([`be94199`](https://github.com/dougborg/katana-openapi-client/commit/be94199a5cba1a16a2b38e6d8d9fcd72c952363a))

- **mcp**: Forward variant-level fields on create_product / create_material /
  create_item
  ([`9e039b1`](https://github.com/dougborg/katana-openapi-client/commit/9e039b1af9dcd472f4a7056f382df00e900c9d94))

- **mcp**: Fulfill_order supports serial-tracked MO variants
  ([#586](https://github.com/dougborg/katana-openapi-client/pull/586),
  [`2cca3a4`](https://github.com/dougborg/katana-openapi-client/commit/2cca3a48e6eccd05cb49d2043a79fb09cc2abc13))

- **mcp**: Fulfill_order supports serial-tracked variants
  ([#547](https://github.com/dougborg/katana-openapi-client/pull/547),
  [`ba31424`](https://github.com/dougborg/katana-openapi-client/commit/ba3142411baa537810cca23ad5f70d28769d592a))

- **mcp**: Parameterize reference tools, drop bulk-list resources
  ([`a5a4eb8`](https://github.com/dougborg/katana-openapi-client/commit/a5a4eb870d35d77a838a0fec6c509cdb4e55490a))

- **mcp**: Redesign variant_details card with parent-derived context
  ([`679909b`](https://github.com/dougborg/katana-openapi-client/commit/679909b7fef3294fcc71dbae67c07e8a9d92963c))

- **mcp**: Surface archived items in search and document archive lifecycle
  ([`cf55c29`](https://github.com/dougborg/katana-openapi-client/commit/cf55c299fd391cdc12dcb315d38a88cb9f7f6317))

### Performance Improvements

- **mcp**: Bulk-upsert cache rows in \_sync_one_locked
  ([`1cedc8c`](https://github.com/dougborg/katana-openapi-client/commit/1cedc8cbc0378c6a7b26ad95753daca748051e73))

- **mcp**: Filtered write-through for list_blocking_ingredients
  ([#592](https://github.com/dougborg/katana-openapi-client/pull/592),
  [`d558a99`](https://github.com/dougborg/katana-openapi-client/commit/d558a99e998157ffc804bf9b3eea0ac890659feb))

### Refactoring

- **mcp**: Address Copilot review findings on #503 modify_item configs
  ([#582](https://github.com/dougborg/katana-openapi-client/pull/582),
  [`b4a230b`](https://github.com/dougborg/katana-openapi-client/commit/b4a230bb0d591776f591f486051cf22e302f57ac))

- **mcp**: Remove redundant \_STOCK_FETCH_CONCURRENCY semaphore
  ([`ac8995d`](https://github.com/dougborg/katana-openapi-client/commit/ac8995d6b1e32710a1cda5c6f130f8336925611c))

- **mcp**: Tighten create_purchase_order entity_type to StrEnum, fail fast on outsourced
  gaps
  ([`3574345`](https://github.com/dougborg/katana-openapi-client/commit/3574345c4bdd701d15c8bc713cf1029b67265253))

### Testing

- **mcp**: Add field-set drift detector for create\_\* tools (closes #519)
  ([`9b6cd6f`](https://github.com/dougborg/katana-openapi-client/commit/9b6cd6f165a2c9761723a47145dd51084d971244))

## v0.58.0 (2026-05-06)

### Bug Fixes

- **client**: Add PENDING to SalesOrderStatus enum
  ([#516](https://github.com/dougborg/katana-openapi-client/pull/516),
  [`d7d666c`](https://github.com/dougborg/katana-openapi-client/commit/d7d666c579600fce2dd23ff1f6bbd255ab780183))

- **mcp**: Expose batch_transactions on MORecipeRowAdd/Update
  ([#518](https://github.com/dougborg/katana-openapi-client/pull/518),
  [`1fa9d20`](https://github.com/dougborg/katana-openapi-client/commit/1fa9d207255d577c365c52794352076360d8e3a2))

- **mcp**: Extend additional_info echo workaround to
  material/product/MO/stock_adjustment
  ([`f73bc0c`](https://github.com/dougborg/katana-openapi-client/commit/f73bc0c2337eb005c64e79caa4263f79edd94bff))

- **mcp**: Make additional_info pre-fetch best-effort to avoid hard-failing on transient
  errors
  ([`cfd4f73`](https://github.com/dougborg/katana-openapi-client/commit/cfd4f73f45b8205863c8a930af8247bbdc713509))

### Chores

- **release**: Mcp v0.56.0
  ([`6c95b31`](https://github.com/dougborg/katana-openapi-client/commit/6c95b315cb4c4394f36e245d85398f46058cf6f5))

- **release**: Mcp v0.56.1
  ([`7b0185d`](https://github.com/dougborg/katana-openapi-client/commit/7b0185d2591b71db37604f959dccdacdb49c0821))

- **release**: Mcp v0.56.2
  ([`1532128`](https://github.com/dougborg/katana-openapi-client/commit/15321283b65e398cc68815088ad943a40eb96fab))

- **release**: Mcp v0.57.0
  ([`01dfda9`](https://github.com/dougborg/katana-openapi-client/commit/01dfda9aa514a8c39b47494b03feda271e7f5f91))

### Features

- **mcp**: Add correct_manufacturing_order and correct_sales_order for closed-record
  edits
  ([`1e24c97`](https://github.com/dougborg/katana-openapi-client/commit/1e24c970e2c1b53b4ddcdd0a551e53e29fdb952f))

### Refactoring

- **mcp**: Extract batch-transactions conversion helpers across receive/stock_transfer
  for consistency with #521
  ([`79b6d82`](https://github.com/dougborg/katana-openapi-client/commit/79b6d82086a7cac269900cb3353e8cc1f415a698))

- **mcp**: Extract patch_additional_info helper for the wipe-on-omit workaround
  ([`217d732`](https://github.com/dougborg/katana-openapi-client/commit/217d7322d26e3e201ab0995222e92a36ecb5a7e1))

### Testing

- **client**: Regression guard for SalesOrderStatus PENDING
  ([#516](https://github.com/dougborg/katana-openapi-client/pull/516),
  [`b4c0a68`](https://github.com/dougborg/katana-openapi-client/commit/b4c0a68293b9f0e8f7ec09f26f15a65d60b60854))

## v0.57.0 (2026-05-05)

### Bug Fixes

- **mcp**: Address Copilot review feedback on #514
  ([#514](https://github.com/dougborg/katana-openapi-client/pull/514),
  [`605d923`](https://github.com/dougborg/katana-openapi-client/commit/605d9239f7d2dc7cfcc18bad2f47bfebe7f0d4b4))

- **mcp**: Expose received_date and batch_transactions on receive_purchase_order
  ([#505](https://github.com/dougborg/katana-openapi-client/pull/505),
  [`09a4ce9`](https://github.com/dougborg/katana-openapi-client/commit/09a4ce92effda9474bab3810df40d0715a5809c1))

- **mcp**: Extra="forbid" on every input model — surface silent field drops
  ([#514](https://github.com/dougborg/katana-openapi-client/pull/514),
  [`605d923`](https://github.com/dougborg/katana-openapi-client/commit/605d9239f7d2dc7cfcc18bad2f47bfebe7f0d4b4))

- **mcp**: Extra="forbid" on every input model — surface silent field drops (#487)
  ([#514](https://github.com/dougborg/katana-openapi-client/pull/514),
  [`605d923`](https://github.com/dougborg/katana-openapi-client/commit/605d9239f7d2dc7cfcc18bad2f47bfebe7f0d4b4))

- **mcp**: Preserve additional_info across modify_purchase_order PATCH
  ([`0ca4640`](https://github.com/dougborg/katana-openapi-client/commit/0ca46405df73575fd602e21a89d73ad081fb5693))

### Chores

- **mcp**: Update client dependency to v0.56.1
  ([`ee5a69d`](https://github.com/dougborg/katana-openapi-client/commit/ee5a69d3b8667ae8b4032842bb98d93a8644281f))

- **release**: Mcp v0.55.0
  ([`d41098e`](https://github.com/dougborg/katana-openapi-client/commit/d41098e0f0a4739c03919b058796570163ae5d11))

### Features

- **client**: Remove Inventory helper and rewrite list_low_stock_items
  ([#510](https://github.com/dougborg/katana-openapi-client/pull/510),
  [`2cfccb3`](https://github.com/dougborg/katana-openapi-client/commit/2cfccb38ee551beeb2fba444aa23e79f937ec879))

### Breaking Changes

- **client**: `KatanaClient.inventory` and the `Inventory` helper class are removed. For
  per-SKU stock lookups, call
  `katana_public_api_client.api.inventory.get_all_inventory_point.asyncio_detailed`
  directly with a `sku` filter — the inventory endpoint provides the canonical stock
  view (on-hand, allocations, incoming) without the per-page pagination guess the legacy
  helpers had to make.

## v0.56.1 (2026-05-05)

### Bug Fixes

- **client**: Generated _parse_\* helpers normalize empty dict to None
  ([#511](https://github.com/dougborg/katana-openapi-client/pull/511),
  [`64a9561`](https://github.com/dougborg/katana-openapi-client/commit/64a956134005e21c3b6e01ca7ab74156884c7010))

- **client**: Generated _parse_\* helpers normalize empty dict to None (#509)
  ([#511](https://github.com/dougborg/katana-openapi-client/pull/511),
  [`64a9561`](https://github.com/dougborg/katana-openapi-client/commit/64a956134005e21c3b6e01ca7ab74156884c7010))

- **mcp**: Handle dict shipping_fee from oneOf parser fallthrough in get_sales_order
  ([#508](https://github.com/dougborg/katana-openapi-client/pull/508),
  [`8eec35b`](https://github.com/dougborg/katana-openapi-client/commit/8eec35b6d3b203c1f9ba192fdca46e3bb3f79f87))

### Chores

- **mcp**: Update client dependency to v0.56.0
  ([`c58ebf6`](https://github.com/dougborg/katana-openapi-client/commit/c58ebf677dbcf9f41b4672b6d1ce9d0edfe47d13))

- **release**: Mcp v0.54.0
  ([`20a13b9`](https://github.com/dougborg/katana-openapi-client/commit/20a13b95f43ac7871302064fbc4fa01752188d5b))

### Refactoring

- **client**: Simplify parse-helper post-processor per /simplify review
  ([#511](https://github.com/dougborg/katana-openapi-client/pull/511),
  [`64a9561`](https://github.com/dougborg/katana-openapi-client/commit/64a956134005e21c3b6e01ca7ab74156884c7010))

## v0.56.0 (2026-05-04)

### Bug Fixes

- **ci**: Match breaking-change marker in release pre-check
  ([#453](https://github.com/dougborg/katana-openapi-client/pull/453),
  [`bee7604`](https://github.com/dougborg/katana-openapi-client/commit/bee7604e91a4a3f75dd67562168d7632c2316374))

- **client**: Align spec examples + correct SalesReturnRefundStatus enum
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- **client**: Align spec with live Katana API — required fields, enums, missing fields
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- **client**: Response-schema drift surfaced by validate_response_examples
  ([#421](https://github.com/dougborg/katana-openapi-client/pull/421),
  [`3b835e5`](https://github.com/dougborg/katana-openapi-client/commit/3b835e58ba5d35013081d09738ea321678431dd8))

- **mcp**: Auto-generate stock_transfer_number when caller omits it
  ([#448](https://github.com/dougborg/katana-openapi-client/pull/448),
  [`f35389a`](https://github.com/dougborg/katana-openapi-client/commit/f35389aacf7c3f7bd62e0e272d637f63334f2a2f))

- **mcp**: Canonical confirmation flow — drop elicitation gate, use CallTool for prefab
  buttons ([#436](https://github.com/dougborg/katana-openapi-client/pull/436),
  [`300018d`](https://github.com/dougborg/katana-openapi-client/commit/300018dbf239a3ef4883f20503b5992df7ffb667))

- **mcp**: Coerce LLM-mistyped list inputs back into Python lists
  ([`30f3fd8`](https://github.com/dougborg/katana-openapi-client/commit/30f3fd866ff40d7b7f3fa9364a3c360f65100a96))

- **mcp**: Conform Prefab UI emission to MCP Apps spec (closes #422)
  ([#435](https://github.com/dougborg/katana-openapi-client/pull/435),
  [`cdbe23a`](https://github.com/dougborg/katana-openapi-client/commit/cdbe23aaf67c192399078ef2593a0e99634b7bf8))

- **mcp**: Convert no-rows ValueError in fulfill_sales_order confirm to refusal response
  ([#446](https://github.com/dougborg/katana-openapi-client/pull/446),
  [`407d678`](https://github.com/dougborg/katana-openapi-client/commit/407d67810ad2d91265cfc1d8a7fcdf279b7caf6c))

- **mcp**: Correct katana_url paths for products and materials
  ([#490](https://github.com/dougborg/katana-openapi-client/pull/490),
  [`3ec36b9`](https://github.com/dougborg/katana-openapi-client/commit/3ec36b9d5a844666e5904cbd994af74a180df0f3))

- **mcp**: Drop server-side require_confirmation elicitation gate
  ([#436](https://github.com/dougborg/katana-openapi-client/pull/436),
  [`300018d`](https://github.com/dougborg/katana-openapi-client/commit/300018dbf239a3ef4883f20503b5992df7ffb667))

- **mcp**: Enforce BLOCK gates on confirm path; demote cache-miss to advisory
  ([#446](https://github.com/dougborg/katana-openapi-client/pull/446),
  [`407d678`](https://github.com/dougborg/katana-openapi-client/commit/407d67810ad2d91265cfc1d8a7fcdf279b7caf6c))

- **mcp**: Fan out parent sync to related entity specs
  ([#462](https://github.com/dougborg/katana-openapi-client/pull/462),
  [`fc47b66`](https://github.com/dougborg/katana-openapi-client/commit/fc47b66f8b464b4870ae2d83dffdbaf9c0a9319a))

- **mcp**: Inline preview→apply args instead of templating from iframe state
  ([#493](https://github.com/dougborg/katana-openapi-client/pull/493),
  [`c265bc8`](https://github.com/dougborg/katana-openapi-client/commit/c265bc87bba54b27f20d24ca9bbf1f5bef37e44b))

- **mcp**: Mirror Katana soft-delete semantics in typed cache
  ([#462](https://github.com/dougborg/katana-openapi-client/pull/462),
  [`fc47b66`](https://github.com/dougborg/katana-openapi-client/commit/fc47b66f8b464b4870ae2d83dffdbaf9c0a9319a))

- **mcp**: Populate preview UIs with fetched data; add BLOCK warning marker (closes
  #443) ([#446](https://github.com/dougborg/katana-openapi-client/pull/446),
  [`407d678`](https://github.com/dougborg/katana-openapi-client/commit/407d67810ad2d91265cfc1d8a7fcdf279b7caf6c))

- **mcp**: Preview branches must fetch backing data; add BLOCK warning marker
  ([#446](https://github.com/dougborg/katana-openapi-client/pull/446),
  [`407d678`](https://github.com/dougborg/katana-openapi-client/commit/407d67810ad2d91265cfc1d8a7fcdf279b7caf6c))

- **mcp**: Render prior_state in markdown, fix verify label, snapshot on delete preview
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Strip Prefab wire envelope from structured_content (mitigation for #422)
  ([#423](https://github.com/dougborg/katana-openapi-client/pull/423),
  [`d1234ef`](https://github.com/dougborg/katana-openapi-client/commit/d1234efeff7a6e54f1160aeaefe9c7577e6468ed))

- **mcp**: Sync row-level entities for PO and SO to catch tombstones
  ([#462](https://github.com/dougborg/katana-openapi-client/pull/462),
  [`fc47b66`](https://github.com/dougborg/katana-openapi-client/commit/fc47b66f8b464b4870ae2d83dffdbaf9c0a9319a))

- **mcp**: Typed-cache freshness — soft-delete semantics + parent/child sync coupling
  ([#462](https://github.com/dougborg/katana-openapi-client/pull/462),
  [`fc47b66`](https://github.com/dougborg/katana-openapi-client/commit/fc47b66f8b464b4870ae2d83dffdbaf9c0a9319a))

- **mcp**: Wire feedback handlers on every Confirm-button click (#495)
  ([#496](https://github.com/dougborg/katana-openapi-client/pull/496),
  [`786576c`](https://github.com/dougborg/katana-openapi-client/commit/786576cdc12fa65ced7f4e4f057dfacc362ec36d))

- **scripts**: Handle non-branch local refs in pre-push-guard
  ([#434](https://github.com/dougborg/katana-openapi-client/pull/434),
  [`b3d727b`](https://github.com/dougborg/katana-openapi-client/commit/b3d727b1f66b988cd70735084f862cfd371906ca))

- **test**: Mark test_documentation_search_functionality as docs
  ([#436](https://github.com/dougborg/katana-openapi-client/pull/436),
  [`300018d`](https://github.com/dougborg/katana-openapi-client/commit/300018dbf239a3ef4883f20503b5992df7ffb667))

### Build System

- **scripts**: Add audit_spec_drift + validate_spec_examples + poe tasks
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- **scripts**: Add validate_response_examples.py + capture findings
  ([#421](https://github.com/dougborg/katana-openapi-client/pull/421),
  [`3b835e5`](https://github.com/dougborg/katana-openapi-client/commit/3b835e58ba5d35013081d09738ea321678431dd8))

- **scripts**: Pull canonical OpenAPI spec from the live API gateway
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- **scripts**: Replace HTML-scrape with two-spec ssr-props pull, retire legacy
  ([#421](https://github.com/dougborg/katana-openapi-client/pull/421),
  [`3b835e5`](https://github.com/dougborg/katana-openapi-client/commit/3b835e58ba5d35013081d09738ea321678431dd8))

### Chores

- Add pre-push hook blocking direct pushes to main from non-main branches
  ([#434](https://github.com/dougborg/katana-openapi-client/pull/434),
  [`b3d727b`](https://github.com/dougborg/katana-openapi-client/commit/b3d727b1f66b988cd70735084f862cfd371906ca))

- Delete obsolete agent docs (AGENT_WORKFLOW.md + 3 guides), add dual-sequence ADR note
  ([#418](https://github.com/dougborg/katana-openapi-client/pull/418),
  [`d436088`](https://github.com/dougborg/katana-openapi-client/commit/d436088f8c0284b8d3ee2828c40f474025997898))

- Mechanical docs cleanup — delete one-shot scripts, archive v0.1.0 plan, fix
  typed-cache docstring
  ([#417](https://github.com/dougborg/katana-openapi-client/pull/417),
  [`8382cf4`](https://github.com/dougborg/katana-openapi-client/commit/8382cf4ecbca5ac75c8f050d4691f12d2ddd22a8))

- Sync uv.lock with released package versions
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- Tech-debt sweep — narrow bare excepts, drop dead clear_registry
  ([#460](https://github.com/dougborg/katana-openapi-client/pull/460),
  [`c07005a`](https://github.com/dougborg/katana-openapi-client/commit/c07005ad750ed103cd34e327251bd23747b6a451))

- **deps)(deps**: Bump the python-minor-patch group with 5 updates
  ([#489](https://github.com/dougborg/katana-openapi-client/pull/489),
  [`f1ec431`](https://github.com/dougborg/katana-openapi-client/commit/f1ec431657e14ce3d131804e7bcc4bbae72af821))

- **mcp**: Post-#342 review nits — fixture renames + factories TYPE_CHECKING cleanup
  ([#415](https://github.com/dougborg/katana-openapi-client/pull/415),
  [`cf7c98a`](https://github.com/dougborg/katana-openapi-client/commit/cf7c98a73cf2dee7614ff1f3c492eae941074901))

- **mcp**: Tighten katana_url helpers per simplify-pass review
  ([#448](https://github.com/dougborg/katana-openapi-client/pull/448),
  [`f35389a`](https://github.com/dougborg/katana-openapi-client/commit/f35389aacf7c3f7bd62e0e272d637f63334f2a2f))

- **mcp**: Use ShowToast for Cancel buttons (drop SendMessage round-trip)
  ([#440](https://github.com/dougborg/katana-openapi-client/pull/440),
  [`0905bcd`](https://github.com/dougborg/katana-openapi-client/commit/0905bcda739b8f6d6a9b6cc51f7402a5a73c5b7c))

- **release**: Mcp v0.44.0
  ([`c01385a`](https://github.com/dougborg/katana-openapi-client/commit/c01385ae18461a53237ede93870ffe9d80fd87c7))

- **release**: Mcp v0.44.1
  ([`dfc75f0`](https://github.com/dougborg/katana-openapi-client/commit/dfc75f09ee278d32f063b9c88cba9c28c05e357d))

- **release**: Mcp v0.45.0
  ([`9a1d394`](https://github.com/dougborg/katana-openapi-client/commit/9a1d394bc2bf64f9b19d4e43c870a453b34ea3f1))

- **release**: Mcp v0.45.1
  ([`4f6015e`](https://github.com/dougborg/katana-openapi-client/commit/4f6015e0eac4637885539464298bebdc57ea7507))

- **release**: Mcp v0.46.0
  ([`3d8c0a1`](https://github.com/dougborg/katana-openapi-client/commit/3d8c0a18d1186529115c10fd7d7f8abefcb3c8fb))

- **release**: Mcp v0.46.1
  ([`47d3d49`](https://github.com/dougborg/katana-openapi-client/commit/47d3d49c2a72696ad7269f6f6fdab1f3b27df8e0))

- **release**: Mcp v0.47.0
  ([`a235f12`](https://github.com/dougborg/katana-openapi-client/commit/a235f122d233119070021880a62847156957bd97))

- **release**: Mcp v0.47.1
  ([`4993383`](https://github.com/dougborg/katana-openapi-client/commit/4993383b9c553044c4250bce3d7cc3e38f10959d))

- **release**: Mcp v0.48.0
  ([`971781b`](https://github.com/dougborg/katana-openapi-client/commit/971781b81dcc12b870a1fe87277aef26ce1a31cf))

- **release**: Mcp v0.49.0
  ([`14fec17`](https://github.com/dougborg/katana-openapi-client/commit/14fec17347ed088f8018461698d886ac31981b7f))

- **release**: Mcp v0.50.0
  ([`ae0ba31`](https://github.com/dougborg/katana-openapi-client/commit/ae0ba3142674956f6d277587d2ebfe5454c45a66))

- **release**: Mcp v0.51.0
  ([`45337ed`](https://github.com/dougborg/katana-openapi-client/commit/45337ed0b4ffd4664cfffe73be931064c4a27c3f))

- **release**: Mcp v0.51.1
  ([`cd08f6e`](https://github.com/dougborg/katana-openapi-client/commit/cd08f6e6e036c97af219c37867c751f3d585fa3b))

- **release**: Mcp v0.52.0
  ([`66f893f`](https://github.com/dougborg/katana-openapi-client/commit/66f893f13fa48c26df118ce0a3eb04b6910b4c3b))

- **release**: Mcp v0.52.1
  ([`1ee37c6`](https://github.com/dougborg/katana-openapi-client/commit/1ee37c69778e5057c1daf1d7a5e2eab94a4c7f98))

- **release**: Mcp v0.53.0
  ([`dd4143e`](https://github.com/dougborg/katana-openapi-client/commit/dd4143e83e16c7118291de4ffa1ec2d483c62820))

### Continuous Integration

- **docs**: Also set NO_MKDOCS_2_WARNING (silences Material's banner)
  ([#424](https://github.com/dougborg/katana-openapi-client/pull/424),
  [`770ef4d`](https://github.com/dougborg/katana-openapi-client/commit/770ef4def081de661cff545b512aa44764eec2ee))

### Documentation

- Realign spec-maintenance docs + spec-auditor agent with #420/#421 tooling
  ([#424](https://github.com/dougborg/katana-openapi-client/pull/424),
  [`770ef4d`](https://github.com/dougborg/katana-openapi-client/commit/770ef4def081de661cff545b512aa44764eec2ee))

- Realign spec-maintenance docs and spec-auditor agent with #420/#421 tooling
  ([#424](https://github.com/dougborg/katana-openapi-client/pull/424),
  [`770ef4d`](https://github.com/dougborg/katana-openapi-client/commit/770ef4def081de661cff545b512aa44764eec2ee))

- **audit**: Refresh upstream spec from live API + add live-spec audit
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- **claude.md**: Add uv.lock drift / pre-commit pitfall
  ([#433](https://github.com/dougborg/katana-openapi-client/pull/433),
  [`50cd212`](https://github.com/dougborg/katana-openapi-client/commit/50cd212290623d50c0f630339ca642cc4d76127a))

- **harness**: Capture /open-pr push-refspec safety in CLAUDE.md + skill
  ([#441](https://github.com/dougborg/katana-openapi-client/pull/441),
  [`b6b020e`](https://github.com/dougborg/katana-openapi-client/commit/b6b020e5ab46e92804420c6fedc3ec7e5998548d))

- **harness**: Codify OpenAPI 3.1 + spec/generator workflow rules in CLAUDE.md
  ([#413](https://github.com/dougborg/katana-openapi-client/pull/413),
  [`bff2bb2`](https://github.com/dougborg/katana-openapi-client/commit/bff2bb2e28e7900c918c4f0eaf6c2aca3957bd39))

- **harness**: Require breaking-change marker for spec/generator changes that drop or
  narrow public surface
  ([#416](https://github.com/dougborg/katana-openapi-client/pull/416),
  [`e09c045`](https://github.com/dougborg/katana-openapi-client/commit/e09c045121e06e25d0d6e42320542ff2574a0675))

- **mcp**: ADR-0020 — consistent tool surface across entity types + cache unification
  ([#477](https://github.com/dougborg/katana-openapi-client/pull/477),
  [`d0a5d81`](https://github.com/dougborg/katana-openapi-client/commit/d0a5d8145b0d157aed345ed943fe1f51657dbeb0))

- **mcp**: Clarify prior_state nullability and applied-vs-verified counts
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Rewrite architecture.md for post-typed-cache / EntitySpec architecture
  ([#419](https://github.com/dougborg/katana-openapi-client/pull/419),
  [`813cf6f`](https://github.com/dougborg/katana-openapi-client/commit/813cf6fc1bc87e63082de03c282d84d138c60df4))

- **mcp**: Update help resource for unified modify\_/delete\_ tool surface
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

### Features

- **client**: Add missing endpoints — custom_field_definitions CRUD +
  sales_orders/search + DELETE /serial_numbers body
  ([#420](https://github.com/dougborg/katana-openapi-client/pull/420),
  [`0fb173f`](https://github.com/dougborg/katana-openapi-client/commit/0fb173f14ac7803377b8dab7e4f10b82d51234cd))

- **client**: Remove broken Inventory.check_stock helper
  ([#507](https://github.com/dougborg/katana-openapi-client/pull/507),
  [`43f438b`](https://github.com/dougborg/katana-openapi-client/commit/43f438bef85e796d2a9d4fb90ddb2c6fa9e97eb0))

- **mcp**: Add 8 purchase order modification tools
  ([#461](https://github.com/dougborg/katana-openapi-client/pull/461),
  [`ce61534`](https://github.com/dougborg/katana-openapi-client/commit/ce615342c554a03e6a8abc1bd6791f4859d8426d))

- **mcp**: Add full PO modification tools + canonical pattern
  ([#461](https://github.com/dougborg/katana-openapi-client/pull/461),
  [`ce61534`](https://github.com/dougborg/katana-openapi-client/commit/ce615342c554a03e6a8abc1bd6791f4859d8426d))

- **mcp**: Add modify_sales_order + delete_sales_order
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Add rebuild_cache tool to force-resync typed cache entities
  ([#497](https://github.com/dougborg/katana-openapi-client/pull/497),
  [`e9268cf`](https://github.com/dougborg/katana-openapi-client/commit/e9268cffe7da37fdc941aeb606a15064cc9cdef4))

- **mcp**: Add shared entity-modification helper
  ([#461](https://github.com/dougborg/katana-openapi-client/pull/461),
  [`ce61534`](https://github.com/dougborg/katana-openapi-client/commit/ce615342c554a03e6a8abc1bd6791f4859d8426d))

- **mcp**: Add variant_ids / sales_order_ids / ingredient_availability filters to
  list_manufacturing_orders
  ([#481](https://github.com/dougborg/katana-openapi-client/pull/481),
  [`0ecc8b6`](https://github.com/dougborg/katana-openapi-client/commit/0ecc8b6bc6d683a5fe756285d05a370d1e5139de))

- **mcp**: Compact MO triage + cross-MO blocking-ingredient rollup
  ([#449](https://github.com/dougborg/katana-openapi-client/pull/449),
  [`8b936d5`](https://github.com/dougborg/katana-openapi-client/commit/8b936d586f58bd9f4b14e1e3e3c0372d3e38cab7))

- **mcp**: Embed katana_url deep-links in tool responses
  ([#448](https://github.com/dougborg/katana-openapi-client/pull/448),
  [`f35389a`](https://github.com/dougborg/katana-openapi-client/commit/f35389aacf7c3f7bd62e0e272d637f63334f2a2f))

- **mcp**: Refactor item modification surface, retire update_item + delete_item
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Refactor MO modification surface, retire recipe-row tools
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Refactor stock-transfer modification surface, retire 3 tools
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Rename confirm parameter to preview across write tools
  ([#492](https://github.com/dougborg/katana-openapi-client/pull/492),
  [`6cfc030`](https://github.com/dougborg/katana-openapi-client/commit/6cfc03040ac428dc8136cd279e6eea72caf2b6e2))

- **mcp**: Surface PO additional-cost row shape, expose cost catalog, reject derived
  fields ([#479](https://github.com/dougborg/katana-openapi-client/pull/479),
  [`724ecba`](https://github.com/dougborg/katana-openapi-client/commit/724ecbac16dbb5216087268487db597ff6ed7154))

- **mcp**: Tolerate JSON-stringified tool args via boundary middleware
  ([#478](https://github.com/dougborg/katana-openapi-client/pull/478),
  [`a865d0c`](https://github.com/dougborg/katana-openapi-client/commit/a865d0c9c7953c7619f811a69bbce47774a62486))

- **mcp**: Unified modification dispatcher + multi-action response shape
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Unified modify\_<entity> + delete\_<entity> tool surface (PR 2)
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Unify PO modification surface into modify_purchase_order +
  delete_purchase_order
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Use CallTool for prefab confirm buttons (drop SendMessage round-trip)
  ([#436](https://github.com/dougborg/katana-openapi-client/pull/436),
  [`300018d`](https://github.com/dougborg/katana-openapi-client/commit/300018dbf239a3ef4883f20503b5992df7ffb667))

### Performance Improvements

- **mcp**: Batch catalog-cache SKU lookups via get_many_by_ids
  ([#456](https://github.com/dougborg/katana-openapi-client/pull/456),
  [`84526cc`](https://github.com/dougborg/katana-openapi-client/commit/84526ccfa6fc68d7a312460421f81a1c5e99c8bc))

### Refactoring

- **client**: Apply mechanical CLAUDE.md anti-pattern fixes from /techdebt
  ([#433](https://github.com/dougborg/katana-openapi-client/pull/433),
  [`50cd212`](https://github.com/dougborg/katana-openapi-client/commit/50cd212290623d50c0f630339ca642cc4d76127a))

- **client**: Mechanical /techdebt fixes — HTTPStatus, broken hasattr in
  get_variant_display_name, dead InventoryHelpers stubs
  ([#433](https://github.com/dougborg/katana-openapi-client/pull/433),
  [`50cd212`](https://github.com/dougborg/katana-openapi-client/commit/50cd212290623d50c0f630339ca642cc4d76127a))

- **mcp**: /simplify after full PR — typed dispatcher, optional fetcher, log fallthrough
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: /simplify after item — None-safe web_url_kind, extract cache helper
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: /simplify after stock-transfer — drop dead code, suppress spurious warning
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Apply remaining /simplify findings before cloning
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Collapse coerce-list field annotations behind type aliases
  ([#428](https://github.com/dougborg/katana-openapi-client/pull/428),
  [`ed73169`](https://github.com/dougborg/katana-openapi-client/commit/ed7316966d6cb169c8162c8f24f1e2df6418438c))

- **mcp**: Collapse confirm builder kwargs and rename confirm → preview
  ([#492](https://github.com/dougborg/katana-openapi-client/pull/492),
  [`6cfc030`](https://github.com/dougborg/katana-openapi-client/commit/6cfc03040ac428dc8136cd279e6eea72caf2b6e2))

- **mcp**: Collapse prefab builder confirm kwargs into single confirm_request
  ([#492](https://github.com/dougborg/katana-openapi-client/pull/492),
  [`6cfc030`](https://github.com/dougborg/katana-openapi-client/commit/6cfc03040ac428dc8136cd279e6eea72caf2b6e2))

- **mcp**: Consolidate cache-name resolution + BLOCK marker per /simplify review
  ([#446](https://github.com/dougborg/katana-openapi-client/pull/446),
  [`407d678`](https://github.com/dougborg/katana-openapi-client/commit/407d67810ad2d91265cfc1d8a7fcdf279b7caf6c))

- **mcp**: Consolidate confirm-button helpers and drop dead state
  ([#498](https://github.com/dougborg/katana-openapi-client/pull/498),
  [`5b23868`](https://github.com/dougborg/katana-openapi-client/commit/5b23868b019b2a16da090f46dd1a49cc4c242425))

- **mcp**: Drop dead Prefab UI builder calls at all tool sites
  ([#423](https://github.com/dougborg/katana-openapi-client/pull/423),
  [`d1234ef`](https://github.com/dougborg/katana-openapi-client/commit/d1234efeff7a6e54f1160aeaefe9c7577e6468ed))

- **mcp**: Extract dispatch primitives — apply factories, plan builders, summary helpers
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Extract run_modify_plan + run_delete_plan drivers, drop dead lookup tables
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Tighten Prefab confirm-button API; drop redundant comments
  ([#436](https://github.com/dougborg/katana-openapi-client/pull/436),
  [`300018d`](https://github.com/dougborg/katana-openapi-client/commit/300018dbf239a3ef4883f20503b5992df7ffb667))

- **mcp**: Tighten unified-modify foundation before cloning to other entities
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

- **mcp**: Unset_dict helper + shared mock_entity_for_modify factory
  ([#464](https://github.com/dougborg/katana-openapi-client/pull/464),
  [`1c56800`](https://github.com/dougborg/katana-openapi-client/commit/1c56800858a080f32305a52342ad29aa6f4b4cd4))

### Testing

- Cache collection-time spec parses + clarify session-fixture docstring per Copilot
  review ([#450](https://github.com/dougborg/katana-openapi-client/pull/450),
  [`80238d8`](https://github.com/dougborg/katana-openapi-client/commit/80238d8e3cfaf8e1242ed98d715b47f27fc88ca9))

- Hoist OpenAPI spec parsing to a session-scoped fixture (was 7 loads, now 1)
  ([#450](https://github.com/dougborg/katana-openapi-client/pull/450),
  [`80238d8`](https://github.com/dougborg/katana-openapi-client/commit/80238d8e3cfaf8e1242ed98d715b47f27fc88ca9))

- Mock asyncio.sleep in test_retry_with_backoff (was 2s, now 0.02s)
  ([#450](https://github.com/dougborg/katana-openapi-client/pull/450),
  [`80238d8`](https://github.com/dougborg/katana-openapi-client/commit/80238d8e3cfaf8e1242ed98d715b47f27fc88ca9))

- Replace wall-clock timing assertion in test_concurrent_requests with structural
  concurrency check ([#450](https://github.com/dougborg/katana-openapi-client/pull/450),
  [`80238d8`](https://github.com/dougborg/katana-openapi-client/commit/80238d8e3cfaf8e1242ed98d715b47f27fc88ca9))

- Tighten test_concurrent_requests per Copilot review
  ([#450](https://github.com/dougborg/katana-openapi-client/pull/450),
  [`80238d8`](https://github.com/dougborg/katana-openapi-client/commit/80238d8e3cfaf8e1242ed98d715b47f27fc88ca9))

- Timing-test flake + speed sweep (saves ~9s = 40% off poe test)
  ([#450](https://github.com/dougborg/katana-openapi-client/pull/450),
  [`80238d8`](https://github.com/dougborg/katana-openapi-client/commit/80238d8e3cfaf8e1242ed98d715b47f27fc88ca9))

- **docs**: Rewrite search test for MkDocs Material output
  ([#457](https://github.com/dougborg/katana-openapi-client/pull/457),
  [`d98e42c`](https://github.com/dougborg/katana-openapi-client/commit/d98e42c7118d255bbf3584f7c611854ea1c8dbac))

- **mcp**: Add unit tests for resource handlers (#206)
  ([#506](https://github.com/dougborg/katana-openapi-client/pull/506),
  [`f5fa57a`](https://github.com/dougborg/katana-openapi-client/commit/f5fa57a0bc47d24a6b21a28e9fe46b66d0d42ff5))

- **mcp**: Isolate cache DB paths in lifespan tests to fix xdist race
  ([#459](https://github.com/dougborg/katana-openapi-client/pull/459),
  [`9090662`](https://github.com/dougborg/katana-openapi-client/commit/9090662078aac6e0ef78927a2b3c812821779a51))

- **mcp**: Pin auto-generation contract for stock_transfer_number
  ([#458](https://github.com/dougborg/katana-openapi-client/pull/458),
  [`62c1540`](https://github.com/dougborg/katana-openapi-client/commit/62c1540ea3c30ac9c99af85623939c5bdbaa1cd5))

### Breaking Changes

- **client**: `katana_public_api_client.helpers.Inventory.check_stock` is removed.
  Third-party callers using `client.inventory.check_stock(sku)` will get an
  AttributeError. Migrate to the inventory API endpoint directly (see migration above) —
  the helper was unreliable because of unfixed pagination + variant-fetch issues; using
  the inventory endpoint is now the supported path.

## v0.55.1 (2026-04-28)

### Bug Fixes

- **client**: Add NO_RECIPE to OutsourcedRecipeIngredientAvailability
  ([#409](https://github.com/dougborg/katana-openapi-client/pull/409),
  [`0611273`](https://github.com/dougborg/katana-openapi-client/commit/06112730bbbd2e29e84592456ba042722283fe41))

## v0.55.0 (2026-04-28)

### Bug Fixes

- **client**: Tighten SalesReturn.refund_status + operators.working_area to enums
  ([#411](https://github.com/dougborg/katana-openapi-client/pull/411),
  [`5d4da09`](https://github.com/dougborg/katana-openapi-client/commit/5d4da09811b2347f4a572d5556f4f13bc14c8bee))

- **client**: Type ManufacturingOrderRecipeRow.ingredient_availability as
  IngredientAvailability
  ([#410](https://github.com/dougborg/katana-openapi-client/pull/410),
  [`ec68692`](https://github.com/dougborg/katana-openapi-client/commit/ec68692fd1f57c06efc936cc1419545b63a41717))

- **mcp**: Address code review: \_context, move \_FETCH_MO_RECIPE constant
  ([#396](https://github.com/dougborg/katana-openapi-client/pull/396),
  [`c4b042f`](https://github.com/dougborg/katana-openapi-client/commit/c4b042f42f09494363913e76497e65ba0214f485))

### Chores

- **mcp**: Update client dependency to v0.54.3
  ([`10ff9a5`](https://github.com/dougborg/katana-openapi-client/commit/10ff9a5a54411dd68b58a10bac232be9f8b58e31))

- **release**: Mcp v0.43.0
  ([`74e8fdb`](https://github.com/dougborg/katana-openapi-client/commit/74e8fdb72c80a676b745e49ad10c1d7cda0d3de2))

### Documentation

- **mcp**: Add ADR-0019 tool description and batch-field conventions
  ([#405](https://github.com/dougborg/katana-openapi-client/pull/405),
  [`02694a9`](https://github.com/dougborg/katana-openapi-client/commit/02694a9efe6577a7fbd4989b70e95eaa3350038e))

- **mcp**: Refresh reporting module docstring + clarify gather safety
  ([#396](https://github.com/dougborg/katana-openapi-client/pull/396),
  [`c4b042f`](https://github.com/dougborg/katana-openapi-client/commit/c4b042f42f09494363913e76497e65ba0214f485))

### Features

- **mcp**: Add ManufacturingOrder→RecipeRow CACHE_RELATIONSHIPS entry
  ([#396](https://github.com/dougborg/katana-openapi-client/pull/396),
  [`c4b042f`](https://github.com/dougborg/katana-openapi-client/commit/c4b042f42f09494363913e76497e65ba0214f485))

- **mcp**: Inventory_velocity batch shape + MO ingredient consumption
  ([#396](https://github.com/dougborg/katana-openapi-client/pull/396),
  [`c4b042f`](https://github.com/dougborg/katana-openapi-client/commit/c4b042f42f09494363913e76497e65ba0214f485))

- **mcp**: Inventory_velocity — batch shape + manufacturing-order consumption
  ([#396](https://github.com/dougborg/katana-openapi-client/pull/396),
  [`c4b042f`](https://github.com/dougborg/katana-openapi-client/commit/c4b042f42f09494363913e76497e65ba0214f485))

### Refactoring

- **client**: Consolidate cache-table generator config behind CacheTableSpec
  ([#407](https://github.com/dougborg/katana-openapi-client/pull/407),
  [`cb34dab`](https://github.com/dougborg/katana-openapi-client/commit/cb34dab5f6ab2005bdedef0d202280f2f0ca0bb7))

### Testing

- **mcp**: Integration tests for inventory_velocity MO filters + min_length
  ([#396](https://github.com/dougborg/katana-openapi-client/pull/396),
  [`c4b042f`](https://github.com/dougborg/katana-openapi-client/commit/c4b042f42f09494363913e76497e65ba0214f485))

## v0.54.3 (2026-04-28)

### Bug Fixes

- **client**: Add PydanticJSON TypeDecorator to fix JSON column serialization of nested
  pydantic models ([#404](https://github.com/dougborg/katana-openapi-client/pull/404),
  [`6767454`](https://github.com/dougborg/katana-openapi-client/commit/67674541ec7b24135d0c8abaa6b8b00b5dc26052))

- **client**: PydanticJSON TypeDecorator fixes JSON column serialization of nested
  pydantic models ([#404](https://github.com/dougborg/katana-openapi-client/pull/404),
  [`6767454`](https://github.com/dougborg/katana-openapi-client/commit/67674541ec7b24135d0c8abaa6b8b00b5dc26052))

### Chores

- **mcp**: Update client dependency to v0.54.2
  ([`756169a`](https://github.com/dougborg/katana-openapi-client/commit/756169af4c5702a4e4471327243600a0bfe8fde8))

## v0.54.2 (2026-04-28)

### Bug Fixes

- **client**: Add BLOCKED to ManufacturingOperationStatus + spec audit report
  ([#408](https://github.com/dougborg/katana-openapi-client/pull/408),
  [`e2c2493`](https://github.com/dougborg/katana-openapi-client/commit/e2c249358e2fa0ddfae509b68cb85c8472f193ac))

### Chores

- **mcp**: Update client dependency to v0.54.1
  ([`b143d68`](https://github.com/dougborg/katana-openapi-client/commit/b143d68dc994cc96b6770aea932a6da393cf7e07))

### Refactoring

- **mcp**: EntitySpec + generic ensure_synced for typed-cache sync
  ([#406](https://github.com/dougborg/katana-openapi-client/pull/406),
  [`4de8394`](https://github.com/dougborg/katana-openapi-client/commit/4de8394f5fd53b2aa65a97121c0c6f99ded3cf64))

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
