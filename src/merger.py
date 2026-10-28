"""
merger.py
---------
Joins the three datasets into one unified DataFrame.

Why we merge:
    - flights.csv has codes (e.g. "AA", "JFK") but not names
    - airlines.csv maps codes to full names ("AA" -> "American Airlines")
    - airports.csv maps codes to city, state, and coordinates

After merging, every flight row contains full context about
its airline, origin airport, and destination airport.

Design decision: splitting merge_airlines and merge_airports into
separate methods makes each step independently readable and testable.
"""

import pandas as pd


class FlightMerger:
    """
    FlightMerger joins flights with airline and airport reference data.

    Two merges are performed:
        1. merge_airlines — adds airline name to each flight
        2. merge_airports — adds city/state/coordinates for origin + destination
    """

    def _report_unmatched(self, df: pd.DataFrame, col: str, label: str) -> None:
        """
        Private helper: reports how many rows failed to match during a merge.

        Design decision: unmatched rows silently become NaN after a left join.
        Reporting them here makes merge quality visible so we can catch
        dirty data early rather than discovering it in analysis.
        """
        unmatched = df[col].isnull().sum()
        if unmatched > 0:
            pct = (unmatched / len(df)) * 100
            print(f"  Warning: {unmatched:,} rows ({pct:.1f}%) "
                  f"unmatched on {label}")
        else:
            print(f"  All rows matched on {label}.")

    def merge_airlines(
        self,
        flights: pd.DataFrame,
        airlines: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Adds the full airline name to each flight row.

        flights  has column: AIRLINE   (e.g. "AA")
        airlines has columns: IATA_CODE, AIRLINE

        We rename airlines.AIRLINE -> AIRLINE_NAME to avoid a column
        name clash with flights.AIRLINE (which holds the code).

        Uses a left join so all flights are kept, even if the airline
        code has no match in the reference table.
        """
        airlines_renamed = airlines.rename(columns={"AIRLINE": "AIRLINE_NAME"})

        df = flights.merge(
            airlines_renamed,
            left_on="AIRLINE",
            right_on="IATA_CODE",
            how="left",
        )

        # Drop duplicate IATA_CODE column brought in from airlines
        df = df.drop(columns=["IATA_CODE"], errors="ignore")

        self._report_unmatched(df, "AIRLINE_NAME", "AIRLINE code")
        print(f"  After airline merge: {df.shape[0]:,} rows x {df.shape[1]} columns")
        return df

    def merge_airports(
        self,
        df: pd.DataFrame,
        airports: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Adds city, state, and coordinates for both origin and destination.

        We merge airports TWICE using add_prefix() to avoid column clashes.
        suffixes=("", "_ref") ensures the original ORIGIN_AIRPORT column
        in flights is preserved and the duplicate from airports is dropped.
        """

        # --- Merge origin airport info ---
        df = df.merge(
            airports.add_prefix("ORIGIN_"),
            left_on="ORIGIN_AIRPORT",
            right_on="ORIGIN_IATA_CODE",
            how="left",
            suffixes=("", "_ref"),
        )
        df = df.drop(columns=["ORIGIN_IATA_CODE", "ORIGIN_AIRPORT_ref"],
                     errors="ignore")
        self._report_unmatched(df, "ORIGIN_CITY", "ORIGIN_AIRPORT code")

        # --- Merge destination airport info ---
        df = df.merge(
            airports.add_prefix("DEST_"),
            left_on="DESTINATION_AIRPORT",
            right_on="DEST_IATA_CODE",
            how="left",
            suffixes=("", "_ref"),
        )
        df = df.drop(columns=["DEST_IATA_CODE", "DEST_AIRPORT_ref"],
                     errors="ignore")
        self._report_unmatched(df, "DEST_CITY", "DESTINATION_AIRPORT code")

        print(f"  After airport merge: {df.shape[0]:,} rows x {df.shape[1]} columns")
        return df