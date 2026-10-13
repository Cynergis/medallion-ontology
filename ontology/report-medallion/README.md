# Report and medallion: the bridge

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
