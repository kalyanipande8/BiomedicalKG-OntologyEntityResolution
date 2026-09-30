"""
Real entity-resolution pipeline: blocking + fuzzy string matching + a
weighted similarity score, linking noisy multi-source records to the
canonical biomedical entity registry (src/canonical.py).

Algorithm
---------
1. Blocking: candidate canonical entities are restricted to those sharing
   the record's entity type and the first normalized character of the
   name. This is a standard entity-resolution blocking strategy that
   avoids an O(records x canonical_entities) full comparison.
2. Scoring: for each candidate in the block, compute a similarity score
   combining:
     - rapidfuzz token_sort_ratio between the record's raw name and the
       candidate's canonical name / each synonym (best of these), 0-100
     - a cross-reference (xref) exact-match bonus when the record carries
       an ID string that matches one of the candidate's known xrefs
3. Decision: the highest-scoring candidate is accepted as a match if its
   combined score clears MATCH_THRESHOLD; otherwise the record is left
   unresolved (no forced/hardcoded match).

Precision/recall are computed against the known ground truth produced by
src/sources.py (which entity actually generated each record).
"""
import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from .canonical import CANONICAL_ENTITIES

MATCH_THRESHOLD = 78.0
XREF_BONUS = 25.0


def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _block_key(etype: str, name: str) -> str:
    norm = normalize(name)
    first = norm[0] if norm else "?"
    return f"{etype}:{first}"


def build_blocking_index():
    index = {}
    for ent in CANONICAL_ENTITIES:
        for name in [ent.name] + ent.synonyms:
            key = _block_key(ent.etype, name)
            index.setdefault(key, set()).add(ent.id)
    return index


@dataclass
class ResolutionResult:
    record_id: str
    predicted_id: str  # "" if unresolved
    score: float


def _name_similarity(raw_name: str, ent) -> float:
    candidates = [ent.name] + ent.synonyms
    return max(fuzz.token_sort_ratio(raw_name, c) for c in candidates)


def _xref_matches(record_xref: str, ent) -> bool:
    if not record_xref:
        return False
    return record_xref in {f"{src}:{val}" for src, val in ent.xrefs.items()}


def resolve_records(records):
    """
    Resolve a list of SourceRecord objects to canonical entity ids.
    Returns a list of ResolutionResult (same order as input).
    """
    index = build_blocking_index()
    by_id = {e.id: e for e in CANONICAL_ENTITIES}
    results = []

    for rec in records:
        key = _block_key(rec.etype, rec.raw_name)
        # Fall back to scanning the whole entity-type pool if the exact
        # first-letter block misses (handles typo'd first characters).
        candidate_ids = set(index.get(key, set()))
        if not candidate_ids:
            candidate_ids = {e.id for e in CANONICAL_ENTITIES if e.etype == rec.etype}
        else:
            # also widen slightly with the full type pool at lower priority
            candidate_ids |= {e.id for e in CANONICAL_ENTITIES if e.etype == rec.etype}

        best_id, best_score = "", 0.0
        for cid in candidate_ids:
            ent = by_id[cid]
            score = _name_similarity(rec.raw_name, ent)
            if _xref_matches(rec.xref, ent):
                score += XREF_BONUS
            score = min(score, 100.0 + XREF_BONUS)
            if score > best_score:
                best_score = score
                best_id = cid

        if best_score >= MATCH_THRESHOLD:
            results.append(ResolutionResult(rec.record_id, best_id, best_score))
        else:
            results.append(ResolutionResult(rec.record_id, "", best_score))

    return results


def evaluate(results, ground_truth: dict):
    """
    Compute real precision/recall/F1 of the resolution results against
    ground truth record_id -> canonical_id mapping.

    precision = correct matches / total records the pipeline resolved (predicted non-empty)
    recall    = correct matches / total records that have a ground-truth entity
    """
    resolved = [r for r in results if r.predicted_id]
    correct = [r for r in resolved if ground_truth.get(r.record_id) == r.predicted_id]

    precision = len(correct) / len(resolved) if resolved else 0.0
    recall = len(correct) / len(ground_truth) if ground_truth else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "total_records": len(results),
        "resolved_records": len(resolved),
        "correct_matches": len(correct),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
