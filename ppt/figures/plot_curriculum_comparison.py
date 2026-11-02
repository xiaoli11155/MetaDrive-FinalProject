from pathlib import Path
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "curriculum_comparison"
OUT.mkdir(parents=True, exist_ok=True)

NF_SCRIPTS = Path(r"C:\Users\ASUS\.codex\skills\nature-figure\scripts")
sys.path.insert(0, str(NF_SCRIPTS))
from audit_panel_alignment import require_matplotlib_panel_alignment


RED = "#C8161D"
DARK_RED = "#8F1016"
GOLD = "#D4AF37"
BLUE = "#4E79A7"
GRAY = "#8A8F98"
LIGHT_GRAY = "#E9E7E3"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    }
)


def save_figure(fig, stem):
    fig.canvas.draw()
    require_matplotlib_panel_alignment(
        fig,
        json_out=str(OUT / f"{stem}.alignment.json"),
        overlay_svg=str(OUT / f"{stem}.alignment.svg"),
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        strict=True,
    )
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def best_checkpoint(path):
    df = pd.read_csv(path)
    return df.sort_values(["success", "mean_reward"], ascending=False).iloc[0]


def outcome_bars(labels, values, title, subtitle, stem, highlight):
    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    y = np.arange(len(labels))
    left = np.zeros(len(labels))
    series = [
        ("成功", values[:, 0], RED),
        ("碰撞", values[:, 1], GOLD),
        ("驶出道路", values[:, 2], GRAY),
    ]
    for name, vals, color in series:
        bars = ax.barh(y, vals, left=left, height=0.52, color=color, label=name)
        for i, (bar, val) in enumerate(zip(bars, vals)):
            if val >= 0.09:
                ax.text(
                    left[i] + val / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0%}",
                    ha="center",
                    va="center",
                    fontsize=12,
                    fontweight="bold" if name == "成功" else "normal",
                    color="white" if name != "碰撞" else "#4A3500",
                )
        left += vals

    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xticks(np.linspace(0, 1, 6), [f"{x:.0%}" for x in np.linspace(0, 1, 6)])
    ax.set_xlabel("100% 回合结果分布")
    ax.tick_params(axis="x", colors="#5B6068")
    ax.set_title(title, loc="left", fontsize=21, fontweight="bold", color=DARK_RED, pad=24)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=11, color="#5B6068")
    ax.legend(ncol=3, loc="lower left", bbox_to_anchor=(0.0, -0.42))
    ax.text(
        1.0,
        -0.43,
        highlight,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=11.5,
        color=RED,
        fontweight="bold",
    )
    fig.subplots_adjust(left=0.25, right=0.98, top=0.76, bottom=0.34)
    save_figure(fig, stem)


def main():
    low_direct = best_checkpoint(ROOT / "metrics/low_density_basic/checkpoint_metrics.csv")
    low_curriculum = best_checkpoint(ROOT / "metrics/low_density_after_no_traffic/checkpoint_metrics.csv")
    low_values = np.array(
        [
            [low_direct.success, low_direct.collision, low_direct.out_of_road],
            [low_curriculum.success, low_curriculum.collision, low_curriculum.out_of_road],
        ],
        dtype=float,
    )
    outcome_bars(
        [
            f"BC → 低密度\n最佳 {int(low_direct.steps/1000)}k 步",
            f"BC → 无交通 → 低密度\n最佳 {int(low_curriculum.steps/1000)}k 步",
        ],
        low_values,
        "低密度：无交通预训练显著提升闭环成功率",
        "各路线按检查点成功率优先、平均奖励次优选取最佳模型；每检查点评估 20 回合",
        "low_density_curriculum_comparison",
        f"成功率 +{(low_curriculum.success-low_direct.success)*100:.0f}%，出界率 −{(low_direct.out_of_road-low_curriculum.out_of_road)*100:.0f}%",
    )

    high = pd.read_csv(ROOT / "metrics/high_density_100_episode_comparison.csv")
    high = high.set_index("experiment").loc[
        ["high_density_basic", "high_density_after_no_traffic", "high_density_after_low_density"]
    ]
    high_values = high[["success", "collision", "out_of_road"]].to_numpy(float)
    outcome_bars(
        [
            "BC → 高密度",
            "BC → 无交通 → 高密度",
            "BC → 无交通 → 低密度 → 高密度",
        ],
        high_values,
        "高密度：逐级课程学习带来最稳定的收益",
        "同一批 100 个随机种子（1000–1099）闭环评估，三条路线具有统一测试口径",
        "high_density_curriculum_comparison",
        f"逐级课程成功率 {high.iloc[2].success:.0%}，较直接训练提升 {(high.iloc[2].success-high.iloc[0].success)*100:.0f}%",
    )


if __name__ == "__main__":
    main()
