from pipeline import run_full_pipeline
from utils.utils import get_api_key

PATIENT_DNA_PATH = "data/dna_input.fasta"
REFERENCE_PATH = "data/dna_reference_hbb.fasta"
ANNOTATION_PATH = "data/annotation.gff3"
CLINVAR_PATH = "data/clinvar.vcf"
CONSERVATION_PATH = "data/conservation.csv"
PROTEIN_STRUCT_PATH = "data/protein_structure.json"


def main():
    api_key = get_api_key()
    results = run_full_pipeline(
        patient_dna_path=PATIENT_DNA_PATH,
        reference_path=REFERENCE_PATH,
        annotation_path=ANNOTATION_PATH,
        clinvar_path=CLINVAR_PATH,
        conservation_path=CONSERVATION_PATH,
        protein_struct_path=PROTEIN_STRUCT_PATH,
        api_key=api_key
    )
    print("\n===== FINAL PIPELINE RESULTS =====\n")
    for idx, report in results.items():
        print(f"Mutation {idx}:")
        print(report)
        print("\n-----------------------------\n")

if __name__ == "__main__":
    main()