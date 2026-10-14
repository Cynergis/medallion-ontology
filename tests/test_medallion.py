"""The medallion units, end to end.

- The committed units are what tools/build.py writes; both compose, and their samples answer every
  question they must.
- The specification's worked instance (design and flow), captured through the gates, is accepted;
  each deliberately broken variant is refused by the blocking rule that names what is wrong, flagged by
  a warning, or reported as a gap (a completeness question that must come back empty), as decided:
  correctness refuses, completeness reports.

Needs the engine (oto-kg, 0.11.7 or later), the flow unit (release 2): FLOW_ONTOLOGY, default
../report-ontology/oto/flow; and for the bridge, the report ontology (release 5): REPORT_ONTOLOGY,
default ../report-ontology/oto/report, else ~/.oto/ontologies/report. The bridge's tests are skipped when it is absent."""
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNITS = os.path.join(ROOT, "ontology")
UNIT = os.path.join(UNITS, "medallion")
FLOW = os.environ.get("FLOW_ONTOLOGY") or os.path.join(os.path.dirname(ROOT), "report-ontology", "oto", "flow")
REPORT = os.environ.get("REPORT_ONTOLOGY") or next(
    (p for p in (os.path.join(os.path.dirname(ROOT), "report-ontology", "oto", "report"), os.path.expanduser("~/.oto/ontologies/report"))
     if os.path.exists(os.path.join(p, "manifest.json"))), "")


def _release(path):
    try:
        return json.load(open(os.path.join(path, "manifest.json"), encoding="utf-8")).get("release", 0)
    except OSError:
        return 0


HAVE_FLOW = _release(FLOW) >= 2
HAVE_REPORT = _release(REPORT) >= 5
pytestmark = pytest.mark.skipif(not HAVE_FLOW, reason="the flow unit (release 2) is needed: set FLOW_ONTOLOGY")
needs_report = pytest.mark.skipif(not HAVE_REPORT, reason="the report ontology (release 5) is needed for the bridge: set REPORT_ONTOLOGY")


@pytest.fixture(scope="module")
def home():
    """A machine with these units, flow, and report when present, and nothing else of the person's."""
    with tempfile.TemporaryDirectory() as root:
        onto = os.path.join(root, "ontologies")
        for name in ("medallion", "report-medallion"):
            shutil.copytree(os.path.join(UNITS, name), os.path.join(onto, name))
        shutil.copytree(FLOW, os.path.join(onto, "flow"))
        if HAVE_REPORT:
            shutil.copytree(REPORT, os.path.join(onto, "report"))
        saved = {k: os.environ.get(k) for k in ("OTO_ONTOLOGIES", "OTO_PACKS", "OTO_REGISTRIES")}
        os.environ.update(OTO_ONTOLOGIES=onto, OTO_PACKS=os.path.join(root, "packs"), OTO_REGISTRIES=os.path.join(root, "registries.json"))
        yield root
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run(*args):
    from oto.cli import main
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(out):
        code = main(list(args))
    return code, out.getvalue()


# ---- the units ----

def test_the_committed_units_are_what_the_build_writes(tmp_path):
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py"), str(tmp_path)], check=True, capture_output=True)
    for unit in ("medallion", "report-medallion"):
        for name in sorted(os.listdir(os.path.join(UNITS, unit))):
            assert open(os.path.join(UNITS, unit, name), encoding="utf-8").read() == \
                open(os.path.join(tmp_path, unit, name), encoding="utf-8").read(), \
                "%s/%s differs from what tools/build.py writes: run it and commit the result" % (unit, name)


def test_medallion_composes_and_its_sample_answers_every_question(home):
    from oto.model import ontologies
    assert ontologies.self_check("medallion") == []


@needs_report
def test_the_bridge_composes_and_its_sample_answers_every_question(home):
    from oto.model import ontologies
    assert ontologies.self_check("report-medallion") == []


# ---- the sample as a capture, and its variants ----

def L(node_id):
    """A sample node's id as a capture item id: unique, since two kinds share short names (fund-holding)."""
    return node_id.replace(".", "-", 1)


def capture_from_sample():
    graph = json.load(open(os.path.join(UNIT, "sample.graph.json"), encoding="utf-8"))
    items = {}
    for n in graph["nodes"]:
        items[n["id"]] = {"type": n["type"], "id": L(n["id"]), "label": n["label"], "fields": dict(n["attributes"]),
                          "links": {}, "where": "7", "quote": n["label"]}
    for e in graph["edges"]:
        items[e["from"]]["links"].setdefault(e["rel"], []).append(L(e["to"]))
    return {"doc": "medallion-pipeline-ontology", "as_of": "2026-10-13", "scope": "fund-profile", "items": list(items.values())}


