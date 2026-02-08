"""
Regulator Tools - Safety validation tools for CRISPR therapy designs
=====================================================================
Tools:
1. blast_genome_search() - Genome-wide search for off-target sites
2. check_gene_essentiality() - Check if gene is critical for survival  
3. verify_pam_shield() - Verify PAM has been properly mutated
4. analyze_structure_risk() - Check for secondary structure formation
5. calculate_safety_score() - Compute overall safety score
"""

from typing import List, Dict
import re


# Essential genes database
ESSENTIAL_GENES = {
    'TP53': {
        'function': 'Tumor suppressor - prevents cancer',
        'risk': 'CRITICAL',
        'category': 'Cancer Prevention'
    },
    'BRCA1': {
        'function': 'DNA repair - prevents breast/ovarian cancer',
        'risk': 'CRITICAL',
        'category': 'Cancer Prevention'
    },
    'BRCA2': {
        'function': 'DNA repair - maintains genome stability',
        'risk': 'CRITICAL',
        'category': 'Cancer Prevention'
    },
    'TTN': {
        'function': 'Cardiac muscle contraction',
        'risk': 'CRITICAL',
        'category': 'Heart Function'
    },
    'MYH7': {
        'function': 'Heart muscle protein - critical for heartbeat',
        'risk': 'CRITICAL',
        'category': 'Heart Function'
    },
    'SCN5A': {
        'function': 'Cardiac sodium channel - heart rhythm',
        'risk': 'CRITICAL',
        'category': 'Heart Function'
    },
    'CFTR': {
        'function': 'Chloride channel - lung function',
        'risk': 'HIGH',
        'category': 'Respiratory'
    },
    'DMD': {
        'function': 'Muscle structure - prevents muscular dystrophy',
        'risk': 'HIGH',
        'category': 'Neuromuscular'
    },
    'PTEN': {
        'function': 'Tumor suppressor',
        'risk': 'CRITICAL',
        'category': 'Cancer Prevention'
    },
    'HBB': {
        'function': 'Beta-globin - oxygen transport',
        'risk': 'MODERATE',
        'category': 'Blood Function'
    },
    'HBD': {
        'function': 'Delta-globin - HBB paralog',
        'risk': 'MODERATE', 
        'category': 'Blood Function'
    }
}


def count_mismatches(seq1: str, seq2: str) -> int:
    """
    Count number of mismatched bases between two DNA sequences.
    
    Args:
        seq1: First DNA sequence
        seq2: Second DNA sequence
        
    Returns:
        int: Number of mismatched positions
    """
    if len(seq1) != len(seq2):
        return max(len(seq1), len(seq2))
    
    return sum(c1 != c2 for c1, c2 in zip(seq1, seq2))


def blast_genome_search(grna_sequence: str, genome_sequence: str, max_mismatches: int = 3) -> List[Dict]:
    """
    Searches entire genome for potential off-target sites.
    
    Args:
        grna_sequence: The 20bp guide RNA sequence
        genome_sequence: The full genome sequence to search
        max_mismatches: Maximum number of mismatches to report (default 3)
        
    Returns:
        List of off-target hit dictionaries
    """
    off_targets = []
    grna_len = len(grna_sequence)
    grna_upper = grna_sequence.upper()
    genome_upper = genome_sequence.upper()
    
    # Annotate genome regions (simplified - in production use real annotation)
    regions = annotate_genome_regions(genome_upper)
    
    # Slide window across genome
    for i in range(len(genome_upper) - grna_len + 1):
        window = genome_upper[i:i + grna_len]
        mismatches = count_mismatches(grna_upper, window)
        
        if mismatches <= max_mismatches:
            # Find which region this hit is in
            region_info = get_region_at_position(i, regions)
            
            hit = {
                'location': f"Position {i}",
                'gene_name': region_info['gene'],
                'region_type': region_info['type'],
                'mismatch_count': mismatches,
                'sequence': window,
                'is_essential': region_info['gene'] in ESSENTIAL_GENES,
                'description': region_info['description']
            }
            off_targets.append(hit)
    
    return off_targets


def annotate_genome_regions(genome: str) -> List[Dict]:
    """
    Creates simplified genome annotation.
    In production, this would use real GTF/GFF annotation files.
    
    Returns:
        List of genomic regions with their annotations
    """
    genome_len = len(genome)
    
    # Simplified annotation - divide genome into regions
    regions = [
        {
            'start': 0,
            'end': min(500, genome_len),
            'gene': 'HBB',
            'type': 'EXON',
            'description': 'Beta-globin gene - oxygen transport'
        }
    ]
    
    # Add more regions if genome is longer
    if genome_len > 500:
        regions.append({
            'start': 500,
            'end': min(1000, genome_len),
            'gene': 'HBD',
            'type': 'EXON',
            'description': 'Delta-globin - HBB paralog'
        })
    
    if genome_len > 1000:
        regions.append({
            'start': 1000,
            'end': min(2000, genome_len),
            'gene': 'INTERGENIC_1',
            'type': 'INTERGENIC',
            'description': 'Non-coding region'
        })
    
    if genome_len > 2000:
        regions.append({
            'start': 2000,
            'end': genome_len,
            'gene': 'INTERGENIC_2',
            'type': 'INTERGENIC',
            'description': 'Non-coding region'
        })
    
    return regions


