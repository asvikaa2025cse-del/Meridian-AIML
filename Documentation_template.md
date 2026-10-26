# Methodology: Business Entity Resolution MVP

## Methodology used

The pipeline uses only the supplied training and test TSVs. It does not use external business directories, APIs, geocoding, or identity lookup. Source 1 is treated as the reference side; records in Sources 2 and 3 are combined into the candidate pool. Source is retained through each record's original prefixed `entity_id`.

## Candidate generation / blocking

Text is Unicode-normalized, lowercased, converted to ASCII where possible, and tokenized to alphanumeric tokens. Business-name blocking removes common legal suffixes (for example, Ltd, Pvt, Corp, Inc, and LLC). A candidate is retained when it shares a normalized name token, shares an address token, has a matching four-character name prefix, or has the same country and matching first name character. When no block fires, a bounded fallback selects up to 80 records ranked by the better of name or address sequence similarity. The candidate file records exactly the final pool scored at inference.

## Features

For each Source 1/candidate pair, the model receives Jaccard overlap, overlap relative to the smaller token set, and sequence similarity for normalized names and addresses; country equality; exact normalized name/address flags; and a first-character name agreement flag. Empty fields yield zero similarity. Country is compared as an open string label and is never restricted to the training countries.

## Model architecture

An ExtraTreesClassifier from scikit-learn is trained on candidate pairs labeled from `train_ground_truth.tsv`. The model is a lightweight conventional ML estimator, not a pretrained language model. Positive ground-truth pairs are included even when blocking missed them, while the same candidate-generation process supplies negative pairs. Training uses 300 randomized trees, minimum leaf size 2, balanced class weights, fixed random seed, and all available labeled Source 1 rows. The default prediction threshold is 0.75 and can be overridden from the command line.

## Validation

The script makes a deterministic grouped holdout split by Source 1 identifier to avoid putting pair rows for an entity in both partitions. It reports candidate-pair F0.5 and the best threshold among a small fixed set. This diagnostic is not the official per-entity macro score and must not be interpreted as one. If the supplied official validator is present at `utils/validate_submission.py`, it is run against both outputs and the test directory.

## Constraints and reproducibility

The only runtime dependency is `scikit-learn==1.5.2`; Python's standard library handles TSV I/O, Unicode normalization, tokenization, and string similarity. The model family is a locally trained lightweight ML matcher, subject to the challenge's MIT/Apache-2.0-compatible model requirement. The pipeline uses no external business lookup or augmentation. Run from the submission root with the commands in `code/business_entity_resolution/README.md`.

## Known limitations

This baseline's blocking can miss transliterations, DBA names, and severe typos. Character-level similarity and more careful validation threshold selection could improve it, but this same-day implementation favors an understandable reproducible baseline. Dataset-specific output files cannot be generated until all required TSVs are supplied.
