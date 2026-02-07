"""
Regulator Tools - Safety validation tools for CRISPR therapy designs
=====================================================================
Tools:
1. blast_genome_search() - Genome-wide search for off-target sites
2. check_gene_essentiality() - Check if gene is critical for survival
3. calculate_off_target_score() - Compute safety risk score
"""

from typing import List, Dict


# Mock genome database - simulates human genome regions
# In production, this would connect to real genomic databases
GENOME_DATABASE = {
    'chr11': [
        {
            'start': 5246696,
            'end': 5248301,
            'gene': 'HBB',
            'sequence': 'GTGCACCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGG',
            'region': 'EXON',
            'description': 'Beta-globin gene - oxygen transport'
        },
        {
            'start': 5255000,
            'end': 5257000,
            'gene': 'HBD',
            'sequence': 'GTGCACCTGACTCCTGTGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGAGGCCCTGGGCAGG',
            'region': 'EXON',
            'description': 'Delta-globin gene - HBB paralog (dangerous off-target)'
        },
        {
            'start': 5200000,
            'end': 5245000,
            'gene': 'HBB_INTRON',
            'sequence': 'ATGCGTACGTACGTACGATCGATCGTAGCTAGCTAGCTAGCTAGCTACGTACGTACGATCGATCG',
            'region': 'INTRON',
            'description': 'Non-coding region'
        }
    ],
    'chr17': [
        {
            'start': 7571720,
            'end': 7590868,
            'gene': 'TP53',
            'sequence': 'CCTGACTTTCAACTCTGTCTCCTTCCTCTTCCTACAGTACTCCCCTGCCCTCAACAAGATGTTTTGCCAACTGGCCAAGACCTGCCCTGTGCAGCTGTGGGTTGATTCCACACCCCCGCCCGGCACCCGCGTCCGCGCCATGGCCATCTACAAGCAGTCACAGCACATGACGGAGGTTGTGAGGCGCTGCCCCCACCATGAGCGCTGCTCAGATAGCGATGGTCTGGCCCCTCCTCAGCATCTTATCCGAGTGGAAGGAAATTTGCGTGTGGAGTATTTGGATGACAGAAACACTTTTCG',
            'region': 'EXON',
            'description': 'Tumor suppressor - prevents cancer (ESSENTIAL)'
        }
    ],
    'chr13': [
        {
            'start': 32889611,
            'end': 32973805,
            'gene': 'BRCA2',
            'sequence': 'ATGCCGCCGTGTGCAGCCAGAAGGACATCTGGATCTTGGTGTAAATTGTAACCTGATGGAACAACAACGTTACGGAAACAGAGTATTAA',
            'region': 'EXON',
            'description': 'DNA repair gene (ESSENTIAL)'
        }
    ],
    'chr2': [
        {
            'start': 178525989,
            'end': 178830802,
            'gene': 'TTN',
            'sequence': 'ATGGCTTCTGTGCGCCGTTCCGGACGTTTCCCGCCCTCCTCCCATGCCTCCCTCATCACCACCACCACCACCACCACCACCACCACCAT',
            'region': 'EXON',
            'description': 'Cardiac muscle protein (ESSENTIAL - heart function)'
        }
    ],
    'intergenic': [
        {
            'start': 1000000,
            'end': 2000000,
            'gene': 'INTERGENIC_REGION_1',
            'sequence': 'ATGCGTACGTACGTACGATCGATCGTAGCTAGCTAGCTAGCTAGCTACGTACGTACGATCGATCGATGCGTACGTACGTACGATCGATCG',
            'region': 'INTERGENIC',
            'description': 'Junk DNA - safe for off-targets'
        }
    ]
}

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
    }
}


