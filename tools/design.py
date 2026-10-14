"""The design slice: the classes of the specification's steps D1 to D7 and D9, how they tie to the flow,
the build plan's tests (release 3), and the bridge to the report ontology. Imported by build.py, which
writes both units.

Names follow DECISIONS.md: ConformedEntity, Dataset and DatasetField, DerivationRule; no Transformation
class (a flow step `executes` the copy policy, entity, output or rule); DataContract is a kind of
Interface; quality has two levels; the report link is the report-medallion bridge.

Correctness is a blocking rule (a fact that contradicts the design is refused at capture). Completeness
is a question that must come back empty (what is missing is a gap, reported, and work goes on): the
specification's instances stay proposed until complete, and a graph fills group by group.
"""


def node(var, kind=None, where=None):
    out = {"node": var}
    if kind:
        out["type"] = kind
    if where:
        out["where"] = where
    return out


def edge(a, rel, b):
    return {"edge": [a, rel, b]}


def flow_scope(step="s"):
    return [node("f", "Flow", {"flowKind": "medallion"}), edge("f", "hasStep", step)]


def policy(rid, when, flag, why, answers, severity="blocking"):
    return {"id": rid, "kind": "policy", "severity": severity, "when": when, "then": {"flag": flag},
            "why": why, "validated_by": "", "answers": answers}


def attr(kind_, label, definition, required=False):
    out = {"type": kind_, "label": label, "definition": definition}
    if required:
        out["required"] = True
    return out


def rel(domain, range_, inverse, label, definition, max_=None):
    out = {"domain": domain, "range": range_, "inverse": inverse, "label": label, "definition": definition}
    if max_:
        out["max"] = max_
    return out


LAYERS = "bronze|silver|gold|control"
TEST_KINDS = ["unit", "contract", "parity", "rerun", "regression", "integration", "forced_failure", "flow"]
#: what a test of each kind may exercise; a kind not listed may exercise any of them
TEST_TARGETS = {"unit": "DerivationRule|QualityRule", "contract": "Output", "parity": "Output", "flow": "Flow",
                "forced_failure": "QualityRule|Runbook"}
TESTED = ["DerivationRule", "QualityRule", "Output", "Runbook", "Flow"]
WORDS = {"DerivationRule": "a derivation rule", "QualityRule": "a quality rule", "Output": "an output", "Runbook": "a runbook", "Flow": "a flow"}

CLASSES = {
    "SourceSystem": {"subclass_of": ["System"], "definition":
                     "A system the pipeline reads from, and how: its kind, the access method, whether filters may run on its side (D2)."},
    "SourceTable": {"definition": "One table or feed of a source system, with its contract: keys, the column a row's date is "
                                  "in, how it changes over time and the evidence for it, when it arrives (D2)."},
    "SourceColumn": {"definition": "A column of a source table: its name, source type, nullability and unit, and the business "
                                   "term it carries (D2, D3)."},
    "CopyPolicy": {"definition": "How a source table reaches bronze: a period slice, new rows by watermark, an as-of read or "
                                 "a change feed; the lookback, the source-side filter, the retention (D2)."},
    "TermMapping": {"definition": "How a source column becomes a business term: the transform from the source form to the "
                                  "canonical one (D3)."},
    "CodeSet": {"definition": "A list of allowed values with their labels per published language (D3)."},
    "CodeMapping": {"definition": "Which value of a source system means which canonical value of a code set (D3)."},
    "ConformedEntity": {"definition": "A silver business entity, resolved once across sources: its grain, how each source's "
                                      "id maps to its key, which instances are in scope, how history is kept, the table it "
                                      "is materialised as (D4). The specification's Entity, renamed (DECISIONS.md)."},
    "IdentityMapping": {"definition": "How one source table's id becomes the conformed key: the id columns, their transform, "
                                      "the target key fields (D4)."},
    "ScopeRule": {"definition": "Which instances of an entity are in scope, how many there should be, by whose count, and "
                                "how far off the count may be (D4)."},
    "HistoryPolicy": {"definition": "Whether an entity keeps history, and how: none, a snapshot per batch, or validity ranges (D4)."},
    "Dataset": {"subclass_of": ["DataStore"], "definition":
                "A physical table or view of the pipeline, in one layer, with its grain, partitioning and fields (D4, D5). "
                "The specification's Table, renamed; a kind of DataStore, so it runs in an environment and has an owner."},
    "DatasetField": {"definition": "A field of a dataset: its type, whether it is required, the business term it carries, and "
                                   "either the rule that derives it or what feeds it (D4, D5). The specification's Field, renamed."},
    "Output": {"definition": "A gold dataset a consumer reads: its shape, the silver entity it is keyed on, whether it needs a "
                             "window of periods, the data product it belongs to (D5)."},
    "DataContract": {"subclass_of": ["Interface"], "definition":
                     "A versioned shape of a dataset others depend on: its fields, keys and change policy (D5). A kind of "
                     "Interface: consumers consume it, a version supersedes the one before it, it has an owner."},
    "DerivationRule": {"definition": "How one field is produced, or rows are filtered: its kind, its logic as a pattern of the "
                                     "vocabulary, its inputs, its behaviour on the standard edge cases, and an example (D6). "
                                     "The specification's Rule, renamed."},
    "EdgeCase": {"definition": "What a derivation rule does on one edge case: a tie, a null input, missing history, an entity "
                               "younger than the lookback, a duplicate input (D6)."},
    "RuleExample": {"definition": "One real input and the output a derivation rule must give for it, worked out by someone "
                                  "other than the generating agent (D6)."},
    "QualityRule": {"definition": "What must be true of the data at one gate (1 landing to bronze, 2 bronze to silver, 3 silver "
                                  "to gold): its targets, its assertion, hard or soft, its tolerance, what happens when it "
                                  "fails, a row that should fail it (D7). Carried out by a flow check on the gate's step."},
    "Tolerance": {"definition": "How far off a count or a figure may be, in which unit, set by whom (D4, D7)."},
    "FailureAction": {"definition": "What happens when a quality rule fails: who is told, which runbook they follow, whether "
                                    "the step retries (D7)."},
    "Identity": {"definition": "A principal the pipeline runs as or a person who reads it: its kind, the environment, its "
                               "access to datasets (D9)."},
    "PipelineTest": {"definition": "A test the build plan promises, and what it proves: its kind (unit, contract, parity, rerun, "
                                   "regression, integration, forced failure, flow), the rule, output, runbook or flow it tests, "
                                   "what it runs on and what must come out (D9). Not a flow TestObligation, which a step's checks "
                                   "derive for its code (DECISIONS.md)."},
}

