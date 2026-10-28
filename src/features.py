"""
features.py
-----------
Adds engineered feature columns to the merged dataset.

Feature engineering means creating NEW columns derived from existing ones.
These new columns make analysis easier and more meaningful.

Features added:
    IS_CANCELLED   — binary flag: was the flight cancelled?
    IS_DIVERTED    — binary flag: was the flight diverted?
    IS_DELAYED     — binary flag: did it arrive more than 15 min late?
    DELAY_CATEGORY — human-readable label for how delayed a flight was
    ROUTE          — origin + destination combined (e.g. "JFK -> LAX")

Design decision: FeatureEngineer uses small private methods (_add_*)
for each feature group. This makes each feature independently readable
and easy to extend without touching unrelated code.
"""

import pandas as pd
import numpy as np
from src.config import ProjectConfig


class FeatureEngineer:
    """
    FeatureEngineer adds derived columns that make analysis cleaner.

    Instead of computing these on-the-fly during analysis,
    we create them once here so every downstream step can reuse them.
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        """
        Constructor: saves config to access the delay threshold.
        """
        self.cfg = cfg

    def _add_binary_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds IS_CANCELLED, IS_DIVERTED, IS_DELAYED as 0/1 columns.

        Using integers (0/1) instead of booleans makes these columns
        directly usable in calculations — e.g. taking the mean gives
        the delay rate as a percentage.
        """
        df["IS_CANCELLED"] = (df["CANCELLED"] == 1).astype(int)
        df["IS_DIVERTED"]  = (df["DIVERTED"]  == 1).astype(int)
        df["IS_DELAYED"]   = (
            df["ARRIVAL_DELAY"] > self.cfg.delay_threshold_minutes
        ).astype(int)
        return df

    def _add_delay_category(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds DELAY_CATEGORY: a human-readable label for delay severity.

        Categories:
            Cancelled     — flight did not operate
            On Time       — arrived within 15 minutes of schedule
            Minor Delay   — 15 to 60 minutes late
            Moderate Delay — 1 to 3 hours late
            Severe Delay  — more than 3 hours late

        Design decision: categories make bar charts and group analysis
        far more readable than raw minute values.
        """
        conditions = [
            df["IS_CANCELLED"] == 1,
            df["ARRIVAL_DELAY"] <= 15,
            df["ARRIVAL_DELAY"] <= 60,
            df["ARRIVAL_DELAY"] <= 180,
            df["ARRIVAL_DELAY"] >  180,
        ]
        labels = ["Cancelled", "On Time", "Minor Delay",
                  "Moderate Delay", "Severe Delay"]

        df["DELAY_CATEGORY"] = np.select(conditions, labels, default="Unknown")
        return df

    def _add_route(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds ROUTE column combining origin and destination.

        Example: ORIGIN=JFK, DESTINATION=LAX -> ROUTE="JFK -> LAX"

        Design decision: combining two columns into one makes route-level
        analysis simpler — group by one column instead of two.
        """
        df["ROUTE"] = df["ORIGIN_AIRPORT"] + " -> " + df["DESTINATION_AIRPORT"]
        return df

    def add_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs all feature engineering steps in sequence.

        Calls each private method so each feature is clearly
        named and independently maintainable.
        """
        df = self._add_binary_flags(df)
        df = self._add_delay_category(df)
        df = self._add_route(df)

        new_cols = ["IS_CANCELLED", "IS_DIVERTED", "IS_DELAYED",
                    "DELAY_CATEGORY", "ROUTE"]
        print(f"  Features added: {', '.join(new_cols)}")
        return df