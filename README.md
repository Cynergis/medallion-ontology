# Medallion ontology

The OTO unit for a **medallion data pipeline**: source systems to bronze, silver and gold, for
one or many data products. Its source is the *Medallion Pipeline Ontology* specification 1.2.0
(capture steps D1–D9, completeness rules, a fixed flow vocabulary, platform bindings). The
specification itself is kept by its author; this repository cites its sections.

A medallion pipeline is a design pattern for a *part* of a product: a report product may design
its application with DDD (`ddd`) and its data with this ontology, and run both on the generic
`flow`. The unit therefore extends two others and redefines neither:

- `software-architecture` (and through it `product` and `portfolio`): the systems, components,
  interfaces, data stores and environments a pipeline lives in, and the product it serves;
- `flow` (release 2, ported in [Cynergis/report-ontology](https://github.com/Cynergis/report-ontology)):
  steps that wait for each other, gates as steps with checks, tables as artifacts.

## What is here: the flow slice

The batch run of a pipeline is plain `flow` data. A `Flow` whose `flowKind` is `medallion` is
governed by this unit's rules, checked when the flow is captured: `oto curate check` refuses a
flow that breaks one.

| Section of the specification | Here |
|---|---|
| 3.8.1 step vocabulary | `Step.stepKind` among the nine kinds; `create_batch`, `check_sources_ready`, `mark_validated` once each; each gate (`Step.gate`: 1, 2, 3) once |
| 3.8.2 order, gate placement | sources checked after the batch opens, copied after they are ready; gate 1 after every copy; silver after gate 1; gate 2 after every entity; gold after gate 2; gate 3 after every output; reconcile after gate 3; validated after gate 3 and every reconciliation |
| 3.8.2 layer direction, 3.8.1 reads and writes | `Artifact.layer`; no step reads a higher layer than it writes; a copy writes bronze, an entity silver, an output gold; an output reads no other output; a gate writes no data |
| 3.8.2 declared dependencies, parallel safety, acyclic | the generic rules of `flow` release 2 |

Questions: MD1 (the steps of each medallion flow, their kinds, groups and layers), MD2 (the
gates and their checks). The sample is the specification's worked fund-profile flow (section 7),
with neutral source names.

## The design (release 2)

The classes of the specification's steps D1–D7 and D9, named as decided in
[DECISIONS.md](DECISIONS.md), on what `product` and `software-architecture` already hold:

| Step | Here |
|---|---|
| D1 data product, consumers | `Product` (+ period kind, period end rule, freshness SLA); consumers are roles, personas, or systems that consume a contract |
| D2 sources | `SourceSystem` (a kind of `System`), `SourceTable`, `SourceColumn`, `CopyPolicy` |
| D3 reference data | `Term` (+ data type, unit), `TermMapping`, `CodeSet`, `CodeMapping` |
| D4 conformed model | `ConformedEntity`, `IdentityMapping`, `ScopeRule`, `HistoryPolicy`, `Dataset` (a kind of `DataStore`), `DatasetField` |
| D5 gold outputs | `Output`, `DataContract` (a kind of `Interface`) |
| D6 rules | `DerivationRule`, `EdgeCase`, `RuleExample` |
| D7 quality | `QualityRule` (carried out by a flow `Check` on its gate's step), `Tolerance`, `FailureAction` |
| D8 flow | a step `executes` the copy policy, entity, output or rule it runs; an artifact `represents` its dataset or source table |
| D9 build plan | `Identity`; `PipelineTest` (release 3): a unit, contract, parity, rerun, regression, integration, forced-failure or flow test, what it is a `test_of`, its fixture and expected result; environments and runbooks are `software-architecture`'s |

**Correctness refuses, completeness reports.** A design that contradicts itself is refused at
`oto curate check`: a field both derived and fed, a rule reading a higher layer than it writes, a
step executing what its kind does not build, two steps executing one thing, an artifact in another
layer than its dataset, an entity or output step not writing its table, a person writing silver or
gold, a test of another kind than what it tests. What is missing is a gap, reported, not blocking,
so a design fills group by group: the questions MD3 to MD17 and MD30 to MD34 must come back empty
before a step's checkpoint (the specification's section 5). The five standard edge cases of a rule
are warnings. MD21 to MD29 and MD35 are the catalogue a reviewer reads at each checkpoint.

**The build plan's tests (release 3).** Every derivation rule has a unit test, every output a
parity test, every medallion flow a flow test, and every runbook that resumes it a forced-failure
test (MD30 to MD33); every test says what it runs on (MD34) and what must come out (required). A
unit test proves a rule, a contract or parity test an output, a flow test a flow, a forced-failure
test a quality rule or a runbook; rerun, regression and integration tests may test any of them.
The sample's seven tests close the build plan. A `PipelineTest` is not `flow`'s `TestObligation`,
which a step's checks derive for that step's code (DECISIONS.md).

## The bridge: report-medallion

`ontology/report-medallion` extends `report` and `medallion`, for a report product with a
pipeline: a report's `Table` `is_dataset` the gold dataset it reads, a `Column` `is_field` the
field behind it, a report's `QualityCheck` is `backed_by` the pipeline rule it relies on. A report
reads gold and a column is a field of its table's dataset (refused otherwise); a read dataset has a
contract (a warning). RM1 is a report value's lineage, RM2 the checks a report relies on.

It needs the report ontology at release 5, which composes `QualityCheck`: `oto/report` in
[Cynergis/report-ontology](https://github.com/Cynergis/report-ontology), which CI checks out beside
`flow` (`REPORT_ONTOLOGY`, default `../report-ontology/oto/report`).

## The packs

What a person installs in Claude Code, each embedding its unit and everything the unit extends, so
nothing else is fetched:

- **`medallion`** (`packs/medallion`): the skill **design-pipeline** walks the specification's nine
  checkpoints, D1 to D9, through the curate gates, a checkpoint closing when its gap questions come
  back empty and its approver confirms the catalogue read back to them; the view **lineage** walks a
  gold or silver field up to its source column, with the step that builds each part, the quality
  rules that guard it, and the gaps on the way.
- **`report-medallion`** (`packs/report-medallion`): the bridge alone, for a report product with a
  pipeline. With it in the project, the lineage view draws the report fields that show a value on
  top.

A product names them beside its own pack (engine 0.11.8 or later resolves an installed pack's
ontology by name): `oto init --pack prd-architecture-studio --ontology product-report,ddd,medallion,report-medallion,flow`.
A change to a unit is released by rebuilding it, then `oto pack refresh packs/<name>` for each pack
that embeds it; the tests refuse a pack that embeds an outdated unit.

## Layout

| Path | Contents |
|---|---|
| `ontology/medallion/`, `ontology/report-medallion/` | The two units: manifest, vocabulary, rules, questions, rationale, sample, README. Written by `tools/build.py`; never edited by hand. |
| `tools/build.py`, `tools/design.py` | Write the units: the flow slice in the first, the design slice and the bridge in the second. Change them, run the build, commit both. |
| `packs/medallion/`, `packs/report-medallion/` | The packs: manifest, embedded ontologies (written by `oto pack refresh`, never by hand), skills, the lineage view. |
| `tests/test_packs.py` | Both packs check clean and embed the committed units; the lineage view, built from each pack's sample, walks a gold field to its source, and with the bridge shows the report field on top. |
| `tests/test_medallion.py` | The committed units are what the build writes; both compose and their samples answer every question; the specification's worked instance is accepted, and twenty variants are each refused, flagged or reported as decided. |
| `DECISIONS.md` | What was decided, by whom and when, and why: names, quality levels, contracts, the report link. |

## Use

```bash
python tools/build.py                                     # write ontology/medallion and ontology/report-medallion
FLOW_ONTOLOGY=../report-ontology/oto/flow pytest -q tests  # needs oto-kg 0.11.8 or later
oto pack refresh packs/medallion && oto pack refresh packs/report-medallion   # after a unit changes
oto ontology add <this repository> --path ontology/medallion          # install them on a machine
oto ontology add <this repository> --path ontology/report-medallion
oto init --empty --pack prd-architecture-studio --ontology product-report,ddd,medallion,report-medallion,flow --project <root>
```