def template_build_flow():
    """A second flow in the same project, of another kind, whose steps declare no medallion kind."""
    return [
        {"type": "Flow", "id": "template-build", "label": "Template build", "fields": {"flowKind": "template-build"},
         "links": {"hasStep": ["tb-inspect", "tb-render"]}, "where": "x", "quote": "x"},
        {"type": "DeterministicStep", "id": "tb-inspect", "label": "inspect the sample PDF",
         "fields": {"stepId": "tb-inspect", "command": "inspect_pdf.py"}, "links": {"writes": ["tb-report"]}, "where": "x", "quote": "x"},
        {"type": "DeterministicStep", "id": "tb-render", "label": "render the template",
         "fields": {"stepId": "tb-render", "command": "render.py"}, "links": {"reads": ["tb-report"], "waitsFor": ["tb-inspect"]}, "where": "x", "quote": "x"},
        {"type": "Artifact", "id": "tb-report", "label": "work/report.json", "fields": {"path": "work/report.json", "format": "json"},
         "links": {}, "where": "x", "quote": "x"},
    ]


def item(cap, node_id):
    return next(i for i in cap["items"] if i["id"] == L(node_id))


def link(cap, node_id, rel, *targets):
    item(cap, node_id)["links"].setdefault(rel, []).extend(L(t) for t in targets)


def unlink(cap, node_id, rel, target):
    item(cap, node_id)["links"][rel].remove(L(target))


def add(cap, node_id, kind, label, **fields):
    cap["items"].append({"type": kind, "id": L(node_id), "label": label, "fields": fields, "links": {}, "where": "7", "quote": label})


def drop(cap, node_id):
    cap["items"] = [i for i in cap["items"] if i["id"] != L(node_id)]
    for i in cap["items"]:
        for rel in list(i["links"]):
            i["links"][rel] = [x for x in i["links"][rel] if x != L(node_id)]


def mutate(name, cap):
    c = copy.deepcopy(cap)
    step = lambda s: "step." + s  # noqa: E731
    # the flow (release 1)
    if name == "fp-07 forgets it waits for fp-06 (it reads silver.fund)":
        item(c, step("fp-07"))["links"]["waitsFor"] = [L(step("fp-05"))]
    elif name == "fp-04 reads what fp-03 writes, in the same parallel group":
        link(c, step("fp-04"), "reads", "artifact.bronze-fund-holding")
    elif name == "the output is built after gate 1, not gate 2":
        item(c, step("fp-09"))["links"]["waitsFor"] = [L(step("fp-05"))]
    elif name == "an entity step also writes a gold table":
        link(c, step("fp-06"), "writes", "artifact.gold-portfolio-holdings")
    elif name == "a second create_batch step":
        add(c, step("fp-00"), "DeterministicStep", "fp-00", stepId="fp-00", stepKind="create_batch", command="<binding> create-batch")
        link(c, "flow.fund-profile", "hasStep", step("fp-00"))
    elif name == "a step kind outside the vocabulary":
        item(c, step("fp-06"))["fields"]["stepKind"] = "transform"
    elif name == "the batch opens after it is validated (a cycle)":
        item(c, step("fp-01"))["links"]["waitsFor"] = [L(step("fp-11"))]
    elif name == "no mark_validated step":
        drop(c, step("fp-11"))
    elif name == "an output reads another output":
        link(c, step("fp-09"), "reads", "artifact.gold-portfolio-allocations")
    elif name == "gate 2 does not say which gate it runs":
        del item(c, step("fp-08"))["fields"]["gate"]
    # the design (release 2)
    elif name == "a field both derived and fed":
        link(c, "field.gold.portfolio_holdings.holding_rank", "fed_by", "field.silver.fund_holding.holding_pct")
    elif name == "a rule reads gold to derive a silver field":
        add(c, "field.silver.fund.top_holding", "DatasetField", "silver.fund.top_holding", data_type="varchar")
        link(c, "dataset.silver.fund", "has_field", "field.silver.fund.top_holding")
        link(c, "field.silver.fund.top_holding", "derived_by", "derivationrule.holdings-top-10")
        link(c, "derivationrule.holdings-top-10", "rule_input", "field.gold.portfolio_allocations.allocation_pct")
    elif name == "a copy step executes an entity":
        link(c, step("fp-03"), "executes", "conformedentity.fund")
    elif name == "two steps execute one output":
        link(c, step("fp-09b"), "executes", "output.portfolio-holdings")
    elif name == "an artifact in another layer than its dataset":
        item(c, "artifact.bronze-fund-holding")["links"]["represents"] = [L("dataset.silver.fund")]
    elif name == "an entity step writes another entity's table":
        item(c, step("fp-07"))["links"]["executes"] = [L("conformedentity.fund")]
    elif name == "a person may write gold":
        item(c, "identity.analyst")["fields"]["access"] = ["gold: write"]
    elif name == "a rule does not say what happens on a tie":
        drop(c, "edgecase.holdings-top-10.tie")
    elif name == "an output no step executes":
        unlink(c, step("fp-09b"), "executes", "output.portfolio-allocations")
    elif name == "an entity fed by a source it has no identity mapping for":
        unlink(c, "conformedentity.fund", "has_identity_mapping", "identitymapping.fund.dim-product")
    # the build plan's tests (release 3)
    elif name == "the rule has no unit test":
        drop(c, "pipelinetest.holdings-top-10-unit")
    elif name == "an output no parity test compares":
        drop(c, "pipelinetest.portfolio-allocations-parity")
    elif name == "the flow has no flow test":
        drop(c, "pipelinetest.fund-profile-flow")
    elif name == "the runbook's recovery is never tried":
        drop(c, "pipelinetest.hard-gate-failure-forced")
    elif name == "a test does not say what it runs on":
        del item(c, "pipelinetest.fund-profile-rerun")["fields"]["fixture"]
    elif name == "a parity test of a derivation rule":
        link(c, "pipelinetest.portfolio-holdings-parity", "test_of", "derivationrule.holdings-top-10")
    elif name == "the flow test tests an output instead":
        item(c, "pipelinetest.fund-profile-flow")["links"]["test_of"] = [L("output.portfolio-holdings")]
    return c


