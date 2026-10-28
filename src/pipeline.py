"""
pipeline.py
-----------
Orchestrates the full data workflow in the correct order.

Think of this as the project manager — it delegates each task
to the right specialist class and coordinates the sequence.

Pipeline steps:
    1. Validate  — confirm all input files exist
    2. Load      — read raw CSVs into DataFrames
    3. Clean     — standardize codes and fix time formats
    4. Merge     — join airlines + airports into flights
    5. Engineer  — add feature flags and derived columns
    6. Save      — write the final dataset to outputs/

Design decision: keeping each step in its own class means if one
step needs to change (e.g. a new data source), only that class
is affected. The pipeline itself stays the same.
"""

import time
import pandas as pd

from src.config    import ProjectConfig
from src.loader    import DataLoader
from src.cleaner   import FlightCleaner
from src.merger    import FlightMerger
from src.features  import FeatureEngineer


class FlightDataPipeline:
    """
    FlightDataPipeline runs the entire data preparation workflow.

    Each processing stage is a separate object, making the code
    modular, testable, and easy to extend.
    """

    def __init__(self, cfg: ProjectConfig) -> None:
        """
        Constructor: stores config and initializes all processing stages.
        """
        self.cfg      = cfg
        self.loader   = DataLoader(cfg)
        self.cleaner  = FlightCleaner(cfg)
        self.merger   = FlightMerger()
        self.engineer = FeatureEngineer(cfg)

    def _step(self, number: int, description: str) -> None:
        """
        Prints a formatted step header.
        Makes terminal output easy to read at a glance.
        """
        print(f"\nStep {number}: {description}")
        print("-" * 45)

    def run(self) -> pd.DataFrame:
        """
        Executes the full pipeline and returns the final DataFrame.
        Times the total run so we know how long the pipeline takes.
        """
        start_time = time.time()
        print("\n" + "=" * 45)
        print("   Flight Data Pipeline — Starting")
        print("=" * 45)

        # STEP 1: VALIDATE
        self._step(1, "Validating input files...")
        self.cfg.validate()

        # STEP 2: LOAD
        self._step(2, "Loading raw datasets...")
        flights, airports, airlines = self.loader.load()

        # STEP 3: CLEAN
        self._step(3, "Cleaning data...")
        flights, airports, airlines = self.cleaner.clean_keys(
            flights, airports, airlines
        )
        flights = self.cleaner.clean_times(flights)

        # STEP 4: MERGE
        self._step(4, "Merging datasets...")
        df = self.merger.merge_airlines(flights, airlines)
        df = self.merger.merge_airports(df, airports)

        # STEP 5: FEATURE ENGINEERING
        self._step(5, "Engineering features...")
        df = self.engineer.add_flags(df)

        # STEP 6: SAVE
        self._step(6, "Saving final dataset...")
        self.cfg.outputs_dir.mkdir(exist_ok=True)
        df.to_csv(self.cfg.output_path, index=False)
        print(f"  Saved to: {self.cfg.output_path}")

        # SUMMARY
        elapsed = time.time() - start_time
        print("\n" + "=" * 45)
        print("   Pipeline Complete")
        print(f"   Final shape : {df.shape[0]:,} rows x {df.shape[1]} columns")
        print(f"   Time elapsed: {elapsed:.1f} seconds")
        print("=" * 45)

        return df