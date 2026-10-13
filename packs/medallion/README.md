# Medallion pipeline

Design a medallion data pipeline for a part of a product, source systems to bronze, silver and gold, checkpoint by checkpoint (D1-D9), and the batch flow that runs it, checked by the medallion rules at every capture.

An OTO pack in the data domain: the ontology `medallion` (release 2) under `ontology/`, the skill `start` that begins a project from it, and the views under `views/`. Install it in Claude Code from the registry's marketplace, or `oto pack add medallion` on a machine.

`oto pack check` validates it; `oto pack refresh` re-embeds the ontology when the registry holds a newer release; `oto pack publish --to <registry>` releases it.