ATTRIBUTES = {
    # D1: the data product is the product's Product
    "Product": {
        "period_kind": attr("enum:daily|weekly|monthly|quarterly|annual|event", "period kind", "How often a period of the data product closes."),
        "period_end_rule": attr("string", "period end rule", "What date ends a period: calendar_month_end, last_business_day, fixed_day: N, or event."),
        "freshness_sla": attr("string", "freshness SLA", "By when, after the period ends, gold must be ready (a duration)."),
    },
    # D3: a business term is the product's Term
    "Term": {
        "data_type": attr("string", "data type", "The canonical type of the term's values."),
        "unit": attr("string", "unit", "The canonical unit, when the term is a quantity (percent, fraction, cents…)."),
    },
    "SourceSystem": {
        "source_kind": attr("enum:rdbms|warehouse|file_drop|api|event_stream", "source kind", "What kind of system the source is."),
        "access_method": attr("enum:direct_query|extract_file|change_feed|api_pull", "access method", "How the pipeline reads it."),
        "source_side_logic_allowed": attr("boolean", "source-side logic allowed", "Whether filters may run on the source side; never business logic."),
    },
    "SourceTable": {
        "schema": attr("string", "schema", "The schema, as the source names it."),
        "table_name": attr("string", "table name", "The table or feed name, as the source names it."),
        "change_behaviour": attr("enum:historized|append_only|overwritten|manual_reload", "change behaviour", "How the table changes over time."),
        "change_behaviour_evidence": attr("string", "change behaviour evidence", "What proves the change behaviour: a drift measurement or the owner's statement."),
        "expected_at_period_end": attr("boolean", "expected at period end", "Whether it must have rows for the period end before a batch runs."),
        "delivery_lag": attr("string", "delivery lag", "How long after the period end it arrives (a duration)."),
    },
    "SourceColumn": {
        "column_name": attr("string", "column name", "The column name, as the source names it."),
        "source_type": attr("string", "source type", "The column's type in the source."),
        "nullable": attr("boolean", "nullable", "Whether it can be null."),
        "unit": attr("string", "unit", "For a number: its unit in the source (percent, fraction, cents…)."),
        "sample_values": attr("list", "sample values", "Three real values, for the fixtures."),
    },
    "CopyPolicy": {
        "method": attr("enum:full_period_slice|incremental_by_watermark|as_of_read|cdc_apply", "method", "How rows reach bronze.", required=True),
        "lookback": attr("string", "lookback", "How far before the period end rows are needed (a duration)."),
        "source_side_filter": attr("string", "source-side filter", "The filter that runs on the source, if any: date_between(period_end - lookback, period_end)."),
        "retention_hot": attr("string", "hot retention", "How long bronze keeps it in hot storage."),
        "retention_cold": attr("string", "cold retention", "How long it is archived."),
    },
    "TermMapping": {
        "transform": attr("string", "transform", "From source form to canonical: identity, rename, trim, upper, lower, lpad: N, char, "
                                                 "divide: N, multiply: N, to_date: format, to_utc: tz, code_map: set, coalesce: [a, b, default].", required=True),
    },
    "CodeSet": {
        "values": attr("list", "values", "The canonical values."),
        "labels": attr("list", "labels", "Each value's label in each published language, as value@language: label."),
    },
    "CodeMapping": {
        "source_value": attr("string", "source value", "The value as the source system writes it.", required=True),
        "canonical_value": attr("string", "canonical value", "The code set's value it means.", required=True),
    },
    "IdentityMapping": {
        "transform": attr("string", "transform", "How the source id is normalised (a transform pattern).", required=True),
        "company_or_tenant_map": attr("list", "company or tenant map", "When a company or tenant code is part of the key: source=canonical pairs."),
    },
    "ScopeRule": {
        "conditions": attr("list", "conditions", "What makes an instance in scope: field operator value, with =, !=, in, not_in, is_null, is_not_null, exists_in."),
        "expected_count": attr("integer", "expected count", "How many instances there should be."),
        "count_as_of": attr("date", "count as of", "The date the expected count holds."),
        "count_source": attr("string", "count source", "Who or what says the count."),
    },
    "HistoryPolicy": {
        "history_kind": attr("enum:none|snapshot_per_batch|scd2", "history kind", "No history, one snapshot per batch, or validity ranges.", required=True),
        "valid_from_rule": attr("string", "valid-from rule", "For scd2: how a range's start is derived."),
        "valid_to_rule": attr("string", "valid-to rule", "For scd2: how a range's end is derived."),
    },
    "Dataset": {
        "layer": attr("enum:" + LAYERS, "layer", "The layer the dataset is in.", required=True),
        "dataset_kind": attr("enum:table|view", "dataset kind", "A physical table or a view."),
        "partition_by": attr("string", "partition by", "The partition key: batch_id for the data layers."),
        "cluster_by": attr("list", "cluster by", "The fields it is clustered by."),
    },
    "DatasetField": {
        "data_type": attr("string", "data type", "The field's type."),
        "required": attr("boolean", "required", "Whether every row has a value."),
    },
    "Output": {
        "shape": attr("enum:long|wide", "shape", "Long (one row per key, dimension and value) unless the consumer cannot read long.", required=True),
        "shape_rationale": attr("string", "shape rationale", "Why wide, when it is."),
        "period_dependency": attr("enum:point_in_time|lookback", "period dependency", "Whether it needs only the period or a window."),
        "lookback": attr("string", "lookback", "How far back, when it needs a window."),
        "needs_history": attr("boolean", "needs history", "Whether a consumer reads past periods, not only the current one."),
    },
    "DataContract": {
        "version": attr("string", "version", "The contract's version label.", required=True),
        "contract_fields": attr("list", "fields", "The promised fields, in order, as name: type, required or optional."),
        "keys": attr("list", "keys", "The fields that identify a row."),
        "change_policy": attr("enum:additive_only|versioned_breaking", "change policy", "Whether columns may be added without a new version."),
    },
    "DerivationRule": {
        "rule_kind": attr("enum:filter|derivation|ranking|aggregation|identity|pivot_in_publication_only", "rule kind", "What kind of rule it is.", required=True),
        "logic": attr("string", "logic", "How, exactly: a pattern of the vocabulary (copy, rank_by, sum_by, latest_by, window_from_returns, "
                                         "ratio, std_dev_over, case, filter, join_lookup) with its parameters, or expression: <text> with reviewed_by."),
        "reviewed_by": attr("string", "reviewed by", "Who signed off a free-form expression."),
        "period_dependency": attr("enum:none|point_in_time|lookback", "period dependency", "Whether the rule depends on the period."),
        "lookback": attr("string", "lookback", "How far back, when it needs a window."),
        "specified_in": attr("string", "specified in", "The section of the specification the rule comes from."),
    },
    "EdgeCase": {
        "case": attr("enum:tie|null_input|missing_history|younger_than_lookback|duplicate_input|out_of_range|other", "case", "Which edge case.", required=True),
        "behaviour": attr("string", "behaviour", "What happens: exclude, include_as: value, error, first_by: field, last_by: field, carry_forward, or prose with reviewed_by.", required=True),
    },
    "RuleExample": {
        "inputs": attr("string", "inputs", "The input rows, or the fixture that holds them."),
        "expected_output": attr("string", "expected output", "The rows that must come out, or the fixture that holds them."),
        "computed_by": attr("enum:person|independent_calculation|reference_output", "computed by", "Who worked out the expected value; never the generating agent."),
    },
    "QualityRule": {
        "rule_id": attr("string", "rule id", "The rule's identifier, cited by the check that carries it out."),
        "gate": attr("integer", "gate", "The boundary it runs at: 1 landing to bronze, 2 bronze to silver, 3 silver to gold.", required=True),
        "assertion": attr("string", "assertion", "What must be true: a pattern (present_for_period, fresh, schema_matches, count_within, unique, "
                                                 "not_null, in_set, mapped, references, count_equals, not_after, in_range, sum_to, change_within, "
                                                 "covered, consistent, long_form) with its parameters, or expression: <predicate> with reviewed_by."),
        "severity": attr("enum:hard|soft", "severity", "Stop the batch, or warn.", required=True),
        "severity_rationale": attr("string", "severity rationale", "Why only warn, when soft."),
        "example_failure": attr("string", "example failure", "A row, or the fixture holding it, that should fail the rule."),
        "specified_in": attr("string", "specified in", "The section of the specification the rule comes from."),
    },
    "Tolerance": {
        "value": attr("number", "value", "How far off.", required=True),
        "tolerance_unit": attr("enum:absolute|percent|count", "unit", "In which unit.", required=True),
        "rationale": attr("string", "rationale", "Why this tolerance."),
    },
    "FailureAction": {
        "auto_retry": attr("boolean", "auto retry", "Whether the step retries by itself."),
        "max_retries": attr("integer", "maximum retries", "How many times, when it does."),
    },
    "Identity": {
        "identity_kind": attr("enum:service|human", "identity kind", "A service principal or a person."),
        "access": attr("list", "access", "Its access, as layer: mode (bronze: read, silver: write…)."),
    },
    "PipelineTest": {
        "test_kind": attr("enum:" + "|".join(TEST_KINDS), "test kind",
                          "unit (a rule on its example), contract (an output keeps its contract's shape), parity (an output matches "
                          "what it replaces, or an independent calculation), rerun (a batch run twice writes the same rows), "
                          "regression (what changed leaves past periods as they were), integration (the steps work together on real "
                          "sources), forced_failure (a failure made on purpose stops the batch and its runbook recovers it), flow "
                          "(the whole batch, in order, ends validated).", required=True),
        "fixture": attr("string", "fixture", "What it runs on: input rows, a fixture file, a past period's batch, a reference output."),
        "expected_result": attr("string", "expected result", "What must come out: rows or the fixture holding them, a figure within a "
                                                             "tolerance, the step a batch stops at and who is told.", required=True),
    },
}

