# Report and medallion

The bridge between a report and the medallion pipeline that feeds it: a report's table is the gold dataset it reads, a column the field behind it, a report check backed by the pipeline rule it relies on.

An OTO pack in the reporting domain: the ontology `report-medallion` (release 1) under `ontology/`, the skill `start` that begins a project from it, and the views under `views/`. Install it in Claude Code from the registry's marketplace, or `oto pack add report-medallion` on a machine.

`oto pack check` validates it; `oto pack refresh` re-embeds the ontology when the registry holds a newer release; `oto pack publish --to <registry>` releases it.
