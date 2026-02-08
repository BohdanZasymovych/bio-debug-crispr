import os
from Bio import SeqIO


def get_api_key() -> str:
    """Get Anthropic API key from environment variable."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return api_key


def read_fasta(file_path):
    record = SeqIO.read(file_path, "fasta")
    
    return {
        "description": record.description,
        "sequence": str(record.seq).upper()
    }