def count_mismatches(seq1: str, seq2: str) -> int:
    """
    Count number of mismatched bases between two DNA sequences
    
    Args:
        seq1: First DNA sequence
        seq2: Second DNA sequence
        
    Returns:
        int: Number of mismatched positions
    """
    if len(seq1) != len(seq2):
        return len(seq1)  # Return max if lengths don't match
    
    return sum(c1 != c2 for c1, c2 in zip(seq1, seq2))


def blast_genome_search(grna_sequence: str, max_mismatches: int = 3) -> List[Dict]:
    """
    Simulates BLAST search across entire genome for potential off-target sites
    
    Args:
        grna_sequence: The 20bp guide RNA sequence (without PAM)
        max_mismatches: Maximum number of mismatches to report (default 3)
        
    Returns:
        List of off-target hit dictionaries with location, gene, region, mismatches
    """
    off_targets = []
    grna_len = len(grna_sequence)
    
    # Search across all chromosomes
    for chrom, regions in GENOME_DATABASE.items():
        for region in regions:
            target_seq = region['sequence']
            
            # Slide window across target sequence
            for i in range(len(target_seq) - grna_len + 1):
                window = target_seq[i:i + grna_len]
                mismatches = count_mismatches(grna_sequence, window)
                
                # Report if within mismatch threshold
                if mismatches <= max_mismatches:
                    is_essential = region['gene'] in ESSENTIAL_GENES
                    
                    hit = {
                        'location': f"{chrom}:{region['start'] + i}",
                        'gene_name': region['gene'],
                        'region_type': region['region'],
                        'mismatch_count': mismatches,
                        'sequence': window,
                        'is_essential': is_essential,
                        'description': region['description']
                    }
                    off_targets.append(hit)
    
    return off_targets


