import os
from Bio import SeqIO
from dotenv import load_dotenv


def get_api_key() -> str:
    """Get Anthropic API key from environment variable."""
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return api_key


def read_fasta(file_path):
    record = SeqIO.read(file_path, "fasta")
    
    # Extract gene name from NCBI format: >ref|NM_000518.5|HBB description
    gene_name = None
    description = record.description
    if "|" in description:
        parts = description.split("|")
        if len(parts) >= 3:
            gene_name = parts[2].split()[0]  # "HBB" from "HBB Homo sapiens..."
    
    return {
        "description": description,
        "sequence": str(record.seq).upper(),
        "gene_name": gene_name
    }