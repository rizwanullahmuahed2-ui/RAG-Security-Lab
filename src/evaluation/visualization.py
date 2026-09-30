"""Charts from actual results, with arbitrary budgets and multiple seeds."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def generate_all_figures(summary: pd.DataFrame, figures_dir: Path) -> None:
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    if summary.empty:
        return
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})
    for metric, title, filename in [
        ("attack_success_rate", "Attack success / all targeted questions", "poisoning_vs_attack_success.png"),
        ("answer_accuracy", "Answer containment accuracy", "poisoning_vs_accuracy.png"),
        ("attack_success_rate_injected", "Attack success / actually attacked questions", "injected_attack_success.png"),
    ]:
        if metric not in summary:
            continue
        fig, ax = plt.subplots(figsize=(8, 4.8))
        for defense, group in summary.groupby("defense_method"):
            series = group.groupby("poison_count")[metric].agg(["mean", "std"])
            ax.errorbar(series.index, series["mean"], yerr=series["std"].fillna(0), marker="o", capsize=3, label=defense)
        ax.set(xlabel="Injected passages", ylabel=title, title=title + "\nMean across seeds; bars = seed standard deviation", ylim=(-.03, 1.03))
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figures_dir / filename, dpi=150)
        plt.close(fig)
    for count, metric, title, filename in [
        (summary.poison_count.max(), "attack_success_rate", "Attack success at largest tested budget", "defense_vs_attack_success.png"),
        (0, "answer_accuracy", "Clean-data answer containment accuracy", "defense_vs_clean_accuracy.png"),
    ]:
        subset = summary.loc[summary.poison_count == count].groupby("defense_method")[metric].mean()
        if subset.empty:
            continue
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.bar(subset.index, subset.values, color="#246b85")
        ax.set(title=title, ylim=(0, 1.05))
        plt.setp(ax.get_xticklabels(), rotation=12, ha="right", fontsize=8)
        fig.tight_layout()
        fig.savefig(figures_dir / filename, dpi=150)
        plt.close(fig)
