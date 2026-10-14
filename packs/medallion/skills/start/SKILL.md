---
name: start
description: >-
  Start or extend an OTO knowledge project in this domain: Design a medallion data pipeline for a part of a product, source systems to bronze, silver and gold, checkpoint by checkpoint (D1-D9), and the batch flow that runs it, checked by the medallion rules at every capture. The pack 'medallion' (release 1) embeds the ontology 'medallion' (release 3), which declares SourceSystem, SourceTable, SourceColumn, CopyPolicy, TermMapping, CodeSet, CodeMapping, ConformedEntity and more. Use when someone wants a knowledge graph, a vocabulary or an interview for this domain.
---

# Medallion pipeline

Design a medallion data pipeline for a part of a product, source systems to bronze, silver and gold, checkpoint by checkpoint (D1-D9), and the batch flow that runs it, checked by the medallion rules at every capture.

This skill comes with the `medallion` pack. The ontology is inside the pack, so nothing is fetched.

## Talking with the person

- **Plain, natural language, in the person's words.** Never say question numbers, ids, class or
  field names, file names or commands, and never paste what a command printed.
- **Technical details only when the person asks for them.** Never offer them, not even as a choice.
- **The same clear shape every time:** say what we are about to do, ask a few questions at a time,
  read back what you understood in plain sentences, confirm, then say what is next.

**A design pattern of `software-architecture`**: for a part of a product that is a medallion data pipeline: its sources, its bronze, silver and gold layers, its rules and the batch flow that runs them. In a project that composes `software-architecture`, such a part is modelled
with this pack's **design-pipeline** skill (`/medallion:design-pipeline`); `oto status` lists the project's patterns.

1. **Start a project from this pack.**

   ```bash
   oto init --name "<project name>" --pack "${CLAUDE_PLUGIN_ROOT}" --project <root>
   ```

   `${CLAUDE_PLUGIN_ROOT}` is this pack's directory; Claude Code fills it in. Outside Claude Code,
   with the pack on the machine (`oto pack add medallion`), `oto init --pack medallion` does the same.
   The project records the ontology's origin, so `oto status` says when a newer release exists and
   `oto ontology diff` shows what changed. Add `--ontology <name>,...` to merge other ontologies
   with the pack's (a product type, the flow).

2. **Go on with this pack's skills**, written for this domain:

   - **medallion:design-pipeline**: Design a medallion data pipeline for a part of a product, in an OTO project that composes `medallion`.

3. **For anything else, the engine's skills**: capture-form to answer the vocabulary's
   questions in an interview, ontology-interview to fit the vocabulary to the documents at hand,
   build-knowledge-base for a folder of documents, query-knowledge for questions. The engine
   plugin `oto` comes with this pack: the `kg_*` tools and the generic skills are available once
   it is installed.

## What the ontology declares

- **SourceSystem**: A system the pipeline reads from, and how: its kind, the access method, whether filters may run on its side (D2).
- **SourceTable**: One table or feed of a source system, with its contract: keys, the column a row's date is in, how it changes over time and the evidence for it, when it arrives (D2).
- **SourceColumn**: A column of a source table: its name, source type, nullability and unit, and the business term it carries (D2, D3).
- **CopyPolicy**: How a source table reaches bronze: a period slice, new rows by watermark, an as-of read or a change feed; the lookback, the source-side filter, the retention (D2).
- **TermMapping**: How a source column becomes a business term: the transform from the source form to the canonical one (D3).
- **CodeSet**: A list of allowed values with their labels per published language (D3).
- **CodeMapping**: Which value of a source system means which canonical value of a code set (D3).
- **ConformedEntity**: A silver business entity, resolved once across sources: its grain, how each source's id maps to its key, which instances are in scope, how history is kept, the table it is materialised as (D4). The specification's Entity, renamed (DECISIONS.md).
- **IdentityMapping**: How one source table's id becomes the conformed key: the id columns, their transform, the target key fields (D4).
- **ScopeRule**: Which instances of an entity are in scope, how many there should be, by whose count, and how far off the count may be (D4).
- **HistoryPolicy**: Whether an entity keeps history, and how: none, a snapshot per batch, or validity ranges (D4).
- **Dataset**: A physical table or view of the pipeline, in one layer, with its grain, partitioning and fields (D4, D5). The specification's Table, renamed; a kind of DataStore, so it runs in an environment and has an owner.
- **DatasetField**: A field of a dataset: its type, whether it is required, the business term it carries, and either the rule that derives it or what feeds it (D4, D5). The specification's Field, renamed.
- **Output**: A gold dataset a consumer reads: its shape, the silver entity it is keyed on, whether it needs a window of periods, the data product it belongs to (D5).
- **DataContract**: A versioned shape of a dataset others depend on: its fields, keys and change policy (D5). A kind of Interface: consumers consume it, a version supersedes the one before it, it has an owner.
- **DerivationRule**: How one field is produced, or rows are filtered: its kind, its logic as a pattern of the vocabulary, its inputs, its behaviour on the standard edge cases, and an example (D6). The specification's Rule, renamed.
- **EdgeCase**: What a derivation rule does on one edge case: a tie, a null input, missing history, an entity younger than the lookback, a duplicate input (D6).
- **RuleExample**: One real input and the output a derivation rule must give for it, worked out by someone other than the generating agent (D6).
- **QualityRule**: What must be true of the data at one gate (1 landing to bronze, 2 bronze to silver, 3 silver to gold): its targets, its assertion, hard or soft, its tolerance, what happens when it fails, a row that should fail it (D7). Carried out by a flow check on the gate's step.
- **Tolerance**: How far off a count or a figure may be, in which unit, set by whom (D4, D7).
- **FailureAction**: What happens when a quality rule fails: who is told, which runbook they follow, whether the step retries (D7).
- **Identity**: A principal the pipeline runs as or a person who reads it: its kind, the environment, its access to datasets (D9).
- **PipelineTest**: A test the build plan promises, and what it proves: its kind (unit, contract, parity, rerun, regression, integration, forced failure, flow), the rule, output, runbook or flow it tests, what it runs on and what must come out (D9). Not a flow TestObligation, which a step's checks derive for its code (DECISIONS.md).

## The views it ships

- `lineage`: `oto serve --http <port> --view lineage`, or `oto build --target site --view lineage`
