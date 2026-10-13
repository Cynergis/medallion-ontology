# Medallion pipeline

Extends `software-architecture` (and so `product` and `portfolio`) and `flow`. A medallion data
pipeline's batch run is plain `flow` data: steps that wait for each other, gates as steps with
checks, tables as artifacts. A `Flow` whose `flowKind` is `medallion` is governed by this
ontology's rules, checked when the flow is captured (`oto curate check` refuses a flow that breaks
one):

- the step kinds are the medallion's (`Step.stepKind`): `create_batch`, `check_sources_ready`, `copy_to_bronze`, `run_gate`, `build_reference`, `build_entity`, `build_output`, `reconcile`, `mark_validated`;
- `create_batch`, `check_sources_ready` and `mark_validated` appear exactly once, and each gate
  (`Step.gate`: 1, 2, 3) runs exactly once;
- the order and the gate placement: the sources are checked after the batch opens, copied after
  they are ready, gate 1 after every copy, silver after gate 1, gate 2 after every entity, gold
  after gate 2, gate 3 after every output, the batch validated after gate 3 and every
  reconciliation;
- the layer direction (`Artifact.layer`): no step reads a higher layer than it writes; a copy
  writes bronze, an entity silver, an output gold; an output reads no other output; a gate writes
  no data.

The generic rules come with `flow` (release 2): a step comes after the writer of what it reads, a
parallel group shares no written artifact, no cycle of waits.

Source: the Medallion Pipeline Ontology specification 1.2.0, sections 3.8.1 and 3.8.2. Not yet
here, and next: the design classes of steps D1 to D7 and D9 (sources, reference data, entities,
outputs, rules, quality rules, build plan) and the coverage rules that tie the flow to them.

## The design (release 2)

The classes of the specification's steps D1 to D7 and D9, named per DECISIONS.md, on what
`product` and `software-architecture` already hold: a data product is a `Product`, a business term
a `Term`, a source system a `SourceSystem` (a kind of `System`), a dataset a `Dataset` (a kind of
`DataStore`, so it runs in an environment and has an owner), a contract a `DataContract` (a kind of
`Interface`, so consumers consume it and versions supersede each other).

A step of the flow `executes` the copy policy, entity, output or rule it runs, and an artifact of
the flow `represents` its dataset or source table. A design that contradicts itself is refused at
capture (a field both derived and fed, a rule reading a higher layer, a step executing what its kind
does not build, two steps executing one thing, an artifact in another layer than its dataset, a
person writing silver or gold). What is missing is a gap, reported and not blocking: the questions
MD3 to MD17 must come back empty before a step's checkpoint, as the specification's section 5 lists.
