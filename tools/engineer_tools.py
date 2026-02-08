import re
from utils.utils import read_fasta


def analyze_candidates(mutation_index: int, target_base: str, fasta_file_path: str) -> list[dict]:
    """
    Finds all gRNA candidates and computes their metrics including repair templates.
    Returns a fully-analyzed report for the LLM to reason over.
    """
    fasta_data = read_fasta(fasta_file_path)
    dna_sequence = fasta_data["sequence"]
    
    candidates = find_pam_sites(dna_sequence, mutation_index)
    
    analyzed = []
    for candidate in candidates:
        spacer = candidate["spacer_sequence"]
        pam_index = candidate["pam_start_index"]
        
        gc_content = calculate_gc_content(spacer)
        safety = check_manufacturing(spacer)
        patch = apply_manufacturing_patch(spacer)
        
        repair_options = generate_repair_template_options(
            dna_sequence, mutation_index, pam_index, target_base
        )
        
        analyzed.append({
            "spacer_sequence": spacer,
            "strand": candidate["strand"],
            "pam_sequence": candidate["pam_sequence"],
            "cut_distance": candidate["cut_distance"],
            "gc_content": round(gc_content, 3),
            "safety": {
                "has_terminator": safety["has_terminator"],
                "hairpin_count": safety["hairpin_count"],
                "starts_with_g": safety["starts_with_g"],
                "last_nucleotide": safety["last_nucleotide"]
            },
            "u6_patch": patch["modification"],
            "repair_template": {
                "is_tryptophan": repair_options["is_tryptophan"],
                "too_short_context": repair_options["too_short_context"],
                "templates": repair_options["templates"]
            }
        })
    
    return analyzed


def generate_repair_template_options(dna_sequence, mutation_index, pam_index, target_base="A"):
    """
    Main Driver: Orchestrates the creation of optimized repair templates.
    Returns early if PAM is unshieldable (TGG/Tryptophan) or context is too short.
    """
    is_tryptophan, too_short_context = check_pam_constraints(dna_sequence, pam_index)
    
    if is_tryptophan or too_short_context:
        return {
            "is_tryptophan": is_tryptophan,
            "too_short_context": too_short_context,
            "templates": []
        }

    candidates = generate_candidates(dna_sequence, mutation_index, pam_index, target_base)
    ranked_candidates = sorted(candidates, key=lambda x: (x['hairpin_score'], abs(x['left_arm_length'] - 60)))

    return {
        "is_tryptophan": False,
        "too_short_context": False,
        "templates": ranked_candidates[:3]
    }


def reverse_complement(seq):
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    return "".join(complement.get(base, base) for base in reversed(seq))


def check_pam_constraints(dna_sequence, pam_index):
    """
    Checks if the PAM is biologically shieldable (not TGG/Tryptophan) 
    and if there is enough DNA context around the cut site.
    
    Returns: (is_tryptophan: bool, too_short_context: bool)
    """
    pam_seq = dna_sequence[pam_index : pam_index + 3]
    is_tryptophan = (pam_seq == "TGG")
    
    cut_site = pam_index - 3
    available_left = cut_site
    available_right = len(dna_sequence) - cut_site
    too_short_context = (available_left < 40 or available_right < 40)

    return is_tryptophan, too_short_context


