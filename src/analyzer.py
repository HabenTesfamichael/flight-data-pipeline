"""
analyzer.py
-----------
Performs exploratory data analysis (EDA) and prints results.

This file is responsible ONLY for computing and printing statistics.


Design decision: separating analysis from visualization follows the
single responsibility principle. Each class does exactly one thing:
    - FlightAnalyzer  -> computes and prints statistics
    - FlightVisualizer -> creates and saves plots

Three analysis sections:

1) Summary Statistics
   Mean, median, std, min, max for key numeric columns.
   Gives an overall picture of the dataset.

2) Group-wise Analysis
   Statistics broken down by airline, day of week, month, and route.
   Reveals patterns that overall averages hide.

3) Correlation Analysis
   Measures linear relationships between numeric columns.
   e.g. Does a longer departure delay cause a longer arrival delay?
"""

import pandas as pd
import numpy as np
from src.config import ProjectConfig


class FlightAnalyzer:
    """
    FlightAnalyzer computes and prints statistics about the dataset.

    
    """

    def __init__(self, df: pd.DataFrame, cfg: ProjectConfig) -> None:
        """
        Constructor: saves the cleaned DataFrame and config.
        """
        self.df  = df
        self.cfg = cfg

    # ===================================================================
    # SECTION 1 - SUMMARY STATISTICS
    # ===================================================================

    def print_summary_statistics(self) -> None:
        """
        Prints comprehensive summary statistics for the dataset.

        Covers:
            - Dataset overview (rows, airlines, airports, routes)
            - Arrival delay: mean, median, std, min, max
            - Departure delay: mean, median, std
            - Cancellation and diversion rates
            - Distance statistics
            - Best and worst airline for delays
            - Busiest route
        """
        df    = self.df
        total = len(df)

        print("\n" + "=" * 55)
        print("   SECTION 1 - Summary Statistics")
        print("=" * 55)

        # --- Dataset overview ---
        print(f"\n  Total flights        : {total:>12,}")
        print(f"  Total airlines       : {df['AIRLINE_NAME'].nunique():>12,}")
        print(f"  Total airports       : {df['ORIGIN_AIRPORT'].nunique():>12,}")
        print(f"  Total unique routes  : {df['ROUTE'].nunique():>12,}")

        # --- Arrival delay ---
        print("\n  --- Arrival Delay (minutes) ---")
        delay = df["ARRIVAL_DELAY"].dropna()
        print(f"  Mean   : {delay.mean():>8.2f} min")
        print(f"  Median : {delay.median():>8.2f} min")
        print(f"  Std Dev: {delay.std():>8.2f} min")
        print(f"  Min    : {delay.min():>8.2f} min  (earliest arrival)")
        print(f"  Max    : {delay.max():>8.2f} min  (latest arrival)")
        print(f"  % Delayed (>15 min): {(df['IS_DELAYED'].mean()*100):.1f}%")

        # --- Departure delay ---
        print("\n  --- Departure Delay (minutes) ---")
        dep = df["DEPARTURE_DELAY"].dropna()
        print(f"  Mean   : {dep.mean():>8.2f} min")
        print(f"  Median : {dep.median():>8.2f} min")
        print(f"  Std Dev: {dep.std():>8.2f} min")

        # --- Cancellations ---
        print("\n  --- Cancellations ---")
        print(f"  Total cancelled    : {df['IS_CANCELLED'].sum():>10,}")
        print(f"  Cancellation rate  : {df['IS_CANCELLED'].mean()*100:>9.2f}%")

        # --- Diversions ---
        print("\n  --- Diversions ---")
        print(f"  Total diverted     : {df['IS_DIVERTED'].sum():>10,}")
        print(f"  Diversion rate     : {df['IS_DIVERTED'].mean()*100:>9.2f}%")

        # --- Distance ---
        print("\n  --- Flight Distance (miles) ---")
        dist = df["DISTANCE"].dropna()
        print(f"  Mean    : {dist.mean():>8.0f} miles")
        print(f"  Median  : {dist.median():>8.0f} miles")
        print(f"  Shortest: {dist.min():>6.0f} miles")
        print(f"  Longest : {dist.max():>6.0f} miles")

        # --- Best and worst airline ---
        airline_delays = df.groupby("AIRLINE_NAME")["IS_DELAYED"].mean().mul(100)

        print("\n  --- Best & Worst Airline for Delays ---")
        print(f"  Best : {airline_delays.idxmin()} "
              f"- {airline_delays.min():.1f}% delayed")
        print(f"  Worst: {airline_delays.idxmax()} "
              f"- {airline_delays.max():.1f}% delayed")

        # --- Busiest route ---
        busiest = df["ROUTE"].value_counts()
        print("\n  --- Busiest Route ---")
        print(f"  {busiest.idxmax()} - {busiest.max():,} flights")

        print("\n" + "=" * 55)

    # ===================================================================
    # SECTION 2 - GROUP-WISE ANALYSIS
    # ===================================================================

    def print_groupwise_analysis(self) -> None:
        """
        Prints group-wise statistics broken down by key categories.

        Groups analyzed:
            - By airline: delay rate, avg delay, cancellation rate
            - By day of week: avg arrival delay with visual bar
            - By month: avg arrival delay with visual bar
            - Top 10 most delayed routes (min 100 flights)
        """
        df = self.df

        print("\n" + "=" * 55)
        print("   SECTION 2 - Group-wise Analysis")
        print("=" * 55)

        # --- By airline ---
        print("\n  --- Delay & Cancellation Rate by Airline ---")

        airline_stats = df.groupby("AIRLINE_NAME").agg(
            Total_Flights   = ("AIRLINE_NAME", "count"),
            Delay_Rate_Pct  = ("IS_DELAYED",   lambda x: round(x.mean() * 100, 1)),
            Avg_Delay_Min   = ("ARRIVAL_DELAY", lambda x: round(x.mean(), 1)),
            Cancel_Rate_Pct = ("IS_CANCELLED",  lambda x: round(x.mean() * 100, 2)),
        ).sort_values("Delay_Rate_Pct", ascending=False)

        print(f"\n  {'Airline':<35} {'Flights':>8} {'Delay%':>7} "
              f"{'AvgDelay':>9} {'Cancel%':>8}")
        print("  " + "-" * 72)
        for name, row in airline_stats.iterrows():
            print(f"  {name[:33]:<35} {row['Total_Flights']:>8,} "
                  f"{row['Delay_Rate_Pct']:>6.1f}% "
                  f"{row['Avg_Delay_Min']:>8.1f}m "
                  f"{row['Cancel_Rate_Pct']:>7.2f}%")

        # --- By day of week ---
        day_names = {1:"Monday", 2:"Tuesday", 3:"Wednesday",
                     4:"Thursday", 5:"Friday", 6:"Saturday", 7:"Sunday"}
        
        print("\n  --- Average Arrival Delay by Day of Week ---")

        day_stats = (df.groupby("DAY_OF_WEEK")["ARRIVAL_DELAY"]
                     .mean().round(2).reset_index())
        day_stats["Day"] = day_stats["DAY_OF_WEEK"].map(day_names)
        for _, row in day_stats.iterrows():
            bar = "+" * max(0, int(row["ARRIVAL_DELAY"]))
            print(f"  {row['Day']:<12}: {row['ARRIVAL_DELAY']:>6.2f} min  {bar}")

        # --- By month ---
        month_names = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May",  6:"Jun",
                       7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
        
        print("\n  --- Average Arrival Delay by Month ---")

        month_stats = (df.groupby("MONTH")["ARRIVAL_DELAY"]
                       .mean().round(2).reset_index())
        for _, row in month_stats.iterrows():
            bar   = "+" * max(0, int(row["ARRIVAL_DELAY"]))
            month = month_names.get(int(row["MONTH"]), str(int(row["MONTH"])))
            print(f"  {month:<5}: {row['ARRIVAL_DELAY']:>6.2f} min  {bar}")

        # --- Top 10 most delayed routes ---
        print("\n  --- Top 10 Most Delayed Routes (avg arrival delay) ---")
        route_delays = (
            df[df["IS_CANCELLED"] == 0]
            .groupby("ROUTE")["ARRIVAL_DELAY"]
            .agg(["mean", "count"])
            .query("count >= 100")
            .sort_values("mean", ascending=False)
            .head(10).round(1)
        )
        for route, row in route_delays.iterrows():
            print(f"  {route:<15}: {row['mean']:>6.1f} min avg "
                  f"({int(row['count']):,} flights)")

        print("\n" + "=" * 55)

    # ===================================================================
    # SECTION 3 - CORRELATION ANALYSIS
    # ===================================================================

    def print_correlation_analysis(self) -> None:
        """
        Prints correlation matrix between key numeric columns.

        Correlation coefficient r ranges from -1 to +1:
            +1 = perfect positive relationship
             0 = no relationship
            -1 = perfect negative relationship

        Key finding: departure delay vs arrival delay correlation.
        """
        df = self.df

        print("\n" + "=" * 55)
        print("   SECTION 3 - Correlation Analysis")
        print("=" * 55)

        corr_cols   = ["DEPARTURE_DELAY", "ARRIVAL_DELAY", "DISTANCE",
                       "AIR_TIME", "TAXI_OUT", "TAXI_IN"]
        corr_cols   = [c for c in corr_cols if c in df.columns]
        corr_matrix = df[corr_cols].corr().round(3)

        print("\n  Correlation Matrix (Pearson r):")
        print(f"\n  {'':<20}", end="")
        for col in corr_cols:
            print(f"  {col[:12]:>12}", end="")
        print()
        print("  " + "-" * (20 + 14 * len(corr_cols)))
        for row_col in corr_cols:
            print(f"  {row_col:<20}", end="")
            for col in corr_cols:
                print(f"  {corr_matrix.loc[row_col, col]:>12.3f}", end="")
            print()

        if "DEPARTURE_DELAY" in corr_cols and "ARRIVAL_DELAY" in corr_cols:
            r = corr_matrix.loc["DEPARTURE_DELAY", "ARRIVAL_DELAY"]
            print(f"\n  Key finding:")
            print(f"  Departure delay vs Arrival delay: r = {r:.3f}")
            if r > 0.8:
                print(f"  Very strong positive correlation.")
                print(f"  Flights that leave late almost always arrive late.")
            elif r > 0.5:
                print(f"  Moderate positive correlation.")

        print("\n" + "=" * 55)
    # ===================================================================
    # OUTLIER ANALYSIS
    # ===================================================================
    def print_outlier_analysis(self) -> None:
        """
        Identifies outliers in key numeric columns using the IQR method.

           IQR (Interquartile Range) method:
           Q1  = 25th percentile
           Q3  = 75th percentile
           IQR = Q3 - Q1
           Lower fence = Q1 - 1.5 * IQR
           Upper fence = Q3 + 1.5 * IQR
           Any value outside these fences is an outlier.

        Design decision: outliers are documented, not removed.
        These are real flight events, not data errors.
        """
        df = self.df

        print("\n" + "=" * 55)
        print("   SECTION 4 - Outlier Analysis")
        print("=" * 55)

        cols = ["ARRIVAL_DELAY", "DEPARTURE_DELAY", "DISTANCE"]

        for col in cols:
            series = df[col].dropna()
            Q1  = series.quantile(0.25)
            Q3  = series.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            outliers = series[(series < lower) | (series > upper)]
            pct = (len(outliers) / len(series)) * 100

            print(f"\n  --- {col} ---")
            print(f"  Q1            : {Q1:.2f}")
            print(f"  Q3            : {Q3:.2f}")
            print(f"  IQR           : {IQR:.2f}")
            print(f"  Lower fence   : {lower:.2f}")
            print(f"  Upper fence   : {upper:.2f}")
            print(f"  Outliers      : {len(outliers):,} ({pct:.1f}% of flights)")
            print(f"  Min value     : {series.min():.2f}")
            print(f"  Max value     : {series.max():.2f}")
            print(f"  Decision      : Preserved — real events, not data errors")

        print("\n" + "=" * 55)
        

    # ===================================================================
    # RUN ALL
    # ===================================================================

    def run_all(self) -> None:
        """
        Runs all three analysis sections in order.
        """
        print("\n" + "=" * 55)
        print("   Running Flight Data Analysis")
        print("=" * 55)

        self.print_summary_statistics()
        self.print_groupwise_analysis()
        self.print_correlation_analysis()
        self.print_outlier_analysis() 