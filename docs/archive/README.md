# Archived documents

Documents that captured a moment in time — implementation plans, refactoring campaigns,
dated audit snapshots, agent-system designs that have since been superseded — get moved
here rather than left in the live tree where they invite confusion.

Conventions:

- Each archived doc lives under `docs/archive/<YYYY-MM>/<filename>.md`, dated by
  *archive month*, not the original-write month.
- The first paragraph of the archived file is a forwarding note explaining when it was
  archived and what to read instead. The rest of the file is preserved verbatim for
  historical context.
- Live-tree references should generally point at the *current* canonical doc, not the
  archived snapshot. Two exceptions where linking into the archive is fine: (a)
  historical context where the snapshot *is* the point (e.g., spec-audit workflows that
  cite past audits as worked examples), and (b) forwarding stubs that need to name the
  predecessor by path. If a live-tree link exists that doesn't fit either case, update
  it to the canonical doc or remove it.

If you need to *update* an archived doc, that's a sign it should be unarchived or its
successor should be updated instead.