PROPERTIES = {
    # D2
    "delivered_by": rel("SourceTable", "SourceSystem", "delivers", "delivered by", "The system the table comes from.", 1),
    "has_key": rel("SourceTable", "SourceColumn", "key_of", "has key", "A column that identifies a row of the table."),
    "date_column": rel("SourceTable", "SourceColumn", "date_column_of", "date column", "The column that says what date a row is about.", 1),
    "has_column": rel("SourceTable", "SourceColumn", "column_of", "has column", "A column the pipeline reads from the table."),
    "copied_by": rel("SourceTable", "CopyPolicy", "copies", "copied by", "How the table reaches bronze.", 1),
    "watermark": rel("CopyPolicy", "SourceColumn", "watermark_of", "watermark", "For an incremental copy: the column that is the watermark.", 1),
    "stewarded_by": rel("SourceTable|Term|CodeSet|QualityRule", "Role", "stewards", "stewarded by",
                        "The role that answers for it: who answers questions about a source table, defines a term, owns a code set or a quality rule."),
    # D3
    "carries_term": rel("SourceColumn|DatasetField", "Term", "term_of", "carries term", "The business term a column or a field carries.", 1),
    "term_code_set": rel("Term", "CodeSet", "lists_values_of", "code set", "The list a term takes its values from.", 1),
    "maps_column": rel("TermMapping", "SourceColumn", "mapped_by", "maps column", "The source column a term mapping reads.", 1),
    "maps_to": rel("TermMapping", "Term", "mapped_from", "maps to", "The business term a term mapping produces.", 1),
    "of_code_set": rel("CodeMapping", "CodeSet", "has_code_mapping", "of code set", "The code set a code mapping maps into.", 1),
    "from_system": rel("CodeMapping", "SourceSystem", "code_mapping_of", "from system", "The source system whose value a code mapping maps.", 1),
    # D4
    "has_identity_mapping": rel("ConformedEntity", "IdentityMapping", "identity_mapping_of", "has identity mapping",
                                "How one source's id becomes the entity's key."),
    "scoped_by": rel("ConformedEntity", "ScopeRule", "scopes", "scoped by", "Which instances of the entity count.", 1),
    "keeps_history": rel("ConformedEntity", "HistoryPolicy", "history_of", "keeps history", "How the entity keeps history.", 1),
    "materialised_as": rel("ConformedEntity|Output", "Dataset", "materialises", "materialised as", "The table an entity or an output is.", 1),
    "from_table": rel("IdentityMapping", "SourceTable", "mapped_in", "from table", "The source table whose id an identity mapping maps.", 1),
    "id_column": rel("IdentityMapping", "SourceColumn", "id_column_of", "id column", "A column that holds the source id."),
    "target_key": rel("IdentityMapping", "DatasetField", "keyed_by", "target key", "A key field of the entity the source id maps to."),
    "within_tolerance": rel("ScopeRule|QualityRule", "Tolerance", "tolerance_of", "within tolerance", "How far off a count or a figure may be.", 1),
    "grain": rel("ConformedEntity|Dataset|Output", "DatasetField", "grain_of", "grain", "A field of the grain: one row per what."),
    "has_field": rel("Dataset", "DatasetField", "field_of", "has field", "A field of the dataset."),
    "bound_to": rel("DatasetField", "CodeSet", "binds", "bound to", "The code set a field's values come from.", 1),
    "derived_by": rel("DatasetField", "DerivationRule", "derives", "derived by", "The rule that computes the field.", 1),
    "fed_by": rel("DatasetField", "SourceColumn|DatasetField", "feeds", "fed by",
                  "What a copied field comes from. If this changes, what is fed by it is affected, transitively."),
    # D5
    "output_of": rel("Output", "Product", "has_output", "output of", "The data product the output belongs to.", 1),
    "joins_to": rel("Output", "ConformedEntity", "joined_by", "joins to", "The silver entity the output is keyed on.", 1),
    "reads_output": rel("Role|Persona", "Output", "read_by_role", "reads output",
                        "A role or a persona who reads the output; a tool, an API or a downstream pipeline is a System that consumes its contract."),
    "contract_of": rel("DataContract", "Dataset", "has_contract", "contract of", "The dataset whose shape the contract promises.", 1),
    # D6
    "rule_input": rel("DerivationRule", "DatasetField|SourceColumn", "input_to", "rule input", "A field or a column the rule reads."),
    "has_edge_case": rel("DerivationRule", "EdgeCase", "edge_case_of", "has edge case", "The rule's behaviour on one edge case."),
    "has_example": rel("DerivationRule", "RuleExample", "example_of", "has example", "An example that proves the rule."),
    # D7
    "targets": rel("QualityRule", "Dataset|DatasetField", "targeted_by", "targets", "A dataset or a field the rule checks."),
    "failure_action": rel("QualityRule", "FailureAction", "action_for", "failure action", "What happens when the rule fails.", 1),
    "carried_out_by": rel("QualityRule", "Check", "carries_out", "carried out by", "The flow check, on its gate's step, that runs the rule."),
    "set_by": rel("Tolerance", "Role", "sets_tolerance", "set by", "The role that set the tolerance.", 1),
    "notifies": rel("FailureAction", "Role", "notified_by", "notifies", "The role told when the rule fails."),
    "follows_runbook": rel("FailureAction", "Runbook", "runbook_for", "follows runbook", "The runbook the notified role follows.", 1),
    # D8: the flow, tied to the design
    "executes": rel("Step", "CopyPolicy|ConformedEntity|Output|DerivationRule", "executed_by", "executes",
                    "What a step of a medallion flow runs: a copy policy, an entity's build, an output's build, a derivation rule. "
                    "The specification's Transformation is the step itself (DECISIONS.md)."),
    "represents": rel("Artifact", "Dataset|SourceTable", "represented_by", "represents",
                      "The design table an artifact of the flow is: a dataset, or a source table.", 1),
    # D9
    "in_environment": rel("Identity", "Environment", "hosts_identity", "in environment", "The environment an identity belongs to.", 1),
    "runs_flow": rel("Identity", "Flow", "run_by", "runs flow", "A flow the identity runs.", None),
    "resumes_from": rel("Runbook", "Step", "resumed_by", "resumes from", "The step a recovery resumes the flow from."),
    "test_of": rel("PipelineTest", "|".join(TESTED), "tested_by", "test of",
                   "What a test proves: a derivation rule, a quality rule, an output, a runbook or a flow."),
}

STANDARD_CASES = ["tie", "null_input", "missing_history", "younger_than_lookback", "duplicate_input"]
BUILD_KINDS = {"copy_to_bronze": "CopyPolicy", "build_entity": "ConformedEntity|DerivationRule", "build_output": "Output|DerivationRule"}

RULES = [
    # correctness: refused at capture
    policy("field-is-derived-or-fed-not-both",
           [node("f", "DatasetField"), edge("f", "derived_by", "r"), edge("f", "fed_by", "x")],
           "a field is both derived by a rule and fed by a column or field",
           "Exactly one of derived_by or fed_by: a field is either computed or copied (D4, D5).", "MD9"),
    policy("rule-reads-no-higher-layer-gold",
           [edge("t", "derived_by", "r"), edge("d", "has_field", "t"), node("d", "Dataset", {"layer": {"in": ["bronze", "silver"]}}),
            edge("r", "rule_input", "i"), edge("di", "has_field", "i"), node("di", "Dataset", {"layer": "gold"})],
           "a rule reads a gold field to produce a bronze or silver one",
           "A rule's inputs sit in the same or a lower layer than its output (D6).", "MD11"),
    policy("rule-reads-no-higher-layer-silver",
           [edge("t", "derived_by", "r"), edge("d", "has_field", "t"), node("d", "Dataset", {"layer": "bronze"}),
            edge("r", "rule_input", "i"), edge("di", "has_field", "i"), node("di", "Dataset", {"layer": "silver"})],
           "a rule reads a silver field to produce a bronze one",
           "A rule's inputs sit in the same or a lower layer than its output (D6).", "MD11"),
    policy("artifact-layer-is-its-dataset-layer",
           [node("a", "Artifact"), edge("a", "represents", "d"), node("d", "Dataset", {"layer": {"!=": "$a.layer"}})],
           "an artifact of the flow sits in another layer than the dataset it represents",
           "The flow's tables are the design's datasets; one layer for both (D8).", "MD1"),
    policy("artifact-of-a-source-table-is-a-source",
           [node("a", "Artifact", {"layer": {"!=": "source"}}), edge("a", "represents", "t"), node("t", "SourceTable")],
           "an artifact representing a source table is not in the source layer",
           "A source table is read from outside, before bronze (D2, D8).", "MD1"),
    policy("one-step-executes-each-design-object",
           [node("x", "CopyPolicy|ConformedEntity|Output|DerivationRule"), edge("s1", "executes", "x"),
            edge("s2", "executes", "x"), node("s2", "Step", {"id": {"!=": "$s1"}})],
           "two steps execute the same copy policy, entity, output or rule",
           "Exactly one step executes a unit of transformation (D8 Single executor).", "MD16"),
    policy("an-entity-step-writes-its-entity",
           flow_scope("s") + [node("s", "Step", {"stepKind": "build_entity"}), edge("s", "executes", "e"), node("e", "ConformedEntity"),
                              edge("e", "materialised_as", "d"), {"not": [edge("s", "writes", "a"), edge("a", "represents", "d")]}],
           "a build_entity step does not write the dataset its entity is materialised as",
           "The step that builds an entity writes the entity's table (D4, D8).", "MD16"),
    policy("an-output-step-writes-its-output",
           flow_scope("s") + [node("s", "Step", {"stepKind": "build_output"}), edge("s", "executes", "o"), node("o", "Output"),
                              edge("o", "materialised_as", "d"), {"not": [edge("s", "writes", "a"), edge("a", "represents", "d")]}],
           "a build_output step does not write the dataset its output is materialised as",
           "The step that builds an output writes the output's table (D5, D8).", "MD16"),
    policy("no-human-writes-silver", [node("i", "Identity", {"identity_kind": "human", "access": {"contains": "silver: write"}})],
           "a person has write access on silver", "No human identity writes silver or gold (D9).", "MD18"),
    policy("no-human-writes-gold", [node("i", "Identity", {"identity_kind": "human", "access": {"contains": "gold: write"}})],
           "a person has write access on gold", "No human identity writes silver or gold (D9).", "MD18"),
]
for step_kind, allowed in BUILD_KINDS.items():
    forbidden = [c for c in ("CopyPolicy", "ConformedEntity", "Output", "DerivationRule") if c not in allowed.split("|")]
    RULES.append(policy("a-%s-step-executes-what-it-builds" % step_kind.replace("_", "-"),
                        flow_scope("s") + [node("s", "Step", {"stepKind": step_kind}), edge("s", "executes", "x"), node("x", "|".join(forbidden))],
                        "a %s step executes a %s" % (step_kind, " or ".join(forbidden)),
                        "A copy runs a copy policy, an entity step an entity and its rules, an output step an output and its rules (D8).", "MD16"))
# the build plan's tests: a test of a kind exercises only what that kind can prove
for test_kind, allowed in TEST_TARGETS.items():
    forbidden = [c for c in TESTED if c not in allowed.split("|")]
    words = " or ".join(WORDS[c] for c in allowed.split("|"))
    RULES.append(policy("a-%s-test-tests-%s" % (test_kind.replace("_", "-"), "-or-".join(WORDS[c].replace(" ", "-") for c in allowed.split("|"))),
                        [node("t", "PipelineTest", {"test_kind": test_kind}), edge("t", "test_of", "x"), node("x", "|".join(forbidden))],
                        "a %s test is a test of something it cannot prove: it tests %s" % (test_kind.replace("_", " "), words),
                        "Each kind of test proves one kind of thing, so the build plan's tests are generated from it (D9).", "MD35"))
# the standard edge cases: a warning each, so the rule can be captured before every case is answered
for case in STANDARD_CASES:
    RULES.append(policy("rule-answers-%s" % case.replace("_", "-"),
                        [node("r", "DerivationRule"), {"not": [edge("r", "has_edge_case", "c"), node("c", "EdgeCase", {"case": case})]}],
                        "the rule does not say what happens on %s" % case.replace("_", " "),
                        "The five standard edge cases are answered before a rule is complete (D6).", "MD12", severity="warn"))


