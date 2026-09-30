"""
Pipeline tests:
  - 50+ simulated source records are actually produced
  - the OWL/RDF ontology has real triples for every canonical entity
  - entity resolution precision/recall land in a reasonable band
  - a known duplicate pair (two differently-named records of the same
    real entity) resolves to the SAME canonical id
  - a known non-duplicate pair (two records of genuinely different,
    but textually similar, entities) resolves to DIFFERENT canonical ids
  - the graph store answers real shortest-path / k-hop queries correctly
"""
from src.sources import generate_source_records, SourceRecord
from src.resolution import resolve_records, evaluate
from src.ontology import build_ontology
from src.canonical import CANONICAL_ENTITIES, CANONICAL_RELATIONSHIPS
from src.graph_store import BiomedicalGraphStore


def test_fifty_plus_source_records():
    records, ground_truth = generate_source_records(min_records=55)
    assert len(records) >= 50
    assert len(ground_truth) == len(records)
    n_sources = len(set(r.source for r in records))
    assert n_sources >= 50, "expected 50+ distinct simulated biomedical sources"


def test_ontology_has_real_triples():
    g = build_ontology()
    assert len(g) > 100
    # every canonical entity should appear as a NamedIndividual with a canonicalName
    q = """
    PREFIX bkg: <http://example.org/biomedkg#>
    SELECT ?ind WHERE { ?ind bkg:canonicalName ?name . }
    """
    rows = list(g.query(q))
    assert len(rows) == len(CANONICAL_ENTITIES)


def test_resolution_precision_recall_reasonable_band():
    records, ground_truth = generate_source_records(min_records=55)
    results = resolve_records(records)
    metrics = evaluate(results, ground_truth)
    assert metrics["resolved_records"] > 0
    # reasonable bands for a real fuzzy-matching ER pipeline on noisy data
    assert 0.6 <= metrics["precision"] <= 1.0
    assert 0.5 <= metrics["recall"] <= 1.0
    assert metrics["f1"] >= 0.5


def test_known_duplicate_pair_links_together():
    """Two records naming the same real drug differently must resolve
    to the same canonical entity (Metformin, DRUG:0001)."""
    r1 = SourceRecord("DUP_A", "SourceDB_TEST1", "Drug", "Metformin Hydrochloride")
    r2 = SourceRecord("DUP_B", "SourceDB_TEST2", "Drug", "Glucophage")
    results = resolve_records([r1, r2])
    ids = {r.record_id: r.predicted_id for r in results}
    assert ids["DUP_A"] == "DRUG:0001"
    assert ids["DUP_B"] == "DRUG:0001"
    assert ids["DUP_A"] == ids["DUP_B"]


def test_known_non_duplicate_pair_stays_separate():
    """Type 1 and Type 2 diabetes are textually similar but are genuinely
    different diseases -- they must NOT be linked to the same canonical id."""
    r1 = SourceRecord("NONDUP_A", "SourceDB_TEST3", "Disease", "Type 2 Diabetes Mellitus")
    r2 = SourceRecord("NONDUP_B", "SourceDB_TEST4", "Disease", "Type 1 Diabetes Mellitus")
    results = resolve_records([r1, r2])
    ids = {r.record_id: r.predicted_id for r in results}
    assert ids["NONDUP_A"] == "DISEASE:0001"
    assert ids["NONDUP_B"] == "DISEASE:0002"
    assert ids["NONDUP_A"] != ids["NONDUP_B"]


def test_graph_store_shortest_path_and_khop():
    store = BiomedicalGraphStore()
    for ent in CANONICAL_ENTITIES:
        store.add_node(ent.id, ent.etype, name=ent.name)
    for subj, pred, obj in CANONICAL_RELATIONSHIPS:
        store.add_relationship(subj, pred, obj)

    path = store.shortest_path("DRUG:0005", "PATHWAY:0004")
    assert path is not None
    assert path["length"] == 1
    assert path["hops"][0] == ("DRUG:0005", "TARGETS", "PATHWAY:0004")

    neighbors = store.k_hop_neighbors("DISEASE:0001", k=2)
    neighbor_ids = {n for n, _ in neighbors}
    assert "DRUG:0001" in neighbor_ids  # Metformin treats T2DM directly
    assert "GENE:0001" in neighbor_ids  # TCF7L2 associated_with T2DM directly

    no_path = store.shortest_path("DISEASE:0004", "DISEASE:0006")
    # Alzheimer's and RA are not connected in this small demo graph
    assert no_path is None
