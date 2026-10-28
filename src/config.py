# config.py
# Stores all project settings in one place.
# Using a dataclass keeps settings organized and prevents accidental changes.

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    """
    ProjectConfig holds all configuration values for the pipeline.

    frozen=True means values cannot be changed after creation,
    which prevents accidental bugs from modifying settings mid-run.

    Design decision: centralizing paths and constants here means
    if the folder structure ever changes, we only update ONE file.
    """

    base_dir: Path

    # Bad codes that appear in CSV columns instead of real values.
    # frozenset is immutable (cannot be changed), safer than a regular set.
    bad_codes: frozenset = frozenset({"NAN", "NA", "NONE", "", "NULL"})

    # A flight is considered delayed if arrival delay exceeds this (minutes).
    delay_threshold_minutes: int = 15

    # ---------------------------------------------------------------
    # Input file paths — built from base_dir so nothing is hardcoded
    # ---------------------------------------------------------------

    @property
    def flight_path(self) -> Path:
        """Path to the raw flights CSV."""
        return self.base_dir / "data" / "flights.csv"

    @property
    def airports_path(self) -> Path:
        """Path to the airports reference CSV."""
        return self.base_dir / "data" / "airports.csv"

    @property
    def airlines_path(self) -> Path:
        """Path to the airlines reference CSV."""
        return self.base_dir / "data" / "airlines.csv"

    # ---------------------------------------------------------------
    # Output paths
    # ---------------------------------------------------------------

    @property
    def outputs_dir(self) -> Path:
        """Directory where all output files are saved."""
        return self.base_dir / "outputs"

    @property
    def output_path(self) -> Path:
        """Path to the final cleaned and merged CSV."""
        return self.outputs_dir / "flights_cleaned.csv"

    # ---------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------

    def validate(self) -> None:
        """
        Checks all required input files exist before the pipeline runs.

        Why this matters: without validation, the pipeline crashes mid-way
        with a confusing error. This gives a clear message immediately.

        Raises FileNotFoundError if any input file is missing.
        """
        required_files = {
            "flights":  self.flight_path,
            "airports": self.airports_path,
            "airlines": self.airlines_path,
        }

        for name, path in required_files.items():
            if not path.exists():
                raise FileNotFoundError(
                    f"[Config] Missing {name} file: {path}\n"
                    f"Please make sure '{path.name}' is in the data/ folder."
                )

        print("  All input files found. Validation passed.")
        