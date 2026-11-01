# Experiment artifacts

训练产物按实验版本分开放置：

| 实验 | 配置 | Checkpoint | TensorBoard 日志 | 录像 |
|---|---|---|---|---|
| v1 baseline | `configs/default.yaml` | `checkpoints/v1_baseline/` | `logs/v1_baseline/` | `videos/v1_baseline/` |
| v2 stage 1 | `configs/v2_stage1.yaml` | `checkpoints/v2_stage1/` | `logs/v2_stage1/` | `videos/v2_stage1/` |
| v2 stage 2 | `configs/v2_stage2.yaml` | `checkpoints/v2_stage2/` | `logs/v2_stage2/` | `videos/v2_stage2/` |

## v1 baseline

第一轮 100 万步训练。最终测试成功率为 0%，产物保留用于对照。

```powershell
python -m metadrive_rl.evaluate checkpoints/v1_baseline/ppo_metadrive_final.zip
tensorboard --logdir logs/v1_baseline
```

## v2 curriculum

Stage 1 使用无交通、较简单道路，学习导航和车道保持；Stage 2 在 Stage 1 模型基础上加入动态交通。

```powershell
python -m metadrive_rl.train --config configs/v2_stage1.yaml
python -m metadrive_rl.train --config configs/v2_stage2.yaml --resume checkpoints/v2_stage1/ppo_metadrive_final.zip
```

每个实验自己的 checkpoint 和 MP4 使用相同训练步数命名，便于一一对应。
