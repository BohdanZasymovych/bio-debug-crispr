import json
import csv
from utils.utils import read_fasta


def analyze_mutations(patient_dna_path,
                    reference_dna_path,
                    annotations_path,
                    clinvar_path,
                    conservations_path,
                    protein_structure_path
                ):
    """
    Analyzes the patient's DNA: finds mutations, gets gene features, and gathers evidence.
    Returns a dict with target_gene and a list of mutation dicts, each containing
    index, ref, alt, feature, and evidence data.
    """
    patient_dna_string = read_fasta(patient_dna_path)["sequence"]
    alignment = align_sequence(patient_dna_string, reference_dna_path)
    indices = [v["index"] for v in alignment["variants"]]
    evidences = get_evidence_batch(indices, clinvar_path, conservations_path, protein_structure_path)
    
    mutations = []
    for variant in alignment["variants"]:
        idx = variant["index"]
        mutations.append({
            "index": idx,
            "ref": variant["ref"],
            "alt": variant["alt"],
            "feature": get_gene_feature(idx, annotations_path),
            "evidence": evidences.get(idx, {})
        })
    
    return {
        "target_gene": alignment["target_gene"],
        "mutations": mutations
    }


def align_sequence(patient_dna_string, reference_dna_path):
    """
    Compares the patient's DNA string against the reference genome to find all mismatches.
    Returns a dict with target_gene, mutations_found count, and list of variants.
    """
    ref_data = read_fasta(reference_dna_path)
    reference = ref_data["sequence"]
    target_gene = ref_data["gene_name"]
    
    variants = []
    for i in range(min(len(patient_dna_string), len(reference))):
        if patient_dna_string[i] != reference[i]:
            variants.append({"index": i, "ref": reference[i], "alt": patient_dna_string[i]})
    
    return {
        "target_gene": target_gene,
        "mutations_found": len(variants),
        "variants": variants
    }


def get_gene_feature(index, annotations_path):
    """
    Checks if the mutation index is at a dangerous Splice Site (±2 bp from exon start/end).
    Returns 'Splice Site', 'Exon', or 'Intron'.
    """
    exons = []
    with open(annotations_path, "r") as f:
        for line in f:
            if not line.startswith("#") and "\texon\t" in line:
                parts = line.strip().split("\t")
                start = int(parts[3]) - 1
                end = int(parts[4]) - 1
                exons.append((start, end))
    
    for start, end in exons:
        if start - 2 <= index <= start + 2 or end - 2 <= index <= end + 2:
            return "Splice Site"
        if start <= index <= end:
            return "Exon"
    return "Intron"


def get_evidence_batch(indices, clinvar_path, conservations_path, protein_structure_path):
    """
    Gathers evidence for each mutation index: clinvar status, conservation score, protein region.
    Returns a dict {index: {clinvar, score, region}}.
    """
    clinvar = {}
    with open(clinvar_path, "r") as f:
        for line in f:
            if not line.startswith("#"):
                parts = line.strip().split()
                if len(parts) < 6:
                    continue
                try:
                    pos = int(parts[1])
                    info = parts[5]
                    if "CLNSIG=" in info:
                        clnsig = info.split("CLNSIG=")[1].split(";")[0]
                        clinvar[pos] = clnsig
                except (IndexError, ValueError):
                    continue
    
    conservation = {}
    with open(conservations_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conservation[int(row["pos"])] = float(row["score"])
    
    with open(protein_structure_path, "r") as f:
        protein = json.load(f)
    
    result = {}
    for idx in indices:
        result[idx] = {
            "clinvar": clinvar.get(idx, "Novel"),
            "score": conservation.get(idx, 0.0),
            "region": protein.get(str(idx), {}).get("region", "Unknown")
        }
    return result
