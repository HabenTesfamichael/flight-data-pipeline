"""
main.py
-------
Entry point for the Flight Data Pipeline project.

Run this file from the project root using:
    python -m src.main
"""



from pathlib import Path
from src.config   import ProjectConfig
from src.pipeline import FlightDataPipeline
from src.analyzer import FlightAnalyzer  
from src.visualizer import FlightVisualizer 


def main() -> None:
    """
    Builds the project config, runs the pipeline, and prints a preview.

    Path explanation:
        __file__              = this file (main.py)
        .resolve()            = absolute path (no ".." ambiguity)
        .parent               = src/ folder
        .parent.parent        = project root folder
    """
    base_dir = Path(__file__).resolve().parent.parent

    # Create config — all paths and constants live here
    cfg = ProjectConfig(base_dir=base_dir)

    # Create and run the pipeline
    pipeline = FlightDataPipeline(cfg)
    df = pipeline.run()

    # Print a preview of the final dataset
    print("\nPreview of final dataset:")
    print(df[["AIRLINE_NAME", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
              "ROUTE", "ARRIVAL_DELAY", "DELAY_CATEGORY",
              "IS_CANCELLED", "IS_DELAYED"]].head(10).to_string())
    
    # Run the analyzer                          
    analyzer = FlightAnalyzer(df, cfg)
    analyzer.run_all()

    # Run the Visualizer
    visualizer = FlightVisualizer (df,cfg)
    visualizer.run_all()


if __name__ == "__main__":   
    main()

   