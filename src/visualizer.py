"""
visualizer.py
-------------
Creates and saves all project visualizations.

Design decision: FlightVisualizer is separated from FlightAnalyzer
following the single responsibility principle. The analyzer computes
and prints statistics. The visualizer creates and saves plots.
Each class can be run independently or together.

Private builder methods (_bar_chart, _hbar_chart) centralize subplot
creation so changing bar chart styling only requires editing one method
rather than every subplot individually. This eliminated approximately
120 lines of repeated code across 9 figures.

9 figures produced (17 subplots total):

    fig01_airline_performance_dashboard.png  (2x2 grid)
    fig02_time_patterns.png                  (1x2 side by side)
    fig03_delay_histograms.png               (1x2 side by side)
    fig04_delay_boxplots.png                 (1x2 side by side)
    fig05_route_analysis.png                 (1x2 side by side)
    fig06_cancellation_analysis.png          (1x2 side by side)
    fig07_delay_category_distribution.png    (single)
    fig08_departure_vs_arrival_scatter.png   (single)
    fig09_correlation_heatmap.png            (single)
    fig10_distance_histogram.png             (single)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from src.config import ProjectConfig


class FlightVisualizer:
    """
    FlightVisualizer creates and saves all 9 project figures.

    Consistent styling applied across all plots via private builder
    methods that centralize subplot creation logic.
    """

    # ── Colors ────────────────────────────────────────────────────────────
    PRIMARY_COLOR = "#2563EB"   # blue  — delay related
    ACCENT_COLOR  = "#DC2626"   # red   — thresholds and warnings
    NAVY          = "#1E3A5F"   # navy  — titles and headers
    COLORS = [
        "#2563EB", "#16A34A", "#DC2626", "#D97706",
        "#7C3AED", "#0891B2", "#DB2777", "#65A30D",
        "#EA580C", "#0369A1", "#6D28D9", "#047857",
        "#B45309", "#BE185D",
    ]

    # ── Formatters defined once, reused everywhere ────────────────────────
    COMMA_FMT = mticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
    PCT_FMT   = mticker.PercentFormatter()

    # ── Short airline names to prevent overflow on bar charts ─────────────
    AIRLINE_SHORT = {
        "Alaska Airlines Inc."         : "Alaska",
        "American Airlines Inc."       : "American",
        "American Eagle Airlines Inc." : "Am. Eagle",
        "Atlantic Southeast Airlines"  : "Atlantic SE",
        "Delta Air Lines Inc."         : "Delta",
        "Frontier Airlines Inc."       : "Frontier",
        "Hawaiian Airlines Inc."       : "Hawaiian",
        "JetBlue Airways"              : "JetBlue",
        "Skywest Airlines Inc."        : "SkyWest",
        "Southwest Airlines Co."       : "Southwest",
        "Spirit Air Lines"             : "Spirit",
        "United Air Lines Inc."        : "United",
        "US Airways Inc."              : "US Airways",
        "Virgin America"               : "Virgin America",
    }

    def __init__(self, df: pd.DataFrame, cfg: ProjectConfig) -> None:
        """
        Constructor: saves DataFrame and config, creates figures directory,
        and applies consistent matplotlib styling for all plots.
        """
        self.df  = df
        self.cfg = cfg

        self.figures_dir = cfg.outputs_dir / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)

        plt.rcParams.update({
            "figure.facecolor":  "white",
            "axes.facecolor":    "white",
            "axes.spines.top":   False,
            "axes.spines.right": False,
            "font.size":         11,
        })

    def __repr__(self) -> str:
        """
        String representation showing flight count and output directory.
        Useful during presentations and debugging.
        """
        return (
            f"FlightVisualizer("
            f"{len(self.df):,} flights, "
            f"figures_dir='{self.figures_dir}')"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PRIVATE HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _save(self, filename: str, n_subplots: int = 1) -> None:
        """
        Saves the current figure to the figures directory.
        Prints filename and subplot count for terminal confirmation.
        """
        path  = self.figures_dir / filename
        label = "subplot" if n_subplots == 1 else "subplots"
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {filename}  ({n_subplots} {label})")

    def _shorten(self, series: pd.Series) -> pd.Series:
        """
        Maps full airline names to short names using AIRLINE_SHORT.
        Falls back to the original name if not in the dictionary.
        Used consistently across all airline plots.
        """
        return series.map(lambda x: self.AIRLINE_SHORT.get(x, x))

    def _style_ax(self, ax, title, xlabel, ylabel, fontsize=12) -> None:
        """
        Applies consistent title and axis labels to a subplot.
        Ensures every subplot has a title and labeled axes.
        """
        ax.set_title(title, fontsize=fontsize, fontweight="bold", pad=10)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=fontsize - 1)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=fontsize - 1)

    def _bar_labels(self, ax, bars, fmt="{:.1f}",
                    offset=0.3, fontsize=9) -> None:
        """
        Adds value labels on top of every bar.
        Called by _bar_chart so this logic is never repeated directly.
        """
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + offset,
                fmt.format(h),
                ha="center", va="bottom", fontsize=fontsize
            )

    def _bar_chart(
        self, ax, x, values, labels, title, xlabel, ylabel,
        colors=None, rotation=35, formatter=None,
        hline=None, label_fmt="{:.1f}", label_offset=0.3,
        alpha=1.0
    ) -> None:
        """
        Builds a complete vertical bar chart subplot in one call.

        Handles: drawing bars, value labels, x tick labels,
        axis formatter, optional horizontal reference line,
        and title + axis labels.

        Design decision: centralizing bar chart creation means changing
        bar styling (edgecolor, label fontsize, etc.) only requires
        editing this one method rather than every subplot individually.
        This eliminated ~120 lines of repeated code across 9 figures.
        """
        if colors is None:
            colors = self.COLORS[:len(values)]

        bars = ax.bar(x, values, color=colors,
                      edgecolor="white", alpha=alpha)
        self._bar_labels(ax, bars, fmt=label_fmt,
                         offset=label_offset, fontsize=8)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=rotation,
                           ha="right", fontsize=8)

        if formatter:
            ax.yaxis.set_major_formatter(formatter)
        if hline is not None:
            ax.axhline(hline, color="black", linewidth=0.8, linestyle="--")

        self._style_ax(ax, title, xlabel, ylabel)

    def _hbar_chart(
        self, ax, labels, values, title, xlabel, ylabel,
        color=None, value_fmt="{:,.0f}", suffix="",
        formatter=None, alpha=1.0
    ) -> None:
        """
        Builds a complete horizontal bar chart subplot in one call.

        Used for route analysis where labels are too long for vertical
        bars. Inverts y-axis so the largest bar appears at the top.

        Design decision: same centralisation philosophy as _bar_chart —
        horizontal bar styling is defined once and reused everywhere.
        """
        if color is None:
            color = self.PRIMARY_COLOR

        bars = ax.barh(labels, values, color=color,
                       edgecolor="white", alpha=alpha)
        for bar in bars:
            w = bar.get_width()
            ax.text(
                w + max(values) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                value_fmt.format(w) + suffix,
                va="center", fontsize=9
            )

        ax.invert_yaxis()
        if formatter:
            ax.xaxis.set_major_formatter(formatter)
        self._style_ax(ax, title, xlabel, ylabel)

    def _ref_lines(self, ax) -> None:
        """
        Adds the standard on-time and delay threshold reference lines.
        Used on all delay distribution subplots for consistency.
            Black dashed = on time (0 min)
            Red dashed   = delay threshold (15 min)
        """
        ax.axvline(0,  color="black",          linestyle="--",
                   linewidth=1.2, label="On time (0 min)")
        ax.axvline(15, color=self.ACCENT_COLOR, linestyle="--",
                   linewidth=1.2, label="Threshold (15 min)")

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 1 — Airline Performance Dashboard (2x2)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_airline_dashboard(self) -> None:
        """
        2x2 dashboard: complete airline performance overview.

        Top left     — Delay rate (%) per airline
        Top right    — Cancellation rate (%) per airline
        Bottom left  — Average arrival delay (min) per airline
        Bottom right — Summary table of all three metrics

        Design decision: one figure tells the complete airline story.
        Red bars = above 0 (late), blue = below 0 (early).
        Green for cancellations to visually distinguish from delays.
        Summary table gives exact numbers for report referencing.

        Figure 1 in the report.
        """
        df = self.df.copy()
        df["AIRLINE_SHORT"] = self._shorten(df["AIRLINE_NAME"])

        stats = df.groupby("AIRLINE_SHORT").agg(
            Delay_Rate  = ("IS_DELAYED",   lambda x: round(x.mean() * 100, 1)),
            Cancel_Rate = ("IS_CANCELLED",  lambda x: round(x.mean() * 100, 2)),
            Avg_Delay   = ("ARRIVAL_DELAY", lambda x: round(x.mean(), 1)),
        ).sort_values("Delay_Rate", ascending=False).reset_index()

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            "Airline Performance Dashboard — "
            "Delay Rate, Cancellation Rate & Avg Delay (2015)",
            fontsize=13, fontweight="bold", color=self.NAVY, y=1.01
        )

        x        = range(len(stats))
        airlines = stats["AIRLINE_SHORT"]

        # Top left: delay rate
        self._bar_chart(
            axes[0, 0], x, stats["Delay_Rate"], airlines,
            "Delay Rate by Airline", "Airline", "Delay Rate (%)",
            colors=self.COLORS[:len(stats)],
            formatter=self.PCT_FMT, label_fmt="{:.1f}%"
        )

        # Top right: cancellation rate
        self._bar_chart(
            axes[0, 1], x, stats["Cancel_Rate"], airlines,
            "Cancellation Rate by Airline", "Airline", "Cancellation Rate (%)",
            colors=["#16A34A"] * len(stats),
            formatter=self.PCT_FMT, label_fmt="{:.2f}%",
            label_offset=0.05, alpha=0.85
        )

        # Bottom left: average delay
        delay_colors = [
            self.ACCENT_COLOR if v > 0 else self.PRIMARY_COLOR
            for v in stats["Avg_Delay"]
        ]
        self._bar_chart(
            axes[1, 0], x, stats["Avg_Delay"], airlines,
            "Average Arrival Delay by Airline", "Airline", "Avg Arrival Delay (min)",
            colors=delay_colors, hline=0,
            label_fmt="{:.1f}", label_offset=0.1
        )

        # Bottom right: summary table
        axes[1, 1].axis("off")
        table_data = [
            [row["AIRLINE_SHORT"],
             f"{row['Delay_Rate']}%",
             f"{row['Cancel_Rate']}%",
             f"{row['Avg_Delay']}m"]
            for _, row in stats.iterrows()
        ]
        tbl = axes[1, 1].table(
            cellText=table_data,
            colLabels=["Airline", "Delay%", "Cancel%", "AvgDelay"],
            cellLoc="center", loc="center",
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1.2, 1.4)
        for j in range(4):
            tbl[0, j].set_facecolor(self.NAVY)
            tbl[0, j].set_text_props(color="white", fontweight="bold")
        for i in range(1, len(table_data) + 1):
            bg = "#F1F5F9" if i % 2 == 0 else "white"
            for j in range(4):
                tbl[i, j].set_facecolor(bg)
        axes[1, 1].set_title("Airline Summary Table",
                              fontsize=12, fontweight="bold", pad=10)

        self._save("fig01_airline_performance_dashboard.png", n_subplots=4)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 2 — Time Patterns (1x2)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_time_patterns(self) -> None:
        """
        Side by side: delay by day of week and by month.

        Left  — Average arrival delay by day of week
        Right — Average arrival delay by month

        Design decision: combining day and month in one figure shows
        the complete temporal picture — weekly and seasonal patterns
        side by side. Red = late on average, blue = early.
        Both subplots built with _bar_chart for consistency.

        Figure 2 in the report.
        """
        day_names = {
            1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu",
            5: "Fri", 6: "Sat", 7: "Sun",
        }
        month_names = {
            1: "Jan",  2: "Feb",  3: "Mar", 4: "Apr",
            5: "May",  6: "Jun",  7: "Jul", 8: "Aug",
            9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
        }

        day_avg = (self.df.groupby("DAY_OF_WEEK")["ARRIVAL_DELAY"]
                   .mean().reset_index())
        day_avg["Day"] = day_avg["DAY_OF_WEEK"].map(day_names)

        month_avg = (self.df.groupby("MONTH")["ARRIVAL_DELAY"]
                     .mean().reset_index())
        month_avg["Month"] = month_avg["MONTH"].map(month_names)

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(
            "Delay Time Patterns — By Day of Week and By Month (2015)",
            fontsize=13, fontweight="bold", color=self.NAVY, y=1.02
        )

        for ax, data, label_col, title, xlabel in [
            (axes[0], day_avg,   "Day",
             "Average Arrival Delay by Day of Week", "Day of Week"),
            (axes[1], month_avg, "Month",
             "Average Arrival Delay by Month",       "Month"),
        ]:
            vals   = data["ARRIVAL_DELAY"].tolist()
            labels = data[label_col].tolist()
            colors = [self.ACCENT_COLOR if v > 0 else self.PRIMARY_COLOR
                      for v in vals]
            self._bar_chart(
                ax, range(len(vals)), vals, labels,
                title, xlabel, "Avg Arrival Delay (minutes)",
                colors=colors, rotation=0, hline=0,
                label_fmt="{:.1f}", label_offset=0.1
            )

        self._save("fig02_time_patterns.png", n_subplots=2)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 3 — Delay Distributions (2x2)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_delay_histograms(self) -> None:
        """
        Side by side histograms: arrival and departure delay distributions.

        Left  — Arrival delay histogram   (clipped -60 to +180 min)
        Right — Departure delay histogram  (clipped -60 to +180 min)

        Histograms are clipped to -60/+180 for readability.
        Extreme outliers beyond this range would compress the scale
        making the main distribution invisible.

        Both subplots use _ref_lines() for consistent on-time and
        threshold reference lines.

        Figure 3 in the report.
        """
        arr_clip = self.df["ARRIVAL_DELAY"].dropna()
        dep_clip = self.df["DEPARTURE_DELAY"].dropna()
        arr_clip = arr_clip[(arr_clip >= -60) & (arr_clip <= 180)]
        dep_clip = dep_clip[(dep_clip >= -60) & (dep_clip <= 180)]

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(
            "Arrival & Departure Delay — Histogram Distribution "
            "(clipped to -60 / +180 min for readability)",
            fontsize=12, fontweight="bold", color=self.NAVY, y=1.02
        )

        # Left: arrival histogram
        axes[0].hist(arr_clip, bins=60, color=self.PRIMARY_COLOR,
                     edgecolor="white", linewidth=0.3)
        self._ref_lines(axes[0])
        axes[0].yaxis.set_major_formatter(self.COMMA_FMT)
        axes[0].legend(fontsize=9)
        self._style_ax(axes[0], "Arrival Delay — Histogram",
                       "Arrival Delay (minutes)", "Number of Flights")

        # Right: departure histogram
        axes[1].hist(dep_clip, bins=60, color=self.COLORS[3],
                     edgecolor="white", linewidth=0.3)
        self._ref_lines(axes[1])
        axes[1].yaxis.set_major_formatter(self.COMMA_FMT)
        axes[1].legend(fontsize=9)
        self._style_ax(axes[1], "Departure Delay — Histogram",
                       "Departure Delay (minutes)", "Number of Flights")

        self._save("fig03_delay_histograms.png", n_subplots=2)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 4 — Delay Box Plots (1x2)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_delay_boxplots(self) -> None:
        """
        Side by side box plots: arrival and departure delay full range.

        Left  — Arrival delay box plot   (full range, outliers visible)
        Right — Departure delay box plot  (full range, outliers visible)

        Box plots show the full range including extreme outliers,
        directly supporting the Section 4 outlier analysis:
            ARRIVAL_DELAY:   89,544 outliers (8.9%), max 1,971 min
            IQR = Q3 - Q1 = 12 - (-12) = 24 minutes
            DEPARTURE_DELAY: 116,851 outliers (11.6%), max 1,988 min
            IQR = Q3 - Q1 = 11 - (-5) = 16 minutes

        Horizontal layout gives maximum width for the outlier spread.
        Max value annotated with an arrow for each subplot.

        Figure 4 in the report.
        """
        arr = self.df["ARRIVAL_DELAY"].dropna()
        dep = self.df["DEPARTURE_DELAY"].dropna()

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(
            "Arrival & Departure Delay — Box Plots "
            "(full range showing all outliers)",
            fontsize=12, fontweight="bold", color=self.NAVY, y=1.02
        )

        shared_props = dict(
            vert=False, patch_artist=True,
            flierprops=dict(marker=".", color=self.ACCENT_COLOR,
                            alpha=0.25, markersize=2),
            medianprops=dict(color="white", linewidth=2.5),
        )

        # Left: arrival box plot
        axes[0].boxplot(
            arr, **shared_props,
            boxprops=dict(facecolor=self.PRIMARY_COLOR, alpha=0.85),
            whiskerprops=dict(color=self.PRIMARY_COLOR, linewidth=1.8),
            capprops=dict(color=self.PRIMARY_COLOR, linewidth=1.8),
        )
        self._ref_lines(axes[0])
        axes[0].set_yticks([])
        axes[0].legend(fontsize=9)
        axes[0].annotate(
            f"Max: {int(arr.max()):,} min  ({int(arr.max())//60}h {int(arr.max())%60}m)",
            xy=(arr.max(), 1), xytext=(arr.max() * 0.5, 1.38),
            fontsize=9, color=self.ACCENT_COLOR, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=self.ACCENT_COLOR, lw=1.4)
        )
        axes[0].annotate(
            f"IQR: Q1=-12  Median=-3  Q3=+12",
            xy=(0, 1), xytext=(arr.max() * 0.3, 0.62),
            fontsize=8, color=self.PRIMARY_COLOR,
        )
        self._style_ax(axes[0],
                       "Arrival Delay — Box Plot"
                       "89,544 outliers (8.9% of flights)",
                       "Arrival Delay (minutes)", "")

        # Right: departure box plot
        axes[1].boxplot(
            dep, **shared_props,
            boxprops=dict(facecolor=self.COLORS[3], alpha=0.85),
            whiskerprops=dict(color=self.COLORS[3], linewidth=1.8),
            capprops=dict(color=self.COLORS[3], linewidth=1.8),
        )
        self._ref_lines(axes[1])
        axes[1].set_yticks([])
        axes[1].legend(fontsize=9)
        axes[1].annotate(
            f"Max: {int(dep.max()):,} min  ({int(dep.max())//60}h {int(dep.max())%60}m)",
            xy=(dep.max(), 1), xytext=(dep.max() * 0.5, 1.38),
            fontsize=9, color=self.ACCENT_COLOR, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=self.ACCENT_COLOR, lw=1.4)
        )
        axes[1].annotate(
            f"IQR: Q1=-5  Median=-1  Q3=+11",
            xy=(0, 1), xytext=(dep.max() * 0.3, 0.62),
            fontsize=8, color=self.COLORS[3],
        )
        self._style_ax(axes[1],
                       "Departure Delay — Box Plot"
                       "116,851 outliers (11.6% of flights)",
                       "Departure Delay (minutes)", "")

        self._save("fig04_delay_boxplots.png", n_subplots=2)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 4 — Route Analysis (1x2)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_route_analysis(self) -> None:
        """
        Side by side horizontal bars: busiest vs most delayed routes.

        Left  — Top 10 busiest routes by flight count
        Right — Top 10 most delayed routes by avg arrival delay

        Design decision: placing both side by side reveals whether
        high traffic causes delays. Only routes with 100+ flights
        included in delay analysis for statistical reliability.
        Both subplots built with _hbar_chart for consistency.

        Figure 4 in the report.
        """
        busy = (self.df["ROUTE"].value_counts()
                .head(10).reset_index())
        busy.columns = ["Route", "Flights"]

        delayed_routes = (
            self.df[self.df["IS_CANCELLED"] == 0]
            .groupby("ROUTE")["ARRIVAL_DELAY"]
            .agg(["mean", "count"])
            .query("count >= 100")
            .sort_values("mean", ascending=False)
            .head(10).round(1).reset_index()
        )
        delayed_routes.columns = ["Route", "Avg Delay", "Flights"]

        fig, axes = plt.subplots(1, 2, figsize=(16, 7))
        fig.suptitle(
            "Route Analysis — Busiest Routes vs Most Delayed Routes (2015)",
            fontsize=13, fontweight="bold", color=self.NAVY, y=1.02
        )

        self._hbar_chart(
            axes[0], busy["Route"], busy["Flights"],
            "Top 10 Busiest Routes", "Number of Flights", "Route",
            color=self.PRIMARY_COLOR,
            formatter=self.COMMA_FMT
        )

        self._hbar_chart(
            axes[1], delayed_routes["Route"], delayed_routes["Avg Delay"],
            "Top 10 Most Delayed Routes (min 100 flights)",
            "Avg Arrival Delay (minutes)", "Route",
            color=self.ACCENT_COLOR, alpha=0.85,
            value_fmt="{:.1f}", suffix=" min"
        )

        self._save("fig05_route_analysis.png", n_subplots=2)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 5 — Cancellation Analysis (1x2)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_cancellation_analysis(self) -> None:
        """
        Side by side: full cancellation story in one figure.

        Left  — Cancellation reasons (A/B/C/D) breakdown
        Right — Cancellation rate per airline

        Design decision: combining reason and rate tells both sides
        of the cancellation story — why flights cancel and which
        airlines cancel most. Green palette used for all cancellation
        plots to distinguish from delay plots (blue).
        Both subplots built with _bar_chart for consistency.

        Figure 5 in the report.
        """
        reason_map = {
            "A": "Airline/\nCarrier",
            "B": "Weather",
            "C": "National\nAir System",
            "D": "Security",
        }
        cancelled = self.df[self.df["IS_CANCELLED"] == 1].copy()
        cancelled["Reason"] = cancelled["CANCELLATION_REASON"].map(reason_map)
        reason_counts = cancelled["Reason"].value_counts().reset_index()
        reason_counts.columns = ["Reason", "Count"]

        cancel_rate = (
            self.df.groupby("AIRLINE_NAME")["IS_CANCELLED"]
            .mean().mul(100)
            .sort_values(ascending=False)
            .reset_index()
        )
        cancel_rate["Airline"] = self._shorten(cancel_rate["AIRLINE_NAME"])

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(
            "Cancellation Analysis — Reasons and Airline Rates (2015)",
            fontsize=13, fontweight="bold", color=self.NAVY, y=1.02
        )

        green_shades = ["#16A34A", "#22C55E", "#4ADE80", "#86EFAC"]

        # Left: reasons
        self._bar_chart(
            axes[0],
            range(len(reason_counts)),
            reason_counts["Count"],
            reason_counts["Reason"],
            "Flight Cancellations by Reason",
            "Cancellation Reason", "Number of Cancellations",
            colors=green_shades[:len(reason_counts)],
            rotation=0,
            formatter=self.COMMA_FMT,
            label_fmt="{:,.0f}", label_offset=50
        )

        # Right: rate by airline
        self._bar_chart(
            axes[1],
            range(len(cancel_rate)),
            cancel_rate["IS_CANCELLED"],
            cancel_rate["Airline"],
            "Cancellation Rate by Airline",
            "Airline", "Cancellation Rate (%)",
            colors=["#16A34A"] * len(cancel_rate),
            formatter=self.PCT_FMT,
            label_fmt="{:.2f}%", label_offset=0.05,
            alpha=0.85
        )

        self._save("fig06_cancellation_analysis.png", n_subplots=2)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 6 — Delay Category Distribution (single)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_delay_category_distribution(self) -> None:
        """
        Bar chart: flights in each delay category with percentage labels.

        Categories: On Time / Minor / Moderate / Severe / Cancelled.
        Standalone — summarizes all 1,048,575 flights in one clean
        overview and deserves its own dedicated space.
        Built with _bar_chart for consistency.

        Figure 6 in the report.
        """
        order  = ["On Time", "Minor Delay", "Moderate Delay",
                  "Severe Delay", "Cancelled"]
        counts = (self.df["DELAY_CATEGORY"].value_counts()
                  .reindex(order, fill_value=0).reset_index())
        counts.columns = ["Category", "Count"]
        pcts = (counts["Count"] / len(self.df) * 100).round(1).tolist()

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(range(len(counts)), counts["Count"],
                      color=self.COLORS[:len(counts)], edgecolor="white")
        # Custom labels showing percentage instead of raw count
        for bar, pct in zip(bars, pcts):
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 1000,
                    f"{pct}%", ha="center", va="bottom", fontsize=10)

        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels(counts["Category"], rotation=0, fontsize=10)
        ax.yaxis.set_major_formatter(self.COMMA_FMT)
        self._style_ax(ax,
                       "Flight Delay Category Distribution — "
                       "All 1,048,575 Flights (2015)",
                       "Delay Category", "Number of Flights", fontsize=12)

        self._save("fig07_delay_category_distribution.png", n_subplots=1)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 7 — Departure vs Arrival Delay Scatter (single)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_departure_vs_arrival_scatter(self) -> None:
        """
        Scatter plot: departure delay vs arrival delay (r = 0.942).

        Only delayed flights (both > 0) plotted.
        Samples 5,000 points for readability at 1M rows.

        Reference line:
            ON    = airline neither recovered nor lost time
            BELOW = airline recovered time in the air
            ABOVE = airline fell further behind

        Standalone — the r=0.942 correlation pattern needs full space.

        Figure 7 in the report.
        """
        delayed = self.df[
            (self.df["DEPARTURE_DELAY"] > 0) &
            (self.df["ARRIVAL_DELAY"]   > 0)
        ].sample(n=min(5000, len(self.df)), random_state=42)

        fig, ax = plt.subplots(figsize=(9, 8))
        ax.scatter(delayed["DEPARTURE_DELAY"], delayed["ARRIVAL_DELAY"],
                   alpha=0.3, s=10, color=self.PRIMARY_COLOR)

        max_val = min(
            delayed[["DEPARTURE_DELAY", "ARRIVAL_DELAY"]].max().max(), 300)
        ax.plot([0, max_val], [0, max_val],
                color=self.ACCENT_COLOR, linestyle="--",
                linewidth=1.8, label="Dep delay = Arr delay  (r = 0.942)")

        ax.legend(fontsize=10)
        ax.set_xlim(0, 300)
        ax.set_ylim(0, 300)
        self._style_ax(ax,
                       "Departure Delay vs Arrival Delay — "
                       "Very Strong Correlation (r = 0.942)",
                       "Departure Delay (minutes)",
                       "Arrival Delay (minutes)", fontsize=12)

        self._save("fig08_departure_vs_arrival_scatter.png", n_subplots=1)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 8 — Correlation Heatmap (single)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_correlation_heatmap(self) -> None:
        """
        Pearson correlation heatmap for key numeric columns.

        Color scale:
            Dark blue  = strong positive (+1)
            White      = no correlation (0)
            Dark red   = strong negative (-1)

        Cells annotated with exact r value.
        White text used when background is too dark for black text.
        Standalone — too detailed to share space with other plots.

        Figure 8 in the report.
        """
        corr_cols   = ["DEPARTURE_DELAY", "ARRIVAL_DELAY", "DISTANCE",
                       "AIR_TIME", "TAXI_OUT", "TAXI_IN"]
        corr_cols   = [c for c in corr_cols if c in self.df.columns]
        corr_matrix = self.df[corr_cols].corr().round(2)

        fig, ax = plt.subplots(figsize=(9, 7))
        im = ax.imshow(corr_matrix.values, cmap="RdBu", vmin=-1, vmax=1)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        ax.set_xticks(range(len(corr_cols)))
        ax.set_yticks(range(len(corr_cols)))
        ax.set_xticklabels(corr_cols, rotation=30, ha="right", fontsize=9)
        ax.set_yticklabels(corr_cols, fontsize=9)

        for i in range(len(corr_cols)):
            for j in range(len(corr_cols)):
                val   = corr_matrix.values[i, j]
                color = "white" if abs(val) > 0.6 else "black"
                ax.text(j, i, f"{val:.2f}",
                        ha="center", va="center",
                        fontsize=9, color=color)

        self._style_ax(ax,
                       "Correlation Heatmap — Key Flight Variables (Pearson r)",
                       "", "", fontsize=12)

        self._save("fig09_correlation_heatmap.png", n_subplots=1)

    # ═══════════════════════════════════════════════════════════════════════
    # FIGURE 9 — Distance Histogram (single)
    # ═══════════════════════════════════════════════════════════════════════

    def plot_distance_histogram(self) -> None:
        """
        Histogram: distribution of flight distances (miles).

        Standalone — describes route characteristics, a different story
        from delay distributions. Short/medium/long haul boundaries
        marked with reference lines.

        Figure 9 in the report.
        """
        distances = self.df["DISTANCE"].dropna()

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(distances, bins=50, color=self.COLORS[1],
                edgecolor="white", linewidth=0.3)

        ax.axvline(500,  color=self.ACCENT_COLOR, linestyle="--",
                   linewidth=1.5,
                   label="Short/Medium haul boundary (500 mi)")
        ax.axvline(1500, color="#D97706", linestyle="--",
                   linewidth=1.5,
                   label="Medium/Long haul boundary (1,500 mi)")

        ax.legend(fontsize=10)
        ax.xaxis.set_major_formatter(self.COMMA_FMT)
        ax.yaxis.set_major_formatter(self.COMMA_FMT)
        self._style_ax(ax,
                       "Distribution of Flight Distances — "
                       "Short, Medium & Long Haul (2015)",
                       "Distance (miles)", "Number of Flights", fontsize=12)

        self._save("fig10_distance_histogram.png", n_subplots=1)

    # ═══════════════════════════════════════════════════════════════════════
    # RUN ALL
    # ═══════════════════════════════════════════════════════════════════════

    def run_all(self) -> None:
        """
        Generates and saves all 9 figures in order.
        Prints a clean summary at the end.
        """
        print("\n" + "=" * 55)
        print("   FlightVisualizer — Generating All Figures")
        print("=" * 55)
        print()

        self.plot_airline_dashboard()
        self.plot_time_patterns()
        self.plot_delay_histograms()
        self.plot_delay_boxplots()
        self.plot_route_analysis()
        self.plot_cancellation_analysis()
        self.plot_delay_category_distribution()
        self.plot_departure_vs_arrival_scatter()
        self.plot_correlation_heatmap()
        self.plot_distance_histogram()

        print()
        print("=" * 55)
        print("   FlightVisualizer — Complete")
        print("   10 figures saved  |  18 subplots total")
        print(f"   Location: {self.figures_dir}")
        print("=" * 55)