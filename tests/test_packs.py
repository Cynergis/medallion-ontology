"""The packs: `medallion` (the pipeline, the design-pipeline skill, the lineage view) and
`report-medallion` (the bridge). Each embeds what it extends, so these tests need only the engine
(oto-kg 0.11.8 or later); they never read the machine's own ontologies or packs."""
import filecmp
import io
import json
import os
from contextlib import redirect_stdout, redirect_stderr

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS = os.path.join(ROOT, "packs")
UNITS = os.path.join(ROOT, "ontology")
LINEAGE = os.path.join(PACKS, "medallion", "views", "lineage")


@pytest.fixture(autouse=True)
def bare_machine(tmp_path, monkeypatch):
    monkeypatch.setenv("OTO_ONTOLOGIES", str(tmp_path / "no-ontologies"))
    monkeypatch.setenv("OTO_PACKS", str(tmp_path / "no-packs"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "no-claude"))


def _oto(*args):
    from oto.cli import main
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(out):
        code = main(list(args))
    assert code in (0, None), out.getvalue()
    return out.getvalue()


PROVENANCE = ("source", "path", "ref", "commit", "registry", "fetched_at", "_about")


def _manifest(path):
    manifest = json.load(open(os.path.join(path, "manifest.json"), encoding="utf-8"))
    return {k: v for k, v in manifest.items() if k not in PROVENANCE}


def _same_tree(a, b):
    """The same files, a manifest compared without the provenance that fetching it records."""
    if os.path.exists(os.path.join(a, "manifest.json")) and _manifest(a) != _manifest(b):
        return False
    cmp = filecmp.dircmp(a, b, ignore=[".DS_Store", "__pycache__", "manifest.json"])
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    if filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)[1:] != ([], []):
        return False
    return all(_same_tree(os.path.join(a, d), os.path.join(b, d)) for d in cmp.common_dirs)


@pytest.mark.parametrize("pack", ["medallion", "report-medallion"])
def test_the_pack_checks_clean(pack):
    from oto.model import packs
    assert packs.check(os.path.join(PACKS, pack)) == []


@pytest.mark.parametrize("pack", ["medallion", "report-medallion"])
def test_the_pack_embeds_the_committed_units(pack):
    """A change to a unit is released by refreshing the packs (`oto pack refresh packs/<name>`)."""
    embedded = os.path.join(PACKS, pack, "ontology")
    for unit in ("medallion", "report-medallion"):
        if os.path.isdir(os.path.join(embedded, unit)):
            assert _same_tree(os.path.join(UNITS, unit), os.path.join(embedded, unit)), \
                "packs/%s embeds an outdated %s: oto pack refresh packs/%s" % (pack, unit, pack)


def _lineage(tmp_path, pack, view):
    root = str(tmp_path / pack)
    _oto("init", "--name", "Lineage", "--slug", "lineage", "--pack", os.path.join(PACKS, pack), "--project", root)
    _oto("build", "--project", root, "--target", "site", "--view", view)
    text = open(os.path.join(root, "build", "site", "data.js"), encoding="utf-8").read()
    data = json.loads(text[text.index("=") + 1:].strip().rstrip(";"))
    return {kind: {x["id"]: x for x in data[kind]} for kind in ("fields", "rules", "columns", "tables", "quality", "outputs")}


def test_the_lineage_view_walks_a_gold_field_up_to_its_source(tmp_path):
    data = _lineage(tmp_path, "medallion", "lineage")
    rank = data["fields"]["field.gold.portfolio_holdings.holding_rank"]
    rule = data["rules"][rank["derived_by"]]
    assert rule["kind"] == "ranking" and rule["built_by"]["kind"] == "build_output"
    assert {c["case"] for c in rule["edge_cases"]} >= {"tie", "null_input"}
    assert "field.silver.fund_holding.holding_pct" in rule["inputs"]
    silver = data["fields"]["field.silver.fund_holding.holding_pct"]
    column = data["columns"][silver["fed_by"][0]]
    assert data["tables"][column["table"]]["copy"]["built_by"]["kind"] == "copy_to_bronze"
    assert rank["report"] == [], "without the bridge the report part is empty"
    assert {q["gate"] for q in data["quality"].values()} == {1, 2, 3}
    assert {t["kind"] for t in rule["tests"]} == {"unit"}, "the rule says how the build plan proves it"
    assert {t["kind"] for t in data["outputs"]["output.portfolio-holdings"]["tests"]} == {"contract", "parity"}


def test_with_the_bridge_the_lineage_view_shows_the_report_field_on_top(tmp_path):
    data = _lineage(tmp_path, "report-medallion", LINEAGE)
    pct = data["fields"]["field.gold.portfolio_holdings.holding_pct"]
    shown = [s for r in pct["report"] for s in r["shown_as"]]
    assert shown and all(s["report"] for s in shown)
    assert all(s["id"].startswith("report.") for s in shown), "a report field carries its id, so it links to the report's page"


def test_the_lineage_view_is_the_studios_page_of_where_the_data_comes_from():
    app = json.load(open(os.path.join(LINEAGE, "app.json"), encoding="utf-8"))
    assert app["place"] == "data" and app["title"] == "Where the data comes from" and "DatasetField" in app["shows"] and app["open"] == ["MD"]
    page = open(os.path.join(LINEAGE, "index.html"), encoding="utf-8").read()
    assert "../_studio/studio.js" in page and 'id="studio-open"' in page
    for gone in ("(MD9)", "(MD11)", "(MD5)", "(D4, D5)", "rule_id", "<code>"):
        assert gone not in page, gone


@pytest.mark.parametrize("pack", ["medallion", "report-medallion"])
def test_every_pack_skill_talks_in_plain_language(pack):
    """Technical details are the record's: no skill talks in codes, ids or engine output, none offers them."""
    import glob
    for skill in sorted(glob.glob(os.path.join(PACKS, pack, "skills", "*", "SKILL.md"))):
        text = open(skill, encoding="utf-8").read()
        assert text.count("## Talking with the person") == 1 and "Never offer them" in text, skill
        assert "engine's words" not in text and "N of M" not in text, skill
