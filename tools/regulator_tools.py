from typing import List, Dict, Any
import re
import os
import json

ESSENTIAL_GENES_DB = {}


def load_essential_genes(json_file_path: str) -> None:
    global ESSENTIAL_GENES_DB
    
    if not os.path.exists(json_file_path):
        print(f"WARNING: Essential genes DB {json_file_path} not found. Safety checks may be compromised.")
        return

    with open(json_file_path, 'r') as f:
        ESSENTIAL_GENES_DB = json.load(f)

def count_mismatches(seq1: str, seq2: str) -> int:
    if len(seq1) != len(seq2):
        return max(len(seq1), len(seq2))
    return sum(c1 != c2 for c1, c2 in zip(seq1, seq2))

def parse_gff3_attributes(attribute_string: str) -> Dict[str, str]:
    attrs = {}
    for item in attribute_string.split(';'):
        if '=' in item:
            key, value = item.strip().split('=', 1)
            attrs[key] = value
    return attrs

def annotate_genome_regions(gff_file_path: str) -> List[Dict]:
    regions = []
    
    if not os.path.exists(gff_file_path):
        return []

    try:
        with open(gff_file_path, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                
                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue
                
                feature_type = parts[2]
                start_1based = int(parts[3])
                end_1based = int(parts[4])
                attributes_str = parts[8]
                
                start_0based = start_1based - 1
                end_0based = end_1based
                
                attrs = parse_gff3_attributes(attributes_str)
                feature_id = attrs.get('ID', attrs.get('Name', attrs.get('gene_name', 'Unknown')))
                
                region_type = feature_type.upper() 
                if region_type not in ['EXON', 'INTRON', 'CDS', 'GENE']:
                    region_type = 'INTERGENIC'

                regions.append({
                    'start': start_0based,
                    'end': end_0based,
                    'gene': feature_id,
                    'type': region_type,
                    'description': f"From {parts[1]}"
                })
                
    except Exception as e:
        print(f"Error parsing GFF3: {e}")
        
    return regions

def get_region_at_position(position: int, regions: List[Dict]) -> Dict:
    for region in regions:
        if region['start'] <= position < region['end']:
            return region
    return {
        'gene': 'Unknown',
        'type': 'INTERGENIC',
        'description': 'No annotation found'
    }

def blast_genome_search(grna_sequence: str, genome_sequence: str, gff_path: str, max_mismatches: int = 3) -> List[Dict]:
    off_targets = []
    grna_len = len(grna_sequence)
    grna_upper = grna_sequence.upper()
    genome_upper = genome_sequence.upper()
    
    regions = annotate_genome_regions(gff_path)
    
    for i in range(len(genome_upper) - grna_len + 1):
        window = genome_upper[i:i + grna_len]
        mismatches = count_mismatches(grna_upper, window)
        
        if mismatches <= max_mismatches:
            region_info = get_region_at_position(i, regions)
            gene_name = region_info['gene']
            
            is_essential = gene_name in ESSENTIAL_GENES_DB
            
            hit = {
                'location': f"Position {i}",
                'gene_name': gene_name,
                'region_type': region_info['type'],
                'mismatch_count': mismatches,
                'sequence': window,
                'is_essential': is_essential,
                'description': region_info['description']
            }
            off_targets.append(hit)
    
    return off_targets

def check_gene_essentiality(gene_name: str) -> Dict:
    if gene_name in ESSENTIAL_GENES_DB:
        gene_info = ESSENTIAL_GENES_DB[gene_name]
        return {
            'gene': gene_name,
            'is_essential': True,
            'function': gene_info.get('function', 'Unknown'),
            'risk_level': gene_info.get('risk', 'HIGH'),
            'category': gene_info.get('category', 'General')
        }
    return {
        'gene': gene_name,
        'is_essential': False,
        'function': 'Unknown',
        'risk_level': 'LOW',
        'category': 'Non-Essential'
    }

def verify_pam_shield(repair_template: str, pam_index: int, mutation_index: int) -> Dict:
    if not repair_template or pam_index is None:
        return {'status': 'N/A', 'details': 'Insufficient info'}
    
    active_pams = list(re.finditer(r'[ATGC]GG', repair_template.upper()))
    shielded_pams = list(re.finditer(r'[ATGC]G[ATC]', repair_template.upper()))
    
    if active_pams:
        return {'status': 'UNSHIELDED', 'risk': 'CRITICAL', 'active_pams': [m.group() for m in active_pams]}
    elif shielded_pams:
        return {'status': 'VERIFIED', 'risk': 'NONE', 'shielded_pams': [m.group() for m in shielded_pams]}
    return {'status': 'UNCLEAR', 'risk': 'MODERATE'}

def analyze_structure_risk(spacer_sequence: str) -> Dict:
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    hairpin_count = 0
    for i in range(min(6, len(spacer_sequence) // 2)):
        if complement.get(spacer_sequence[i].upper()) == spacer_sequence[-(i + 1)].upper():
            hairpin_count += 1
        else:
            break
            
    has_terminator = 'TTTT' in spacer_sequence.upper()
    risk_level = 'NONE'
    warnings = []
    
    if hairpin_count >= 3:
        risk_level = 'HIGH' if hairpin_count >= 4 else 'MODERATE'
        warnings.append(f'Hairpin risk ({hairpin_count})')
    if has_terminator:
        risk_level = 'HIGH'
        warnings.append('Poly-T terminator found')
        
    return {
        'risk_level': risk_level,
        'hairpin_count': hairpin_count,
        'has_terminator': has_terminator,
        'warnings': warnings
    }

def calculate_safety_score(off_targets: List[Dict], pam_shield_status: Dict, 
                          structural_risk: Dict, target_gene: str) -> Dict:
    score = 100
    issues = []
    
    exon_hits = [ot for ot in off_targets 
                 if ot['region_type'] in ['EXON', 'CDS'] and ot['gene_name'] != target_gene]
    essential_hits = [ot for ot in off_targets 
                      if ot['is_essential'] and ot['gene_name'] != target_gene]
    
    for ot in essential_hits:
        if ot['mismatch_count'] <= 2:
            return {'score': 0, 'risk_level': 'CRITICAL', 'recommendation': 'REJECT', 
                    'issues': [f"CRITICAL: Hit essential gene {ot['gene_name']}"]}
    
    for ot in exon_hits:
        if ot['mismatch_count'] <= 1:
            score -= 50
            issues.append(f"HIGH: Hit exon {ot['gene_name']}")
        elif ot['mismatch_count'] == 2:
            score -= 30
            issues.append(f"MODERATE: Hit exon {ot['gene_name']}")
            
    if pam_shield_status.get('status') == 'UNSHIELDED':
        return {'score': 0, 'risk_level': 'CRITICAL', 'recommendation': 'REJECT', 
                'issues': ["CRITICAL: PAM unshielded"]}
                
    if structural_risk['risk_level'] == 'HIGH': score -= 30
    elif structural_risk['risk_level'] == 'MODERATE': score -= 15
    
    recommendation = 'APPROVE' if score >= 80 else 'WARNING' if score >= 60 else 'REJECT'
    return {'score': max(0, score), 'risk_level': recommendation, 'recommendation': recommendation, 'issues': issues}