#: scenario -> (rules that must fire, refused at check, completeness questions that must report a gap)
SCENARIOS = {
    "the specification's flow, as declared": ([], False, []),
    "the same, beside a template-build flow of another kind": ([], False, []),
    "fp-07 forgets it waits for fp-06 (it reads silver.fund)": (["step-waits-for-the-writer-of-what-it-reads"], True, []),
    "fp-04 reads what fp-03 writes, in the same parallel group": (["parallel-steps-share-no-artifact"], True, []),
    "the output is built after gate 1, not gate 2": (["medallion-output-after-gate-2"], True, []),
    "an entity step also writes a gold table": (["medallion-entity-writes-silver"], True, []),
    "a second create_batch step": (["medallion-flow-has-one-create-batch"], True, []),
    "a step kind outside the vocabulary": (["medallion-step-kind-is-known"], True, []),
    "the batch opens after it is validated (a cycle)": (["no-step-waits-for-itself"], True, []),
    "no mark_validated step": (["medallion-flow-has-mark-validated"], True, []),
    "an output reads another output": (["medallion-output-reads-no-other-output"], True, []),
    "gate 2 does not say which gate it runs": (["medallion-gate-has-a-number"], True, []),
    "a field both derived and fed": (["field-is-derived-or-fed-not-both"], True, []),
    "a rule reads gold to derive a silver field": (["rule-reads-no-higher-layer-gold"], True, []),
    "a copy step executes an entity": (["a-copy-to-bronze-step-executes-what-it-builds"], True, []),
    "two steps execute one output": (["one-step-executes-each-design-object"], True, []),
    "an artifact in another layer than its dataset": (["artifact-layer-is-its-dataset-layer"], True, []),
    "an entity step writes another entity's table": (["an-entity-step-writes-its-entity"], True, ["MD16"]),
    "a person may write gold": (["no-human-writes-gold"], True, []),
    "a rule does not say what happens on a tie": (["rule-answers-tie"], False, []),
    "an output no step executes": ([], False, ["MD16"]),
    "an entity fed by a source it has no identity mapping for": ([], False, ["MD7"]),
    "the rule has no unit test": ([], False, ["MD30"]),
    "an output no parity test compares": ([], False, ["MD31"]),
    "the flow has no flow test": ([], False, ["MD32"]),
    "the runbook's recovery is never tried": ([], False, ["MD33"]),
    "a test does not say what it runs on": ([], False, ["MD34"]),
    "a parity test of a derivation rule": (["a-parity-test-tests-an-output"], True, []),
    "the flow test tests an output instead": (["a-flow-test-tests-a-flow"], True, ["MD32"]),
}


@pytest.fixture(scope="module")
def project(home):
    root = os.path.join(home, "project")
    code, out = run("init", "--name", "Medallion check", "--slug", "mcheck", "--ontology", "medallion", "--empty", "--project", root)
    assert code == 0, out
    os.makedirs(os.path.join(root, "captures"), exist_ok=True)
    return root


