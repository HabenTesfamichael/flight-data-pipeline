"""
loader.py
---------
Loads the raw CSV files into pandas DataFrames.

Design decision: wrapping file loading in a class makes it easy to
swap data sources later (e.g., loading from a database instead of CSV)
without changing any other file in the project.
"""

import pandas as pd
from pathlib import Path
from src.config import ProjectConfig


class DataLoader:
    """
    DataLoader is responsible for reading the 3 raw datasets:
        - flights.csv
        - airports.csv
        - airlines.csv

    It validates that files exist and reports their shapes
    so we can confirm loading worked correctly.
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        """
        Constructor: saves config so all methods can access file paths.
        """
        self.cfg = cfg

    def _check_file(self, path: Path) -> None:
        """
        Private helper: raises a clear error if a file is missing.

        Design decision: checking files here (not just in config.validate)
        gives a second layer of protection right before reading.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"[DataLoader] File not found: {path}"
            )

    def load(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Reads all 3 CSV files and returns them as DataFrames.

        Returns:
            flights  (pd.DataFrame): raw flight records
            airports (pd.DataFrame): airport reference data
            airlines (pd.DataFrame): airline reference data
        """

        # Check files exist before attempting to read
        self._check_file(self.cfg.flight_path)
        self._check_file(self.cfg.airports_path)
        self._check_file(self.cfg.airlines_path)

        # low_memory=False prevents mixed-type warnings on large files
        flights  = pd.read_csv(self.cfg.flight_path, low_memory=False)
        airports = pd.read_csv(self.cfg.airports_path)
        airlines = pd.read_csv(self.cfg.airlines_path)

        # Report shapes so we can verify loading was successful
        print(f"  Flights  loaded: {flights.shape[0]:>10,} rows x {flights.shape[1]} columns")
        print(f"  Airports loaded: {airports.shape[0]:>10,} rows x {airports.shape[1]} columns")
        print(f"  Airlines loaded: {airlines.shape[0]:>10,} rows x {airlines.shape[1]} columns")

        return flights, airports, airlines