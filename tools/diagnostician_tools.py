import json
import csv
from utils.utils import read_fasta


def align_sequence(patient_dna_string):
    """
    Compares the patient's DNA string against the reference genome to find all mismatches.
    Returns a dict with mutations_found count and list of variants.
    """
    reference = read_fasta("data/reference_hbb.fasta")["sequence"]
    variants = []
    for i in range(min(len(patient_dna_string), len(reference))):
        if patient_dna_string[i] != reference[i]:
            variants.append({"index": i, "ref": reference[i], "alt": patient_dna_string[i]})
    return {"mutations_found": len(variants), "variants": variants}


def get_gene_feature(index):
    """
    Checks if the mutation index is at a dangerous Splice Site (±2 bp from exon start/end).
    Returns 'Splice Site', 'Exon', or 'Intron'.
    """
    exons = []
    with open("data/annotation.gff3", "r") as f:
        for line in f:
            if not line.startswith("#") and "\texon\t" in line:
                parts = line.strip().split("\t")
                start = int(parts[3]) - 1  # Convert to 0-based
                end = int(parts[4]) - 1
                exons.append((start, end))
    
    for start, end in exons:
        if start - 2 <= index <= start + 2 or end - 2 <= index <= end + 2:
            return "Splice Site"
        if start <= index <= end:
            return "Exon"
    return "Intron"


def get_evidence_batch(indices):
    """
    Gathers evidence for each mutation index: clinvar status, conservation score, protein region.
    Returns a dict {index: {clinvar, score, region}}.
    """
    # Clinvar
    clinvar = {}
    with open("data/clinvar.vcf", "r") as f:
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
    with open("data/conservation.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conservation[int(row["pos"])] = float(row["score"])
    
    with open("data/protein_structure.json", "r") as f:
        protein = json.load(f)
    
    result = {}
    for idx in indices:
        result[idx] = {
            "clinvar": clinvar.get(idx, "Novel"),
            "score": conservation.get(idx, 0.0),
            "region": protein.get(str(idx), {}).get("region", "Unknown")
        }
    return result