def q(who, question, why, when, select, gate):
    return {"who": who, "question": question, "why": why, "validated_by": "", "ask": {"when": when, "select": select}, "gate": gate}


QUESTIONS = {
    "MD3": q("a data engineer", "Which source tables have no evidence for how they change?",
             "A change behaviour nobody measured decides the copy policy on a guess (D2).",
             [node("t", "SourceTable", {"change_behaviour_evidence": {"exists": False}})], ["t.label", "t.change_behaviour"], "empty"),
    "MD4": q("a data engineer", "Which source tables have no copy policy?",
             "A table with no copy policy never reaches bronze (D2).",
             [node("t", "SourceTable"), {"not_edge": ["t", "copied_by", "*"]}], ["t.label"], "empty"),
    "MD5": q("a reference-data steward", "Which source columns that silver reads carry no business term?",
             "Silver is built on terms; a column with no term has no canonical meaning (D2, D3).",
             [node("c", "SourceColumn"), edge("f", "fed_by", "c"), edge("d", "has_field", "f"), node("d", "Dataset", {"layer": "silver"}),
              {"not_edge": ["c", "carries_term", "*"]}], ["c.label", "f.label"], "empty"),
    "MD6": q("a reference-data steward", "Which term mappings use a code map for a term that has no code set?",
             "A code map needs the list it maps into (D3).",
             [node("m", "TermMapping", {"transform": {"contains": "code_map"}}), edge("m", "maps_to", "t"),
              {"not_edge": ["t", "term_code_set", "*"]}], ["m.label", "t.label"], "empty"),
    "MD7": q("a platform lead", "Which conformed entities are fed by a source table they have no identity mapping for?",
             "Every source that delivers an entity says how its id becomes the entity's key (D4).",
             [node("e", "ConformedEntity"), edge("e", "materialised_as", "d"), edge("d", "has_field", "f"), edge("f", "fed_by", "c"),
              edge("t", "has_column", "c"), node("t", "SourceTable"),
              {"not": [edge("e", "has_identity_mapping", "m"), edge("m", "from_table", "t")]}], ["e.label", "t.label"], "empty"),
    "MD8": q("a platform lead", "Which scope rules have no expected count?",
             "Gate 2 reconciles an entity against its expected count (D4).",
             [node("s", "ScopeRule", {"expected_count": {"exists": False}})], ["s.label"], "empty"),
    "MD9": q("an analyst", "Which fields of an output are neither derived by a rule nor fed by a column or a field?",
             "Every output field says where its value comes from (D5, D6).",
             [node("o", "Output"), edge("o", "materialised_as", "d"), edge("d", "has_field", "f"),
              {"not_edge": ["f", "derived_by", "*"]}, {"not_edge": ["f", "fed_by", "*"]}], ["o.label", "f.label"], "empty"),
    "MD10": q("an analyst", "Which wide outputs do not say why they are wide?",
              "Long is the default; wide needs a reason (D5).",
              [node("o", "Output", {"shape": "wide", "shape_rationale": {"exists": False}})], ["o.label"], "empty"),
    "MD11": q("an analyst", "Which derivation rules have no example?",
              "An example is the rule's unit test (D6, D9).",
              [node("r", "DerivationRule"), {"not_edge": ["r", "has_example", "*"]}], ["r.label"], "empty"),
    "MD12": q("an analyst", "What does each derivation rule do on each edge case it answers?",
              "The five standard cases (tie, null input, missing history, younger than the lookback, duplicate input) are answered "
              "before a rule is complete; the rules flag a missing one (D6).",
              [node("r", "DerivationRule"), {"optional": [edge("r", "has_edge_case", "c"), node("c", "EdgeCase")]}],
              ["r.label", "c.case", "c.behaviour"], "any"),
    "MD13": q("a platform lead", "Which soft quality rules do not say why they only warn?",
              "A soft rule lets a batch through; the reason is recorded (D7).",
              [node("r", "QualityRule", {"severity": "soft", "severity_rationale": {"exists": False}})], ["r.rule_id"], "empty"),
    "MD14": q("a platform lead", "Which quality rules have no row that should fail them?",
              "The failing example is the rule's forced-failure test (D7, D9).",
              [node("r", "QualityRule", {"example_failure": {"exists": False}})], ["r.rule_id"], "empty"),
    "MD15": q("a platform lead", "Which gate steps of a medallion flow carry out no hard quality rule?",
              "A gate with no hard rule cannot stop a batch (D7).",
              flow_scope("g") + [node("g", "Step", {"stepKind": "run_gate"}),
                                 {"not": [edge("g", "hasCheck", "c"), edge("r", "carried_out_by", "c"), node("r", "QualityRule", {"severity": "hard"})]}],
              ["g.stepId", "g.gate"], "empty"),
    "MD16": q("a platform lead", "Which entities and outputs does no step execute?",
              "Every entity and every output is built by exactly one step of the flow (D8 Coverage).",
              [node("x", "ConformedEntity|Output"), {"not_edge": ["*", "executes", "x"]}], ["x.label", "x.type"], "empty"),
    "MD17": q("a platform lead", "Which source tables are copied by no step?",
              "Every source table has a copy_to_bronze step (D8 Coverage).",
              [node("t", "SourceTable"), edge("t", "copied_by", "p"), {"not_edge": ["*", "executes", "p"]}], ["t.label"], "empty"),
    "MD18": q("a platform lead", "Which identities run the pipeline or read it, in which environment, with which access?",
              "The build plan's identities; no person writes silver or gold (D9).",
              [node("i", "Identity"), {"optional": [edge("i", "in_environment", "e"), node("e", "Environment")]}],
              ["i.label", "i.identity_kind", "i.access", "e.label"], "any"),
    "MD19": q("a platform lead", "Which quality rules run at which gate, through which check, failing to whom?",
              "The quality catalogue, as it runs: each rule, its gate, its check and its failure action (D7).",
              [node("r", "QualityRule"), {"optional": [edge("r", "carried_out_by", "c"), node("c", "Check")]},
               {"optional": [edge("r", "failure_action", "a"), edge("a", "notifies", "who")]}],
              ["r.rule_id", "r.gate", "r.severity", "c.checkId", "who.label"], "non_empty"),
    "MD20": q("an analyst", "Where does field $FIELD come from: the rule that derives it, or the column or field that feeds it?",
              "Lineage, one hop at a time: what a change upstream reaches downstream (D5, D6).",
              [node("$FIELD", "DatasetField"), {"optional": [edge("$FIELD", "derived_by", "r"), node("r", "DerivationRule")]},
               {"optional": [edge("$FIELD", "fed_by", "x")]}],
              ["r.label", "r.logic", "x.label", "x.type"], "any"),
}
QUESTIONS["MD20"]["params"] = {"FIELD": {"type": "DatasetField"}}