def get_region_at_position(position: int, regions: List[Dict]) -> Dict:
    """
    Finds which genomic region a position falls into.
    
    Args:
        position: Genomic position
        regions: List of annotated regions
        
    Returns:
        Region information dict
    """
    for region in regions:
        if region['start'] <= position < region['end']:
            return region
    
    # Default fallback
    return {
        'gene': 'UNKNOWN',
        'type': 'INTERGENIC',
        'description': 'Unknown region'
    }


def check_gene_essentiality(gene_name: str) -> Dict:
    """
    Checks if a gene is essential for survival.
    
    Args:
        gene_name: Name of the gene to check
        
    Returns:
        Dictionary with essentiality information
    """
    if gene_name in ESSENTIAL_GENES:
        gene_info = ESSENTIAL_GENES[gene_name]
        return {
            'gene': gene_name,
            'is_essential': True,
            'function': gene_info['function'],
            'risk_level': gene_info['risk'],
            'category': gene_info['category']
        }
    else:
        return {
            'gene': gene_name,
            'is_essential': False,
            'function': 'Unknown or non-essential function',
            'risk_level': 'LOW',
            'category': 'Non-Essential'
        }


def verify_pam_shield(repair_template: str, pam_index: int, mutation_index: int) -> Dict:
    """
    Verifies that the PAM has been properly mutated in the repair template.
    The PAM (NGG) should be changed to NGA, NGT, or NGC to prevent re-cutting.
    
    Args:
        repair_template: The proposed repair template sequence
        pam_index: Original PAM position in genome
        mutation_index: Position of the mutation
        
    Returns:
        Dictionary with PAM shield status
    """
    if not repair_template or pam_index is None:
        return {
            'status': 'N/A',
            'details': 'Insufficient information for PAM verification'
        }
    
    # Calculate where PAM should be in the repair template
    # This is a simplified check - in production would need exact alignment
    
    # Look for any NGG patterns (active PAM)
    active_pams = list(re.finditer(r'[ATGC]GG', repair_template.upper()))
    
    # Look for shielded PAMs (NGA, NGT, NGC)
    shielded_pams = list(re.finditer(r'[ATGC]G[ATC]', repair_template.upper()))
    
    if active_pams:
        return {
            'status': 'UNSHIELDED',
            'details': f'Found {len(active_pams)} active PAM site(s) in repair template',
            'active_pams': [m.group() for m in active_pams],
            'risk': 'CRITICAL'
        }
    elif shielded_pams:
        return {
            'status': 'VERIFIED',
            'details': 'PAM has been properly mutated to prevent re-cutting',
            'shielded_pams': [m.group() for m in shielded_pams],
            'risk': 'NONE'
        }
    else:
        return {
            'status': 'UNCLEAR',
            'details': 'Could not locate PAM in repair template',
            'risk': 'MODERATE'
        }


