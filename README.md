# AMPs-via-VAE

Conditional variational autoencoder (cVAE) for **antimicrobial peptide (AMP)** generation with multi-label conditioning, post-training analysis, and classifier-based in-silico screening.

## Project status

This repository is the **final implementation stage** of the course project.  
The current scope includes:

- AMP dataset preprocessing and label extraction,
- GRU-based conditional VAE training,
- post-training analysis of generated peptides,
- internal multi-label classifier for condition-adherence evaluation,
- external screening workflow with AIPAMPDS,
- reproducible saving of checkpoints, vocabulary, splits, and analysis tables.

This repository does **not** claim wet-lab validation or real biological efficacy. All results are strictly **in-silico**.

## Project idea

The goal of the project is to generate peptide sequences that look like plausible AMPs and can be steered toward selected activity conditions.

We model each peptide as:

- a character-level amino-acid sequence,
- its sequence length,
- a 7-dimensional binary condition vector

```text
[
  is_antibacterial,
  is_anti_gram_positive,
  is_anti_gram_negative,
  is_antifungal,
  is_antiviral,
  is_antiparasitic,
  is_anticancer
]
```

The generative backbone is a conditional VAE trained on AMP sequences.  
Evaluation is split into three layers:

1. **reconstruction and generation diagnostics**,
2. **internal classifier-based condition adherence**,
3. **external screening with AIPAMPDS**.

This separation is intentional: generation loss alone does not tell us whether sampled peptides follow the requested biological condition.

## Repository structure

```text
AMPs-via-VAE/
├── Data/
│   ├── raw_data/
│   │   ├── parser_APD6_DB.py
│   │   ├── parser_CAMP4_DB.py
│   │   ├── c_vector.py
│   │   └── preprocessing.py
│   ├── processed/
│   │   ├── master_dataset.csv
│   │   └── other intermediate CSV files
│   └── notebooks/
│       ├── 01_cVAE_preprocess_apd6.ipynb
│       └── class_imbalance_analysis_cvector.ipynb
├── model_training/
│   ├── data/
│   │   ├── preprocessed/
│   │   └── aipampds/
│   ├── models/
│   │   ├── best_cvae.pt / best_vae.pt
│   │   ├── internal_classifier.pt
│   │   ├── tuned_thresholds.json
│   │   └── other saved artifacts
│   ├── models_artifacts/
│   │   ├── best_cvae.pt
│   │   ├── vocab.pkl
│   │   ├── cvae_config.json
│   │   ├── split_indices.pkl
│   │   └── training_history.pkl
│   └── notebooks/
│       ├── cvae_training.ipynb
│       ├── cvae_post_training_analysis.ipynb
│       ├── internal_classifier_adherence.ipynb
│       └── external_classifier_screening.ipynb
├── docs/
├── README.md
├── requirements.txt
└── .gitignore
```

## Data pipeline

The project uses public AMP sources and converts them into a unified peptide-level dataset.

Main preprocessing steps:

1. parse and collect peptide records,
2. normalize sequence strings,
3. extract activity labels from text annotations,
4. build the 7-label condition vector,
5. filter to canonical amino acids,
6. deduplicate by sequence,
7. save a cleaned master dataset for modeling.

The resulting dataset is used both for generator training and for later evaluation notebooks.

## Modeling overview

### 1. cVAE generator

The main generator is a **GRU-based conditional VAE**.

High-level design:

- character-level embedding layer,
- GRU encoder,
- latent posterior parameterization `(mu, logvar)`,
- reparameterization trick,
- autoregressive GRU decoder,
- conditioning through the activity vector `c`.

The decoder is conditioned on both the sampled latent vector and the activity vector.  
Training uses:

- token-level reconstruction loss,
- KL regularization,
- KL warmup,
- gradient clipping,
- early stopping.

Artifacts saved after training:

- vocabulary,
- model checkpoint,
- configuration,
- deterministic split indices,
- training history.

### 2. Post-training analysis

The analysis notebook is separated from training and reloads only the saved artifacts.

It covers:

- reconstruction token accuracy and exact-match rate,
- generation validity / uniqueness / novelty,
- real vs generated sequence comparison,
- amino-acid composition,
- physicochemical properties,
- latent-space visualization with t-SNE,
- interpolation trajectories,
- export of summary CSV files for the final report.

### 3. Internal classifier

A separate **BiLSTM-based multi-label classifier** is trained on the project dataset.

Its purpose is not to serve as ground truth.  
Its purpose is to provide a **separate internal evaluator** for:

- label ranking quality,
- threshold tuning under imbalance,
- condition-adherence scoring of generated peptides,
- candidate reranking.

### 4. External screening

The notebook `external_classifier_screening.ipynb` supports external screening with **AIPAMPDS**.

Workflow:

1. generate peptides for supported conditions,
2. export FASTA and metadata,
3. upload the batch to AIPAMPDS,
4. download the screening CSV,
5. merge results back,
6. summarize activity, hemolysis, and species selectivity.

This external step is used as an additional independent signal beyond the in-repo classifier.

## How to run

## 1. Install dependencies

Create and activate a virtual environment, then install the project requirements.

```bash
pip install -r requirements.txt
```

If notebook-specific packages are missing, install them in the same environment.

## 2. Run preprocessing

Use the scripts under `Data/raw_data/` and the preprocessing notebooks to build the cleaned dataset.

Expected output:

- cleaned peptide table,
- extracted label columns,
- merged master dataset.

## 3. Train the cVAE

Open:

```text
model_training/notebooks/cvae_training.ipynb
```

This notebook:

- loads the cleaned dataset,
- builds the tokenizer,
- creates deterministic train/val/test splits,
- trains the GRU-based cVAE,
- saves all artifacts to `model_training/models_artifacts/`.

## 4. Run post-training analysis

Open:

```text
model_training/notebooks/cvae_post_training_analysis.ipynb
```

This notebook:

- reloads the saved cVAE,
- reproduces the same dataset split,
- computes reconstruction and generation diagnostics,
- compares real and generated peptides,
- exports analysis tables.

## 5. Train the internal classifier and score adherence

Open:

```text
model_training/notebooks/internal_classifier_adherence.ipynb
```

This notebook:

- trains the internal multi-label classifier,
- evaluates held-out classification quality,
- tunes decision thresholds,
- reloads the cVAE,
- scores generated peptides for requested-condition adherence.

## 6. Run external screening workflow

Open:

```text
model_training/notebooks/external_classifier_screening.ipynb
```

This notebook:

- reloads the cVAE,
- generates peptides for externally supported conditions,
- exports FASTA and metadata for AIPAMPDS,
- loads the downloaded AIPAMPDS CSV,
- computes condition-level external metrics.

## Notes on reproducibility

The repository tries to keep downstream analysis reproducible by saving:

- token vocabulary,
- model configuration,
- split indices,
- training history,
- checkpoints,
- exported analysis tables.

The post-training notebook is analysis-only and does not retrain the generator.

## Main limitations

This project is a compact course implementation, not a production biological design platform.

Current limitations:

- no wet-lab validation,
- no homology-aware split in the internal classifier baseline,
- strong class imbalance for several labels,
- external screening is still model-based, not experimental,
- condition control is useful but not fully disentangled.

## Safety note

The repository is intended for **educational and research purposes only**.

Generated peptides are evaluated only with computational proxies.  
No sequence in this repository should be interpreted as a validated antimicrobial candidate or a medical recommendation.

## Authors

- Artem Panov
- Anastasiia Ozerova
