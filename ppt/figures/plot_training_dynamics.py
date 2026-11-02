from pathlib import Path
import re
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "training_dynamics"
OUT.mkdir(parents=True, exist_ok=True)

NF_SCRIPTS = Path(r"C:\Users\ASUS\.codex\skills\nature-figure\scripts")
sys.path.insert(0, str(NF_SCRIPTS))
from audit_panel_alignment import require_matplotlib_panel_alignment


RED = "#C8161D"
DARK_RED = "#8F1016"
GOLD = "#D4AF37"
BLUE = "#4E79A7"
TEAL = "#3A8D8C"
GRAY = "#8A8F98"
GRID = "#E5E2DE"
BC_LINE = "#B28A1C"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 11,
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


def style_axis(ax):
    ax.grid(color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)


def parse_bc_losses(path):
    pattern = re.compile(r"epoch=(\d+) validation_mse=([0-9.]+)")
    rows = []
    raw = path.read_bytes()
    text = raw.decode("utf-16", errors="ignore") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.replace(b"\x00", b"").decode("utf-8", errors="ignore")
    for line in text.splitlines():
        match = pattern.search(line)
        if match:
            rows.append((int(match.group(1)), float(match.group(2))))
    return pd.DataFrame(rows, columns=["epoch", "validation_mse"])


def plot_bc():
    losses = parse_bc_losses(ROOT / "logs/low_density_improved_v2/bc_stdout.log")
    data = np.load(ROOT / "datasets/low_density_traffic_bc/idm_demonstrations.npz")
    actions = data["actions"]

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.2))
    ax = axes[0]
    epochs = losses.epoch.to_numpy(dtype=float)
    mse = losses.validation_mse.to_numpy(dtype=float)
    ax.plot(epochs, mse, color=RED, linewidth=2.7, marker="o", markersize=3.5)
    ax.fill_between(epochs, mse, mse.min() * 0.92, color=RED, alpha=0.09)
    best = losses.loc[losses.validation_mse.idxmin()]
    ax.scatter([best.epoch], [best.validation_mse], s=58, color=GOLD, edgecolor=DARK_RED, zorder=5)
    ax.set_title(f"a  模仿学习收敛过程（最低 MSE {best.validation_mse:.4f}）", loc="left", fontsize=15, fontweight="bold")
    ax.set_xlabel("训练轮次（epoch）")
    ax.set_ylabel("验证集动作 MSE")
    ax.tick_params(colors="#5B6068")

    ax = axes[1]
    hb = ax.hexbin(actions[:, 0], actions[:, 1], gridsize=42, mincnt=1, cmap="Reds", bins="log")
    ax.axvline(0, color="#666666", linewidth=0.8)
    ax.axhline(0, color="#666666", linewidth=0.8)
    ax.set_xlim(-1.03, 1.03)
    ax.set_ylim(-1.03, 1.03)
    ax.set_title("b  IDM 专家动作覆盖", loc="left", fontsize=16, fontweight="bold")
    ax.set_xlabel("转向控制（左 − / 右 +）")
    ax.set_ylabel("纵向控制（制动 − / 加速 +）")
    ax.tick_params(colors="#5B6068")

    fig.suptitle("行为克隆：先学习可用驾驶先验，再进入强化学习", fontsize=21, fontweight="bold", color=DARK_RED, x=0.08, y=0.99, ha="left")
    fig.text(0.08, 0.865, "300 条专家轨迹 · 130,005 个样本 · 155 维观测 · 2 维连续控制", color="#5B6068", fontsize=11.5)
    fig.subplots_adjust(left=0.08, right=0.95, top=0.74, bottom=0.15, wspace=0.28)
    save_figure(fig, "behavior_cloning_training_revised")


def read_metrics(name):
    return pd.read_csv(ROOT / f"metrics/{name}/checkpoint_metrics.csv")


def summarize_episode_csv(name):
    df = pd.read_csv(ROOT / "metrics" / name)
    counts = df.outcome.value_counts(normalize=True)
    return {
        "mean_reward": float(df.reward.mean()),
        "success": float(counts.get("success", 0.0)),
        "collision": float(counts.get("collision", 0.0)),
        "out_of_road": float(counts.get("out_of_road", 0.0)),
    }


