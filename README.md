# Data-Driven Aid Allocation Model

> **Domain:** Financial Analysis

## Overview

NGOs face more needs than budget. Choosing which countries to support and how to split funds is often subjective, constrained by patchy data and shifting crises. Programs compete without a common yardstick, making trade-offs opaque. Fragmented indicators, incomparable baselines, and manual spreadsheets slow decisions. Without a transparent, evidence-led model, funds risk drifting to familiar regions rather than greatest need; duplication across partners grows; response speed drops during emergencies. Donors increasingly expect quantifiable rationale and auditable allocations. The cost of inaction is wasted spend, lower beneficiary coverage, and reputational risk affecting future grants.

## Approach

- Ran discovery with program, finance, M&E teams to define objectives, constraints (ring-fenced funds, minimums), ethical guardrails
- Built country-level dataset from public sources (e.g., World Bank, UN, WHO) spanning poverty, food security, fragility, disaster risk, health access, delivery cost
- Normalized and imputed indicators; reduced redundancy via PCA; set participatory weights using AHP with documented rationale
- Scored and clustered countries into peer bands; stress-tested scenarios for shocks (disasters, conflict spikes, currency swings)
- Optimized allocation using linear programming under budget and policy constraints; generated baseline and alternative splits
- Delivered dashboard with maps, explainability (factor contributions), sensitivity sliders; scheduled monthly refresh and back-tested against historical outcomes

## Skills & Technologies

- Data Engineering
- Indicator Normalization
- Multi-Criteria Decision Analysis
- Principal Component Analysis
- Linear Programming
- Clustering Analysis
- Sensitivity Analysis
- Dashboard Design
