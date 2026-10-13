"""Write the medallion ontology (ontology/medallion), the OTO unit this repository publishes.

    python tools/build.py              # writes ontology/medallion and ontology/report-medallion
    python tools/build.py <folder>     # writes them under another folder (the tests compare the two)

Release 1 was the flow slice: the rules a declared medallion flow must satisfy. Release 2 adds the
design slice (tools/design.py): the classes of steps D1 to D7 and D9, how the flow executes them,
and the report-medallion bridge.

The flow itself is plain `flow` data (steps, waits, checks, artifacts). This ontology adds the
medallion's own vocabulary on the flow's terms (the step kinds, a gate's number, a table's layer)
and the validations of the specification's section 3.8.2 that are specific to a medallion
pipeline. The design classes (sources, entities, outputs, rules) come in the next slice.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import design  # noqa: E402

ROOT_OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ontology")
OUT = os.path.join(ROOT_OUT, "medallion")
BRIDGE_OUT = os.path.join(ROOT_OUT, "report-medallion")
NS = "https://cynergis.ai/ont/medallion#"
KINDS = ["create_batch", "check_sources_ready", "copy_to_bronze", "run_gate", "build_reference",
         "build_entity", "build_output", "reconcile", "mark_validated"]
WORK = "DeterministicStep|OcrStep|ClaudeStep|HumanStep"
SPEC = "medallion-pipeline-ontology"


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
    """The patterns that put a step in a medallion flow."""
    return [node("f", "Flow", {"flowKind": "medallion"}), edge("f", "hasStep", step)]


def kind(var, value, extra=None):
    where = {"stepKind": value}
    where.update(extra or {})
    return node(var, "Step", where)


def policy(rid, when, flag, why, answers):
    return {"id": rid, "kind": "policy", "severity": "blocking", "when": when, "then": {"flag": flag},
            "why": why, "validated_by": "", "answers": answers}


def comes_after(rid, later, earlier, why, later_extra=None, earlier_extra=None):
    """Every step of kind `later` comes after a step of kind `earlier` in the same flow."""
    return policy(rid, flow_scope("s") + [kind("s", later, later_extra),
                                          {"not": [edge("s", "after", "g"), edge("f", "hasStep", "g"), kind("g", earlier, earlier_extra)]}],
                  "a %s step does not come after %s" % (later, earlier + ("" if not earlier_extra else " (gate %s)" % earlier_extra["gate"])),
                  why, "MD1")


def after_every(rid, later, earlier, why, later_extra=None, earlier_extra=None):
    """A step of kind `later` comes after every step of kind `earlier` in the same flow."""
    return policy(rid, flow_scope("s") + [kind("s", later, later_extra), edge("f", "hasStep", "e"), kind("e", earlier, earlier_extra),
                                          {"not_edge": ["s", "after", "e"]}],
                  "a %s step%s runs before a %s step has finished" % (later, "" if not later_extra else " (gate %s)" % later_extra["gate"], earlier),
                  why, "MD1")


RULES = [
    policy("medallion-step-declares-its-kind",
           flow_scope("s") + [node("s", WORK, {"stepKind": {"exists": False}})],
           "a step of a medallion flow declares no step kind",
           "The kinds are the flow's vocabulary; a step without one cannot be checked against it (spec 3.8.1).", "MD1"),
    policy("medallion-step-kind-is-known",
           flow_scope("s") + [node("s", "Step", {"stepKind": {"not_in": KINDS}})],
           "the step kind is not one of the medallion's: %s" % ", ".join(KINDS),
           "A flow uses only the fixed kinds, so the implementation agent can emit every step from a template (spec 3.8.1, 3.8.2 Vocabulary).", "MD1"),
    policy("medallion-gate-has-a-number",
           flow_scope("s") + [node("s", "Step", {"stepKind": "run_gate", "gate": {"exists": False}})],
           "a run_gate step does not say which gate it runs (1, 2 or 3)",
           "Each gate runs at one boundary: 1 landing to bronze, 2 bronze to silver, 3 silver to gold (spec 3.7).", "MD2"),
]
for one in ("create_batch", "check_sources_ready", "mark_validated"):
    RULES.append(policy("medallion-flow-has-%s" % one.replace("_", "-"),
                        [node("f", "Flow", {"flowKind": "medallion"}), {"not": [edge("f", "hasStep", "s"), kind("s", one)]}],
                        "the medallion flow has no %s step" % one,
                        "Exactly one %s per flow (spec 3.8.1)." % one, "MD1"))
    RULES.append(policy("medallion-flow-has-one-%s" % one.replace("_", "-"),
                        flow_scope("a") + [kind("a", one), edge("f", "hasStep", "b"), kind("b", one, {"id": {"!=": "$a"}})],
                        "the medallion flow has more than one %s step" % one,
                        "Exactly one %s per flow (spec 3.8.1)." % one, "MD1"))
for gate in (1, 2, 3):
    RULES.append(policy("medallion-flow-runs-gate-%d" % gate,
                        [node("f", "Flow", {"flowKind": "medallion"}), {"not": [edge("f", "hasStep", "s"), kind("s", "run_gate", {"gate": gate})]}],
                        "the medallion flow has no step that runs gate %d" % gate,
                        "Every gate runs exactly once per batch (spec 3.8.1).", "MD2"))
RULES.append(policy("medallion-flow-runs-each-gate-once",
                    flow_scope("a") + [kind("a", "run_gate"), edge("f", "hasStep", "b"),
                                       kind("b", "run_gate", {"gate": "$a.gate", "id": {"!=": "$a"}})],
                    "two steps of the medallion flow run the same gate",
                    "Every gate runs exactly once per batch (spec 3.8.1).", "MD2"))
# order and gate placement (spec 3.8.2 Order, Gate placement)
RULES += [
    comes_after("medallion-sources-checked-after-the-batch-opens", "check_sources_ready", "create_batch",
                "The sources are checked for an open batch (spec 3.8.1, order 1-2)."),
    comes_after("medallion-copy-after-the-sources-are-ready", "copy_to_bronze", "check_sources_ready",
                "A source is copied only when every expected source has rows for the period (spec 3.8.1, order 2-3)."),
    after_every("medallion-gate-1-after-every-copy", "run_gate", "copy_to_bronze",
                "Gate 1 checks the whole of bronze, so it waits for every copy (spec 3.8.1, order 3-4).", later_extra={"gate": 1}),
    comes_after("medallion-reference-after-gate-1", "build_reference", "run_gate",
                "Reference data is built from a bronze that passed gate 1 (spec 3.8.1, order 4-5).", earlier_extra={"gate": 1}),
    comes_after("medallion-entity-after-gate-1", "build_entity", "run_gate",
                "A silver entity is built only from a bronze that passed gate 1 (spec 3.8.2 Gate placement).", earlier_extra={"gate": 1}),
    after_every("medallion-gate-2-after-every-entity", "run_gate", "build_entity",
                "Gate 2 checks the whole of silver, so it waits for every entity (spec 3.8.1, order 6-7).", later_extra={"gate": 2}),
    comes_after("medallion-output-after-gate-2", "build_output", "run_gate",
                "A gold output is built only from a silver that passed gate 2 (spec 3.8.2 Gate placement).", earlier_extra={"gate": 2}),
    after_every("medallion-gate-3-after-every-output", "run_gate", "build_output",
                "Gate 3 checks the whole of gold, so it waits for every output (spec 3.8.1, order 8-9).", later_extra={"gate": 3}),
    comes_after("medallion-reconcile-after-gate-3", "reconcile", "run_gate",
                "A gold total is reconciled once gold passed gate 3 (spec 3.8.1, order 9-10).", earlier_extra={"gate": 3}),
    comes_after("medallion-validated-after-gate-3", "mark_validated", "run_gate",
                "The batch is validated only after gate 3 (spec 3.8.2 Gate placement).", earlier_extra={"gate": 3}),
    after_every("medallion-validated-after-every-reconcile", "mark_validated", "reconcile",
                "Every reconciliation has run before the batch is handed to approval (spec 3.8.1, order 10-11)."),
]
# layer direction and what each kind writes (spec 3.8.1 Reads/Writes, 3.8.2 Layer direction)
RULES += [
    policy("medallion-no-step-reads-above-what-it-writes",
           flow_scope("s") + [edge("s", "reads", "a"), node("a", "Artifact", {"layer": "gold"}),
                              edge("s", "writes", "b"), node("b", "Artifact", {"layer": {"in": ["bronze", "silver"]}})],
           "the step reads gold and writes a lower layer", "Data moves up the layers, never down (spec 3.8.2 Layer direction).", "MD1"),
    policy("medallion-no-step-reads-silver-into-bronze",
           flow_scope("s") + [edge("s", "reads", "a"), node("a", "Artifact", {"layer": "silver"}),
                              edge("s", "writes", "b"), node("b", "Artifact", {"layer": "bronze"})],
           "the step reads silver and writes bronze", "Data moves up the layers, never down (spec 3.8.2 Layer direction).", "MD1"),
    policy("medallion-copy-writes-bronze",
           flow_scope("s") + [kind("s", "copy_to_bronze"), edge("s", "writes", "a"), node("a", "Artifact", {"layer": {"not_in": ["bronze"]}})],
           "a copy_to_bronze step writes outside bronze", "A copy lands one source in bronze, and nothing else (spec 3.8.1).", "MD1"),
    policy("medallion-entity-writes-silver",
           flow_scope("s") + [kind("s", "build_entity"), edge("s", "writes", "a"), node("a", "Artifact", {"layer": {"not_in": ["silver"]}})],
           "a build_entity step writes outside silver", "An entity is one silver table (spec 3.8.1).", "MD1"),
    policy("medallion-output-writes-gold",
           flow_scope("s") + [kind("s", "build_output"), edge("s", "writes", "a"), node("a", "Artifact", {"layer": {"not_in": ["gold"]}})],
           "a build_output step writes outside gold", "An output is one gold table (spec 3.8.1).", "MD1"),
    policy("medallion-output-reads-no-other-output",
           flow_scope("s") + [kind("s", "build_output"), edge("s", "reads", "a"), node("a", "Artifact", {"layer": "gold"})],
           "a build_output step reads a gold table", "An output reads silver; one output reading another is forbidden (spec 3.8.1).", "MD1"),
    policy("medallion-gate-writes-no-data",
           flow_scope("s") + [kind("s", "run_gate"), edge("s", "writes", "a"), node("a", "Artifact", {"layer": {"in": ["bronze", "silver", "gold"]}})],
           "a run_gate step writes a data layer", "A gate reads and records; it changes no data (spec 3.8.1).", "MD2"),
]

QUESTIONS = {
    "MD1": {"who": "a platform lead",
            "question": "Which steps make up each medallion flow, of which kind, in which parallel group, reading and writing which layers?",
            "why": "The declared flow is what a reviewer approves and what the implementation agent emits; each step's kind and layers are "
                   "what the medallion's rules check (spec 3.8).",
            "validated_by": "",
            "ask": {"when": [node("f", "Flow", {"flowKind": "medallion"}), edge("f", "hasStep", "s"), node("s", "Step"),
                             {"optional": [edge("s", "reads|writes", "a"), node("a", "Artifact")]}],
                    "select": ["f.label", "s.stepId", "s.stepKind", "s.parallelGroup", "a.path", "a.layer"]},
            "gate": "non_empty"},
    "MD2": {"who": "a platform lead",
            "question": "Which gate does each run_gate step run, and which checks does it hold, hard or soft?",
            "why": "A gate is where a batch stops; its checks are the quality rules of that boundary (spec 3.7, 3.8.1).",
            "validated_by": "",
            "ask": {"when": [node("s", "Step", {"stepKind": "run_gate"}), {"optional": [edge("s", "hasCheck", "c"), node("c", "Check")]}],
                    "select": ["s.stepId", "s.gate", "c.checkId", "c.blocking"]},
            "gate": "non_empty"},
}

CONFIG = {
    "_about": "The medallion pipeline's first slice: the vocabulary and rules a declared medallion flow must satisfy, on the "
              "flow's own terms. The flow is plain flow data; a Flow with flowKind medallion is governed by these rules. "
              "The design classes (sources, entities, outputs, rules) come in the next slice.",
    "_summary": "A medallion data pipeline's batch flow: its fixed step kinds, a gate's number, a table's layer, and the rules "
                "that make a declared flow valid (order, gate placement, layer direction), checked when the flow is captured.",
    "name": "Medallion pipeline", "ontology_version": 1, "strict_domains": False, "languages": ["en"],
    "classes": {}, "properties": {},
    "attributes": {
        "Artifact": {"layer": {"type": "enum:source|bronze|silver|gold|control", "label": "layer",
                               "definition": "The layer a table of the pipeline sits in: a source read from outside, bronze (copied as "
                                             "is), silver (conformed), gold (what consumers read), or control (the batch's own records)."}},
        "Step": {"gate": {"type": "integer", "label": "gate",
                          "definition": "For a run_gate step, the boundary it checks: 1 landing to bronze, 2 bronze to silver, "
                                        "3 silver to gold."}},
    },
}

MANIFEST = {"name": "medallion", "release": 1, "domain": "data",
            "summary": CONFIG["_summary"], "extends": ["software-architecture", "flow"], "namespace": NS,
            "engine": ">=0.11.7", "carries": ["vocabulary", "rationale", "rules", "questions", "sample", "readme"],
            "maintainer": "Cynergis",
            "changelog": [{"release": 1, "at": "2026-10-13",
                           "note": "The flow slice of the Medallion Pipeline Ontology (spec 1.2.0): the step kinds, gate and layer, "
                                   "and the rules of 3.8.1 and 3.8.2 that are specific to a medallion flow, on flow release 2."}]}

RATIONALE = {"_about": "Why each term exists. The two attributes refine flow terms; the rules carry their own `why`, citing the "
                       "specification's section. `validated_by` is empty until a person who knows the domain confirms the entry.",
             "classes": {}, "properties": {}}

README = """# Medallion pipeline: the flow slice

