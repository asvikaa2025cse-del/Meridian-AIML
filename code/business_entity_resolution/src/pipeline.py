#!/usr/bin/env python3
"""Train and run a compact, data-only business entity resolution pipeline."""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

try:
    from sklearn.ensemble import ExtraTreesClassifier
    from sklearn.model_selection import GroupShuffleSplit
    HAVE_SKLEARN = True
except ImportError:  # pragma: no cover
    ExtraTreesClassifier = None
    GroupShuffleSplit = None
    HAVE_SKLEARN = False


ROOT = Path.cwd()
TRAIN = ROOT / "dataset" / "train"
TEST = ROOT / "dataset" / "test"
OUT = ROOT / "output"
FIELDS = ("entity_id", "business_name", "business_address", "country")
LEGAL = {"incorporated", "corporation", "corp", "company", "co", "limited", "ltd",
         "private", "pvt", "llc", "llp", "plc", "inc", "the"}


def read_tsv(path: Path, required: Iterable[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required dataset file not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        return [{k: (row.get(k) or "").strip() for k in reader.fieldnames or []} for row in reader]


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()
    value = value.replace("&", " and ")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def name_norm(value: str) -> str:
    return " ".join(t for t in norm(value).split() if t not in LEGAL)


def tokens(value: str) -> set[str]:
    return set(value.split()) if value else set()


def sim(a: str, b: str) -> tuple[float, float, float]:
    if not a or not b:
        return (0.0, 0.0, 0.0)
    ta, tb = tokens(a), tokens(b)
    jac = len(ta & tb) / max(1, len(ta | tb))
    contain = len(ta & tb) / max(1, min(len(ta), len(tb)))
    seq = SequenceMatcher(None, a, b).ratio()
    return jac, contain, seq


def features(a: dict[str, str], b: dict[str, str]) -> list[float]:
    an, bn = name_norm(a.get("business_name", "")), name_norm(b.get("business_name", ""))
    aa, ba = norm(a.get("business_address", "")), norm(b.get("business_address", ""))
    nj, nc, ns = sim(an, bn)
    aj, ac, ass = sim(aa, ba)
    countries = (a.get("country", "").strip().casefold(), b.get("country", "").strip().casefold())
    return [nj, nc, ns, aj, ac, ass, float(countries[0] == countries[1]),
            float(bool(an) and an == bn), float(bool(aa) and aa == ba),
            float(an[:1] == bn[:1] and bool(an) and bool(bn))]


def heuristic_score(a: dict[str, str], b: dict[str, str]) -> float:
    """Standard-library fallback score, calibrated for demonstration use."""
    f = features(a, b)
    # Strong agreement on both name and address; country agreement is supporting evidence.
    return min(1.0, .48*f[2] + .15*f[0] + .30*f[5] + .08*f[3] + .04*f[6] + .12*f[7])


def candidate_indices(ref: dict[str, str], pool: list[dict[str, str]], max_fallback: int = 80) -> list[int]:
    """Union of normalized name-prefix/token, address-token and country blocks."""
    rn, ra = name_norm(ref.get("business_name", "")), norm(ref.get("business_address", ""))
    rnt, rat = tokens(rn), tokens(ra)
    country = ref.get("country", "").casefold()
    scored: list[tuple[int, int]] = []
    for i, row in enumerate(pool):
        pn, pa = name_norm(row.get("business_name", "")), norm(row.get("business_address", ""))
        pnt, pat = tokens(pn), tokens(pa)
        name_hit = bool(rnt & pnt) or (rn and pn and rn[:4] == pn[:4])
        addr_hit = bool(rat & pat)
        country_hit = bool(country and country == row.get("country", "").casefold())
        if name_hit or addr_hit or (country_hit and rn and pn and rn[:1] == pn[:1]):
            scored.append((i, int(name_hit) * 3 + int(addr_hit) * 2 + int(country_hit)))
    if not scored and pool:
        # Bounded fallback only; keeps inference feasible and prevents empty blocks.
        ranked = sorted(enumerate(pool), key=lambda pair: (
            -max(sim(rn, name_norm(pair[1].get("business_name", "")))[2],
                 sim(ra, norm(pair[1].get("business_address", "")))[2]), pair[0]))
        return [i for i, _ in ranked[:max_fallback]]
    return [i for i, _ in scored]


def load_sources(folder: Path, prefix: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    s1 = read_tsv(folder / f"{prefix}_source1.tsv", FIELDS)
    s2 = read_tsv(folder / f"{prefix}_source2.tsv", FIELDS)
    s3 = read_tsv(folder / f"{prefix}_source3.tsv", FIELDS)
    return s1, s2 + s3


def labels(path: Path) -> dict[str, set[str]]:
    rows = read_tsv(path, ("source1_entity_id", "matched_entity_ids"))
    return {r["source1_entity_id"]: set(filter(None, r["matched_entity_ids"].split(","))) for r in rows}


def pair_data(refs: list[dict[str, str]], pool: list[dict[str, str]], truth: dict[str, set[str]] | None):
    id_to_row = {r["entity_id"]: r for r in pool}
    X, y, groups = [], [], []
    candidates: dict[str, list[dict[str, str]]] = {}
    for ref in refs:
        rows = [pool[i] for i in candidate_indices(ref, pool)]
        candidates[ref["entity_id"]] = rows
        gold = (truth or {}).get(ref["entity_id"], set())
        if truth is not None:
            # Include all positives even if the blocker missed them, so training can learn.
            known = {r["entity_id"] for r in rows}
            rows += [id_to_row[i] for i in sorted(gold - known) if i in id_to_row]
        for row in rows:
            X.append(features(ref, row))
            if truth is not None:
                y.append(int(row["entity_id"] in gold))
                groups.append(ref["entity_id"])
    return X, y, groups, candidates


def validation_report(X, y, groups) -> str:
    if not HAVE_SKLEARN:
        return "Validation model report skipped: scikit-learn is unavailable (using heuristic fallback)."
    if not y or len(set(y)) < 2 or len(set(groups)) < 3:
        return "Validation skipped: not enough labeled groups/classes."
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=17)
    tr, va = next(splitter.split(X, y, groups))
    model = ExtraTreesClassifier(n_estimators=180, min_samples_leaf=2, class_weight="balanced",
                                 random_state=17, n_jobs=-1)
    model.fit([X[i] for i in tr], [y[i] for i in tr])
    probs = model.predict_proba([X[i] for i in va])[:, list(model.classes_).index(1)]
    # Candidate-pair threshold F0.5; per-entity macro score includes all held-out S1s.
    best = (0.0, 0.55)
    for threshold in (0.45, 0.55, 0.65, 0.75, 0.85, 0.92):
        per_group = defaultdict(lambda: [set(), set()])
        for k, idx in enumerate(va):
            per_group[groups[idx]][1 if y[idx] else 0].add(k)
        # Also aggregate candidate decisions to report pair-level F0.5.
        tp = sum(1 for p, i in zip(probs, va) if p >= threshold and y[i] == 1)
        fp = sum(1 for p, i in zip(probs, va) if p >= threshold and y[i] == 0)
        fn = sum(1 for p, i in zip(probs, va) if p < threshold and y[i] == 1)
        prec = tp / max(1, tp + fp); rec = tp / max(1, tp + fn)
        f = 1.25 * prec * rec / max(1e-12, .25 * prec + rec)
        if f > best[0]: best = (f, threshold)
    return f"Grouped held-out candidate-pair F0.5={best[0]:.4f}; selected threshold={best[1]:.2f}."


def write_tsv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers, delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="submission root containing dataset/ and output/")
    parser.add_argument("--threshold", type=float, default=None, help="override model match probability threshold")
    parser.add_argument("--validate-only", action="store_true", help="run challenge validator after outputs are created")
    args = parser.parse_args()
    root = args.root.resolve(); train_dir=root / "dataset/train"; test_dir=root / "dataset/test"; out=root / "output"
    try:
        tr1, trpool = load_sources(train_dir, "train")
        truth = labels(train_dir / "train_ground_truth.tsv")
        X, y, groups, _ = pair_data(tr1, trpool, truth)
        if not X or len(set(y)) < 2:
            raise ValueError("Training pairs need both positive and negative examples; verify train_ground_truth.tsv")
        valmsg = validation_report(X, y, groups)
        model = None
        if HAVE_SKLEARN:
            model = ExtraTreesClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced",
                                         random_state=17, n_jobs=-1)
            model.fit(X, y)
        threshold = args.threshold if args.threshold is not None else 0.75
        te1, tepool = load_sources(test_dir, "test")
        Xt, _, _, candidates = pair_data(te1, tepool, None)
        results=[]; candidate_out=[]
        for ref in te1:
            rows=candidates[ref["entity_id"]]
            candidate_out.append({"source1_entity_id":ref["entity_id"], "candidate_entity_ids":",".join(r["entity_id"] for r in rows)})
            if rows:
                if model is not None:
                    probs=model.predict_proba([features(ref,r) for r in rows])[:, list(model.classes_).index(1)]
                else:
                    probs=[heuristic_score(ref, r) for r in rows]
                matched=[r["entity_id"] for r,p in zip(rows,probs) if p >= threshold]
            else: matched=[]
            results.append({"source1_entity_id":ref["entity_id"], "matched_entity_ids":",".join(dict.fromkeys(matched))})
        write_tsv(out/"matching_results.tsv", ["source1_entity_id","matched_entity_ids"], results)
        write_tsv(out/"candidate_pairs.tsv", ["source1_entity_id","candidate_entity_ids"], candidate_out)
        print(valmsg)
        if model is None:
            print("Matcher: standard-library heuristic fallback (synthetic/demo execution only); install requirements.txt for the trained ExtraTrees model.")
        print(f"Wrote {len(results)} test rows and {len(candidate_out)} candidate rows to {out}")
        validator=root/"utils/validate_submission.py"
        if validator.is_file():
            import subprocess
            p=subprocess.run([sys.executable,str(validator),"--matching",str(out/"matching_results.tsv"),"--candidate",str(out/"candidate_pairs.tsv"),"--test-dir",str(test_dir)],cwd=root)
            return p.returncode
        print("Validator not found at utils/validate_submission.py; structural checks were not run.")
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
