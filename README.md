# BIO-DEBUG CRISPR Analysis Tool

**BIO-DEBUG** is an AI-powered tool for CRISPR gene editing analysis. It helps researchers and clinicians assess DNA mutations, design gRNA candidates, validate edit safety, and generate clinical reports—all in a user-friendly web interface.

## Manual Setup & Run (All Systems)

1. **Find your Python interpreter**
   - Try: `python3`, `python`, or `py` (one should work)

2. **Create a virtual environment**
   ```bash
   # Replace <python_cmd> with your working command (python3, python, or py)
   <python_cmd> -m venv .venv
   ```

3. **Activate the virtual environment**
   - **Linux/macOS:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (cmd):**
     ```cmd
     .venv\Scripts\activate
     ```
   - **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

4. **Install dependencies**
   ```bash
   pip install -e .
   ```
   - If you see 'pip not found', install it:
     - **Linux:** `sudo apt install python3-pip`
     - **macOS:** `python3 -m ensurepip --upgrade`
     - **Windows:** Download from [pip documentation](https://pip.pypa.io/en/stable/installation/)
   - If you see 'externally-managed-environment' or PEP 668 error:
     - Add `--break-system-packages` to the pip command:
       ```bash
       pip install --break-system-packages -e .
       ```
     - This is safe in a virtual environment, but do not use it system-wide.

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Open the Streamlit link in your browser**
   - If the app does not open automatically, copy the URL shown in the terminal (e.g. `http://localhost:8501`) and paste it into your web browser.

---


## CRISPR Overview and Key Terms

**CRISPR (Clustered Regularly Interspaced Short Palindromic Repeats)** is a revolutionary genome editing technology derived from a natural defense mechanism found in bacteria. It enables precise, targeted changes to DNA in living organisms. The CRISPR-Cas9 system, the most widely used variant, uses a guide RNA (gRNA) to direct the Cas9 nuclease to a specific DNA sequence, where it introduces a double-strand break. This break can then be repaired by the cell, allowing for gene disruption, correction, or insertion.

**Key Terms:**

- **gRNA (guide RNA):** A synthetic RNA molecule that directs the Cas9 protein to the target DNA sequence.
- **Cas9:** An endonuclease enzyme that cuts DNA at a location specified by the gRNA.
- **PAM (Protospacer Adjacent Motif):** A short DNA sequence required for Cas9 binding and cleavage, typically "NGG" for SpCas9.
- **Off-target effects:** Unintended DNA modifications at sites other than the intended target.
- **On-target efficiency:** The effectiveness of CRISPR in editing the intended DNA site.
- **Variant annotation:** The process of identifying and describing the effects of DNA sequence changes.
- **In silico validation:** Computer-based simulation and analysis of CRISPR edits before laboratory experiments.

## gRNA Design: Challenges and Solutions

Designing effective guide RNAs (gRNAs) for CRISPR editing presents several challenges and restrictions:

- **Off-target effects:** gRNAs may bind to unintended genomic sites, causing unwanted mutations.
- **PAM sequence requirements:** The target site must be adjacent to a specific PAM sequence (e.g., NGG for SpCas9), limiting possible editing locations.
- **Sequence context:** Some genomic regions are less accessible due to chromatin structure or DNA methylation.
- **GC content and secondary structure:** gRNAs with extreme GC content or strong secondary structures may have reduced efficiency.
- **Genetic variation:** Natural variants in the target region can reduce gRNA binding or specificity.

**How BIO-DEBUG addresses these challenges:**

- Performs genome-wide off-target prediction and scoring to minimize unintended edits.
- Automatically checks for PAM sequence presence and suggests only valid target sites.
- Evaluates gRNA candidates for optimal GC content and minimal secondary structure.
- Integrates variant annotation to avoid designing gRNAs in polymorphic or clinically relevant regions.
- Provides in silico validation and efficiency scoring for each gRNA candidate, helping users select the safest and most effective options.

---

## Detailed Description

**BIO-DEBUG CRISPR Analysis Tool** is designed to streamline and automate the analysis of CRISPR gene editing experiments. The tool provides a modular, agent-based architecture to support the full workflow from DNA input to clinical reporting. It is suitable for both research and clinical settings, offering:

- **DNA Mutation Analysis:** Upload DNA sequences (FASTA, VCF, GFF3, etc.) and annotate variants using integrated data sources (e.g., ClinVar, conservation scores).
- **gRNA Design:** Automated design and evaluation of guide RNA candidates, including off-target prediction and scoring.
- **Edit Validation:** In silico validation of CRISPR edits for safety, efficiency, and clinical relevance.
- **Automated Reporting:** Generation of detailed, human-readable reports summarizing findings, risks, and recommendations.
- **Interactive Web UI:** Built with Streamlit for easy, interactive exploration and visualization of results.

## Technical Implementation

The project is organized as follows:

- **app.py**: Entry point for the Streamlit web application.
- **main.py / pipeline.py**: Orchestrate the main workflow and data processing pipeline.
- **agents/**: Implements the core agent classes:
  - `diagnostician.py`: Analyzes DNA mutations and annotates variants.
  - `engineer.py`: Designs and evaluates gRNA candidates.
  - `regulator.py`: Validates edits for safety and regulatory compliance.
  - `reporter.py`: Generates clinical and technical reports.
- **core/**: Contains core logic and data models:
  - `contracts.py`: Defines interfaces and contracts for agents and tools.
  - `dna.py`: DNA sequence handling and manipulation.
  - `events.py`: Event-driven communication between components.
  - `state.py`: Manages application state and context.
- **tools/**: Modular tools for each agent (e.g., variant annotation, gRNA scoring, report formatting).
- **data/**: Example datasets for testing and demonstration (FASTA, VCF, GFF3, JSON, CSV).
- **ui/**: Streamlit UI components and styles for a modern, user-friendly interface.
- **utils/**: Utility functions and logging.

### Key Technologies

- **Python 3.8+**
- **Streamlit** for the web interface
- **Biopython** for data processing
- **Modular, agent-based architecture** for extensibility

### Extending the Tool

- Add new agents or tools by creating modules in `agents/` or `tools/` and registering them in the pipeline.
- Integrate additional data sources by placing files in `data/` and updating the relevant agent/tool logic.
- Customize the UI by editing components in `ui/components/` and styles in `ui/styles.py` or `ui/styles.css`.

For more information, see the code comments and docstrings throughout the repository.