def plot_low_density_training():
    bc = summarize_episode_csv("bc_only_low_density_20ep.csv")
    routes = [
        ("BC → 低密度", read_metrics("low_density_basic").query("steps <= 700000"), GRAY),
        ("BC → 无交通 → 低密度", read_metrics("low_density_after_no_traffic").query("steps <= 700000"), RED),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.1))
    for label, df, color in routes:
        x = df.steps / 1000
        axes[0].plot(x, df.success * 100, label=label, color=color, linewidth=2.5, marker="o", markersize=4)
        axes[1].plot(x, df.mean_reward, label=label, color=color, linewidth=2.5, marker="o", markersize=4)
    axes[0].axhline(bc["success"] * 100, color=BC_LINE, linewidth=2.0, linestyle=(0, (6, 4)), label="仅 BC（未 PPO）")
    axes[1].axhline(bc["mean_reward"], color=BC_LINE, linewidth=2.0, linestyle=(0, (6, 4)), label="仅 BC（未 PPO）")
    axes[0].set_title("")
    axes[0].text(0, 1.03, "a  闭环成功率", transform=axes[0].transAxes, ha="left", va="bottom", fontsize=16, fontweight="bold")
    axes[0].set_xlabel("PPO 训练步数（k）")
    axes[0].set_ylabel("成功率（%）")
    axes[0].set_ylim(0, 100)
    axes[1].set_title("b  平均回合奖励", loc="left", fontsize=16, fontweight="bold")
    axes[1].set_xlabel("PPO 训练步数（k）")
    axes[1].set_ylabel("平均奖励")
    for ax in axes:
        style_axis(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=3, loc="lower center", bbox_to_anchor=(0.53, 0.01))
    fig.suptitle("低密度训练过程：无交通预训练提高上限，但仍存在波动", fontsize=21, fontweight="bold", color=DARK_RED, x=0.08, ha="left")
    fig.text(0.08, 0.87, "每 50k 步保存检查点并进行 20 回合闭环评估；曲线展示全部现有检查点", color="#5B6068", fontsize=11.5)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.74, bottom=0.22, wspace=0.23)
    save_figure(fig, "low_density_training_dynamics")


def plot_high_density_training():
    bc = summarize_episode_csv("bc_only_high_density_20ep.csv")
    routes = [
        ("BC → 高密度", read_metrics("high_density_basic").query("steps <= 400000"), GRAY),
        ("BC → 无交通 → 高密度", read_metrics("high_density_after_no_traffic").query("steps <= 400000"), BLUE),
        ("BC → 无交通 → 低密度 → 高密度", read_metrics("high_density_after_low_density").query("steps <= 400000"), RED),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.1))
    for label, df, color in routes:
        x = df.steps / 1000
        axes[0].plot(x, df.success * 100, label=label, color=color, linewidth=2.35, marker="o", markersize=3.8)
        axes[1].plot(x, df.out_of_road * 100, label=label, color=color, linewidth=2.35, marker="o", markersize=3.8)
    axes[0].axhline(bc["success"] * 100, color=BC_LINE, linewidth=2.0, linestyle=(0, (6, 4)), label="仅 BC（未 PPO）")
    axes[1].axhline(bc["out_of_road"] * 100, color=BC_LINE, linewidth=2.0, linestyle=(0, (6, 4)), label="仅 BC（未 PPO）")
    axes[0].set_title("")
    axes[0].set_xlabel("高密度 PPO 训练步数（k）")
    axes[0].set_ylabel("成功率（%）")
    axes[1].set_title("")
    axes[1].set_xlabel("高密度 PPO 训练步数（k）")
    axes[1].set_ylabel("驶出道路率（%）")
    for ax in axes:
        ax.set_ylim(0, 100)
        style_axis(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc="lower center", bbox_to_anchor=(0.53, 0.01), fontsize=9.8)
    fig.suptitle("高密度训练过程：逐级课程更早达到较高成功率", fontsize=21, fontweight="bold", color=DARK_RED, x=0.08, ha="left")
    fig.text(0.08, 0.87, "检查点评估用于观察训练动态；最终横向结论采用统一 100 回合评估", color="#5B6068", fontsize=11.5)
    fig.text(0.08, 0.765, "a  闭环成功率", ha="left", va="bottom", fontsize=16, fontweight="bold")
    fig.text(0.55, 0.765, "b  驶出道路率", ha="left", va="bottom", fontsize=16, fontweight="bold")
    fig.subplots_adjust(left=0.08, right=0.98, top=0.74, bottom=0.22, wspace=0.32)
    save_figure(fig, "high_density_training_dynamics")


