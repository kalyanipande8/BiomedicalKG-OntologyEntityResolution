"""
Canonical biomedical entity registry.

This is the "ground truth" set of real-world entities (diseases, drugs,
genes, pathways) that the entity-resolution pipeline is trying to link
noisy, multi-source records back to. Each canonical entity carries a
handful of realistic synonyms and cross-reference IDs (drawn from real
ontologies/vocabularies: MONDO/UMLS-style disease IDs, DrugBank-style
drug IDs, HGNC gene symbols/IDs, Reactome-style pathway IDs) so that the
simulated source records below can plausibly disagree about naming and
identifiers, which is the whole point of entity resolution.
"""
from dataclasses import dataclass, field


@dataclass
class CanonicalEntity:
    id: str            # canonical internal ID, e.g. "DISEASE:0001"
    etype: str          # "Disease" | "Drug" | "Gene" | "Pathway"
    name: str
    synonyms: list = field(default_factory=list)
    xrefs: dict = field(default_factory=dict)  # source_name -> external id


CANONICAL_ENTITIES = [
    # ---------------- Diseases ----------------
    CanonicalEntity("DISEASE:0001", "Disease", "Type 2 Diabetes Mellitus",
                     synonyms=["Type 2 Diabetes", "T2DM", "Diabetes Mellitus Type 2",
                               "Non-insulin-dependent diabetes mellitus", "Adult-onset diabetes"],
                     xrefs={"MONDO": "MONDO:0005148", "UMLS": "C0011860", "ICD10": "E11"}),
    CanonicalEntity("DISEASE:0002", "Disease", "Type 1 Diabetes Mellitus",
                     synonyms=["Type 1 Diabetes", "T1DM", "Insulin-dependent diabetes mellitus",
                               "Juvenile diabetes"],
                     xrefs={"MONDO": "MONDO:0005147", "UMLS": "C0011854", "ICD10": "E10"}),
    CanonicalEntity("DISEASE:0003", "Disease", "Essential Hypertension",
                     synonyms=["Hypertension", "High Blood Pressure", "Primary Hypertension", "HTN"],
                     xrefs={"MONDO": "MONDO:0005044", "UMLS": "C0085580", "ICD10": "I10"}),
    CanonicalEntity("DISEASE:0004", "Disease", "Alzheimer Disease",
                     synonyms=["Alzheimer's Disease", "AD", "Alzheimer Dementia", "Senile dementia Alzheimer type"],
                     xrefs={"MONDO": "MONDO:0004975", "UMLS": "C0002395", "ICD10": "G30"}),
    CanonicalEntity("DISEASE:0005", "Disease", "Non-Small Cell Lung Carcinoma",
                     synonyms=["NSCLC", "Non-Small Cell Lung Cancer", "Non-small cell carcinoma of lung"],
                     xrefs={"MONDO": "MONDO:0005233", "UMLS": "C0007131", "ICD10": "C34"}),
    CanonicalEntity("DISEASE:0006", "Disease", "Rheumatoid Arthritis",
                     synonyms=["RA", "Rheumatoid arthritis, autoimmune"],
                     xrefs={"MONDO": "MONDO:0008383", "UMLS": "C0003873", "ICD10": "M06"}),

    # ---------------- Drugs ----------------
    CanonicalEntity("DRUG:0001", "Drug", "Metformin",
                     synonyms=["Metformin Hydrochloride", "Glucophage", "Metformin HCl", "Dimethylbiguanide"],
                     xrefs={"DrugBank": "DB00331", "CHEMBL": "CHEMBL1431", "RxNorm": "6809"}),
    CanonicalEntity("DRUG:0002", "Drug", "Insulin Glargine",
                     synonyms=["Lantus", "Insulin glargine recombinant", "Glargine"],
                     xrefs={"DrugBank": "DB00047", "CHEMBL": "CHEMBL1201499", "RxNorm": "274783"}),
    CanonicalEntity("DRUG:0003", "Drug", "Lisinopril",
                     synonyms=["Prinivil", "Zestril", "Lisinopril dihydrate"],
                     xrefs={"DrugBank": "DB00722", "CHEMBL": "CHEMBL1560", "RxNorm": "29046"}),
    CanonicalEntity("DRUG:0004", "Drug", "Donepezil",
                     synonyms=["Aricept", "Donepezil hydrochloride", "Donepezil HCl"],
                     xrefs={"DrugBank": "DB00843", "CHEMBL": "CHEMBL502", "RxNorm": "3155"}),
    CanonicalEntity("DRUG:0005", "Drug", "Osimertinib",
                     synonyms=["Tagrisso", "AZD9291", "Osimertinib mesylate"],
                     xrefs={"DrugBank": "DB09330", "CHEMBL": "CHEMBL3353410", "RxNorm": "1873987"}),
    CanonicalEntity("DRUG:0006", "Drug", "Methotrexate",
                     synonyms=["Rheumatrex", "Trexall", "Amethopterin"],
                     xrefs={"DrugBank": "DB00563", "CHEMBL": "CHEMBL34259", "RxNorm": "6851"}),

    # ---------------- Genes ----------------
    CanonicalEntity("GENE:0001", "Gene", "TCF7L2",
                     synonyms=["Transcription factor 7-like 2", "TCF-4", "TCF4-like 2"],
                     xrefs={"HGNC": "HGNC:11641", "Ensembl": "ENSG00000148737", "NCBIGene": "6934"}),
    CanonicalEntity("GENE:0002", "Gene", "INS",
                     synonyms=["Insulin gene", "Preproinsulin", "IDDM2"],
                     xrefs={"HGNC": "HGNC:6081", "Ensembl": "ENSG00000254647", "NCBIGene": "3630"}),
    CanonicalEntity("GENE:0003", "Gene", "AGT",
                     synonyms=["Angiotensinogen", "Serpin A8", "SERPINA8"],
                     xrefs={"HGNC": "HGNC:333", "Ensembl": "ENSG00000135744", "NCBIGene": "183"}),
    CanonicalEntity("GENE:0004", "Gene", "APOE",
                     synonyms=["Apolipoprotein E", "AD2"],
                     xrefs={"HGNC": "HGNC:613", "Ensembl": "ENSG00000130203", "NCBIGene": "348"}),
    CanonicalEntity("GENE:0005", "Gene", "EGFR",
                     synonyms=["Epidermal growth factor receptor", "ERBB1", "HER1"],
                     xrefs={"HGNC": "HGNC:3236", "Ensembl": "ENSG00000146648", "NCBIGene": "1956"}),
    CanonicalEntity("GENE:0006", "Gene", "PTPN22",
                     synonyms=["Protein tyrosine phosphatase non-receptor type 22", "LYP"],
                     xrefs={"HGNC": "HGNC:9646", "Ensembl": "ENSG00000134242", "NCBIGene": "26191"}),

    # ---------------- Pathways ----------------
    CanonicalEntity("PATHWAY:0001", "Pathway", "Insulin Signaling Pathway",
                     synonyms=["Insulin signalling pathway", "Insulin receptor signaling"],
                     xrefs={"Reactome": "R-HSA-74752", "KEGG": "hsa04910"}),
    CanonicalEntity("PATHWAY:0002", "Pathway", "Renin-Angiotensin System",
                     synonyms=["RAAS pathway", "Renin angiotensin aldosterone system", "RAS pathway"],
                     xrefs={"Reactome": "R-HSA-2022377", "KEGG": "hsa04614"}),
    CanonicalEntity("PATHWAY:0003", "Pathway", "Amyloid Precursor Protein Metabolism",
                     synonyms=["APP metabolic pathway", "Amyloid-beta processing pathway"],
                     xrefs={"Reactome": "R-HSA-9679506", "KEGG": "hsa05010"}),
    CanonicalEntity("PATHWAY:0004", "Pathway", "EGFR Signaling Pathway",
                     synonyms=["Epidermal growth factor receptor signaling", "ErbB signaling pathway"],
                     xrefs={"Reactome": "R-HSA-177929", "KEGG": "hsa04012"}),
    CanonicalEntity("PATHWAY:0005", "Pathway", "T Cell Receptor Signaling Pathway",
                     synonyms=["TCR signaling", "T-cell receptor signalling pathway"],
                     xrefs={"Reactome": "R-HSA-202403", "KEGG": "hsa04660"}),
]

