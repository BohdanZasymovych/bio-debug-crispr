import json
from agents.diagnostician import run_diagnostician_agent
from tools.diagnostician_tools import analyze_mutations

from agents.engineer import run_engineer_agent
from agents.regulator import run_regulator_agent


def run_diagnostician_pipeline(
    patient_dna_path, 
    reference_path, 
    annotation_path, 
    clinvar_path, 
    conservations_path, 
    protein_structure_path, 
    api_key
):

    mutation_analysis = analyze_mutations(patient_dna_path,
        reference_path,
        annotation_path,
        clinvar_path,
        conservations_path,
        protein_structure_path
    )
    
    reports = {}
    for mutation in mutation_analysis["mutations"]:
        idx = mutation["index"]
        report = run_diagnostician_agent(mutation, mutation_analysis["target_gene"], api_key)
        reports[idx] = report
        
    return reports


def run_engineer_pipeline(diagnostician_reports, reference_path, api_key):
    engineer_reports = {}

    for idx, diag_report in diagnostician_reports.items():
        target_base = diag_report.get("alt")
        engineer_report = run_engineer_agent(
            mutation_index=idx,
            target_base=target_base,
            fasta_file_path=reference_path,
            api_key=api_key
        )
        engineer_reports[idx] = engineer_report
    return engineer_reports


def run_regulator_pipeline(engineer_reports, api_key):
    regulator_reports = {}
    for idx, eng_report in engineer_reports.items():
        regulator_report = run_regulator_agent(eng_report, api_key)
        regulator_reports[idx] = regulator_report
    return regulator_reports


def run_full_pipeline(
    patient_dna_path, 
    reference_path, 
    annotation_path, 
    clinvar_path, 
    conservation_path, 
    protein_struct_path, 
    api_key
):
    diagnostician_reports = run_diagnostician_pipeline(
        patient_dna_path, 
        reference_path, 
        annotation_path, 
        clinvar_path, 
        conservation_path, 
        protein_struct_path, 
        api_key
    )
    
    engineer_reports = run_engineer_pipeline(diagnostician_reports, reference_path, api_key)
    regulator_reports = run_regulator_pipeline(engineer_reports, api_key)

    final = {
        idx: {
            "diagnostician": diagnostician_reports[idx],
            "engineer": engineer_reports.get(idx),
            "regulator": regulator_reports.get(idx)
        }
        for idx in diagnostician_reports
    }
    
    with open("results.json", 'w') as f:
        json.dump(final, f, indent=2, default=str)

    return final