QUESTIONS.update({
    "MD21": q("a product owner", "What is each data product: its period, the date that ends it, by when gold is ready, its outputs and who reads them?",
              "The product definition checkpoint (D1).",
              [node("p", "Product", {"period_kind": {"exists": True}}),
               {"optional": [edge("o", "output_of", "p"), node("o", "Output")]}, {"optional": [edge("who", "reads_output", "o")]}],
              ["p.label", "p.period_kind", "p.period_end_rule", "p.freshness_sla", "o.label", "who.label"], "any"),
    "MD22": q("a source owner", "Which source tables does each source system deliver, read how, keyed on what, changing how, copied how?",
              "The source contracts checkpoint (D2).",
              [node("s", "SourceSystem"), edge("t", "delivered_by", "s"), node("t", "SourceTable"),
               {"optional": [edge("t", "copied_by", "p"), node("p", "CopyPolicy")]}, {"optional": [edge("p", "watermark", "w")]},
               {"optional": [edge("t", "date_column", "dc")]}, {"optional": [edge("t", "has_key", "k")]},
               {"optional": [edge("t", "stewarded_by", "who")]}, {"optional": [edge("t", "has_column", "c"), node("c", "SourceColumn")]}],
              ["s.label", "s.source_kind", "s.access_method", "s.source_side_logic_allowed", "t.schema", "t.table_name", "t.change_behaviour",
               "t.change_behaviour_evidence", "t.expected_at_period_end", "t.delivery_lag", "dc.label", "k.label", "who.label",
               "p.method", "p.lookback", "p.source_side_filter", "p.retention_hot", "p.retention_cold", "w.label",
               "c.column_name", "c.source_type", "c.nullable", "c.unit", "c.sample_values"], "any"),
    "MD23": q("a reference-data steward", "Which term does each mapped source column carry, through which transform, and which code sets map which source values?",
              "The reference data checkpoint (D3).",
              [node("m", "TermMapping"), edge("m", "maps_column", "c"), edge("m", "maps_to", "t"), node("t", "Term"),
               {"optional": [edge("t", "term_code_set", "cs"), node("cs", "CodeSet")]},
               {"optional": [edge("cm", "of_code_set", "cs"), node("cm", "CodeMapping"), edge("cm", "from_system", "s")]}],
              ["c.label", "m.transform", "t.label", "t.data_type", "t.unit", "cs.values", "cs.labels", "cm.source_value", "cm.canonical_value", "s.label"], "any"),
    "MD24": q("a platform lead", "How is each conformed entity resolved: its dataset and grain, each source's identity mapping, its scope and tolerance, its history?",
              "The entity design checkpoint (D4).",
              [node("e", "ConformedEntity"), edge("e", "materialised_as", "d"),
               {"optional": [edge("e", "has_identity_mapping", "m"), node("m", "IdentityMapping"), edge("m", "from_table", "t"),
                             edge("m", "id_column", "ic"), edge("m", "target_key", "tk")]},
               {"optional": [edge("e", "scoped_by", "s"), node("s", "ScopeRule")]},
               {"optional": [edge("s", "within_tolerance", "tol"), node("tol", "Tolerance"), edge("tol", "set_by", "by")]},
               {"optional": [edge("e", "keeps_history", "h"), node("h", "HistoryPolicy")]}, {"optional": [edge("e", "grain", "g")]}],
              ["e.label", "d.label", "g.label", "t.label", "ic.label", "m.transform", "m.company_or_tenant_map", "tk.label",
               "s.conditions", "s.expected_count", "s.count_as_of", "s.count_source", "tol.value", "tol.tolerance_unit", "tol.rationale", "by.label",
               "h.history_kind", "h.valid_from_rule", "h.valid_to_rule"], "any"),
    "MD25": q("an analyst", "What does each output promise: its dataset, layer and fields, the entity it joins, its contract's version, keys and change policy?",
              "The output contract checkpoint (D5).",
              [node("o", "Output"), edge("o", "materialised_as", "d"), node("d", "Dataset"),
               {"optional": [edge("o", "joins_to", "e")]}, {"optional": [edge("d", "has_field", "f"), node("f", "DatasetField")]},
               {"optional": [edge("f", "bound_to", "cs")]}, {"optional": [edge("k", "contract_of", "d"), node("k", "DataContract")]}],
              ["o.label", "o.shape", "o.shape_rationale", "o.period_dependency", "o.lookback", "o.needs_history", "e.label",
               "d.label", "d.layer", "d.dataset_kind", "d.partition_by", "d.cluster_by", "f.label", "f.data_type", "f.required", "cs.label",
               "k.version", "k.contract_fields", "k.keys", "k.change_policy"], "any"),
    "MD26": q("an analyst", "How is each derivation rule defined: its kind, logic, inputs, period dependency, the field it derives and its example?",
              "The field mapping checkpoint (D6).",
              [node("r", "DerivationRule"), {"optional": [edge("f", "derived_by", "r")]}, {"optional": [edge("r", "rule_input", "i")]},
               {"optional": [edge("r", "has_example", "x"), node("x", "RuleExample")]}],
              ["r.label", "r.rule_kind", "r.logic", "r.reviewed_by", "r.period_dependency", "r.lookback", "r.specified_in", "f.label", "i.label",
               "x.inputs", "x.expected_output", "x.computed_by"], "any"),
    "MD27": q("a platform lead", "What does each quality rule check, how, with which tolerance, and what happens when it fails?",
              "The quality catalogue checkpoint (D7).",
              [node("r", "QualityRule"), {"optional": [edge("r", "targets", "t")]}, {"optional": [edge("r", "within_tolerance", "tol")]},
               {"optional": [edge("r", "failure_action", "a"), node("a", "FailureAction"), edge("a", "follows_runbook", "rb")]},
               {"optional": [edge("r", "stewarded_by", "who")]}],
              ["r.rule_id", "r.gate", "r.assertion", "r.severity", "r.severity_rationale", "r.example_failure", "r.specified_in", "t.label",
               "tol.label", "a.auto_retry", "a.max_retries", "rb.label", "who.label"], "any"),
    "MD28": q("a platform lead", "What does each step of a medallion flow execute in the design, and which design table does each artifact it writes represent?",
              "The flow, tied to the design (D8): coverage and the single executor are read from it.",
              flow_scope("s") + [{"optional": [edge("s", "executes", "x")]},
                                 {"optional": [edge("s", "writes", "a"), edge("a", "represents", "d")]}],
              ["s.stepId", "s.stepKind", "x.label", "x.type", "d.label"], "any"),
    "MD29": q("a platform lead", "Which runbooks resume a failed flow from which step?",
              "A recovery names an existing step, so it stays true when the flow changes (D9).",
              [node("rb", "Runbook"), edge("rb", "resumes_from", "s"), node("s", "Step")], ["rb.label", "s.stepId"], "any"),
})
QUESTIONS.update({
    "MD30": q("a platform lead", "Which derivation rules does no unit test exercise?",
              "A rule's unit test runs its worked example on the built code; without it a wrong number reaches gold unnoticed (D9).",
              [node("r", "DerivationRule"), {"not": [edge("t", "test_of", "r"), node("t", "PipelineTest", {"test_kind": "unit"})]}],
              ["r.label"], "empty"),
    "MD31": q("a platform lead", "Which outputs does no parity test compare with what they replace?",
              "Before a consumer switches to an output, it is shown to give the figures it gets today, or an independent "
              "calculation's (D9).",
              [node("o", "Output"), {"not": [edge("t", "test_of", "o"), node("t", "PipelineTest", {"test_kind": "parity"})]}],
              ["o.label"], "empty"),
    "MD32": q("a platform lead", "Which medallion flows does no flow test run from start to end?",
              "The steps are tested one by one; only a flow test shows the batch runs in order and ends validated (D9).",
              [node("f", "Flow", {"flowKind": "medallion"}),
               {"not": [edge("t", "test_of", "f"), node("t", "PipelineTest", {"test_kind": "flow"})]}],
              ["f.label"], "empty"),
    "MD33": q("a platform lead", "Which runbooks of a medallion flow does no forced-failure test exercise?",
              "A recovery nobody tried fails the night it is needed: a failure made on purpose shows the batch stops, the right "
              "person is told and the run resumes where the runbook says (D9).",
              [node("rb", "Runbook"), edge("rb", "resumes_from", "s"), node("s", "Step"),
               {"not": [edge("t", "test_of", "rb"), node("t", "PipelineTest", {"test_kind": "forced_failure"})]}],
              ["rb.label"], "empty"),
    "MD34": q("a platform lead", "Which tests do not say what they run on?",
              "A test is written from its fixture and its expected result; with no fixture it cannot be written (D9).",
              [node("t", "PipelineTest", {"fixture": {"exists": False}})], ["t.label", "t.test_kind"], "empty"),
    "MD35": q("a platform lead", "Which tests prove the pipeline: of which kind, testing what, on what, expecting what?",
              "The build plan's tests checkpoint (D9): what is proved before the pipeline is built and trusted.",
              [node("t", "PipelineTest"), {"optional": [edge("t", "test_of", "x")]}],
              ["t.label", "t.test_kind", "x.label", "x.type", "t.fixture", "t.expected_result"], "any"),
})
QUESTIONS["MD18"]["ask"]["when"].append({"optional": [edge("i", "runs_flow", "fl")]})
QUESTIONS["MD18"]["ask"]["select"].append("fl.label")