Extends `software-architecture` (and so `product` and `portfolio`) and `flow`. A medallion data
pipeline's batch run is plain `flow` data: steps that wait for each other, gates as steps with
checks, tables as artifacts. A `Flow` whose `flowKind` is `medallion` is governed by this
ontology's rules, checked when the flow is captured (`oto curate check` refuses a flow that breaks
one):

- the step kinds are the medallion's (`Step.stepKind`): %s;
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
""" % ", ".join("`%s`" % k for k in KINDS)


def stamp(n):
    n.update({"status": "current", "as_of": "2026-10-13", "valid_from": "2026-10-13", "source_doc": SPEC, "sources": [SPEC],
              "aliases": [], "tags": [], "evidence": [{"doc": SPEC, "where": "7", "quote": n["label"]}]})
    return n


def sample():
    """The specification's worked instance: the fund-profile flow, abridged to the steps it declares."""
    nodes, edges = [], []

    def n(nid, kind_, label, **attrs):
        nodes.append(stamp({"id": nid, "type": kind_, "label": label, "summary": label,
                            "attributes": {k: v for k, v in attrs.items() if v is not None}}))
        return nid

    def e(a, rel, b):
        edges.append({"from": a, "rel": rel, "to": b})

    flow = n("flow.fund-profile", "Flow", "Fund profile batch", flowKind="medallion", trigger="on_sources_ready", resumable=True, value="1")
    tables = {"src-fund-holding": ("source.fund_holding", "source"), "src-dim-product": ("source.dim_product", "source"),
              "control-batch": ("control.batch", "control"), "bronze-fund-holding": ("bronze.source__fund_holding", "bronze"),
              "bronze-dim-product": ("bronze.source__dim_product", "bronze"), "silver-fund": ("silver.fund", "silver"),
              "silver-fund-holding": ("silver.fund_holding", "silver"), "gold-portfolio-holdings": ("gold.portfolio_holdings", "gold"),
              "gold-portfolio-allocations": ("gold.portfolio_allocations", "gold")}
    for tid, (path, layer) in tables.items():
        n("artifact." + tid, "Artifact", path, path=path, format="table", layer=layer, carries=["DataStore"])
    n("param.pct-tolerance", "ConfigParameter", "pct_tolerance", paramName="pct_tolerance", value="0.5")
    n("metric.allocation-sum", "Metric", "allocation_sum", metricName="allocation_sum")
    n("outcome.pass", "Outcome", "pass", outcomeName="pass")
    n("outcome.fail", "Outcome", "fail", outcomeName="fail")
    steps = [  # id, kind, gate, waits for, reads, writes, parallel group, what it executes (the binding names the command)
        ("fp-01", "create_batch", None, [], [], ["control-batch"], None, "create-batch"),
        ("fp-02", "check_sources_ready", None, ["fp-01"], ["src-fund-holding", "src-dim-product"], [], None, "check-sources-ready"),
        ("fp-03", "copy_to_bronze", None, ["fp-02"], ["src-fund-holding"], ["bronze-fund-holding"], "copy", "copy-fund-holding"),
        ("fp-04", "copy_to_bronze", None, ["fp-02"], ["src-dim-product"], ["bronze-dim-product"], "copy", "copy-dim-product"),
        ("fp-05", "run_gate", 1, ["fp-03", "fp-04"], ["bronze-fund-holding", "bronze-dim-product"], [], None, "gate 1"),
        ("fp-06", "build_entity", None, ["fp-05"], ["bronze-dim-product", "bronze-fund-holding"], ["silver-fund"], None, "build-fund"),
        ("fp-07", "build_entity", None, ["fp-05", "fp-06"], ["bronze-fund-holding", "silver-fund"], ["silver-fund-holding"], None, "build-fund-holding"),
        ("fp-08", "run_gate", 2, ["fp-06", "fp-07"], ["silver-fund", "silver-fund-holding"], [], None, "gate 2"),
        ("fp-09", "build_output", None, ["fp-08"], ["silver-fund", "silver-fund-holding"], ["gold-portfolio-holdings"], "gold", "build-portfolio-holdings"),
        ("fp-09b", "build_output", None, ["fp-08"], ["silver-fund-holding"], ["gold-portfolio-allocations"], "gold", "build-portfolio-allocations"),
        ("fp-10", "run_gate", 3, ["fp-09", "fp-09b"], ["gold-portfolio-holdings", "gold-portfolio-allocations"], [], None, "gate 3"),
        ("fp-11", "mark_validated", None, ["fp-10"], [], ["control-batch"], None, "mark-validated"),
    ]
    for sid, kind_, gate, waits, reads, writes, group, executes in steps:
        n("step." + sid, "DeterministicStep", sid, stepId=sid, stepKind=kind_, gate=gate, parallelGroup=group,
          command="<binding> %s --batch {batch_id} --period-end {period_end}" % executes)
        e(flow, "hasStep", "step." + sid)
        for w in waits:
            e("step." + sid, "waitsFor", "step." + w)
        for a in reads:
            e("step." + sid, "reads", "artifact." + a)
        for a in writes:
            e("step." + sid, "writes", "artifact." + a)
    n("param.expected-fund-count", "ConfigParameter", "expected_fund_count", paramName="expected_fund_count", value="103")
    n("metric.fund-count", "Metric", "fund_count", metricName="fund_count")
    n("invariant.idempotent", "Invariant", "idempotent",
      statement="A step re-run for the same batch and period end writes the same rows.", concerns=["DataStore"])

    def check(cid, step, label, kind_, expression, metric=None, param=None, invariant=False):
        n("check." + cid, "Check", label, checkId=cid, checkKind=kind_, expression=expression, blocking="hard")
        e("step." + step, "hasCheck", "check." + cid)
        e("check." + cid, "onFail", "outcome.fail")
        if metric:
            e("check." + cid, "measuresMetric", metric)
            e("step." + step, "records", metric)
        if param:
            e("check." + cid, "comparedTo", param)
        if invariant:
            e("invariant.idempotent", "enforcedBy", "check." + cid)

    # the checks the specification gives each step: a batch opens once, sources are present, every
    # transformation is idempotent (re-run test), each gate holds its quality rules
    check("no-active-batch", "fp-01", "no batch is active for the period", "control", "count(control.batch where state = active) == 0")
    check("sources-present-for-period", "fp-02", "every expected source has rows for the period end", "control",
          "present_for_period(source.fund_holding) and present_for_period(source.dim_product)")
    for sid in ("fp-03", "fp-04", "fp-06", "fp-07", "fp-09", "fp-09b"):
        check("%s-rerun" % sid, sid, "%s writes the same rows when re-run" % sid, "rerun", "rows(rerun(batch_id)) == rows(batch_id)", invariant=True)
    check("bronze-keys-unique", "fp-05", "bronze keys are unique", "gate1", "unique(bronze.source__fund_holding, [fund_id, holding_name, effective_date])")
    check("fund-count-equals-expected", "fp-08", "silver fund count equals the expected count", "gate2",
          "count(silver.fund) == expected_fund_count", metric="metric.fund-count", param="param.expected-fund-count")
    check("allocations-sum-100", "fp-10", "allocations sum to 100", "gate3", "abs(sum(allocation_pct) - 100) <= pct_tolerance",
          metric="metric.allocation-sum", param="param.pct-tolerance")
    check("all-gates-passed", "fp-11", "every gate of the batch passed", "control", "state(gate 1) == state(gate 2) == state(gate 3) == passed")
    return {"_about": "The fund-profile flow of the specification's worked instance (section 7), as plain flow data with the "
                      "medallion's kinds, gates and layers. Replace it.", "nodes": nodes, "edges": edges}


