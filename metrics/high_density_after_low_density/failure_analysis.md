# High-density best-model failure analysis

Model: `checkpoints/high_density_after_low_density/ppo_metadrive_150000_steps.zip`

Evaluation: 100 episodes, scenario seeds 1000-1099. Traffic has additional
stochasticity, so a scenario seed fixes the map but does not always reproduce
the same traffic outcome.

## Aggregate result

| Outcome | Count | Mean reward | Mean steps | Mean route completion | Mean max intersection risk |
|---|---:|---:|---:|---:|---:|
| Success | 50 | 886.76 | 530.3 | 0.987 | 0.346 |
| Collision | 23 | 212.83 | 279.8 | 0.550 | 0.697 |
| Out of road | 27 | 304.48 | 313.7 | 0.538 | 0.332 |

Collision episodes have roughly twice the peak intersection risk of successful
episodes. Out-of-road episodes have almost the same intersection risk as
successful episodes, indicating that many departures are caused by route and
curve tracking rather than emergency avoidance.

## Recorded examples

| Seed | Replayed outcome | Visual classification |
|---:|---|---|
| 1000 | Collision | Turning conflict with cross traffic at an intersection |
| 1032 | Collision | Overlapping turning/merging trajectories at an intersection |
| 1041 | Collision | Insufficient yielding or following distance behind a turning vehicle |
| 1076 | Collision | Same-lane or rear-end conflict away from an intersection |
| 1046 | Out of road | Gradual inside drift on a long curve without urgent traffic risk |
| 1023 | Success | Originally failed in evaluation but succeeded during replay |

## Reward diagnostic

`max_wrong_decision_action` was zero in every episode, including all collision
episodes. The current wrong-decision signal is therefore not discriminating the
observed unsafe actions and should be redesigned before the next training run.

