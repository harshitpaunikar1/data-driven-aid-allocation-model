# Data-Driven Aid Allocation Model Diagrams

Generated on 2026-04-26T04:29:37Z from README narrative plus project blueprint requirements.

## Country scoring methodology

```mermaid
flowchart TD
    N1["Step 1\nRan discovery with program, finance, M&E teams to define objectives, constraints ("]
    N2["Step 2\nBuilt country-level dataset from public sources (e.g., World Bank, UN, WHO) spanni"]
    N1 --> N2
    N3["Step 3\nNormalized and imputed indicators; reduced redundancy via PCA; set participatory w"]
    N2 --> N3
    N4["Step 4\nScored and clustered countries into peer bands; stress-tested scenarios for shocks"]
    N3 --> N4
    N5["Step 5\nOptimized allocation using linear programming under budget and policy constraints;"]
    N4 --> N5
```

## PCA component contributions

```mermaid
flowchart LR
    N1["Inputs\nMedical PDFs, guidelines, or evidence documents"]
    N2["Decision Layer\nPCA component contributions"]
    N1 --> N2
    N3["User Surface\nOperator-facing UI or dashboard surface described in the README"]
    N2 --> N3
    N4["Business Outcome\nOperating cost per workflow"]
    N3 --> N4
```

## Evidence Gap Map

```mermaid
flowchart LR
    N1["Present\nREADME, diagrams.md, local SVG assets"]
    N2["Missing\nSource code, screenshots, raw datasets"]
    N1 --> N2
    N3["Next Task\nReplace inferred notes with checked-in artifacts"]
    N2 --> N3
```