CONFIG["classes"] = design.CLASSES
CONFIG["properties"] = design.PROPERTIES
for _kind, _declared in design.ATTRIBUTES.items():
    CONFIG["attributes"].setdefault(_kind, {}).update(_declared)
CONFIG["_about"] = ("The medallion pipeline: its batch flow on the flow's terms (release 1) and its design (release 2): the classes "
                    "of the specification's steps D1 to D7 and D9, and how the flow executes them. Names follow DECISIONS.md.")
CONFIG["_summary"] = ("A medallion data pipeline, source systems to bronze, silver and gold: its sources, reference data, conformed "
                      "entities, gold outputs and contracts, derivation and quality rules, build plan, and the batch flow that "
                      "executes them, with the rules a design and a declared flow must satisfy.")
RULES += design.RULES
QUESTIONS.update(design.QUESTIONS)
RATIONALE["classes"], RATIONALE["properties"] = design.rationale()
RATIONALE["_about"] = ("Why each term exists: the specification's step it comes from. The rules carry their own `why`. "
                       "`validated_by` is empty until a person who knows the domain confirms the entry.")
MANIFEST["release"] = 2
MANIFEST["summary"] = CONFIG["_summary"]
MANIFEST["changelog"] = [
    {"release": 2, "at": "2026-10-13",
     "note": "The design slice (spec 1.2.0, D1 to D7 and D9): sources, reference data, conformed entities, datasets, outputs and "
             "data contracts, derivation and quality rules, identities; a flow step executes the design; correctness as blocking "
             "rules, completeness as questions that must come back empty. Names per DECISIONS.md."}] + MANIFEST["changelog"]
