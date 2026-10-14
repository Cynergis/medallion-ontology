---
name: design-pipeline
description: >-
  Design a medallion data pipeline for a part of a product, in an OTO project that composes
  `medallion`: the data product and its consumers, the sources and how each is copied to bronze,
  the reference data, the conformed silver entities, the gold outputs and their contracts, the
  derivation and quality rules, the batch flow that runs them and the build plan, checkpoint by
  checkpoint (D1 to D9), each refused by the medallion rules when it contradicts itself and
  reported when it is incomplete. Use when a part of the product is a data pipeline: "design the
  pipeline", "onboard a source", "define the gold output", "the quality rules at gate 2", "declare
  the batch flow", or when a studio's architecture-build reaches a part that follows the medallion
  pattern.
---

# Design a medallion pipeline

A medallion pipeline is a design pattern for a part of a product, not for the whole of it: one
product may model its application with DDD and its data with this pattern, and run both on the
generic `flow`. This skill designs the part that is a pipeline. The `medallion` ontology decides
what to ask: its classes say what an answer looks like, its rules refuse a design that contradicts
itself, and its questions (MD1 to MD29) report what is missing.

The design says **what** the pipeline does, never **how** on a given platform: no engine,
orchestrator, framework or language is captured here. That is the platform binding, a separate
document; if someone names a tool, record it as a decision of the architecture, not on these items.

## Before the first question

1. The project composes `medallion`: `oto status --project <root>` names it, and the vocabulary
   holds `ConformedEntity`. The pattern is chosen when the project starts:
   `oto init --pack <studio> --ontology product-<type>,medallion,flow` beside the others, or
   `oto init --pack "${CLAUDE_PLUGIN_ROOT}"` for a pipeline alone. A report product with a pipeline
   adds the `report-medallion` bridge (its own pack). A project started without `medallion` cannot
   add it afterwards.
2. The architecture comes first when there is one: the systems, components, data stores and
   environments of `software-architecture`. A source system is a `System` another team owns; a
   dataset is a `DataStore`; a contract is an `Interface`. What is already there is referenced,
   never captured twice: the product, roles, personas, terms, decisions, open questions.
3. Which part: the data product this pipeline serves and the outputs it promises. Keep to them.

## How each group is captured

