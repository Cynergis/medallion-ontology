"""The medallion unit: what the build writes, a clean self-check, and the rules of a declared medallion
flow, run end to end: the specification's worked flow captured through the gates is accepted, and each
deliberately broken variant is refused at `oto curate check` by the rule that names what is wrong.

Needs the engine (oto-kg, 0.11.7 or later) and the flow unit (release 2): FLOW_ONTOLOGY names the
folder holding flow's manifest, default ../report-ontology/oto/flow."""
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
UNIT = os.path.join(ROOT, "ontology", "medallion")
FLOW = os.environ.get("FLOW_ONTOLOGY") or os.path.join(os.path.dirname(ROOT), "report-ontology", "oto", "flow")

pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(FLOW, "manifest.json")),
                                reason="the flow unit is needed: set FLOW_ONTOLOGY or check out report-ontology beside this repository")


@pytest.fixture(scope="module")
def home():
    """A machine with the medallion and flow units, and nothing else of the person's."""
    with tempfile.TemporaryDirectory() as root:
        onto = os.path.join(root, "ontologies")
        shutil.copytree(UNIT, os.path.join(onto, "medallion"))
        shutil.copytree(FLOW, os.path.join(onto, "flow"))
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


def test_the_committed_unit_is_what_the_build_writes(tmp_path):
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py"), str(tmp_path)], check=True, capture_output=True)
    for name in sorted(os.listdir(UNIT)):
        assert open(os.path.join(UNIT, name), encoding="utf-8").read() == open(os.path.join(tmp_path, name), encoding="utf-8").read(), \
            "%s differs from what tools/build.py writes: run it and commit the result" % name


def test_the_unit_composes_and_its_sample_answers_every_question(home):
    from oto.model import ontologies
    assert ontologies.self_check("medallion") == []


def capture_from_sample():
    """The ontology's sample as a capture: one item per node, its links by local id."""
    graph = json.load(open(os.path.join(UNIT, "sample.graph.json"), encoding="utf-8"))
    local = {n["id"]: n["id"].split(".", 1)[1] for n in graph["nodes"]}
    items = {}
    for n in graph["nodes"]:
        items[local[n["id"]]] = {"type": n["type"], "id": local[n["id"]], "label": n["label"], "fields": dict(n["attributes"]),
                                 "links": {}, "where": "7", "quote": n["label"]}
    for e in graph["edges"]:
        items[local[e["from"]]]["links"].setdefault(e["rel"], []).append(local[e["to"]])
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



def item(cap, iid):
    return next(i for i in cap["items"] if i["id"] == iid)



def mutate(name, cap):
    c = copy.deepcopy(cap)
    if name == "fp-07 forgets it waits for fp-06 (it reads silver.fund)":
        item(c, "fp-07")["links"]["waitsFor"] = ["fp-05"]
    elif name == "fp-04 reads what fp-03 writes, in the same parallel group":
        item(c, "fp-04")["links"]["reads"].append("bronze-fund-holding")
    elif name == "the output is built after gate 1, not gate 2":
        item(c, "fp-09")["links"]["waitsFor"] = ["fp-05"]
    elif name == "an entity step also writes a gold table":
        item(c, "fp-06")["links"]["writes"].append("gold-portfolio-holdings")
    elif name == "a second create_batch step":
        c["items"].append({"type": "DeterministicStep", "id": "fp-00", "label": "fp-00", "where": "7", "quote": "fp-00",
                           "fields": {"stepId": "fp-00", "stepKind": "create_batch", "command": "<binding> create-batch"}, "links": {}})
        item(c, "fund-profile")["links"]["hasStep"].append("fp-00")
    elif name == "a step kind outside the vocabulary":
        item(c, "fp-06")["fields"]["stepKind"] = "transform"
    elif name == "the batch opens after it is validated (a cycle)":
        item(c, "fp-01")["links"]["waitsFor"] = ["fp-11"]
    elif name == "no mark_validated step":
        c["items"] = [i for i in c["items"] if i["id"] != "fp-11"]
        item(c, "fund-profile")["links"]["hasStep"].remove("fp-11")
        for i in c["items"]:
            for rel in list(i["links"]):
                i["links"][rel] = [x for x in i["links"][rel] if x != "fp-11"]
    elif name == "an output reads another output":
        item(c, "fp-09")["links"]["reads"].append("gold-portfolio-holdings")
    elif name == "gate 2 does not say which gate it runs":
        del item(c, "fp-08")["fields"]["gate"]
    return c



SCENARIOS = {
    "the specification's flow, as declared": [],
    "the same, beside a template-build flow of another kind": [],
    "fp-07 forgets it waits for fp-06 (it reads silver.fund)": ["step-waits-for-the-writer-of-what-it-reads"],
    "fp-04 reads what fp-03 writes, in the same parallel group": ["parallel-steps-share-no-artifact"],
    "the output is built after gate 1, not gate 2": ["medallion-output-after-gate-2"],
    "an entity step also writes a gold table": ["medallion-entity-writes-silver"],
    "a second create_batch step": ["medallion-flow-has-one-create-batch"],
    "a step kind outside the vocabulary": ["medallion-step-kind-is-known"],
    "the batch opens after it is validated (a cycle)": ["no-step-waits-for-itself"],
    "no mark_validated step": ["medallion-flow-has-mark-validated"],
    "an output reads another output": ["medallion-output-reads-no-other-output"],
    "gate 2 does not say which gate it runs": ["medallion-gate-has-a-number"],
}


@pytest.fixture(scope="module")
def project(home):
    root = os.path.join(home, "project")
    code, out = run("init", "--name", "Medallion check", "--slug", "mcheck", "--ontology", "medallion", "--empty", "--project", root)
    assert code == 0, out
    os.makedirs(os.path.join(root, "captures"), exist_ok=True)
    return root


@pytest.mark.parametrize("name", list(SCENARIOS))
def test_a_declared_flow_is_accepted_or_refused_by_the_rule_that_names_what_is_wrong(project, name):
    expected = SCENARIOS[name]
    cap = mutate(name, capture_from_sample())
    if "template-build" in name:
        cap["items"] += template_build_flow()
    path = os.path.join(project, "captures", "flow.json")
    json.dump(cap, open(path, "w", encoding="utf-8"), indent=1)
    run("curate", "abort", "--project", project)
    assert run("curate", "start", "--project", project)[0] == 0
    code, out = run("curate", "propose", "--project", project, "--from", path)
    assert code == 0, out
    code, out = run("curate", "add", "--project", project, "--from", os.path.join(project, "proposals", "medallion-pipeline-ontology.json"))
    assert code == 0, out
    code, out = run("curate", "check", "--project", project, "--show", "200")
    run("curate", "abort", "--project", project)
    rules = {r["id"] for r in json.load(open(os.path.join(project, "rules.json"), encoding="utf-8"))["rules"]}
    fired = {rid for rid in rules if rid in out}
    refused = "blocking problem" in out
    assert refused == bool(expected), out
    assert set(expected) <= fired, "expected %s, fired %s" % (expected, sorted(fired))