_flow_sample = sample


def sample():
    graph = _flow_sample()
    nodes, edges = design.design_sample(stamp)
    graph["nodes"] += nodes
    graph["edges"] += edges
    graph["_about"] = ("The specification's worked instance (section 7), whole: the fund-profile data product, its two sources, the "
                       "fund and fund-holding entities, two gold outputs and a contract, the top-10 rule, a hard quality rule at "
                       "each gate, and the flow that executes them. Neutral source names. Replace it.")
    return graph


README = README.replace("# Medallion pipeline: the flow slice", "# Medallion pipeline") + """
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
"""


def write(name, payload):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        if isinstance(payload, str):
            f.write(payload)
        else:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.write("\n")


os.makedirs(OUT, exist_ok=True)
write("manifest.json", MANIFEST)
write("ontology.config.json", CONFIG)
write("rules.json", {"_about": "The validations of a declared medallion flow (spec 3.8.1, 3.8.2) and of its design (D2 to D9), each naming the question it "
                               "protects.", "rules": RULES})
write("questions.json", {"_about": "What a medallion pipeline's reviewers ask: the flow (MD1, MD2), what the design still lacks "
                                   "(MD3 to MD17, empty when complete), and the catalogue (MD18 to MD20).", "questions": QUESTIONS})
write("ontology.rationale.json", RATIONALE)
write("sample.graph.json", sample())
write("README.md", README)
print("wrote %s: %d rules, %d questions, %d sample nodes" % (OUT, len(RULES), len(QUESTIONS), len(sample()["nodes"])))