def plot_summary_table():
    bc_low = summarize_episode_csv("bc_only_low_density_20ep.csv")
    bc_high = summarize_episode_csv("bc_only_high_density_20ep.csv")
    low_direct = read_metrics("low_density_basic").sort_values(["success", "mean_reward"], ascending=False).iloc[0]
    low_curr = read_metrics("low_density_after_no_traffic").sort_values(["success", "mean_reward"], ascending=False).iloc[0]
    high = pd.read_csv(ROOT / "metrics/high_density_100_episode_comparison.csv").set_index("experiment")

    rows = [
        ["低密度", "仅 BC（未 PPO）", "—", "20", bc_low],
        ["低密度", "BC → 低密度", f"{int(low_direct.steps/1000)}k", "20", low_direct],
        ["低密度", "BC → 无交通 → 低密度", f"{int(low_curr.steps/1000)}k", "20", low_curr],
        ["高密度", "仅 BC（未 PPO）", "—", "20", bc_high],
        ["高密度", "BC → 高密度", "450k", "100", high.loc["high_density_basic"]],
        ["高密度", "BC → 无交通 → 高密度", "700k", "100", high.loc["high_density_after_no_traffic"]],
        ["高密度", "BC → 无交通 → 低密度 → 高密度", "150k", "100", high.loc["high_density_after_low_density"]],
    ]
    cell_text = []
    for env, route, checkpoint, episodes, values in rows:
        cell_text.append(
            [
                env,
                route,
                checkpoint,
                episodes,
                f"{float(values['mean_reward']):.1f}",
                f"{float(values['success']):.0%}",
                f"{float(values['collision']):.0%}",
                f"{float(values['out_of_road']):.0%}",
            ]
        )

    fig, ax = plt.subplots(figsize=(13.4, 6.2))
    ax.axis("off")
    columns = ["环境", "训练路线", "检查点", "回合数", "平均奖励", "成功率", "碰撞率", "出界率"]
    widths = [0.08, 0.30, 0.09, 0.08, 0.11, 0.10, 0.10, 0.10]
    table = ax.table(cellText=cell_text, colLabels=columns, colWidths=widths, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(11.5)
    table.scale(1, 2.0)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#D8D5D0")
        cell.set_linewidth(0.8)
        if row == 0:
            cell.set_facecolor(DARK_RED)
            cell.get_text().set_color("white")
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor("#F6F3F0" if row in (1, 4) else "white")
            if col == 1:
                cell.get_text().set_ha("left")
            if col == 5:
                cell.get_text().set_color(RED)
                cell.get_text().set_fontweight("bold")
    fig.suptitle("综合结果：课程学习逐级提升复杂交通中的闭环能力", fontsize=21, fontweight="bold", color=DARK_RED, x=0.06, y=0.98, ha="left")
    fig.text(0.06, 0.89, "低密度为检查点 20 回合评估；高密度三条 PPO 路线采用统一 100 回合评估；BC 基线单独评估 20 回合", color="#5B6068", fontsize=11.5)
    fig.subplots_adjust(left=0.04, right=0.98, top=0.82, bottom=0.08)
    save_figure(fig, "comprehensive_results_table")


def grouped_outcome_bars(labels, values, title, subtitle, takeaway, stem):
    fig, ax = plt.subplots(figsize=(12.6, 5.7))
    x = np.arange(len(labels))
    width = 0.22
    series = [
        ("成功率", values[:, 0], RED),
        ("碰撞率", values[:, 1], GOLD),
        ("出界率", values[:, 2], GRAY),
    ]
    for index, (name, vals, color) in enumerate(series):
        bars = ax.bar(x + (index - 1) * width, vals * 100, width=width, label=name, color=color)
        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2.0,
                f"{val:.0%}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight="bold" if name == "成功率" else "normal",
                color=DARK_RED if name == "成功率" else "#4A4F56",
            )
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("回合占比（%）")
    ax.tick_params(axis="y", colors="#5B6068")
    ax.legend(ncol=3, loc="lower left", bbox_to_anchor=(0.0, -0.39))
    ax.set_title(title, loc="left", fontsize=21, fontweight="bold", color=DARK_RED, pad=28)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=11.5, color="#5B6068")
    ax.text(1.0, -0.39, takeaway, transform=ax.transAxes, ha="right", va="top", fontsize=12, color=RED, fontweight="bold")
    fig.subplots_adjust(left=0.09, right=0.98, top=0.76, bottom=0.34)
    save_figure(fig, stem)