def generate_candidates(dna, mut_idx, pam_idx, target_base):
    """
    Slides the window and generates valid template sequences.
    """
    candidates = []
    cut_site = pam_idx - 3
    total_len = 120
    max_shift = (total_len // 2) - 40

    for shift in range(-max_shift, max_shift + 1):
        left_arm = (total_len // 2) + shift
        right_arm = (total_len // 2) - shift
        
        start = cut_site - left_arm
        end = cut_site + right_arm
        
        raw_seq = list(dna[start:end])
        final_seq = apply_modifications(raw_seq, start, mut_idx, pam_idx, target_base)
        
        hairpin_count = get_hairpin_count(final_seq)
        
        candidates.append({
            "sequence": final_seq,
            "left_arm_length": left_arm,
            "right_arm_length": right_arm,
            "hairpin_score": hairpin_count
        })
    return candidates


def apply_modifications(seq_chars, start_idx, mut_idx, pam_idx, target_base):
    """
    Applies the Cure (Mutation Fix) and the Shield (Silent Mutation).
    """
    rel_mut = mut_idx - start_idx
    if 0 <= rel_mut < len(seq_chars):
        seq_chars[rel_mut] = target_base
        
    rel_pam = pam_idx - start_idx
    if 0 <= rel_pam < len(seq_chars) - 2:
        seq_chars[rel_pam + 2] = 'A' 
        
    return "".join(seq_chars)


def find_pam_sites(dna_sequence, mutation_index, window_size=20):
    """
    Scans for SpCas9 PAMs (NGG) within a specific window around the mutation.
    Returns valid candidates for gRNA design.
    """
    start = max(0, mutation_index - window_size)
    end = min(len(dna_sequence), mutation_index + window_size)
    
    sub_sequence = dna_sequence[start:end]
    candidates = []

    for match in re.finditer(r"(?=([ATGC]GG))", sub_sequence):
        local_pam_index = match.start()
        global_pam_index = start + local_pam_index
        
        cut_site = global_pam_index - 3
        distance = abs(cut_site - mutation_index)
        
        candidates.append({
            "strand": "+",
            "pam_sequence": match.group(1),
            "pam_start_index": global_pam_index,
            "cut_distance": distance,
            "spacer_sequence": dna_sequence[global_pam_index-20 : global_pam_index]
        })

    for match in re.finditer(r"(?=(CC[ATGC]))", sub_sequence):
        local_pam_index = match.start()
        global_pam_index = start + local_pam_index
        
        cut_site = global_pam_index + 6 
        distance = abs(cut_site - mutation_index)
        
        raw_spacer = dna_sequence[global_pam_index+3 : global_pam_index+23]
        
        candidates.append({
            "strand": "-",
            "pam_sequence": match.group(1),
            "pam_start_index": global_pam_index,
            "cut_distance": distance,
            "spacer_sequence": reverse_complement(raw_spacer)
        })

    valid_candidates = [c for c in candidates if c['cut_distance'] <= 15]
    return sorted(valid_candidates, key=lambda x: x['cut_distance'])


def calculate_gc_content(sequence):
    """
    Calculates the percentage of G and C nucleotides.
    """
    g_count = sequence.count('G')
    c_count = sequence.count('C')
    return (g_count + c_count) / len(sequence) * 100


def check_manufacturing(sequence):
    """
    Validates gRNA manufacturability for U6 promoter-based expression systems.
    
    Checks for:
    - starts_with_g: U6 promoter requires 'G' at transcription start for efficient expression
    - has_terminator: Poly-T (TTTT) acts as Pol III terminator, causing premature truncation
    - has_hairpin: Strong secondary structures reduce Cas9 loading efficiency
    - last_nucleotide: Desides cut efficiency

    Returns dict with boolean flags and the last nucleotide for downstream analysis.
    """
    starts_with_g = sequence.upper().startswith("G")
    has_terminator = "TTTT" in sequence.upper()
    hairpin_count = get_hairpin_count(sequence)
    
    return {
        "starts_with_g": starts_with_g,
        "has_terminator": has_terminator,
        "hairpin_count": hairpin_count,
        "last_nucleotide": sequence[-1]
    }


def apply_manufacturing_patch(sequence):
    """
    Ensures the gRNA sequence starts with 'G' for U6 promoter compatibility.
    If it doesn't, it prepends a 'G'.
    """
    seq = sequence.upper()
    if seq.startswith("G"):
        return {
            "original": seq,
            "patched": seq,
            "modification": "None",
            "final_length": len(seq)
        }
    else:
        return {
            "original": seq,
            "patched": "G" + seq,
            "modification": "Prepended 'G' for U6 efficiency",
            "final_length": len(seq) + 1
        }


def get_hairpin_count(sequence):
    """
    Counts complementary nucleotides between 5' and 3' ends that could form hairpin structures.
    Higher count indicates stronger potential for secondary structure formation.
    
    Returns: Number of consecutive complementary base pairs (0-4).
    """
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C'}
    count = 0
    
    for i in range(len(sequence) // 2):
        five_prime = sequence[i].upper()
        three_prime = sequence[-(i + 1)].upper()
        
        if complement.get(five_prime) == three_prime:
            count += 1
        else:
            break
    
    return count
