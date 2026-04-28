"""
Aid allocation optimizer for data-driven NGO resource distribution.
Allocates limited aid budgets across beneficiary groups using need scores and constraints.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from scipy.optimize import linprog
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available. Falling back to greedy allocation.")


@dataclass
class BeneficiaryGroup:
    group_id: str
    name: str
    population: int
    need_score: float       # 0-100, higher means more need
    current_coverage: float # fraction already covered 0-1
    priority_category: str  # critical, high, medium, low
    region: str
    max_allocation: Optional[float] = None  # cap per group


@dataclass
class AllocationResult:
    group_id: str
    name: str
    allocated_budget: float
    allocated_per_capita: float
    coverage_after: float
    need_score: float
    priority_category: str


class AidAllocationOptimizer:
    """
    Distributes a total aid budget across beneficiary groups.
    Supports need-weighted greedy allocation and LP-based optimal allocation.
    Enforces regional caps and minimum coverage thresholds.
    """

    PRIORITY_WEIGHTS = {"critical": 4.0, "high": 2.5, "medium": 1.5, "low": 1.0}

    def __init__(self, total_budget: float, cost_per_person: float = 50.0,
                 min_coverage_threshold: float = 0.1):
        self.total_budget = total_budget
        self.cost_per_person = cost_per_person
        self.min_coverage_threshold = min_coverage_threshold
        self.groups: List[BeneficiaryGroup] = []
        self.results: List[AllocationResult] = []

    def add_group(self, group: BeneficiaryGroup) -> None:
        self.groups.append(group)

    def load_from_dataframe(self, df: pd.DataFrame) -> None:
        required = ["group_id", "name", "population", "need_score",
                    "current_coverage", "priority_category", "region"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        for _, row in df.iterrows():
            self.add_group(BeneficiaryGroup(
                group_id=str(row["group_id"]),
                name=str(row["name"]),
                population=int(row["population"]),
                need_score=float(row["need_score"]),
                current_coverage=float(row["current_coverage"]),
                priority_category=str(row["priority_category"]),
                region=str(row["region"]),
                max_allocation=float(row["max_allocation"]) if "max_allocation" in df.columns else None,
            ))

    def _compute_weights(self) -> np.ndarray:
        weights = []
        for g in self.groups:
            uncovered = max(0.0, 1.0 - g.current_coverage)
            priority_w = self.PRIORITY_WEIGHTS.get(g.priority_category.lower(), 1.0)
            w = (g.need_score / 100.0) * uncovered * priority_w * g.population
            weights.append(w)
        total_w = sum(weights) or 1.0
        return np.array([w / total_w for w in weights])

    def greedy_allocate(self) -> List[AllocationResult]:
        """Distribute budget proportional to need-weighted population scores."""
        weights = self._compute_weights()
        raw_allocations = weights * self.total_budget
        results = []
        for g, alloc in zip(self.groups, raw_allocations):
            if g.max_allocation is not None:
                alloc = min(alloc, g.max_allocation)
            people_reached = alloc / self.cost_per_person
            new_coverage = min(1.0, g.current_coverage + people_reached / g.population)
            results.append(AllocationResult(
                group_id=g.group_id,
                name=g.name,
                allocated_budget=round(alloc, 2),
                allocated_per_capita=round(alloc / g.population, 4),
                coverage_after=round(new_coverage, 4),
                need_score=g.need_score,
                priority_category=g.priority_category,
            ))
        self.results = results
        return results

    def lp_allocate(self) -> List[AllocationResult]:
        """
        Use linear programming to maximize weighted coverage gain subject to budget.
        Falls back to greedy if scipy is unavailable.
        """
        if not SCIPY_AVAILABLE:
            logger.warning("scipy unavailable, using greedy allocation.")
            return self.greedy_allocate()
        n = len(self.groups)
        priority_w = np.array([self.PRIORITY_WEIGHTS.get(g.priority_category.lower(), 1.0)
                                for g in self.groups])
        pop = np.array([g.population for g in self.groups], dtype=float)
        # Maximize sum(priority_w[i] * alloc[i] / (cost_per_person * pop[i]))
        # Equivalent: minimize negated objective
        c = -(priority_w / (self.cost_per_person * pop))
        # Budget constraint: sum(alloc) <= total_budget
        A_ub = np.ones((1, n))
        b_ub = np.array([self.total_budget])
        bounds = []
        for g in self.groups:
            max_possible = (1.0 - g.current_coverage) * g.population * self.cost_per_person
            upper = min(max_possible, g.max_allocation) if g.max_allocation else max_possible
            bounds.append((0, upper))
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
        if not res.success:
            logger.warning("LP solver did not converge: %s. Falling back to greedy.", res.message)
            return self.greedy_allocate()
        results = []
        for g, alloc in zip(self.groups, res.x):
            people_reached = alloc / self.cost_per_person
            new_coverage = min(1.0, g.current_coverage + people_reached / g.population)
            results.append(AllocationResult(
                group_id=g.group_id,
                name=g.name,
                allocated_budget=round(float(alloc), 2),
                allocated_per_capita=round(float(alloc) / g.population, 4),
                coverage_after=round(new_coverage, 4),
                need_score=g.need_score,
                priority_category=g.priority_category,
            ))
        self.results = results
        return results

    def coverage_summary(self) -> Dict:
        """Aggregate coverage gains by priority category."""
        if not self.results:
            return {}
        df = pd.DataFrame([r.__dict__ for r in self.results])
        summary = {}
        for cat, grp in df.groupby("priority_category"):
            summary[cat] = {
                "total_budget_allocated": round(grp["allocated_budget"].sum(), 2),
                "avg_coverage_after": round(grp["coverage_after"].mean(), 4),
                "groups": len(grp),
            }
        summary["total"] = {
            "total_budget_allocated": round(df["allocated_budget"].sum(), 2),
            "groups": len(df),
        }
        return summary

    def unmet_need_report(self) -> pd.DataFrame:
        """Identify groups with coverage below the minimum threshold after allocation."""
        if not self.results:
            return pd.DataFrame()
        records = []
        for r in self.results:
            if r.coverage_after < self.min_coverage_threshold:
                records.append({
                    "group_id": r.group_id,
                    "name": r.name,
                    "coverage_after": r.coverage_after,
                    "need_score": r.need_score,
                    "priority_category": r.priority_category,
                })
        return pd.DataFrame(records)


if __name__ == "__main__":
    np.random.seed(42)
    groups_data = pd.DataFrame({
        "group_id": [f"G{i:03d}" for i in range(1, 21)],
        "name": [f"District {i}" for i in range(1, 21)],
        "population": np.random.randint(5000, 50000, 20),
        "need_score": np.random.uniform(30, 95, 20).round(1),
        "current_coverage": np.random.uniform(0.0, 0.4, 20).round(2),
        "priority_category": np.random.choice(["critical", "high", "medium", "low"], 20),
        "region": np.random.choice(["North", "South", "East", "West"], 20),
    })

    optimizer = AidAllocationOptimizer(total_budget=5_000_000, cost_per_person=50.0)
    optimizer.load_from_dataframe(groups_data)
    results = optimizer.lp_allocate()

    result_df = pd.DataFrame([r.__dict__ for r in results])
    print("Allocation results (top 5 by budget):")
    print(result_df.sort_values("allocated_budget", ascending=False).head(5).to_string(index=False))

    print("\nCoverage summary by category:")
    for cat, stats in optimizer.coverage_summary().items():
        print(f"  {cat}: {stats}")

    unmet = optimizer.unmet_need_report()
    print(f"\nGroups below {optimizer.min_coverage_threshold*100:.0f}% coverage: {len(unmet)}")