#: Why each class exists: what the implementation agent could not generate, or a reviewer could not check, without it.
WHY_CLASSES = {
    "SourceSystem": ("MD22", "The copy mechanism depends on how a system is read; a filter on the source is allowed only where its owner agreed.",
                     "A plain System with these as attributes of every system: rejected, they mean nothing for an application."),
    "SourceTable": ("MD22", "A source table's change behaviour decides its copy policy, and its keys and date column decide the slice; a guess "
                            "here corrupts every batch silently.", ""),
    "SourceColumn": ("MD22", "Silver fields are fed by columns and terms are carried by them; the fixtures need their real values.", ""),
    "CopyPolicy": ("MD22", "The bronze copy is generated from it: method, lookback, filter, retention.", "Attributes on the source table: "
                                                                                                         "rejected, a policy is reviewed and changed on its own."),
    "TermMapping": ("MD23", "The transform from source form to canonical is what the silver build applies, per column.", ""),
    "CodeSet": ("MD23", "Allowed values and their labels per language are checked at gate 2 (in_set) and published by the report.", ""),
    "CodeMapping": ("MD23", "Two sources write the same meaning differently; the mapping is what makes them one value.", ""),
    "ConformedEntity": ("MD24", "Silver resolves each business thing once; every output joins to it, so it is designed before any output.",
                        "The specification's name Entity: rejected, ddd declares Entity for something else (DECISIONS.md)."),
    "IdentityMapping": ("MD24", "Each source spells the same id its own way; without the mapping two rows of one fund are two funds.", ""),
    "ScopeRule": ("MD24", "Gate 2 reconciles the entity against an expected count; the scope says which instances count.", ""),
    "HistoryPolicy": ("MD24", "Whether past periods are kept decides the silver build and what consumers can ask for.", ""),
    "Dataset": ("MD25", "Every layer's tables are generated from it: layer, partitioning, grain, fields.",
                "The specification's name Table: rejected, the report ontology declares Table for the table a report reads (DECISIONS.md)."),
    "DatasetField": ("MD25", "A field's type, term and origin (derived or fed) are what lineage and the contract are made of.",
                     "The specification's name Field: rejected, the report ontology declares Field (DECISIONS.md)."),
    "Output": ("MD25", "What a consumer reads, and its shape and period dependency, decide the gold build.", ""),
    "DataContract": ("MD25", "A consumer depends on a shape; a breaking change without a new version breaks it silently.",
                     "Reusing Interface as is, or a class unrelated to it: rejected for a kind of Interface (DECISIONS.md)."),
    "DerivationRule": ("MD26", "Each gold value is generated from its rule; ambiguity here becomes a wrong number in a published document.",
                       "The specification's name Rule: rejected, the report ontology declares Rule (DECISIONS.md)."),
    "EdgeCase": ("MD12", "A tie, a null, a short history are where generated code most often guesses; the behaviour is decided once.", ""),
    "RuleExample": ("MD26", "The unit test of a rule, worked out by someone other than the agent that writes the code.", ""),
    "QualityRule": ("MD19", "What stops a bad batch, and at which boundary; the gate's check is generated from it.",
                    "The report's QualityCheck: rejected, two levels with no overlap (DECISIONS.md)."),
    "Tolerance": ("MD24", "A count or a figure is never exact by accident; who set the tolerance is who answers for it.", ""),
    "FailureAction": ("MD19", "A failed gate without a named person and runbook waits until someone notices.", ""),
    "Identity": ("MD18", "Access is generated per environment; the rule that no person writes silver or gold is checked on it.", ""),
    "PipelineTest": ("MD35", "What proves the pipeline before anyone relies on it: the implementation agent writes each test from its "
                             "fixture and expected result, and a rule, an output, a runbook or a flow with no test shows as missing.",
                     "The flow's TestObligation: rejected, it is derived from a step's checks for that step's code, not promised by "
                     "the build plan for the design. The specification's name Test: rejected, it would read as any test of the "
                     "product (DECISIONS.md)."),
}
#: Why each relation exists.
WHY_PROPERTIES = {
    "delivered_by": "A table's system decides its access method and who owns it.",
    "has_key": "The keys are what uniqueness is checked on at gate 1 and what identity mappings read.",
    "date_column": "The period slice filters on it; without it the copy cannot select a period.",
    "has_column": "What the pipeline reads, and nothing else, so an unused column never reaches bronze.",
    "copied_by": "Every source table has exactly one way into bronze (MD4, MD17).",
    "watermark": "An incremental copy needs the column that says what is new.",
    "stewarded_by": "Someone answers for a source table, a term, a code set, a quality rule; ownership sits on a role.",
    "carries_term": "A field means a business term, not a column name; lineage and labels follow the term.",
    "term_code_set": "A term with a list of values is checked against it.",
    "maps_column": "The mapping applies to one source column.",
    "maps_to": "The mapping produces one business term, which every silver field carrying that term is then checked against.",
    "of_code_set": "A source value maps into one code set, so the gate-2 check (in_set) knows which values are allowed.",
    "from_system": "The same value means different things in different systems.",
    "has_identity_mapping": "One mapping per source that delivers the entity (MD7).",
    "scoped_by": "The scope decides which instances gate 2 counts.",
    "keeps_history": "The silver build differs by history policy.",
    "materialised_as": "An entity or an output is one physical table, which its step writes.",
    "from_table": "One identity mapping per source table: the same entity is spelled differently in each source that delivers it.",
    "id_column": "The columns that hold the id in that source.",
    "target_key": "The key fields of the entity the id becomes.",
    "within_tolerance": "How far off a count or a figure may be before the gate fails.",
    "grain": "One row per what: uniqueness is checked on it and an output's keys come from it.",
    "has_field": "A dataset's fields are what its contract promises and its consumers read.",
    "bound_to": "A field whose values come from a code set is checked against it at gate 2.",
    "derived_by": "A computed field names the rule that computes it, so the code is generated from the rule.",
    "fed_by": "A copied field names what it is copied from; changes upstream reach it through this.",
    "output_of": "An output belongs to one data product, whose period and freshness it follows.",
    "joins_to": "An output is keyed on a silver entity; coverage (every in-scope entity has a row) is checked through it.",
    "reads_output": "Who reads an output, beside the systems that consume its contract.",
    "contract_of": "A contract promises the shape of one dataset.",
    "rule_input": "A rule's inputs sit in the same or a lower layer (refused otherwise).",
    "has_edge_case": "The behaviour on each standard edge case is decided, not guessed by generated code (MD12).",
    "has_example": "Every rule has an example its unit test is made from (MD11).",
    "targets": "What a quality rule checks, by dataset or field, so the gate's check is generated against the right table.",
    "failure_action": "A failed rule with no recorded action waits until someone notices, and the batch's consumers read what it let through.",
    "carried_out_by": "The design rule and the check that runs it at its gate are tied, so a gate with no hard rule shows (MD15).",
    "set_by": "Who set a tolerance answers for it when a batch passes a gate it should not have, or fails one it should have passed.",
    "notifies": "A failure is somebody's to handle: the role told is the role that answers for the rule at its gate.",
    "follows_runbook": "The notified role follows a written recovery, so a failure at night is handled the way it was decided by day.",
    "executes": "Each step of the flow runs one piece of the design; coverage and the single executor are checked through it (MD16, MD17).",
    "represents": "The flow's tables are the design's datasets; their layers must agree.",
    "in_environment": "Access is granted per environment, so an identity's rights in development never reach production.",
    "runs_flow": "A flow runs as a service identity, never as a person, so who changed the data is always the pipeline.",
    "resumes_from": "A recovery names the step it resumes from, so the runbook stays true when the flow changes.",
    "test_of": "A test names what it proves, so what nothing proves shows (MD30 to MD33), and a test of the wrong kind is refused.",
}


def rationale():
    """Why each class and relation exists, and the question that needs it."""
    classes = {}
    for name in CLASSES:
        question, why, alternatives = WHY_CLASSES[name]
        classes[name] = {"question": QUESTIONS[question]["question"], "why": why, "alternatives": alternatives, "validated_by": ""}
    props = {name: {"question": PROPERTIES[name]["label"], "why": WHY_PROPERTIES[name], "alternatives": "", "validated_by": ""}
             for name in PROPERTIES}
    return classes, props


# ============================ the sample: the specification's worked instance ============================

