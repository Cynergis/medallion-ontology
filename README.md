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

Next slices: the design classes of steps D1–D7 and D9 (sources, reference data, conformed
entities, gold outputs and contracts, transformation rules, quality rules, the build plan), the
coverage rules that tie the flow to them (every source copied, every entity and output built),
and a `medallion` pack with a pipeline-design skill and a lineage view.

## Layout

| Path | Contents |
|---|---|
| `ontology/medallion/` | The unit: manifest, vocabulary, rules, questions, rationale, sample, README. Written by `tools/build.py`; never edited by hand. |
| `tools/build.py` | Writes the unit. Change it, run it, commit both. |
| `tests/test_medallion.py` | The committed unit is what the build writes; it composes and its sample answers every question; the specification's flow is accepted and ten broken variants are each refused by the right rule. |

## Use

```bash
python tools/build.py                                     # write ontology/medallion
FLOW_ONTOLOGY=../report-ontology/oto/flow pytest -q tests  # needs oto-kg 0.11.7 or later
oto ontology add <this repository> --path ontology/medallion   # install it on a machine
oto init --empty --pack prd-architecture-studio --ontology product-report,ddd,medallion,flow --project <root>
```