def plot_comprehensive_bars():
    bc_low = summarize_episode_csv("bc_only_low_density_20ep.csv")
    low_direct = read_metrics("low_density_basic").sort_values(["success", "mean_reward"], ascending=False).iloc[0]
    low_curr = read_metrics("low_density_after_no_traffic").sort_values(["success", "mean_reward"], ascending=False).iloc[0]
    low_values = np.array(
        [
            [bc_low["success"], bc_low["collision"], bc_low["out_of_road"]],
            [low_direct.success, low_direct.collision, low_direct.out_of_road],
            [low_curr.success, low_curr.collision, low_curr.out_of_road],
        ],
        dtype=float,
    )
    grouped_outcome_bars(
        ["仅 BC\n未 PPO", "BC → 低密度\n最佳 450k", "BC → 无交通 → 低密度\n最佳 600k"],
        low_values,
        "低密度综合结果：无交通课程将成功率提升至 85%",
        "BC 基线与 PPO 检查点均采用相同 20 回合测试口径",
        "相较仅 BC：成功率 +40%，碰撞率 −25%，出界率 −15%",
        "low_density_comprehensive_bars",
    )

    bc_high = summarize_episode_csv("bc_only_high_density_20ep.csv")
    high = pd.read_csv(ROOT / "metrics/high_density_100_episode_comparison.csv").set_index("experiment")
    high_values = np.array(
        [
            [bc_high["success"], bc_high["collision"], bc_high["out_of_road"]],
            high.loc["high_density_basic", ["success", "collision", "out_of_road"]].to_numpy(float),
            high.loc["high_density_after_no_traffic", ["success", "collision", "out_of_road"]].to_numpy(float),
            high.loc["high_density_after_low_density", ["success", "collision", "out_of_road"]].to_numpy(float),
        ],
        dtype=float,
    )
    grouped_outcome_bars(
        ["仅 BC\n未 PPO", "BC → 高密度\n450k", "BC → 无交通 → 高密度\n700k", "BC → 无交通 → 低密度 → 高密度\n150k"],
        high_values,
        "高密度综合结果：逐级课程获得最高成功率与最低出界率",
        "仅 BC 为 20 回合基线；三条 PPO 路线采用同一批 100 个随机种子统一评估",
        "逐级课程：成功率 51%，出界率 25%",
        "high_density_comprehensive_bars",
    )


def plot_combined_outcome_comparison():
    bc_low = summarize_episode_csv("bc_only_low_density_20ep.csv")
    low_direct = read_metrics("low_density_basic").sort_values(["success", "mean_reward"], ascending=False).iloc[0]
    low_curr = read_metrics("low_density_after_no_traffic").sort_values(["success", "mean_reward"], ascending=False).iloc[0]
    low_routes = [
        ("仅 BC", np.array([bc_low["success"], bc_low["collision"], bc_low["out_of_road"]]), BC_LINE),
        ("直接 PPO", np.array([low_direct.success, low_direct.collision, low_direct.out_of_road]), GRAY),
        ("无交通课程", np.array([low_curr.success, low_curr.collision, low_curr.out_of_road]), RED),
    ]

    bc_high = summarize_episode_csv("bc_only_high_density_20ep.csv")
    high = pd.read_csv(ROOT / "metrics/high_density_100_episode_comparison.csv").set_index("experiment")
    high_routes = [
        ("仅 BC", np.array([bc_high["success"], bc_high["collision"], bc_high["out_of_road"]]), BC_LINE),
        ("直接 PPO", high.loc["high_density_basic", ["success", "collision", "out_of_road"]].to_numpy(float), GRAY),
        ("无交通课程", high.loc["high_density_after_no_traffic", ["success", "collision", "out_of_road"]].to_numpy(float), BLUE),
        ("逐级课程", high.loc["high_density_after_low_density", ["success", "collision", "out_of_road"]].to_numpy(float), RED),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.0))
    categories = ["成功率", "碰撞率", "出界率"]
    x = np.arange(len(categories))
    for ax, title, routes, width in [
        (axes[0], "a  低密度", low_routes, 0.23),
        (axes[1], "b  高密度", high_routes, 0.18),
    ]:
        offsets = (np.arange(len(routes)) - (len(routes) - 1) / 2) * width
        for offset, (label, values, color) in zip(offsets, routes):
            bars = ax.bar(x + offset, values * 100, width=width * 0.92, label=label, color=color)
            for bar, value in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1.8,
                    f"{value:.0%}",
                    ha="center",
                    va="bottom",
                    fontsize=10.5,
                    fontweight="bold" if value == max(values) else "normal",
                    color="#4A4F56",
                )
        ax.set_xticks(x, categories)
        ax.set_ylim(0, 100)
        ax.set_title(title, loc="left", fontsize=17, fontweight="bold")
        ax.tick_params(axis="y", colors="#5B6068")
        ax.legend(ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.28), fontsize=10)
    axes[0].set_ylabel("回合占比（%）")
    fig.suptitle("综合结果：按成功、碰撞与出界直接比较训练路线", fontsize=21, fontweight="bold", color=DARK_RED, x=0.07, y=0.98, ha="left")
    fig.text(0.07, 0.89, "左：低密度（20 回合检查点评估）｜右：高密度（BC 为 20 回合，PPO 路线为统一 100 回合评估）", color="#5B6068", fontsize=11.5)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.78, bottom=0.25, wspace=0.20)
    save_figure(fig, "combined_low_high_outcome_comparison")


def main():
    plot_bc()
    plot_low_density_training()
    plot_high_density_training()
    plot_summary_table()
    plot_comprehensive_bars()
    plot_combined_outcome_comparison()


if __name__ == "__main__":
    main()