def analyze_structure_risk(spacer_sequence: str) -> Dict:
    """
    Analyzes the gRNA for secondary structure formation risk.
    Checks for hairpin potential and GC clustering.
    
    Args:
        spacer_sequence: The 20bp guide RNA sequence
        
    Returns:
        Dictionary with structural risk assessment
    """
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    
    # 1. Check for hairpin formation (complementarity between 5' and 3' ends)
    hairpin_count = 0
    for i in range(min(6, len(spacer_sequence) // 2)):
        five_prime = spacer_sequence[i].upper()
        three_prime = spacer_sequence[-(i + 1)].upper()
        
        if complement.get(five_prime) == three_prime:
            hairpin_count += 1
        else:
            break
    
    # 2. Check for GC clustering (consecutive G or C)
    max_gc_run = 0
    current_gc_run = 0
    
    for base in spacer_sequence.upper():
        if base in ['G', 'C']:
            current_gc_run += 1
            max_gc_run = max(max_gc_run, current_gc_run)
        else:
            current_gc_run = 0
    
    # 3. Check for poly-T terminator
    has_terminator = 'TTTT' in spacer_sequence.upper()
    
    # Assess overall risk
    risk_level = 'NONE'
    warnings = []
    
    if hairpin_count >= 4:
        risk_level = 'HIGH'
        warnings.append(f'Strong hairpin potential ({hairpin_count} complementary bases)')
    elif hairpin_count >= 3:
        risk_level = 'MODERATE'
        warnings.append(f'Moderate hairpin risk ({hairpin_count} complementary bases)')
    
    if max_gc_run >= 5:
        risk_level = max(risk_level, 'MODERATE', key=lambda x: ['NONE', 'MODERATE', 'HIGH'].index(x))
        warnings.append(f'GC clustering detected ({max_gc_run} consecutive GC)')
    
    if has_terminator:
        risk_level = 'HIGH'
        warnings.append('Poly-T terminator found - will truncate expression')
    
    return {
        'risk_level': risk_level,
        'hairpin_count': hairpin_count,
        'max_gc_run': max_gc_run,
        'has_terminator': has_terminator,
        'warnings': warnings
    }


def calculate_safety_score(off_targets: List[Dict], pam_shield_status: Dict, 
                          structural_risk: Dict, target_gene: str) -> Dict:
    """
    Calculates an overall safety score based on all checks.
    
    Args:
        off_targets: List of off-target hits
        pam_shield_status: PAM shield verification result
        structural_risk: Structural analysis result
        target_gene: The intended target gene
        
    Returns:
        Dictionary with safety score and recommendation
    """
    score = 100  # Start with perfect score
    issues = []
    
    # 1. Off-target penalties
    exon_hits = [ot for ot in off_targets 
                 if ot['region_type'] == 'EXON' and ot['gene_name'] != target_gene]
    essential_hits = [ot for ot in off_targets 
                      if ot['is_essential'] and ot['gene_name'] != target_gene]
    
    # Critical: Essential gene hits with high similarity
    for ot in essential_hits:
        if ot['mismatch_count'] <= 2:
            score = 0
            issues.append(f"CRITICAL: Hits essential gene {ot['gene_name']} with {ot['mismatch_count']} mismatches")
            return {
                'score': 0,
                'risk_level': 'CRITICAL',
                'recommendation': 'REJECT',
                'issues': issues
            }
    
    # High risk: Exon hits in different genes
    for ot in exon_hits:
        if ot['mismatch_count'] <= 1:
            score -= 50
            issues.append(f"HIGH RISK: Hits exon in {ot['gene_name']} with {ot['mismatch_count']} mismatches")
        elif ot['mismatch_count'] == 2:
            score -= 30
            issues.append(f"MODERATE RISK: Hits exon in {ot['gene_name']} with 2 mismatches")
    
    # 2. PAM shield penalties
    if pam_shield_status.get('status') == 'UNSHIELDED':
        score = 0
        issues.append("CRITICAL: PAM not properly shielded - will re-cut corrected DNA")
        return {
            'score': 0,
            'risk_level': 'CRITICAL',
            'recommendation': 'REJECT',
            'issues': issues
        }
    elif pam_shield_status.get('status') == 'UNCLEAR':
        score -= 20
        issues.append("WARNING: PAM shield status unclear")
    
    # 3. Structural risk penalties
    if structural_risk.get('risk_level') == 'HIGH':
        score -= 30
        issues.extend(structural_risk.get('warnings', []))
    elif structural_risk.get('risk_level') == 'MODERATE':
        score -= 15
        issues.extend(structural_risk.get('warnings', []))
    
    # Determine final recommendation
    if score >= 80:
        recommendation = 'APPROVE'
        risk_level = 'LOW'
    elif score >= 60:
        recommendation = 'WARNING'
        risk_level = 'MODERATE'
    else:
        recommendation = 'REJECT'
        risk_level = 'HIGH'
    
    return {
        'score': max(0, score),
        'risk_level': risk_level,
        'recommendation': recommendation,
        'issues': issues
    }


# Example usage for testing
if __name__ == "__main__":
    print("=" * 70)
    print("REGULATOR TOOLS - TESTING")
    print("=" * 70)
    
    # Test genome search
    test_genome = "ATGCGTACGTACGTACGATCGATCGTAGCTAGCTAGCTAGCTAGCTACGTACGTACGATCGATCG" * 10
    test_grna = "ATGCGTACGTACGTACGATC"
    
    print(f"\nTest 1: Off-target search")
    print(f"gRNA: {test_grna}")
    print(f"Genome length: {len(test_genome)}")
    
    off_targets = blast_genome_search(test_grna, test_genome)
    print(f"Off-targets found: {len(off_targets)}")
    
    # Test PAM shield
    print(f"\n\nTest 2: PAM shield verification")
    repair_with_shield = "ATGCGACGTACGTACGATC"  # NGA instead of NGG
    repair_no_shield = "ATGCGGCGTACGTACGATC"   # Still has NGG
    
    result1 = verify_pam_shield(repair_with_shield, 100, 105)
    result2 = verify_pam_shield(repair_no_shield, 100, 105)
    
    print(f"Repair with shield: {result1['status']}")
    print(f"Repair without shield: {result2['status']}")
    
    # Test structural analysis
    print(f"\n\nTest 3: Structural analysis")
    hairpin_grna = "ATGCGTACGTACGTACGCAT"  # Complementary ends
    safe_grna = "ATGCGTACGTACGTACGATC"
    
    struct1 = analyze_structure_risk(hairpin_grna)
    struct2 = analyze_structure_risk(safe_grna)
    
    print(f"Hairpin gRNA risk: {struct1['risk_level']} ({struct1['hairpin_count']} complementary)")
    print(f"Safe gRNA risk: {struct2['risk_level']} ({struct2['hairpin_count']} complementary)")