# ============================ the bridge: report-medallion ============================

BRIDGE_MANIFEST = {"name": "report-medallion", "release": 1, "domain": "reporting",
                   "summary": "Where a report meets its pipeline: a report's table is the gold dataset it reads, a column the dataset field "
                              "behind it, a report's quality check the pipeline rule it relies on.",
                   "extends": ["report", "medallion"], "namespace": "https://cynergis.ai/ont/report-medallion#",
                   "engine": ">=0.11.7", "carries": ["vocabulary", "rationale", "rules", "questions", "sample", "readme"],
                   "maintainer": "Cynergis",
                   "changelog": [{"release": 1, "at": "2026-10-13",
                                  "note": "The report link of DECISIONS.md: is_dataset, is_field, backed_by; a report reads gold, a column is "
                                          "a field of its table's dataset, a read dataset has a contract."}]}
BRIDGE_CONFIG = {"_about": "A bridge, extending report and medallion, for a report product with a medallion pipeline. Neither ontology "
                           "carries the other's vocabulary; a project that has both adds this one.",
                 "_summary": BRIDGE_MANIFEST["summary"], "name": "Report and medallion", "ontology_version": 1,
                 "strict_domains": False, "languages": ["en"], "classes": {}, "properties": design.BRIDGE_PROPERTIES, "attributes": {}}