def design_sample(stamp):
    """Sources, terms, the two entities, the outputs and their contract, one rule with its cases and example, the
    quality rules of the three gates, the build plan's identity: everything the fund-profile flow executes."""
    nodes, edges = [], []

    def n(nid, kind_, label, **attrs):
        nodes.append(stamp({"id": nid, "type": kind_, "label": label, "summary": label,
                            "attributes": {k: v for k, v in attrs.items() if v is not None}}))
        return nid

    def e(a, rel_, b):
        edges.append({"from": a, "rel": rel_, "to": b})

    # D1: the data product, its roles and its consumers
    n("product.fund-profile", "Product", "Fund profile", stage="building", domain="reporting", period_kind="monthly",
      period_end_rule="calendar_month_end", freshness_sla="2 business days")
    for rid, label in (("product-owner", "product owner"), ("platform-lead", "platform lead"), ("data-owner", "source data owner"),
                       ("reference-steward", "reference-data steward"), ("analyst", "analyst")):
        n("role." + rid, "Role", label)
    n("system.bi-fund-pages", "System", "BI fund pages")
    n("environment.prod", "Environment", "prod")
    e("product.fund-profile", "owned_by", "role.product-owner")
    n("valueproposition.trusted-fact-sheets", "ValueProposition", "monthly fact sheets an adviser can trust, two business days after month end")
    e("product.fund-profile", "offers", "valueproposition.trusted-fact-sheets")
    n("successcriterion.gold-on-time", "SuccessCriterion", "gold is ready on time every month",
      metric="months gold was ready within the freshness SLA, of the last twelve", target="12 of 12")
    e("successcriterion.gold-on-time", "measures", "valueproposition.trusted-fact-sheets")
    n("capability.fund-reporting", "Capability", "fund reporting")
    e("capability.fund-reporting", "owned_by", "role.product-owner")
    n("system.fund-profile-pipeline", "System", "fund profile pipeline")
    for sid, cid, label in (("sourcesystem.source", "component.source-database", "source database"),
                            ("system.bi-fund-pages", "component.fund-pages", "fund pages"),
                            ("system.fund-profile-pipeline", "component.batch-jobs", "batch jobs")):
        n(cid, "Component", label)
        e(cid, "part_of", sid)
        e(cid, "runs_in", "environment.prod")
        e(sid, "enables", "capability.fund-reporting")
    n("runbook.hard-gate-failure", "Runbook", "Hard gate failure")
    # D2: sources
    n("sourcesystem.source", "SourceSystem", "source", source_kind="rdbms", access_method="direct_query", source_side_logic_allowed=True)
    for tid, table, change, evidence, lag in (
            ("fund-holding", "fund_holding", "manual_reload", "drift probe 2026-09: the Sept-30 slice changed on Oct 8", "3 business days"),
            ("dim-product", "dim_product", "overwritten", "owner statement 2026-10-13", "1 business day")):
        n("sourcetable." + tid, "SourceTable", "source." + table, schema="source", table_name=table, change_behaviour=change,
          change_behaviour_evidence=evidence, expected_at_period_end=True, delivery_lag=lag)
        e("sourcetable." + tid, "delivered_by", "sourcesystem.source")
        e("sourcetable." + tid, "stewarded_by", "role.data-owner")
        n("copypolicy." + tid, "CopyPolicy", "copy " + table, method="full_period_slice", lookback="1 month",
          source_side_filter="date_between(period_end - lookback, period_end)", retention_hot="13 months", retention_cold="7 years")
        e("sourcetable." + tid, "copied_by", "copypolicy." + tid)
    columns = {"fund-holding": [("fund_id", "varchar", False, None), ("holding_name", "varchar", False, None),
                                ("effective_date", "date", False, None), ("holding_pct", "decimal", True, "percent"),
                                ("language_code", "char(2)", False, None)],
               "dim-product": [("prod_cr_id", "integer", False, None), ("state", "varchar", False, None)]}
    for tid, cols in columns.items():
        for name, typ, nullable, unit in cols:
            cid = "sourcecolumn.%s.%s" % (tid, name)
            n(cid, "SourceColumn", "%s.%s" % (tid.replace("-", "_"), name), column_name=name, source_type=typ, nullable=nullable, unit=unit)
            e("sourcetable." + tid, "has_column", cid)
    for key in ("fund_id", "holding_name", "effective_date"):
        e("sourcetable.fund-holding", "has_key", "sourcecolumn.fund-holding." + key)
    e("sourcetable.fund-holding", "date_column", "sourcecolumn.fund-holding.effective_date")
    e("sourcetable.dim-product", "has_key", "sourcecolumn.dim-product.prod_cr_id")
    # D3: terms and reference data
    for tid, label, typ, unit in (("fund-id", "fund id", "char(5)", None), ("holding-weight", "holding weight", "decimal", "percent"),
                                  ("fund-state", "fund state", "varchar", None), ("holding-name", "holding name", "varchar", None),
                                  ("language", "language", "char(2)", None)):
        n("term." + tid, "Term", label, data_type=typ, unit=unit, definition="The " + label + ".")
        e("term." + tid, "stewarded_by", "role.reference-steward")
    n("codeset.fund-state", "CodeSet", "fund state", values=["OPEN", "CLOSED"],
      labels=["OPEN@en: Open", "OPEN@fr: Ouvert", "CLOSED@en: Closed", "CLOSED@fr: Fermé"])
    e("term.fund-state", "term_code_set", "codeset.fund-state")
    e("codeset.fund-state", "stewarded_by", "role.reference-steward")
    for value, canonical in (("A", "OPEN"), ("C", "CLOSED")):
        n("codemapping.source-%s" % value.lower(), "CodeMapping", "source %s is %s" % (value, canonical), source_value=value, canonical_value=canonical)
        e("codemapping.source-%s" % value.lower(), "of_code_set", "codeset.fund-state")
        e("codemapping.source-%s" % value.lower(), "from_system", "sourcesystem.source")
    for mid, col, term, transform in (("holding-pct", "fund-holding.holding_pct", "holding-weight", "identity"),
                                      ("prod-cr-id", "dim-product.prod_cr_id", "fund-id", "lpad: 5, '0'"),
                                      ("state", "dim-product.state", "fund-state", "code_map: fund-state"),
                                      ("fund-id", "fund-holding.fund_id", "fund-id", "identity"),
                                      ("holding-name", "fund-holding.holding_name", "holding-name", "trim"),
                                      ("language-code", "fund-holding.language_code", "language", "lower")):
        n("termmapping." + mid, "TermMapping", "%s is %s" % (col, term), transform=transform)
        e("termmapping." + mid, "maps_column", "sourcecolumn." + col)
        e("termmapping." + mid, "maps_to", "term." + term)
        e("sourcecolumn." + col, "carries_term", "term." + term)
    # D4 and D5: datasets and their fields, by layer
    datasets = {"bronze.source__fund_holding": "bronze", "bronze.source__dim_product": "bronze", "silver.fund": "silver",
                "silver.fund_holding": "silver", "gold.portfolio_holdings": "gold", "gold.portfolio_allocations": "gold",
                "control.batch": "control"}
    for name, layer in datasets.items():
        n("dataset." + name, "Dataset", name, layer=layer, dataset_kind="table", partition_by="batch_id" if layer != "control" else "batch_id")
        e("dataset." + name, "runs_in", "environment.prod")
        e("dataset." + name, "owned_by", "role.platform-lead")
        e("component.batch-jobs", "writes_to", "dataset." + name)
    fields = {  # dataset: [(field, type, required, term, fed by or None)]
        "silver.fund": [("fund_id", "char(5)", True, "fund-id", ["sourcecolumn.dim-product.prod_cr_id"]),
                        ("state", "varchar", True, "fund-state", ["sourcecolumn.dim-product.state"])],
        "silver.fund_holding": [("fund_id", "char(5)", True, "fund-id", ["sourcecolumn.fund-holding.fund_id"]),
                                ("holding_name", "varchar", True, "holding-name", ["sourcecolumn.fund-holding.holding_name"]),
                                ("holding_pct", "decimal", True, "holding-weight", ["sourcecolumn.fund-holding.holding_pct"]),
                                ("language_code", "char(2)", True, "language", ["sourcecolumn.fund-holding.language_code"])],
        "gold.portfolio_holdings": [("fund_id", "char(5)", True, "fund-id", ["field.silver.fund_holding.fund_id"]),
                                    ("language_code", "char(2)", True, "language", ["field.silver.fund_holding.language_code"]),
                                    ("holding_name", "varchar", True, "holding-name", ["field.silver.fund_holding.holding_name"]),
                                    ("holding_pct", "decimal", True, "holding-weight", ["field.silver.fund_holding.holding_pct"]),
                                    ("holding_rank", "integer", True, None, None)],
        "gold.portfolio_allocations": [("fund_id", "char(5)", True, "fund-id", ["field.silver.fund_holding.fund_id"]),
                                       ("allocation_pct", "decimal", True, "holding-weight", ["field.silver.fund_holding.holding_pct"])],
    }
    for ds, fs in fields.items():
        for name, typ, required, term, fed in fs:
            fid = "field.%s.%s" % (ds, name)
            n(fid, "DatasetField", "%s.%s" % (ds, name), data_type=typ, required=required)
            e("dataset." + ds, "has_field", fid)
            if term:
                e(fid, "carries_term", "term." + term)
            for x in fed or []:
                e(fid, "fed_by", x)
    e("field.silver.fund.state", "bound_to", "codeset.fund-state")
    for ds, grain in (("silver.fund", ["fund_id"]), ("silver.fund_holding", ["fund_id", "holding_name", "language_code"]),
                      ("gold.portfolio_holdings", ["fund_id", "language_code", "holding_rank"]), ("gold.portfolio_allocations", ["fund_id"])):
        for g in grain:
            e("dataset." + ds, "grain", "field.%s.%s" % (ds, g))
    # D4: the two entities
    n("tolerance.count-exact", "Tolerance", "exact count", value=0, tolerance_unit="count", rationale="The fact-sheet list is exhaustive.")
    e("tolerance.count-exact", "set_by", "role.platform-lead")
    n("tolerance.count-10", "Tolerance", "ten rows", value=10, tolerance_unit="count", rationale="A fund may hold fewer than ten positions.")
    e("tolerance.count-10", "set_by", "role.platform-lead")
    for eid, ds, mappings, count in (
            ("fund", "silver.fund", [("dim-product", ["prod_cr_id"], "lpad: 5, '0'")], 103),
            ("fund-holding", "silver.fund_holding", [("fund-holding", ["fund_id"], "identity")], 1030)):
        n("conformedentity." + eid, "ConformedEntity", eid.replace("-", " "))
        e("conformedentity." + eid, "materialised_as", "dataset." + ds)
        n("historypolicy." + eid, "HistoryPolicy", eid + " history", history_kind="snapshot_per_batch")
        e("conformedentity." + eid, "keeps_history", "historypolicy." + eid)
        n("scoperule." + eid, "ScopeRule", eid + " scope",
          conditions=["state != CLOSED"] if eid == "fund" else ["fund_id exists_in silver.fund"],
          expected_count=count, count_as_of="2026-06-30",
          count_source="the fact-sheet list" if eid == "fund" else "the fact-sheet list: 103 funds, ten holdings each")
        e("conformedentity." + eid, "scoped_by", "scoperule." + eid)
        e("scoperule." + eid, "within_tolerance", "tolerance.count-exact" if eid == "fund" else "tolerance.count-10")
        for tid, cols, transform in mappings:
            mid = "identitymapping.%s.%s" % (eid, tid)
            n(mid, "IdentityMapping", "%s id from source.%s" % (eid, tid.replace("-", "_")), transform=transform)
            e("conformedentity." + eid, "has_identity_mapping", mid)
            e(mid, "from_table", "sourcetable." + tid)
            for c in cols:
                e(mid, "id_column", "sourcecolumn.%s.%s" % (tid, c))
            e(mid, "target_key", "field.%s.fund_id" % ds)
    # silver.fund_holding's fund_id comes from fund_holding, so the fund entity also maps that source
    n("identitymapping.fund.fund-holding", "IdentityMapping", "fund id from source.fund_holding", transform="identity")
    e("conformedentity.fund", "has_identity_mapping", "identitymapping.fund.fund-holding")
    e("identitymapping.fund.fund-holding", "from_table", "sourcetable.fund-holding")
    e("identitymapping.fund.fund-holding", "id_column", "sourcecolumn.fund-holding.fund_id")
    e("identitymapping.fund.fund-holding", "target_key", "field.silver.fund.fund_id")
    # D5: the outputs and the contract the BI pages consume
    for oid, ds in (("portfolio-holdings", "gold.portfolio_holdings"), ("portfolio-allocations", "gold.portfolio_allocations")):
        n("output." + oid, "Output", oid.replace("-", "_"), shape="long", period_dependency="point_in_time", needs_history=False)
        e("output." + oid, "materialised_as", "dataset." + ds)
        e("output." + oid, "output_of", "product.fund-profile")
        e("output." + oid, "joins_to", "conformedentity.fund")
    e("role.analyst", "reads_output", "output.portfolio-holdings")
    n("datacontract.portfolio-holdings-v1", "DataContract", "portfolio_holdings v1", version="1",
      contract_fields=["fund_id: char(5), required", "language_code: char(2), required", "holding_name: varchar, required",
                       "holding_pct: decimal, required", "holding_rank: integer, required"],
      keys=["fund_id", "language_code", "holding_rank"], change_policy="additive_only")
    e("datacontract.portfolio-holdings-v1", "contract_of", "dataset.gold.portfolio_holdings")
    e("datacontract.portfolio-holdings-v1", "owned_by", "role.product-owner")
    e("system.bi-fund-pages", "consumes", "datacontract.portfolio-holdings-v1")
    # D6: the ranking rule
    n("derivationrule.holdings-top-10", "DerivationRule", "holdings top 10", rule_kind="ranking",
      logic="rank_by: {order: [holding_pct desc], partition: [fund_id, language_code], top: 10, ties: first_by: holding_name}",
      period_dependency="point_in_time", specified_in="§spec-3.4")
    e("field.gold.portfolio_holdings.holding_rank", "derived_by", "derivationrule.holdings-top-10")
    for i in ("holding_pct", "fund_id", "language_code"):
        e("derivationrule.holdings-top-10", "rule_input", "field.silver.fund_holding." + i)
    for case, behaviour in (("tie", "first_by: holding_name"), ("null_input", "exclude"), ("missing_history", "exclude"),
                            ("younger_than_lookback", "include_as: null"), ("duplicate_input", "error")):
        cid = "edgecase.holdings-top-10." + case
        n(cid, "EdgeCase", "holdings top 10 on " + case.replace("_", " "), case=case, behaviour=behaviour)
        e("derivationrule.holdings-top-10", "has_edge_case", cid)
    n("ruleexample.holdings-top-10", "RuleExample", "holdings top 10 example", inputs="Fixture/holdings-in",
      expected_output="Fixture/holdings-out", computed_by="independent_calculation")
    e("derivationrule.holdings-top-10", "has_example", "ruleexample.holdings-top-10")
    # D7: a hard rule at each gate, carried out by the flow's checks
    n("tolerance.pct-0-5", "Tolerance", "half a percent", value=0.5, tolerance_unit="percent", rationale="Rounding of published weights.")
    e("tolerance.pct-0-5", "set_by", "role.platform-lead")
    n("failureaction.hard-gate", "FailureAction", "stop and tell the platform lead", auto_retry=False)
    e("failureaction.hard-gate", "notifies", "role.platform-lead")
    e("failureaction.hard-gate", "follows_runbook", "runbook.hard-gate-failure")
    for qid, gate, assertion, targets, check, tol in (
            ("bronze-keys-unique", 1, "unique: {table: bronze.source__fund_holding, keys: [fund_id, holding_name, effective_date]}",
             ["dataset.bronze.source__fund_holding"], "check.bronze-keys-unique", None),
            ("fund-count-equals-expected", 2, "count_equals: {table: silver.fund, expected: scope_rule.expected_count, tolerance: count-exact}",
             ["dataset.silver.fund"], "check.fund-count-equals-expected", "tolerance.count-exact"),
            ("allocations-sum-100", 3, "sum_to: {partition: [fund_id], total: 100, tolerance: pct-0.5}",
             ["dataset.gold.portfolio_allocations", "field.gold.portfolio_allocations.allocation_pct"], "check.allocations-sum-100", "tolerance.pct-0-5")):
        rid = "qualityrule." + qid
        n(rid, "QualityRule", qid.replace("-", "_"), rule_id=qid.replace("-", "_"), gate=gate, assertion=assertion, severity="hard",
          example_failure="Fixture/%s-bad" % qid, specified_in="§validation-gate-%d" % gate)
        for t in targets:
            e(rid, "targets", t)
        e(rid, "carried_out_by", check)
        e(rid, "failure_action", "failureaction.hard-gate")
        e(rid, "stewarded_by", "role.platform-lead")
        if tol:
            e(rid, "within_tolerance", tol)
    # D8: what each step of the flow executes, and which design table each artifact is
    for step, x in (("fp-03", "copypolicy.fund-holding"), ("fp-04", "copypolicy.dim-product"), ("fp-06", "conformedentity.fund"),
                    ("fp-07", "conformedentity.fund-holding"), ("fp-09", "output.portfolio-holdings"),
                    ("fp-09", "derivationrule.holdings-top-10"), ("fp-09b", "output.portfolio-allocations")):
        e("step." + step, "executes", x)
    for artifact, x in (("src-fund-holding", "sourcetable.fund-holding"), ("src-dim-product", "sourcetable.dim-product"),
                        ("bronze-fund-holding", "dataset.bronze.source__fund_holding"), ("bronze-dim-product", "dataset.bronze.source__dim_product"),
                        ("silver-fund", "dataset.silver.fund"), ("silver-fund-holding", "dataset.silver.fund_holding"),
                        ("gold-portfolio-holdings", "dataset.gold.portfolio_holdings"),
                        ("gold-portfolio-allocations", "dataset.gold.portfolio_allocations"), ("control-batch", "dataset.control.batch")):
        e("artifact." + artifact, "represents", x)
    # D9: the identity the pipeline runs as, and the runbook's recovery point
    n("identity.pipeline", "Identity", "pipeline service", identity_kind="service",
      access=["source: read", "bronze: write", "silver: write", "gold: write", "control: write"])
    e("identity.pipeline", "in_environment", "environment.prod")
    e("identity.pipeline", "runs_flow", "flow.fund-profile")
    n("identity.analyst", "Identity", "analyst", identity_kind="human", access=["gold: read"])
    e("identity.analyst", "in_environment", "environment.prod")
    e("runbook.hard-gate-failure", "resumes_from", "step.fp-05")
    # D9: the tests the build plan promises, drafted from D6 to D8 and confirmed by the platform lead
    for tid, test_kind, label, exercised, fixture, expected in (
            ("holdings-top-10-unit", "unit", "holdings top 10 on its example", ["derivationrule.holdings-top-10"],
             "Fixture/holdings-in", "Fixture/holdings-out"),
            ("portfolio-holdings-contract", "contract", "portfolio holdings keep contract v1", ["output.portfolio-holdings"],
             "gold.portfolio_holdings after a month-end batch", "the fields, types and keys of portfolio holdings v1, in order"),
            ("portfolio-holdings-parity", "parity", "portfolio holdings match the current fact sheets", ["output.portfolio-holdings"],
             "Fixture/fact-sheet-holdings-2026-09", "the same ten holdings per fund and language, in the same order, weights within half a percent"),
            ("portfolio-allocations-parity", "parity", "portfolio allocations match the current fact sheets", ["output.portfolio-allocations"],
             "Fixture/fact-sheet-allocations-2026-09", "the same allocations per fund, within half a percent"),
            ("fund-profile-flow", "flow", "a month-end batch from start to end", ["flow.fund-profile"],
             "Fixture/month-end-sources", "every step passes in order, gold is written and the batch is marked validated"),
            ("fund-profile-rerun", "rerun", "the same batch run twice", ["flow.fund-profile"],
             "Fixture/month-end-sources, run twice for one period end", "the second run writes the same rows as the first"),
            ("hard-gate-failure-forced", "forced_failure", "a duplicate holding stops the batch at gate 1",
             ["runbook.hard-gate-failure", "qualityrule.bronze-keys-unique"], "Fixture/bronze-keys-unique-bad",
             "gate 1 stops the batch, the platform lead is told, and once the source is fixed the run resumes from gate 1")):
        n("pipelinetest." + tid, "PipelineTest", label, test_kind=test_kind, fixture=fixture, expected_result=expected)
        for x in exercised:
            e("pipelinetest." + tid, "test_of", x)
    return nodes, edges


