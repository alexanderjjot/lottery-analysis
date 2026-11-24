from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def analyze_lottery_ds(
    csv_file: str | Path,
    last_n_draws: int = 84,
    output_dir: str | Path = "outputs",
) -> pd.DataFrame:
    """
    Exploratory & stochastic analysis of historical lottery draws.
    Computes the 'draws ago' recency metric for each drawn number prior to each draw,
    evaluates descriptive statistics, and derives mean/median centroid vectors.
    """
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {csv_path}")

    df = pd.read_csv(
        csv_path,
        sep=";",
        encoding="utf-8-sig",
        header=0,
        names=["draw_num", "day", "month", "year", "n1", "n2", "n3", "n4", "n5", "col9", "bonus"],
    )
    df = df.dropna(subset=["year", "month", "day", "n1", "n2", "n3", "n4", "n5"]).copy()
    df["date"] = pd.to_datetime(df[["year", "month", "day"]], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    main_cols = ["n1", "n2", "n3", "n4", "n5"]
    last_seen = {num: -1 for num in range(1, 36)}
    history_records = []

    for idx, row in df.iterrows():
        current_numbers = [int(row[col]) for col in main_cols]
        draw_draws_ago = [
            idx if last_seen[num] == -1 else idx - 1 - last_seen[num]
            for num in current_numbers
        ]

        for num in current_numbers:
            last_seen[num] = idx

        history_records.append(
            {
                "draw_num": row["draw_num"],
                "date": row["date"],
                "sum_draws_ago": int(sum(draw_draws_ago)),
                "mean_draws_ago": float(np.mean(draw_draws_ago)),
                "numbers": current_numbers,
                "draws_ago_list": draw_draws_ago,
            }
        )

    df_analysis = pd.DataFrame(history_records)
    recent_df = df_analysis.tail(last_n_draws).copy()
    recent_df["sorted_draws_ago"] = recent_df["draws_ago_list"].apply(sorted)

    # Descriptive statistics
    stats = recent_df["sum_draws_ago"].describe()
    print("=== DATA SCIENCE LOTTERY ANALYSIS ===")
    print(
        f"Window: last {last_n_draws} draws "
        f"({recent_df['date'].min().strftime('%Y-%m-%d')} to {recent_df['date'].max().strftime('%Y-%m-%d')})\n"
    )
    print("--- Descriptive Statistics: Sum of 'Draws Ago' ---")
    print(f"Mean:     {stats['mean']:.2f}")
    print(f"Median:   {stats['50%']:.2f}")
    print(f"Std Dev:  {stats['std']:.2f}")
    print(f"Min / Max:{stats['min']:.0f} / {stats['max']:.0f}")
    print(f"Q1 / Q3:  {stats['25%']:.2f} / {stats['75%']:.2f}\n")

    # Mean & median centroid vectors across sorted positions
    sorted_matrix = np.vstack(recent_df["sorted_draws_ago"].to_numpy())
    mean_centroid = np.mean(sorted_matrix, axis=0)
    median_centroid = np.median(sorted_matrix, axis=0)
    print("--- Sorted Position Centroid Vectors ---")
    print(f"Mean centroid vector:   {np.round(mean_centroid, 2).tolist()}")
    print(f"Median centroid vector: {np.round(median_centroid, 2).tolist()}\n")

    # Summary table
    recent_table = recent_df[["draw_num", "date", "sorted_draws_ago", "sum_draws_ago"]]
    print(f"=== Sorted 'Draws Ago' Breakdown (Last {last_n_draws} Draws) ===")
    print(recent_table.to_string(index=False))
    print("-" * 60)

    # Visualization
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    chart_file = out_path / "lottery_ds_trend.png"

    plt.figure(figsize=(12, 6))
    plt.plot(
        recent_df["date"],
        recent_df["sum_draws_ago"],
        marker="o",
        linestyle="-",
        color="#1f77b4",
        alpha=0.6,
        label="Sum of 'Draws Ago' per draw",
    )
    recent_df["rolling_mean"] = recent_df["sum_draws_ago"].rolling(window=10).mean()
    plt.plot(
        recent_df["date"],
        recent_df["rolling_mean"],
        color="#d62728",
        linewidth=2.5,
        label="10-Draw Rolling Mean",
    )

    plt.title(f"Sum of 'Draws Ago' Dynamics (Last {last_n_draws} Draws)", fontsize=14, fontweight="bold")
    plt.xlabel("Draw Date", fontsize=12)
    plt.ylabel("Sum of 'Draws Ago' (5 Drawn Numbers)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(chart_file, dpi=300)
    plt.close()

    print(f"Chart saved to: {chart_file}")
    return recent_df


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    default_csv = project_root / "data" / "wyniki-pensja-sortowane.csv"
    default_output = project_root / "outputs"
    analyze_lottery_ds(default_csv, last_n_draws=84, output_dir=default_output)