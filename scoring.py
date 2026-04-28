"""
Vulnerability scoring model for aid allocation prioritization.
Computes composite need scores from multi-dimensional indicators using weighted aggregation.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class IndicatorConfig:
    name: str
    weight: float
    higher_is_worse: bool = True  # if True, higher raw values map to higher need
    description: str = ""


class VulnerabilityScorer:
    """
    Computes 0-100 composite vulnerability scores for beneficiary groups.
    Supports configurable indicator weights, normalization, and sensitivity analysis.
    """

    DEFAULT_INDICATORS = [
        IndicatorConfig("poverty_rate_pct", weight=0.30, higher_is_worse=True,
                        description="Percentage of population below poverty line"),
        IndicatorConfig("malnutrition_rate_pct", weight=0.25, higher_is_worse=True,
                        description="Percentage of under-5 children with stunting"),
        IndicatorConfig("access_to_water_pct", weight=0.20, higher_is_worse=False,
                        description="Percentage with safe water access"),
        IndicatorConfig("school_enrollment_pct", weight=0.15, higher_is_worse=False,
                        description="Primary school net enrollment rate"),
        IndicatorConfig("healthcare_access_pct", weight=0.10, higher_is_worse=False,
                        description="Percentage with access to basic healthcare"),
    ]

    def __init__(self, indicators: Optional[List[IndicatorConfig]] = None):
        self.indicators = indicators or self.DEFAULT_INDICATORS
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(i.weight for i in self.indicators)
        if abs(total - 1.0) > 1e-6:
            logger.warning("Indicator weights sum to %.4f, expected 1.0. Normalizing.", total)
            for ind in self.indicators:
                ind.weight = ind.weight / total

    def normalize_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Min-max normalize each indicator column to [0, 1].
        Inverts direction for indicators where lower raw value = higher need.
        """
        result = df.copy()
        for ind in self.indicators:
            col = ind.name
            if col not in result.columns:
                logger.warning("Indicator column not found: %s. Skipping.", col)
                continue
            col_min = result[col].min()
            col_max = result[col].max()
            rng = col_max - col_min
            if rng < 1e-9:
                result[f"{col}_norm"] = 0.5
            else:
                normalized = (result[col] - col_min) / rng
                result[f"{col}_norm"] = normalized if ind.higher_is_worse else 1.0 - normalized
        return result

    def compute_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute a 0-100 weighted composite vulnerability score for each row.
        Adds 'vulnerability_score' and 'score_band' columns.
        """
        df = self.normalize_indicators(df)
        score = np.zeros(len(df))
        for ind in self.indicators:
            norm_col = f"{ind.name}_norm"
            if norm_col in df.columns:
                score += ind.weight * df[norm_col].fillna(0.5).values
        df["vulnerability_score"] = (score * 100).round(2)
        df["score_band"] = pd.cut(
            df["vulnerability_score"],
            bins=[0, 25, 50, 75, 100],
            labels=["low", "medium", "high", "critical"],
            include_lowest=True,
        )
        return df

    def rank_groups(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Return top N most vulnerable groups sorted by score descending."""
        if "vulnerability_score" not in df.columns:
            df = self.compute_composite_score(df)
        return df.sort_values("vulnerability_score", ascending=False).head(top_n).reset_index(drop=True)

    def sensitivity_analysis(self, df: pd.DataFrame, perturb: float = 0.05) -> pd.DataFrame:
        """
        Compute how much the ranking changes when each indicator weight is perturbed by +perturb.
        Returns a DataFrame with rank correlation coefficients per indicator.
        """
        if "vulnerability_score" not in df.columns:
            df = self.compute_composite_score(df.copy())
        base_rank = df["vulnerability_score"].rank(ascending=False)
        records = []
        for ind in self.indicators:
            perturbed = [IndicatorConfig(i.name, i.weight, i.higher_is_worse) for i in self.indicators]
            for p in perturbed:
                if p.name == ind.name:
                    p.weight = min(1.0, p.weight + perturb)
            total_w = sum(p.weight for p in perturbed)
            for p in perturbed:
                p.weight /= total_w
            scorer_p = VulnerabilityScorer(indicators=perturbed)
            df_p = scorer_p.compute_composite_score(df.copy().drop(
                columns=["vulnerability_score", "score_band"], errors="ignore"
            ))
            new_rank = df_p["vulnerability_score"].rank(ascending=False)
            corr = float(base_rank.corr(new_rank, method="spearman"))
            records.append({"indicator": ind.name, "rank_correlation": round(corr, 4)})
        return pd.DataFrame(records).sort_values("rank_correlation")

    def score_summary(self, df: pd.DataFrame) -> Dict:
        """Return distribution statistics for vulnerability scores."""
        if "vulnerability_score" not in df.columns:
            df = self.compute_composite_score(df)
        s = df["vulnerability_score"]
        return {
            "mean": round(float(s.mean()), 2),
            "std": round(float(s.std()), 2),
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "p25": round(float(s.quantile(0.25)), 2),
            "p50": round(float(s.quantile(0.50)), 2),
            "p75": round(float(s.quantile(0.75)), 2),
            "band_distribution": df["score_band"].value_counts().to_dict(),
        }


if __name__ == "__main__":
    np.random.seed(42)
    n = 50
    sample_df = pd.DataFrame({
        "group_id": [f"G{i:03d}" for i in range(1, n + 1)],
        "region": np.random.choice(["North", "South", "East", "West"], n),
        "poverty_rate_pct": np.random.uniform(5, 80, n).round(1),
        "malnutrition_rate_pct": np.random.uniform(5, 60, n).round(1),
        "access_to_water_pct": np.random.uniform(20, 100, n).round(1),
        "school_enrollment_pct": np.random.uniform(40, 100, n).round(1),
        "healthcare_access_pct": np.random.uniform(10, 90, n).round(1),
    })

    scorer = VulnerabilityScorer()
    scored_df = scorer.compute_composite_score(sample_df)
    print("Score distribution:")
    print(scored_df["vulnerability_score"].describe().round(2))
    print("\nTop 10 most vulnerable groups:")
    top = scorer.rank_groups(scored_df, top_n=10)
    print(top[["group_id", "region", "vulnerability_score", "score_band"]].to_string(index=False))
    print("\nScore summary:", scorer.score_summary(scored_df))
    sens = scorer.sensitivity_analysis(sample_df.copy())
    print("\nSensitivity analysis:")
    print(sens.to_string(index=False))