# ============================ the bridge to the report ontology ============================

BRIDGE_PROPERTIES = {
    "is_dataset": rel("Table", "Dataset", "is_report_table", "is dataset", "The gold dataset a report's table is.", 1),
    "is_field": rel("Column", "DatasetField", "is_report_column", "is field", "The dataset field a report's column is.", 1),
    "backed_by": rel("QualityCheck", "QualityRule", "backs", "backed by",
                     "The pipeline's quality rule a report's check relies on: the data is checked at its gate, the report checks what it adds."),
}
BRIDGE_RULES = [
    policy("a-report-reads-gold", [node("t", "Table"), edge("t", "is_dataset", "d"), node("d", "Dataset", {"layer": {"!=": "gold"}})],
           "a report's table is a dataset outside gold", "A report reads gold: what consumers read (DECISIONS.md, D5).", "RM1"),
    policy("a-report-column-is-a-field-of-its-table", [node("c", "Column"), edge("c", "inTable", "t"), edge("t", "is_dataset", "d"),
                                                     edge("c", "is_field", "f"), {"not_edge": ["d", "has_field", "f"]}],
           "a report column is a field of another dataset than its table's", "A column and its table are one dataset and one of its fields.", "RM1"),
    policy("a-report-reads-a-contracted-dataset", [node("t", "Table"), edge("t", "is_dataset", "d"), {"not_edge": ["*", "contract_of", "d"]}],
           "a report reads a gold dataset no data contract governs",
           "What a report depends on is promised by a contract, so a change to it is versioned (D5).", "RM1", severity="warn"),
]
BRIDGE_QUESTIONS = {
    "RM1": q("an analyst", "Which report columns are which gold dataset fields, and where does each field come from?",
             "The lineage of a report's value: the column, the gold field, the rule or the field that feeds it.",
             [node("c", "Column"), edge("c", "is_field", "f"), node("f", "DatasetField"),
              {"optional": [edge("c", "inTable", "t"), edge("t", "is_dataset", "d")]},
              {"optional": [edge("f", "derived_by", "r"), node("r", "DerivationRule")]}, {"optional": [edge("f", "fed_by", "x")]}],
             ["c.columnName", "d.label", "f.label", "r.label", "x.label"], "non_empty"),
    "RM2": q("compliance", "Which report quality checks rely on which pipeline quality rules, at which gate?",
             "Two levels, no overlap: the pipeline checks the data at its gate; the report checks what it adds (DECISIONS.md).",
             [node("k", "QualityCheck"), edge("k", "backed_by", "r"), node("r", "QualityRule")],
             ["k.label", "r.rule_id", "r.gate"], "any"),
}
