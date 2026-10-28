"""
cleaner.py
----------
Cleans and standardizes raw data before merging and analysis.

Two types of cleaning are performed:

1) Code cleaning (clean_keys):
   Standardizes airport and airline IATA codes so merges work correctly.
   " jfk ", "Jfk", "JFK" all become "JFK".

2) Time cleaning (clean_times):
   Converts HHMM integer time columns into readable "HH:MM" strings.
   5 -> "00:05", 830 -> "08:30", 2354 -> "23:54"

Design decision: ALL raw data formatting issues are fixed here,
before any merging or feature engineering happens. This follows
the single responsibility principle — cleaner.py fixes data quality,
features.py creates new columns from already-clean data.
"""

import numpy as np
import pandas as pd
from src.config import ProjectConfig


class FlightCleaner:
    """
    FlightCleaner standardizes airport/airline codes and fixes
    time column formatting so downstream steps work correctly.
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        """
        Constructor: saves config to access bad_codes.
        """
        self.cfg = cfg

    # -------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------

    def _clean_code_series(self, s: pd.Series) -> pd.Series:
        """
        Private helper: cleans ONE column (Series) of IATA codes.

        Steps:
            1. Convert to string  →  handles any numeric values
            2. Strip whitespace   →  " JFK " becomes "JFK"
            3. Uppercase          →  "jfk" becomes "JFK"
            4. Replace bad codes  →  "NA", "NONE", "" become NaN
        """
        s = s.astype(str)
        s = s.str.strip()
        s = s.str.upper()
        s = s.where(~s.isin(self.cfg.bad_codes), np.nan)
        return s

    def _hhmm_to_str(self, series: pd.Series) -> pd.Series:
        """
        Private helper: converts HHMM integer format to "HH:MM" string.

        Why this is needed:
            Raw time columns store times as plain integers with no
            leading zeros or colons. This makes them confusing to read
            and impossible to use in time-based calculations directly.

        Examples:
            5    -> "00:05"   (12:05 AM)
            830  -> "08:30"   (8:30 AM)
            1200 -> "12:00"   (noon)
            2354 -> "23:54"   (11:54 PM)

        Steps:
            1. Fill NaN with 0 and convert to integer
            2. Extract hours   — integer divide by 100
            3. Extract minutes — remainder after dividing by 100
            4. Zero-pad both   — ensures "08" not "8"
            5. Join with ":"
        """
        series  = series.fillna(0).astype(int)
        hours   = series // 100
        minutes = series %  100
        return (
            hours.astype(str).str.zfill(2)
            + ":"
            + minutes.astype(str).str.zfill(2)
        )

    def _report_missing(self, df: pd.DataFrame, label: str) -> None:
        """
        Private helper: prints a missing value summary for a DataFrame.

        Design decision: making missing values visible during cleaning
        helps catch data quality problems early, before they silently
        affect analysis results.
        """
        missing = df.isnull().sum()
        missing = missing[missing > 0]

        if missing.empty:
            print(f"    [{label}] No missing values found.")
        else:
            print(f"    [{label}] Missing values:")
            for col, count in missing.items():
                pct = (count / len(df)) * 100
                print(f"      - {col}: {count:,} missing ({pct:.1f}%)")

    # -------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------

    def clean_keys(
        self,
        flights: pd.DataFrame,
        airports: pd.DataFrame,
        airlines: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Cleans IATA code columns in all three datasets.

        Works on copies — original DataFrames are never modified.
        This is called immutability: raw data stays intact for debugging.

        Returns:
            Cleaned copies of (flights, airports, airlines).
        """
        flights  = flights.copy()
        airports = airports.copy()
        airlines = airlines.copy()

        # --- Clean airport and airline codes in flights ---
        flights["ORIGIN_AIRPORT"]      = self._clean_code_series(flights["ORIGIN_AIRPORT"])
        flights["DESTINATION_AIRPORT"] = self._clean_code_series(flights["DESTINATION_AIRPORT"])
        flights["AIRLINE"]             = self._clean_code_series(flights["AIRLINE"])

        # --- Clean IATA codes in reference tables ---
        airports["IATA_CODE"] = self._clean_code_series(airports["IATA_CODE"])
        airlines["IATA_CODE"] = self._clean_code_series(airlines["IATA_CODE"])
        
        # --- Ensure ARRIVAL_DELAY is numeric ---
        # Cancelled flights have no arrival delay.
        # pd.to_numeric with errors="coerce" converts any non-numeric
        # values to NaN so they are excluded from delay calculations
        # rather than accidentally treated as zero-delay flights.
        flights["ARRIVAL_DELAY"]   = pd.to_numeric(flights["ARRIVAL_DELAY"],   errors="coerce")
        flights["DEPARTURE_DELAY"] = pd.to_numeric(flights["DEPARTURE_DELAY"], errors="coerce")
        # --- Report missing values ---
        print("  Missing value report:")
        self._report_missing(flights,  "Flights")
        self._report_missing(airports, "Airports")
        self._report_missing(airlines, "Airlines")

        print("  Key columns cleaned successfully.")
        return flights, airports, airlines

    def clean_times(self, flights: pd.DataFrame) -> pd.DataFrame:
        """
        Converts all HHMM integer time columns to readable "HH:MM" strings.

        Columns converted:
            SCHEDULED_DEPARTURE, DEPARTURE_TIME, WHEELS_OFF,
            WHEELS_ON, SCHEDULED_ARRIVAL, ARRIVAL_TIME

        Design decision: we overwrite the original columns rather than
        creating new ones because the raw integer format is never useful
        — there is no reason to keep it alongside the readable version.

        Returns:
            flights DataFrame with time columns converted to strings.
        """
        flights = flights.copy()

        time_columns = [
            "SCHEDULED_DEPARTURE",
            "DEPARTURE_TIME",
            "WHEELS_OFF",
            "WHEELS_ON",
            "SCHEDULED_ARRIVAL",
            "ARRIVAL_TIME",
        ]

        for col in time_columns:
            if col in flights.columns:
                flights[col] = self._hhmm_to_str(flights[col])

        print(f"  Time columns converted to HH:MM: {', '.join(time_columns)}")
        return flights