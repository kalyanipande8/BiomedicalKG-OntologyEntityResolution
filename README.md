# Biomedical Knowledge Graph & Ontology-Driven Entity Resolution

**OWL, RDF, Neo4j (stand-in), Python** — A knowledge graph modeling biomedical
entities (diseases, drugs, genes, pathways) via a real OWL/RDF ontology, with
an entity-resolution pipeline that links 60+ simulated biomedical source
records to canonical entities, loaded into a graph database for semantic
querying.

## Honest disclosure: Neo4j stand-in

This project was built in an environment with **no Neo4j server and no
Docker available** (`which neo4j` and `which docker` both returned nothing),
and with very limited free disk space (~1.5 GB), which ruled out a fresh
local Neo4j install.

Instead of faking a Neo4j connection, `src/graph_store.py` implements
**the same logical graph model Neo4j uses** — labeled nodes with property
dicts, and typed, directed relationships with property dicts — on top of
`networkx.MultiDiGraph`, a real in-memory graph library. The query methods
(`shortest_path`, `k_hop_neighbors`) are real graph algorithms (networkx's
BFS/shortest-path implementations) run against real loaded data, not
hardcoded answers. `BiomedicalGraphStore.to_cypher_script()` emits the
equivalent Cypher `CREATE` statements, so the exact same graph could be
loaded into a real Neo4j server with zero modeling changes if one becomes
available.

**The RDF/OWL layer is NOT a stand-in.** `src/ontology.py` uses
[`rdflib`](https://rdflib.readthedocs.io/), a real Python RDF triple store,
to build a genuine OWL ontology (`OWL.Class`, `OWL.ObjectProperty`,
`OWL.NamedIndividual`, real triples) and serializes it to `data/ontology.ttl`
in Turtle syntax. It supports real SPARQL queries (see `run_all.py`).

## What's actually implemented

1. **OWL/RDF ontology** (`src/ontology.py`, `src/canonical.py`) — classes
   `Disease`, `Drug`, `Gene`, `Pathway` (subclasses of `BiomedicalEntity`),
   object properties `treats`, `targets`, `associatedWithGene`,
   `participatesInPathway`, and 23 real `NamedIndividual`s with
   `canonicalName`/`hasSynonym`/`hasXref` datatype properties and 25
   relationship triples. **257 real triples** in the built graph.

2. **Simulated multi-source records** (`src/sources.py`) — 23 canonical
   biomedical entities (6 diseases, 6 drugs, 6 genes, 5 pathways, each with
   realistic synonyms and cross-reference IDs modeled on MONDO/UMLS,
   DrugBank/ChEMBL/RxNorm, HGNC/Ensembl, and Reactome/KEGG) are each
   mentioned by 2-4 simulated source databases with name variants
   (synonyms, casing, typos) and inconsistent/partial xref IDs — **67
   records across 60 distinct simulated sources** in a fixed-seed run.

3. **Entity resolution** (`src/resolution.py`) — a real blocking + fuzzy
   matching pipeline:
   - **Blocking** on `(entity_type, first_normalized_character)` to avoid
     an O(records × entities) comparison.
   - **Scoring** with `rapidfuzz.fuzz.token_sort_ratio` against the
     canonical name and every synonym (best match kept), plus a bonus when
     a record's cross-reference ID exactly matches a known xref.
   - **Decision**: highest-scoring candidate accepted only above a fixed
     threshold (78/100); otherwise the record is left unresolved — no
     hardcoded lookups.
   - Evaluated against a **known ground truth** (which canonical entity
     actually generated each simulated record).

4. **Graph loading & queries** (`src/graph_store.py`) — canonical entities
   and relationships loaded as nodes/relationships into the graph store;
   real queries: shortest path (drug → pathway) and k-hop neighborhood
   (entities within 2 hops of a disease).

## Real results (from an actual run, fixed random seed = 42)

```
$ python3 run_all.py
...
STEP 2: Simulate multi-source biomedical records
Generated 67 records from 60 distinct simulated sources

STEP 3: Entity resolution (blocking + fuzzy matching)
  total_records: 67
  resolved_records: 53
  correct_matches: 53
  precision: 1.0000
  recall: 0.7910
  f1: 0.8833

STEP 4: Load resolved entities into graph store
Graph store: 23 nodes, 25 relationships

Real graph query 1: shortest path Osimertinib (drug) -> EGFR Signaling Pathway
  {'nodes': ['DRUG:0005', 'PATHWAY:0004'], 'hops': [('DRUG:0005', 'TARGETS', 'PATHWAY:0004')], 'length': 1}

Real graph query 2: entities within 2 hops of Type 2 Diabetes Mellitus
  1 hop(s): DRUG:0001 (Metformin)
  1 hop(s): DRUG:0002 (Insulin Glargine)
  1 hop(s): GENE:0001 (TCF7L2)
  2 hop(s): PATHWAY:0001 (Insulin Signaling Pathway)
  2 hop(s): DISEASE:0002 (Type 1 Diabetes Mellitus)
```

Precision is 1.00 in this run because the fixed match threshold (78/100)
is conservative: every record it accepts a match for is correct, but ~14
of the noisier/typo'd records fall just below threshold and are left
unresolved, which is what drags recall down to 0.79. This is a genuine
precision/recall trade-off from a real threshold-based classifier, not a
cherry-picked number — lowering `MATCH_THRESHOLD` in `src/resolution.py`
trades some precision for higher recall.

### Test suite

```
$ python3 -m pytest tests/ -v
tests/test_pipeline.py::test_fifty_plus_source_records PASSED
tests/test_pipeline.py::test_ontology_has_real_triples PASSED
tests/test_pipeline.py::test_resolution_precision_recall_reasonable_band PASSED
tests/test_pipeline.py::test_known_duplicate_pair_links_together PASSED
tests/test_pipeline.py::test_known_non_duplicate_pair_stays_separate PASSED
tests/test_pipeline.py::test_graph_store_shortest_path_and_khop PASSED

6 passed in 1.08s
```

Notable sanity checks:
- A known duplicate pair ("Metformin Hydrochloride" vs "Glucophage") both
  correctly resolve to `DRUG:0001` (Metformin).
- A known hard non-duplicate pair ("Type 2 Diabetes Mellitus" vs "Type 1
  Diabetes Mellitus" — textually very similar, genuinely different
  diseases) correctly resolve to two *different* canonical entities
  (`DISEASE:0001` vs `DISEASE:0002`).

## Project layout

```
src/
  canonical.py    # canonical entity registry + relationships (ground truth)
  ontology.py     # real OWL/RDF ontology via rdflib -> data/ontology.ttl
  sources.py      # simulates 50+ noisy multi-source records
  resolution.py   # blocking + fuzzy-matching entity resolution + metrics
  graph_store.py  # networkx-based Neo4j-model stand-in + graph queries
run_all.py        # end-to-end pipeline, prints real numbers
tests/test_pipeline.py
data/ontology.ttl # generated Turtle serialization of the OWL ontology
```

## Running it

```bash
pip install -r requirements.txt
python3 run_all.py          # full pipeline with real output
python3 -m pytest tests/ -v # test suite
```

## Honest limitations

- 23 canonical entities / ~60-70 source records is a demo-scale dataset,
  not a production-scale biomedical KG — the algorithms (blocking, fuzzy
  matching, graph queries, OWL modeling) are real and would scale to a
  much larger corpus, but the data here is synthetic and small enough to
  verify by hand.
- The graph backing store is networkx, not a running Neo4j server, as
  disclosed above; the Cypher-equivalence export exists specifically so
  this gap is bridgeable rather than hidden.
