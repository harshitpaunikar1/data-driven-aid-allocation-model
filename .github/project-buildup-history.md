# Project Buildup History: Data-Driven Aid Allocation Model

- Repository: `data-driven-aid-allocation-model`
- Category: `product_case_study`
- Subtype: `optimization`
- Source: `project_buildup_2021_2025_daily_plan_extra.csv`
## 2024-09-02 - Day 2: Problem scoping

- Task summary: Started the Data-Driven Aid Allocation Model case study properly today. The problem involves allocating emergency aid to geographies affected by a crisis, where the goal is to maximize people-hours of relief per dollar spent while respecting logistical constraints. Spent today formalizing the objective function and constraints based on real NGO allocation frameworks. Also gathered historical data on aid delivery efficiency by region and intervention type to use as impact estimates.
- Deliverable: Problem formalized. Objective function written. Historical efficiency data gathered.
## 2024-09-09 - Day 3: Optimization model

- Task summary: Built the core optimization model for the Aid Allocation case study. Used a linear programming formulation with the scipy solver. The model takes budget as input and outputs the recommended allocation across six intervention categories and four geographic zones. Ran it at three budget levels to show how the allocation strategy changes — at low budget it concentrates, at high budget it spreads more evenly due to diminishing returns constraints.
- Deliverable: LP model complete. Allocation shown at three budget levels. Diminishing returns captured.
## 2024-09-09 - Day 3: Optimization model

- Task summary: The solver was returning slightly negative values for some allocation variables due to floating point issues — added a clamp to zero to handle this cleanly.
- Deliverable: Floating point clamp added to allocation outputs.
## 2024-09-09 - Day 3: Optimization model

- Task summary: Added a constraint validation step that checks if the input data is feasible before calling the solver, to avoid cryptic solver errors when inputs are bad.
- Deliverable: Input feasibility check added before solver call.
## 2024-10-28 - Day 4: Presentation layer

- Task summary: Built the presentation layer for the Aid Allocation case study today. The optimization model output is not self-explanatory to a non-technical audience, so wrote a detailed narrative explaining the recommended allocation, why the model chose each zone and intervention category, and how confident the recommendation is given the uncertainty in impact estimates. Also created a one-page summary intended for a decision-maker briefing.
- Deliverable: Narrative explanation and one-page briefing summary written.
## 2024-12-02 - Day 5: Repository cleanup

- Task summary: Did a thorough repository cleanup for the Data-Driven Aid Allocation Model. Removed intermediate scratch notebooks, organized the data directory, made sure the requirements file was complete and accurate, and wrote setup instructions that I verified worked from scratch. Also added a brief note on the model's limitations — particularly that the impact estimates come from historical data and may not generalize to novel crisis types.
- Deliverable: Repository cleaned. Setup instructions verified. Limitations section added.
