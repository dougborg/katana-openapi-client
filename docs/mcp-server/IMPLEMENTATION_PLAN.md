# MCP Server Implementation Plan

This document tracks the implementation of the Katana MCP Server as defined in
[ADR-010](../adr/0010-katana-mcp-server.md).

## Overview

- **Total Issues**: 24
- **Total Estimate**: 110-146 hours (~3 weeks with 2-3 developers)
- **Architecture**: Monorepo with uv workspace
- **Target**: v0.1.0 MVP release

## Milestones

### Milestone 1: Infrastructure Setup (Week 1)

**Goal**: Repository structure and basic server ready

- Issue #1: Set up uv workspace
- Issue #2: Create package structure
- Issue #3: Basic FastMCP server

**Completion Criteria**: Server runs and authenticates, ready for tools

### Milestone 2: Core Tools (Week 1-2)

**Goal**: All 12 tools implemented and tested

**Inventory Tools** (Issues #4-6):

- Issue #4: check_inventory
- Issue #5: list_low_stock_items
- Issue #6: search_products

**Sales Order Tools** (Issues #7-9):

- Issue #7: create_sales_order
- Issue #8: get_sales_order_status
- Issue #9: list_recent_sales_orders

**Purchase Order Tools** (Issues #10-12):

- Issue #10: create_purchase_order
- Issue #11: get_purchase_order_status
- Issue #12: receive_purchase_order

**Manufacturing Tools** (Issues #13-15):

- Issue #13: create_manufacturing_order
- Issue #14: get_manufacturing_order_status
- Issue #15: list_active_manufacturing_orders

**Completion Criteria**: All 12 tools working with tests

### Milestone 3: Resources & Prompts (Week 3)

**Goal**: MCP resources and workflow prompts

- Issue #16: Inventory resources
- Issue #17: Order resources
- Issue #18: Manufacturing resources
- Issue #19: Workflow prompts

**Completion Criteria**: 5 resources + 3 prompts implemented

### Milestone 4: Documentation & Release (Week 3)

**Goal**: Production-ready v0.1.0 release

- Issue #20: Comprehensive documentation
- Issue #21: Integration tests
- Issue #22: Usage examples
- Issue #23: PyPI publishing setup
- Issue #24: Release checklist

**Completion Criteria**: v0.1.0 published to PyPI

## Dependency Graph

```mermaid
graph TD
    %% Infrastructure Layer (Green)
    I1[#1: UV Workspace<br/>2-4h]:::infra
    I2[#2: Package Structure<br/>2-3h]:::infra
    I3[#3: Basic Server<br/>4-6h]:::infra

    %% Inventory Tools (Blue)
    T4[#4: check_inventory<br/>4-6h]:::inventory
    T5[#5: list_low_stock<br/>4-6h]:::inventory
    T6[#6: search_products<br/>4-6h]:::inventory

    %% Sales Order Tools (Purple)
    T7[#7: create_sales_order<br/>6-8h]:::sales
    T8[#8: get_so_status<br/>3-4h]:::sales
    T9[#9: list_recent_so<br/>3-4h]:::sales

    %% Purchase Order Tools (Orange)
    T10[#10: create_po<br/>6-8h]:::purchase
    T11[#11: get_po_status<br/>3-4h]:::purchase
    T12[#12: receive_po<br/>4-6h]:::purchase

    %% Manufacturing Tools (Red)
    T13[#13: create_mo<br/>6-8h]:::manufacturing
    T14[#14: get_mo_status<br/>3-4h]:::manufacturing
    T15[#15: list_active_mo<br/>3-4h]:::manufacturing

    %% Resources (Cyan)
    R16[#16: Inventory Resources<br/>4-6h]:::resource
    R17[#17: Order Resources<br/>4-6h]:::resource
    R18[#18: Mfg Resources<br/>4-6h]:::resource

    %% Prompts & Docs (Yellow)
    P19[#19: Workflow Prompts<br/>4-6h]:::prompt
    D20[#20: Documentation<br/>6-8h]:::docs
    D21[#21: Integration Tests<br/>6-8h]:::docs
    D22[#22: Examples<br/>3-4h]:::docs

    %% Release (Gray)
    RL23[#23: PyPI Setup<br/>3-4h]:::release
    RL24[#24: Release Checklist<br/>4-6h]:::release

    %% Dependencies - Infrastructure
    I1 --> I2
    I2 --> I3

    %% Dependencies - Tools require server
    I3 --> T4
    I3 --> T7
    I3 --> T10
    I3 --> T13

    %% Dependencies - Tool groups
    T4 --> T5
    T4 --> T6
    T7 --> T8
    T7 --> T9
    T10 --> T11
    T10 --> T12
    T13 --> T14
    T13 --> T15

    %% Dependencies - Resources require tools
    T4 --> R16
    T8 --> R17
    T11 --> R17
    T14 --> R18

    %% Dependencies - Prompts require multiple tools
    T4 --> P19
    T7 --> P19
    T13 --> P19

    %% Dependencies - Documentation requires all tools
    T4 --> D20
    T5 --> D20
    T6 --> D20
    T7 --> D20
    T8 --> D20
    T9 --> D20
    T10 --> D20
    T11 --> D20
    T12 --> D20
    T13 --> D20
    T14 --> D20
    T15 --> D20
    R16 --> D20
    R17 --> D20
    R18 --> D20
    P19 --> D20

    %% Dependencies - Integration tests require all tools
    T4 --> D21
    T7 --> D21
    T10 --> D21
    T13 --> D21

    %% Dependencies - Examples require docs
    D20 --> D22

    %% Dependencies - Release requires package structure
    I2 --> RL23

    %% Dependencies - Final release requires everything
    D20 --> RL24
    D21 --> RL24
    D22 --> RL24
    RL23 --> RL24

    %% Styling
    classDef infra fill:#90EE90,stroke:#333,stroke-width:2px,color:#000
    classDef inventory fill:#87CEEB,stroke:#333,stroke-width:2px,color:#000
    classDef sales fill:#DDA0DD,stroke:#333,stroke-width:2px,color:#000
    classDef purchase fill:#FFB347,stroke:#333,stroke-width:2px,color:#000
    classDef manufacturing fill:#FF6B6B,stroke:#333,stroke-width:2px,color:#000
    classDef resource fill:#40E0D0,stroke:#333,stroke-width:2px,color:#000
    classDef prompt fill:#FFD700,stroke:#333,stroke-width:2px,color:#000
    classDef docs fill:#D3D3D3,stroke:#333,stroke-width:2px,color:#000
    classDef release fill:#A9A9A9,stroke:#333,stroke-width:2px,color:#fff
```

## Parallelization Strategy

### Can Work in Parallel (No Dependencies Between Groups)

**Group A - Inventory Tools** (After #3):

- #4, then #5 and #6 can run in parallel

**Group B - Sales Order Tools** (After #3):

- #7, then #8 and #9 can run in parallel

**Group C - Purchase Order Tools** (After #3):

- #10, then #11 and #12 can run in parallel

**Group D - Manufacturing Tools** (After #3):

- #13, then #14 and #15 can run in parallel

**Maximum Parallelization**: After #3 is complete, 4 agents can work simultaneously on
#4, #7, #10, and #13.

### Must Run Sequentially

1. #1 → #2 → #3 (Infrastructure setup)
1. Each tool group's first issue must complete before related issues
1. Resources (#16-18) require their respective tools
1. Documentation (#20-22) requires all tools complete
1. Release (#24) requires everything

## Critical Path

The longest dependency chain determines minimum completion time:

```
#1 → #2 → #3 → #7 → #8 → #17 → #20 → #22 → #24
2h + 3h + 6h + 8h + 4h + 6h + 8h + 4h + 6h = 47 hours minimum
```

With 3 developers working in parallel on independent tasks, realistic completion is
**2-3 weeks**.

## Assignment Strategy

### Week 1 - Infrastructure & First Tools

**Agent 1** (Infrastructure specialist):

- #1: UV workspace setup
- #2: Package structure
- #3: Basic server
- Then: #16 (Inventory resources)

**Agent 2** (Inventory & Purchase Orders):

- Wait for #3
- #4: check_inventory
- #5: list_low_stock_items
- #10: create_purchase_order

**Agent 3** (Sales & Manufacturing):

- Wait for #3
- #7: create_sales_order
- #13: create_manufacturing_order

### Week 2 - Complete Tools & Resources

**Agent 1**:

- #6: search_products
- #17: Order resources
- #23: PyPI setup

**Agent 2**:

- #11: get_purchase_order_status
- #12: receive_purchase_order
- #18: Manufacturing resources

**Agent 3**:

- #8: get_sales_order_status
- #9: list_recent_sales_orders
- #14: get_manufacturing_order_status
- #15: list_active_manufacturing_orders

### Week 3 - Polish & Release

**Agent 1**:

- #20: Comprehensive documentation

**Agent 2**:

- #21: Integration tests

**Agent 3**:

- #19: Workflow prompts
- #22: Usage examples

**All Agents**:

- #24: Release checklist (collaborative final testing)

## Issue Dependencies Reference

Use this when creating issues to set proper `blocked-by` labels:

| Issue | Blocked By         | Blocks                     |
| ----- | ------------------ | -------------------------- |
| #1    | -                  | #2                         |
| #2    | #1                 | #3, #23                    |
| #3    | #2                 | #4, #7, #10, #13           |
| #4    | #3                 | #5, #6, #16, #19, #20, #21 |
| #5    | #4                 | #20                        |
| #6    | #4                 | #20                        |
| #7    | #3                 | #8, #9, #19, #20, #21      |
| #8    | #7                 | #17, #20                   |
| #9    | #7                 | #20                        |
| #10   | #3                 | #11, #12, #20, #21         |
| #11   | #10                | #17, #20                   |
| #12   | #10                | #20                        |
| #13   | #3                 | #14, #15, #19, #20, #21    |
| #14   | #13                | #18, #20                   |
| #15   | #13                | #20                        |
| #16   | #4                 | #20                        |
| #17   | #8, #11            | #20                        |
| #18   | #14                | #20                        |
| #19   | #4, #7, #13        | #20                        |
| #20   | All tools          | #22, #24                   |
| #21   | #4, #7, #10, #13   | #24                        |
| #22   | #20                | #24                        |
| #23   | #2                 | #24                        |
| #24   | #20, #21, #22, #23 | -                          |

## Labels

Each issue should have these labels:

- **Type**: `infrastructure`, `tool`, `resource`, `prompt`, `documentation`, `testing`,
  `release`
- **Domain**: `inventory`, `sales-orders`, `purchase-orders`, `manufacturing`,
  `mcp-server`
- **Milestone**: `phase-1`, `phase-2` (future)
- **Priority**: `p0-critical`, `p1-high`, `p2-medium`, `p3-low`

## Next Steps

1. Create GitHub milestone: "MCP Server v0.1.0 MVP"
1. Create labels in repository
1. Create all 24 issues with proper dependencies
1. Set up GitHub Project board with dependency visualization
1. Assign issues to agents based on availability