def check_gene_essentiality(gene_name: str) -> Dict:
    """
    Checks if a gene is essential for survival
    
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


def calculate_off_target_score(off_targets: List[Dict], target_gene: str) -> Dict:
    """
    Calculates a safety score based on off-target analysis
    
    Args:
        off_targets: List of off-target hits from blast_genome_search
        target_gene: The intended target gene name
        
    Returns:
        Dictionary with safety score, risk level, and recommendation
    """
    if not off_targets:
        return {
            'score': 100,
            'risk_level': 'MINIMAL',
            'recommendation': 'APPROVE',
            'reason': 'No off-target sites detected - exceptionally specific design'
        }
    
    # Categorize off-targets
    exon_hits = [ot for ot in off_targets if ot['region_type'] == 'EXON' and ot['gene_name'] != target_gene]
    essential_hits = [ot for ot in off_targets if ot['is_essential'] and ot['gene_name'] != target_gene]
    perfect_matches = [ot for ot in off_targets if ot['mismatch_count'] == 0 and ot['gene_name'] != target_gene]
    
    # CRITICAL - Essential gene hits with high similarity
    if essential_hits and any(ot['mismatch_count'] <= 2 for ot in essential_hits):
        worst_hit = min(essential_hits, key=lambda x: x['mismatch_count'])
        return {
            'score': 0,
            'risk_level': 'CRITICAL',
            'recommendation': 'REJECT',
            'reason': f'Hits essential gene {worst_hit["gene_name"]} with {worst_hit["mismatch_count"]} mismatches - {worst_hit["description"]}'
        }
    
    # HIGH RISK - Exon hits in different genes
    if exon_hits and any(ot['mismatch_count'] <= 1 for ot in exon_hits):
        worst_hit = min(exon_hits, key=lambda x: x['mismatch_count'])
        return {
            'score': 25,
            'risk_level': 'HIGH',
            'recommendation': 'REJECT',
            'reason': f'Hits coding region (EXON) in {worst_hit["gene_name"]} with {worst_hit["mismatch_count"]} mismatches'
        }
    
    # MODERATE RISK - Multiple perfect matches
    if len(perfect_matches) > 0:
        return {
            'score': 40,
            'risk_level': 'MODERATE',
            'recommendation': 'REJECT',
            'reason': f'Multiple perfect match sites detected ({len(perfect_matches) + 1} total including target)'
        }
    
    # LOW RISK - Exon hits with 2+ mismatches
    if exon_hits and any(ot['mismatch_count'] == 2 for ot in exon_hits):
        return {
            'score': 60,
            'risk_level': 'MODERATE',
            'recommendation': 'REJECT',
            'reason': 'Exon hits with 2 mismatches - consider redesign for higher specificity'
        }
    
    # ACCEPTABLE - Only intergenic/intron hits with good mismatch tolerance
    intergenic_only = all(ot['region_type'] in ['INTERGENIC', 'INTRON'] for ot in off_targets if ot['gene_name'] != target_gene)
    
    if intergenic_only:
        return {
            'score': 85,
            'risk_level': 'LOW',
            'recommendation': 'APPROVE',
            'reason': 'All off-targets are in non-coding regions (intergenic/intron) - acceptable safety profile'
        }
    
    # DEFAULT - Good specificity
    return {
        'score': 75,
        'risk_level': 'LOW',
        'recommendation': 'APPROVE',
        'reason': 'Off-targets have sufficient mismatches (3+) and minimal risk'
    }


def get_genome_statistics() -> Dict:
    """
    Returns statistics about the genome database (for debugging/info)
    
    Returns:
        Dictionary with genome database statistics
    """
    total_regions = sum(len(regions) for regions in GENOME_DATABASE.values())
    chromosomes = list(GENOME_DATABASE.keys())
    
    return {
        'total_regions': total_regions,
        'chromosomes': chromosomes,
        'essential_genes_count': len(ESSENTIAL_GENES),
        'essential_genes': list(ESSENTIAL_GENES.keys())
    }


# Example usage for testing
if __name__ == "__main__":
    print("=" * 70)
    print("REGULATOR TOOLS - TESTING")
    print("=" * 70)
    
    # Test 1: Safe gRNA (specific to HBB)
    print("\nTest 1: Safe gRNA design")
    print("-" * 70)
    safe_grna = "GTGCACCTGACTCCTGAGGA"
    off_targets = blast_genome_search(safe_grna)
    score = calculate_off_target_score(off_targets, "HBB")
    print(f"gRNA: {safe_grna}")
    print(f"Off-targets found: {len(off_targets)}")
    print(f"Safety Score: {score['score']}/100")
    print(f"Decision: {score['recommendation']}")
    print(f"Reason: {score['reason']}")
    
    # Test 2: Dangerous gRNA (hits paralog HBD)
    print("\n\nTest 2: Dangerous gRNA (hits paralog)")
    print("-" * 70)
    dangerous_grna = "GTGCACCTGACTCCTGTGGA"
    off_targets = blast_genome_search(dangerous_grna)
    score = calculate_off_target_score(off_targets, "HBB")
    print(f"gRNA: {dangerous_grna}")
    print(f"Off-targets found: {len(off_targets)}")
    
    for ot in off_targets:
        print(f"  - {ot['gene_name']} ({ot['region_type']}) - {ot['mismatch_count']} mismatches")
    
    print(f"Safety Score: {score['score']}/100")
    print(f"Decision: {score['recommendation']}")
    print(f"Reason: {score['reason']}")
    
    # Test 3: Essential gene check
    print("\n\nTest 3: Essential gene check")
    print("-" * 70)
    for gene in ['TP53', 'HBB', 'UNKNOWN_GENE']:
        info = check_gene_essentiality(gene)
        print(f"{gene}: Essential={info['is_essential']}, Risk={info['risk_level']}, Function={info['function']}")
    
    # Genome stats
    print("\n\nGenome Database Statistics:")
    print("-" * 70)
    stats = get_genome_statistics()
    print(f"Total regions: {stats['total_regions']}")
    print(f"Chromosomes: {', '.join(stats['chromosomes'])}")
    print(f"Essential genes tracked: {stats['essential_genes_count']}")