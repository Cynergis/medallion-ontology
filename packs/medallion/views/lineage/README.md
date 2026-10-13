# Lineage, a view of the pipeline's knowledge base

Where each value of a medallion pipeline comes from: pick a gold or silver field, and the page
walks upstream through the rule that derives it or the field that feeds it, to the source column
and the table and system it is copied from. Each step of the chain names the flow step that builds
it and the quality rules that guard it, by gate and severity. A field with no lineage, a rule with
no worked example and a column with no business term are shown as gaps (MD9, MD11, MD5).

When the project also composes the `report-medallion` bridge, the report fields that show a value
are drawn on top, and a quality rule says which report checks rely on it. Without the bridge that
part is empty (`$optional`), and the page works the same.

It is an OTO **view**: `app.json` declares the one data file it reads, `data.js`, filled from the
graph by `projections/lineage.json`. Nobody edits `data.js`; the engine writes it on every build.

```bash
oto serve --project <root> --view lineage                  # live, from the store
oto build --project <root> --target site --view lineage    # static: build/site/
```
