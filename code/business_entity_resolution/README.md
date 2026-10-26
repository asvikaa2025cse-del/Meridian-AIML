# Business Entity Resolution MVP

This is a data-only entity matcher for the challenge. It reads the supplied TSV files, trains a compact ExtraTrees classifier from the training ground truth, predicts Source 2/3 links for every Source 1 test record, and writes the two required outputs.

## Files and run

Expected submission-root layout:

```text
dataset/train/train_source{1,2,3}.tsv
dataset/train/train_ground_truth.tsv
dataset/test/test_source{1,2,3}.tsv
utils/validate_submission.py   # optional official validator
code/business_entity_resolution/src/pipeline.py
output/
```

From the submission root, install the pinned dependency and run:

```sh
python3 -m pip install -r code/business_entity_resolution/requirements.txt
python3 code/business_entity_resolution/src/pipeline.py
```

Optional arguments: `--root PATH` selects a different submission root, and `--threshold 0.75` overrides the conservative match threshold. The pipeline invokes `utils/validate_submission.py` with the challenge-specified arguments if the script is present. It reports a clear missing-file error otherwise. No business data is downloaded or queried.

Outputs are UTF-8 TSVs with one row per test Source 1 record:

* `output/matching_results.tsv`: `source1_entity_id`, `matched_entity_ids`
* `output/candidate_pairs.tsv`: `source1_entity_id`, `candidate_entity_ids`

The output columns use the exact header names and blank singleton representation specified by the challenge.

## Notes

The default probability threshold is precision-oriented because the leaderboard uses macro F0.5. A grouped holdout report is printed during training when scikit-learn is available. The pipeline uses the trained ExtraTrees model when installed; if it is missing, a standard-library heuristic fallback permits offline smoke runs and is clearly reported. Install scikit-learn from a trusted package source for the intended trained model. Neither path uses downloaded pretrained models or external business data.