Run OTO's **capture-form** skill on the project's `capture.json` (inside the PRD & Architecture
Studio, its **elicit** skill, which adds the studio's menu). A few related items at a time, in the
words of the person answering, never the ontology's; `kg_define <term>` when a term is unclear.
Every confirmed group goes through the gates as a capture with `scope` the data product:

```bash
oto curate start --project <root>
oto curate propose --project <root> --from captures/<product>-<step>-<group>.json
oto curate add --project <root> --from proposals/<doc>.json
oto curate check --project <root>
oto curate apply --project <root> --by "<who gave it>" --note "<step>: <what it made answerable>"
```

Read the check in the engine's words. **Blocking** is a contradiction: a field both derived and
fed, a rule reading a higher layer than it writes, a step building in the wrong layer, two steps
executing one thing, a person writing silver or gold. Fix the capture and propose it again; never
force. **A gap** is something missing: report it with who can answer it and go on. A person who does
not know an answer leaves the item out; do not guess, and never invent a count, a tolerance or an
example.

## The nine checkpoints

Each step ends at a checkpoint its approver closes. A checkpoint is closed when its gap questions
come back **empty** (`oto query --project <root> questions`, or `kg_ask MD<n>`) and its approver
confirms the catalogue question read back to them: then apply the last group with
`--by "<approver>" --note "checkpoint D<n>: <name>"`. Until then, say what is owed and by whom.
D4 to D7 repeat per entity or output; say which are closed.

| Step | Captures | Gaps, empty to close | Read back | Approver |
|---|---|---|---|---|
| D1 Data product | the `Product`'s `period_kind`, `period_end_rule`, `freshness_sla`; each `Output` by name and grain, `output_of` the product; who `reads_output` | — | MD21 | product owner |
| D2 Sources | `SourceSystem` (kind, access method, whether filters may run there); each `SourceTable` it delivers: keys, date column, `change_behaviour` with its evidence, arrival; its `SourceColumn`s; the `CopyPolicy` that copies it to bronze | MD3, MD4 | MD22 | source owner, platform lead |
| D3 Reference data | the `Term` each column read by silver carries (`TermMapping`, its transform); `CodeSet`s with labels per published language; `CodeMapping`s per source system | MD5, MD6 | MD23 | reference-data steward |
| D4 Conformed model | each `ConformedEntity`: grain, one `IdentityMapping` per source table that feeds it, `ScopeRule` with an expected count and its tolerance, `HistoryPolicy`, the silver `Dataset` and `DatasetField`s it is materialised as | MD7, MD8 | MD24 | platform lead |
| D5 Gold outputs | each `Output` in full: shape (a wide one says why), the entity it `joins_to`, its period dependency, the gold `Dataset`; its `DataContract`: version, fields, keys, change policy, who consumes it | MD10 | MD25 | analyst, product owner |
| D6 Rules | each `DerivationRule`: kind, logic as a pattern, inputs, period dependency; every gold field `derived_by` a rule or `fed_by` a column or field, never both; a `RuleExample` worked out by a person, not by you; its `EdgeCase`s | MD9, MD11 | MD26, MD12 | analyst |
| D7 Quality | each `QualityRule` at its gate (1 bronze, 2 silver, 3 gold): targets, assertion, hard or soft (a soft one says why), `Tolerance`, `FailureAction` (who is told, which runbook), a row that should fail it | MD13, MD14 | MD27, MD19 | platform lead, approver |
| D8 Flow | once per data product, after D6 and D7 are closed: see below | MD15, MD16, MD17 | MD1, MD2, MD28 | platform lead |
| D9 Build plan | the `Identity`s that run or read it, per `Environment`, with their access; the `Runbook`s and the step each `resumes_from` | — | MD18, MD29 | platform lead |

The five standard edge cases of a rule (a tie, a null input, missing history, an entity younger
than the lookback, a duplicate input) are warnings until answered: ask each one, and record what
the rule does, not that it is "handled".

## D8: the flow

The batch run is plain `flow` data: a `Flow` with `flowKind: medallion`, its `trigger`, and
`resumable`. Each `Step` declares its `stepKind`, one of `create_batch`, `check_sources_ready`,
`copy_to_bronze`, `run_gate` (with its `gate`: 1, 2 or 3), `build_reference`, `build_entity`,
`build_output`, `reconcile`, `mark_validated`; what it `waitsFor`; its `parallelGroup`; the
`Artifact`s it `reads` and `writes`, each with its `layer` and the dataset or source table it
`represents`; and the copy policy, entity, output or rule it `executes`. A gate step `hasCheck`
the flow `Check`s that carry out its hard quality rules (`carried_out_by`).

The medallion rules check the order and the layers at every capture: sources checked after the
batch opens, gate 1 after every copy, silver after gate 1, gold after gate 2, validation last; no
step reads a higher layer than it writes; parallel steps share no written artifact; no cycle of
waits. Draft the steps from D2 to D7 (one copy per copy policy, one build per entity and output,
one gate per layer), show them to the platform lead as a table (step, kind, waits for, group,
reads, writes, executes), and capture what they confirm.

## Finishing, and the build

Report the checkpoints: which are closed, by whom; the open gaps per step with who can answer
each. A design is ready to build when D1 to D9 are closed. Building is the `flow` pack's
**implement-step** skill, one step at a time, with the step's brief in hand (`kg_brief`); the
platform binding says how each step kind is realised. For a report fed by this pipeline, the
`report-medallion` bridge links a report's table to the gold dataset it reads (RM1 traces a
report's value back to its source column).

Show the pipeline with this pack's **lineage** view: pick a gold or silver field and it walks up to
the source column, with the step that builds each part and the quality rules that guard it, and the
gaps on the way. Every project that declares this pack has it: `oto serve --project <root> --http
<port>` lists it on the project's home page beside the other packs' views, `oto build --project
<root> --target site` writes it into the site, and `--view lineage` shows it alone.

Do not edit the vocabulary, another data product's items, or anything outside this pipeline.
