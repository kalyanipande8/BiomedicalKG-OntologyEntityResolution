"""
Simulates 50+ biomedical "source" records referencing the canonical entities
in src/canonical.py, with realistic entity-resolution noise:

  - name variants (synonyms, abbreviations, casing, punctuation)
  - light typos / OCR-style character noise
  - inconsistent / partial cross-reference IDs (some sources give one xref
    system, some give none, some give a different one)
  - each canonical entity is mentioned by MULTIPLE distinct "sources"

This mimics the real-world entity-resolution problem of merging records
about the same disease/drug/gene/pathway pulled from 50+ different
databases/registries that each named it slightly differently.

The ground-truth linkage (record_id -> canonical entity id) is returned
alongside the records, so precision/recall can be computed for real.
"""
import random
from dataclasses import dataclass, field

from .canonical import CANONICAL_ENTITIES

RNG = random.Random(42)

SOURCE_NAMES = [f"SourceDB_{i:02d}" for i in range(1, 61)]  # 60 simulated data sources


@dataclass
class SourceRecord:
    record_id: str
    source: str
    etype: str
    raw_name: str
    xref: str = ""   # e.g. "DrugBank:DB00331" -- may be empty


def _typo(name: str) -> str:
    """Introduce a small, realistic character-level perturbation."""
    if len(name) < 4:
        return name
    i = RNG.randrange(1, len(name) - 1)
    ops = ["swap", "drop", "dup"]
    op = RNG.choice(ops)
    if op == "swap" and i + 1 < len(name):
        chars = list(name)
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
        return "".join(chars)
    if op == "drop":
        return name[:i] + name[i + 1:]
    return name[:i] + name[i] + name[i:]


def _variant_name(ent) -> str:
    """Pick a name variant: canonical name, a synonym, or a noisy version."""
    pool = [ent.name] + ent.synonyms
    base = RNG.choice(pool)
    roll = RNG.random()
    if roll < 0.15:
        return _typo(base)
    if roll < 0.30:
        return base.upper()
    if roll < 0.45:
        return base.lower()
    return base


def generate_source_records(min_records: int = 55):
    """
    Returns (records, ground_truth) where ground_truth maps
    record_id -> canonical entity id.
    """
    records = []
    ground_truth = {}
    rec_counter = 0
    src_pool = list(SOURCE_NAMES)
    RNG.shuffle(src_pool)
    src_idx = 0

    # Each canonical entity gets between 2 and 4 source mentions,
    # guaranteeing >= 50 total records across 24 entities.
    for ent in CANONICAL_ENTITIES:
        n_mentions = RNG.choice([2, 3, 3, 4])
        for _ in range(n_mentions):
            rec_counter += 1
            record_id = f"REC{rec_counter:04d}"
            source = src_pool[src_idx % len(src_pool)]
            src_idx += 1

            name = _variant_name(ent)

            xref = ""
            if ent.xrefs and RNG.random() < 0.6:
                src_name, src_id = RNG.choice(list(ent.xrefs.items()))
                xref = f"{src_name}:{src_id}"

            records.append(SourceRecord(record_id, source, ent.etype, name, xref))
            ground_truth[record_id] = ent.id

    # Pad with a few more mentions of random entities if under the minimum
    while len(records) < min_records:
        ent = RNG.choice(CANONICAL_ENTITIES)
        rec_counter += 1
        record_id = f"REC{rec_counter:04d}"
        source = src_pool[src_idx % len(src_pool)]
        src_idx += 1
        name = _variant_name(ent)
        xref = ""
        if ent.xrefs and RNG.random() < 0.6:
            src_name, src_id = RNG.choice(list(ent.xrefs.items()))
            xref = f"{src_name}:{src_id}"
        records.append(SourceRecord(record_id, source, ent.etype, name, xref))
        ground_truth[record_id] = ent.id

    return records, ground_truth


if __name__ == "__main__":
    recs, gt = generate_source_records()
    print(f"Generated {len(recs)} source records across "
          f"{len(set(r.source for r in recs))} distinct sources")
    for r in recs[:10]:
        print(r, "->", gt[r.record_id])
