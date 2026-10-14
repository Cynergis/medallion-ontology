# Decisions

What was decided about this ontology, by whom and when, and why. The specification is the
*Medallion Pipeline Ontology* 1.2.0; where this ontology departs from its wording, the reason is here.

## 2026-10-13: the flow slice first, on the generic flow

- **The batch run is plain `flow` data**, not a flow type of its own: steps that wait for each other,
  gates as steps with checks, tables as artifacts. A `Flow` whose `flowKind` is `medallion` is governed
  by this ontology's rules. *Why:* one flow vocabulary for every process (a pipeline's batch run, a
  report's template build); what is specific to a medallion is its step kinds, gates, layers and rules.
- **The specification's validations are rules checked at capture** (`oto curate check` refuses a flow
  that breaks one), not invariants checked when tests run. *Why:* the specification says the plugin
  refuses to close a step while a declaration disagrees with the rules.
- **The generic validations belong to `flow`** (release 2): a step comes after the writer of what it
  reads, a parallel group shares no written artifact, no cycle of waits. The medallion-specific ones
  (step kinds and their multiplicity, order and gate placement, layer direction) belong here.
- **The repository is public**, so the sample uses neutral source names and the specification itself
  is not committed.

Decided by Chiheb Dkhil.

## 2026-10-13: names, quality, contracts, and the report link

Four names of the specification clash with names other ontologies use for other things; a project
that composes them would keep one definition silently.

| Specification | Here | Clashes with | Why this name |
|---|---|---|---|
| `Entity` | `ConformedEntity` | `ddd`'s `Entity` | Names what silver does: conform the sources into one entity |
| `Table`, `Field` | `Dataset`, `DatasetField` | `report`'s `Table`, `Field` | The common data-platform word for a table in a layer; the report's `Table` links to a gold `Dataset` |
| `Rule` | `DerivationRule` | `report`'s `Rule` | Covers derivation, filter, ranking and aggregation: how a value is produced |
| `Transformation` | none: the flow step `implements` the rules, the entity or the copy policy | `report`'s `Transformation` | A flow step already reads, writes and is executed; "exactly one step executes it" then holds by construction |

- **Quality: two levels, no overlap.** A check on bronze, silver or gold data is a medallion
  `QualityRule` at its gate, carried out by a `flow` `Check` on the gate step. The report's
  `QualityCheck` keeps what only the report adds (a rendered value, a label, a page) and may cite the
  gold rule it relies on. *Why:* each check is captured once, where it runs; two reports reading one
  gold table do not write the same check twice.
- **Contracts: `DataContract`, a kind of `software-architecture`'s `Interface`.** It carries the
  specification's version, fields, keys and change policy; consumers `consume` it, versions
  `supersede` each other, it has an owner, and every architecture question about interfaces includes
  it. *Why:* a gold table's contract is an interface others depend on; a subclass keeps the
  specification's precision without declaring consumption, versioning and ownership again.
- **The report link: a bridge ontology, `report-medallion`**, extending `report` and `medallion`. It
  says a report's `Table` is the gold `Dataset` it reads and a `Column` the `DatasetField` behind it,
  with the rules that follow. *Why:* a report without a pipeline, or a pipeline without a report,
  never carries the other's vocabulary; a report product with a pipeline adds the bridge at init.

Decided by Chiheb Dkhil.

## 2026-10-13: the packs

- **The bridge is its own pack, `report-medallion`**, beside `medallion`. *Why:* a pack embeds one
  ontology and what it extends, and a refresh rewrites what it embeds; a pipeline with no report
  must not carry the report vocabulary, so the medallion pack cannot carry the bridge.
- **The lineage view lives in the `medallion` pack**, and draws the report side only when the bridge
  is in the project (`$optional`). A project started from another pack names it by path. *Why:* the
  lineage is the pipeline's; the report is one consumer of it.
- **A checkpoint closes when its gap questions come back empty and its approver confirms**: the last
  group of the step is applied with the approver as `--by`. What is missing is reported, never
  invented. *Why:* the specification's "a step cannot close with a proposed instance in it", on the
  gates the engine already has.

The bridge's own pack decided by Chiheb Dkhil; the view's place and the checkpoint rule proposed
with the packs, confirmed by merging them.

## 2026-10-14: the build plan's tests (release 3)

- **A test the build plan promises is a `PipelineTest`**: its kind, what it is a `test_of` (a
  derivation rule, a quality rule, an output, a runbook or a flow), what it runs on (`fixture`) and
  what must come out (`expected_result`, required). *Why:* the implementation agent writes each test
  from its fixture and expected result, and what nothing tests shows as missing. The specification's
  name *Test* would read as any test of the product; `flow`'s `TestObligation` is another thing,
  derived from a step's checks for that step's code, not promised by the build plan for the design.
- **The specification's eight kinds**: unit, contract, parity, rerun, regression, integration,
  forced failure, flow. Five are tied to what they prove, refused otherwise: a unit test a rule
  (derivation or quality), a contract or parity test an output, a flow test a flow, a forced-failure
  test a quality rule or a runbook. Rerun, regression and integration tests may test any of them.
  *Why:* each kind is generated from one template; a parity test of a rule has nothing to compare.
- **What is missing is a gap, as for the rest of the design** (MD30 to MD34): a derivation rule with
  no unit test, an output with no parity test, a medallion flow with no flow test, a runbook that
  resumes it with no forced-failure test, a test that does not say what it runs on. D9 closes when
  they come back empty; MD35 is its read-back. A test with no expected result is not captured.
- **The relation is `test_of`, not `exercises`**: `product` already declares `exercises` (a
  scenario is a concrete path through a requirement or a journey step), and a relation keeps one domain across the ontologies a product
  composes.
- **The lineage page shows how each rule and output is tested**, and says so when nothing tests it.

Proposed with release 3, confirmed by merging it.