# Relationships between canonical entities: (subject_id, predicate, object_id)
CANONICAL_RELATIONSHIPS = [
    ("DRUG:0001", "TREATS", "DISEASE:0001"),
    ("DRUG:0002", "TREATS", "DISEASE:0001"),
    ("DRUG:0002", "TREATS", "DISEASE:0002"),
    ("DRUG:0003", "TREATS", "DISEASE:0003"),
    ("DRUG:0004", "TREATS", "DISEASE:0004"),
    ("DRUG:0005", "TREATS", "DISEASE:0005"),
    ("DRUG:0006", "TREATS", "DISEASE:0006"),
    ("GENE:0001", "ASSOCIATED_WITH", "DISEASE:0001"),
    ("GENE:0002", "ASSOCIATED_WITH", "DISEASE:0002"),
    ("GENE:0003", "ASSOCIATED_WITH", "DISEASE:0003"),
    ("GENE:0004", "ASSOCIATED_WITH", "DISEASE:0004"),
    ("GENE:0005", "ASSOCIATED_WITH", "DISEASE:0005"),
    ("GENE:0006", "ASSOCIATED_WITH", "DISEASE:0006"),
    ("GENE:0001", "PARTICIPATES_IN", "PATHWAY:0001"),
    ("GENE:0002", "PARTICIPATES_IN", "PATHWAY:0001"),
    ("GENE:0003", "PARTICIPATES_IN", "PATHWAY:0002"),
    ("GENE:0004", "PARTICIPATES_IN", "PATHWAY:0003"),
    ("GENE:0005", "PARTICIPATES_IN", "PATHWAY:0004"),
    ("GENE:0006", "PARTICIPATES_IN", "PATHWAY:0005"),
    ("DRUG:0001", "TARGETS", "PATHWAY:0001"),
    ("DRUG:0002", "TARGETS", "PATHWAY:0001"),
    ("DRUG:0003", "TARGETS", "PATHWAY:0002"),
    ("DRUG:0004", "TARGETS", "PATHWAY:0003"),
    ("DRUG:0005", "TARGETS", "PATHWAY:0004"),
    ("DRUG:0006", "TARGETS", "PATHWAY:0005"),
]


def by_id(entity_id: str) -> CanonicalEntity:
    for e in CANONICAL_ENTITIES:
        if e.id == entity_id:
            return e
    raise KeyError(entity_id)