def check(project, cap):
    path = os.path.join(project, "captures", "capture.json")
    json.dump(cap, open(path, "w", encoding="utf-8"), indent=1)
    run("curate", "abort", "--project", project)
    assert run("curate", "start", "--project", project)[0] == 0
    code, out = run("curate", "propose", "--project", project, "--from", path)
    assert code == 0, out
    code, out = run("curate", "add", "--project", project, "--from", os.path.join(project, "proposals", cap["doc"] + ".json"))
    assert code == 0, out
    code, out = run("curate", "check", "--project", project, "--show", "500")
    run("curate", "abort", "--project", project)
    return out


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_a_design_and_its_flow_are_accepted_refused_flagged_or_reported(project, name):
    rules, refused, gaps = SCENARIOS[name]
    cap = mutate(name, capture_from_sample())
    if "template-build" in name:
        cap["items"] += template_build_flow()
    out = check(project, cap)
    known = {r["id"] for r in json.load(open(os.path.join(project, "rules.json"), encoding="utf-8"))["rules"]}
    fired = {rid for rid in known if rid in out}
    assert ("blocking problem" in out) == refused, out
    assert set(rules) <= fired, "expected %s, fired %s" % (rules, sorted(fired))
    for qid in gaps:   # an empty-gate question that finds rows is violated; a non-empty one with none, unanswered
        assert "question %s violated" % qid in out or "question %s unanswered" % qid in out, "expected a gap on %s:\n%s" % (qid, out)
    if not rules and not refused:
        assert not fired, "unexpected findings: %s" % sorted(fired)


def test_a_test_that_says_nothing_it_expects_is_not_captured(project):
    """A test is its expected result: one without it is refused when the capture is proposed, before any check."""
    cap = capture_from_sample()
    del item(cap, "pipelinetest.fund-profile-flow")["fields"]["expected_result"]
    path = os.path.join(project, "captures", "capture.json")
    json.dump(cap, open(path, "w", encoding="utf-8"), indent=1)
    run("curate", "abort", "--project", project)
    assert run("curate", "start", "--project", project)[0] == 0
    code, out = run("curate", "propose", "--project", project, "--from", path)
    run("curate", "abort", "--project", project)
    assert code != 0 and "expected_result is required and missing" in out, out


def test_the_sample_closes_the_build_plan():
    """D9 can close on the sample: every rule, output, medallion flow and runbook that resumes it has its test."""
    graph = json.load(open(os.path.join(UNIT, "sample.graph.json"), encoding="utf-8"))
    kinds = {n["id"]: n["type"] for n in graph["nodes"]}
    tests = {n["id"]: n["attributes"]["test_kind"] for n in graph["nodes"] if n["type"] == "PipelineTest"}
    tested = {(tests[e["from"]], e["to"]) for e in graph["edges"] if e["rel"] == "test_of"}
    resumes = {e["from"] for e in graph["edges"] if e["rel"] == "resumes_from"}
    for nid, kind in kinds.items():
        need = {"DerivationRule": "unit", "Output": "parity", "Flow": "flow"}.get(kind) or ("forced_failure" if nid in resumes else None)
        if need:
            assert (need, nid) in tested, "%s has no %s test" % (nid, need)
    assert set(tests.values()) >= {"unit", "contract", "parity", "rerun", "flow", "forced_failure"}


# ---- the bridge ----

@needs_report
def test_a_report_reads_a_gold_field_and_its_lineage_answers(home):
    root = os.path.join(home, "bridge")
    code, out = run("init", "--name", "Report with pipeline", "--slug", "rwp", "--ontology", "report-medallion", "--project", root)
    assert code == 0, out
    assert run("build", "--project", root)[0] == 0
    code, out = run("query", "--project", root, "ask", "RM1")
    assert code == 0 and "answered" in out and "gold.portfolio_holdings" in out and "holding_pct" in out, out
    # a report's table that is a silver dataset is refused
    graph = json.load(open(os.path.join(root, "graph.json"), encoding="utf-8"))
    for e in graph["edges"]:
        if e["rel"] == "is_dataset":
            e["to"] = "dataset.silver.fund"
    assert run("curate", "start", "--project", root, "--force")[0] == 0
    candidate = os.path.join(root, "graph.candidate.json")
    json.dump(graph, open(candidate, "w", encoding="utf-8"))
    code, out = run("curate", "check", "--project", root, "--show", "200")
    run("curate", "abort", "--project", root)
    assert "a-report-reads-gold" in out and "blocking problem" in out, out
