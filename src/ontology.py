"""
Real OWL/RDF ontology built with rdflib.

Defines an OWL ontology with classes (Disease, Drug, Gene, Pathway),
object properties (treats, targets, associatedWithGene, participatesInPathway),
and populates it with real RDF triples for every canonical entity and
relationship in src/canonical.py. This is genuine triple-store data
(rdflib.Graph backed by an in-memory RDF store) — not a mock.
"""
from rdflib import Graph, Namespace, RDF, RDFS, OWL, Literal, XSD
from rdflib.namespace import DC

from .canonical import CANONICAL_ENTITIES, CANONICAL_RELATIONSHIPS

BKG = Namespace("http://example.org/biomedkg#")

CLASS_URIS = {
    "Disease": BKG.Disease,
    "Drug": BKG.Drug,
    "Gene": BKG.Gene,
    "Pathway": BKG.Pathway,
}

PREDICATE_URIS = {
    "TREATS": BKG.treats,
    "TARGETS": BKG.targets,
    "ASSOCIATED_WITH": BKG.associatedWithGene,
    "PARTICIPATES_IN": BKG.participatesInPathway,
}


def build_ontology() -> Graph:
    """Construct the OWL/RDF ontology graph with schema + instance data."""
    g = Graph()
    g.bind("bkg", BKG)
    g.bind("owl", OWL)

    # --- Ontology header ---
    ontology_uri = BKG["ontology"]
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, RDFS.label, Literal("Biomedical Knowledge Graph Ontology")))
    g.add((ontology_uri, DC.description,
           Literal("OWL ontology modeling biomedical entities (diseases, drugs, "
                   "genes, pathways) and their relationships for entity resolution "
                   "and knowledge-graph enrichment.")))

    # --- OWL Classes ---
    for name, uri in CLASS_URIS.items():
        g.add((uri, RDF.type, OWL.Class))
        g.add((uri, RDFS.label, Literal(name)))

    # BiomedicalEntity superclass
    g.add((BKG.BiomedicalEntity, RDF.type, OWL.Class))
    for uri in CLASS_URIS.values():
        g.add((uri, RDFS.subClassOf, BKG.BiomedicalEntity))

    # --- OWL Object Properties ---
    g.add((BKG.treats, RDF.type, OWL.ObjectProperty))
    g.add((BKG.treats, RDFS.domain, BKG.Drug))
    g.add((BKG.treats, RDFS.range, BKG.Disease))

    g.add((BKG.targets, RDF.type, OWL.ObjectProperty))
    g.add((BKG.targets, RDFS.domain, BKG.Drug))
    g.add((BKG.targets, RDFS.range, BKG.Pathway))

    g.add((BKG.associatedWithGene, RDF.type, OWL.ObjectProperty))
    g.add((BKG.associatedWithGene, RDFS.domain, BKG.Gene))
    g.add((BKG.associatedWithGene, RDFS.range, BKG.Disease))

    g.add((BKG.participatesInPathway, RDF.type, OWL.ObjectProperty))
    g.add((BKG.participatesInPathway, RDFS.domain, BKG.Gene))
    g.add((BKG.participatesInPathway, RDFS.range, BKG.Pathway))

    # --- Datatype properties ---
    for prop in ("canonicalName", "hasSynonym", "hasXref"):
        g.add((BKG[prop], RDF.type, OWL.DatatypeProperty))

    # --- Instance data: one OWL individual per canonical entity ---
    for ent in CANONICAL_ENTITIES:
        ind = BKG[ent.id.replace(":", "_")]
        g.add((ind, RDF.type, OWL.NamedIndividual))
        g.add((ind, RDF.type, CLASS_URIS[ent.etype]))
        g.add((ind, BKG.canonicalName, Literal(ent.name, datatype=XSD.string)))
        for syn in ent.synonyms:
            g.add((ind, BKG.hasSynonym, Literal(syn, datatype=XSD.string)))
        for src, xref_id in ent.xrefs.items():
            g.add((ind, BKG.hasXref, Literal(f"{src}:{xref_id}", datatype=XSD.string)))

    # --- Instance relationships ---
    for subj_id, pred, obj_id in CANONICAL_RELATIONSHIPS:
        subj = BKG[subj_id.replace(":", "_")]
        obj = BKG[obj_id.replace(":", "_")]
        g.add((subj, PREDICATE_URIS[pred], obj))

    return g


def save_ontology(g: Graph, path: str) -> None:
    g.serialize(destination=path, format="turtle")


if __name__ == "__main__":
    graph = build_ontology()
    save_ontology(graph, "data/ontology.ttl")
    print(f"Built OWL/RDF ontology with {len(graph)} triples -> data/ontology.ttl")