BRIDGE_SAMPLE = {
    "_about": "The report ontology's sample table read as the medallion sample's gold holdings: two columns, two fields.",
    "nodes": [],
    "edges": [{"from": "table.warehouse.reports.fund_profile_balanced", "rel": "is_dataset", "to": "dataset.gold.portfolio_holdings"},
              {"from": "table.warehouse.reports.fund_profile_balanced.fund_id", "rel": "is_field", "to": "field.gold.portfolio_holdings.fund_id"},
              {"from": "table.warehouse.reports.fund_profile_balanced.holdings_top_pct", "rel": "is_field",
               "to": "field.gold.portfolio_holdings.holding_pct"}]}
BRIDGE_README = """# Report and medallion: the bridge

Extends `report` and `medallion`, so neither carries the other's vocabulary: a report without a
pipeline, or a pipeline without a report, never sees it. A report product with a medallion pipeline
adds it when the project starts (`--ontology product-report,ddd,medallion,report-medallion,flow`).

- `is_dataset`: a report's `Table` is the gold `Dataset` it reads; `is_field`: a `Column` is the
  `DatasetField` behind it. A report reads gold, and a column is a field of its own table's dataset
  (blocking); a dataset a report reads has a data contract (a warning).
- `backed_by`: a report's `QualityCheck` relies on the pipeline's `QualityRule`. Two levels, no
  overlap (DECISIONS.md): the data is checked at its gate; the report checks what it adds.

RM1 is the lineage of a report's value (column, gold field, the rule or the field that feeds it);
RM2 the checks a report relies on.
"""
os.makedirs(BRIDGE_OUT, exist_ok=True)
_out = OUT
OUT = BRIDGE_OUT
write("manifest.json", BRIDGE_MANIFEST)
write("ontology.config.json", BRIDGE_CONFIG)
write("rules.json", {"_about": "Where a report meets its pipeline, each rule naming the question it protects.", "rules": design.BRIDGE_RULES})
write("questions.json", {"_about": "The lineage of a report's value, and the checks it relies on.", "questions": design.BRIDGE_QUESTIONS})
write("ontology.rationale.json", {"_about": "Why each relation exists. `validated_by` is empty until confirmed.", "classes": {},
                                  "properties": {
                                      "is_dataset": {"question": design.BRIDGE_QUESTIONS["RM1"]["question"], "alternatives": "", "validated_by": "",
                                                     "why": "A report reads a table its pipeline builds; without the link its lineage stops at the report."},
                                      "is_field": {"question": design.BRIDGE_QUESTIONS["RM1"]["question"], "alternatives": "", "validated_by": "",
                                                   "why": "A report's value is traced to the gold field, and from there to the rule or the source behind it."},
                                      "backed_by": {"question": design.BRIDGE_QUESTIONS["RM2"]["question"], "alternatives": "", "validated_by": "",
                                                    "why": "Two levels, no overlap: a report check that relies on a pipeline rule says so, instead of checking the data again."}}})
write("sample.graph.json", BRIDGE_SAMPLE)
write("README.md", BRIDGE_README)
OUT = _out
print("wrote %s: %d relations, %d rules, %d questions" % (BRIDGE_OUT, len(design.BRIDGE_PROPERTIES), len(design.BRIDGE_RULES), len(design.BRIDGE_QUESTIONS)))
