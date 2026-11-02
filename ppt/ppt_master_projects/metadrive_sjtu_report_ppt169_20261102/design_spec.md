<!-- ppt-master-schema: design-spec/v1 -->
# MetaDrive 强化学习自动驾驶项目汇报 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | MetaDrive 强化学习自动驾驶项目汇报 |
| Canvas Format | PPT 16:9, 1280 × 720 |
| Page Count | 14 |
| Primary Language | zh-CN |
| Target Audience | 课程答辩教师与同学 |
| Communication Intent | 简洁汇报任务、方法、训练过程、横向结果与失败分析 |
| Desired Audience Outcome | 理解行为克隆与课程学习为何能提升复杂交通闭环驾驶能力 |
| Core Message / Ask / Action | 行为克隆提供驾驶先验，逐级课程学习在高密度交通中取得最高成功率并降低出界 |
| Delivery Context | 现场课程答辩 |
| Artifact Afterlife | 项目归档与 GitHub 展示 |
| Reading Mode | balanced |
| Content Strategy | 允许压缩和重组，全部指标保持真实，不提 V1–V4 |
| Design Style | 交大红数据叙事 |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — workflow default |
| Custom Animations | disabled — user-confirmed production plan |
| Narration Audio | disabled — user-confirmed production plan |
| Created Date | 2026-11-02 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 64 px horizontal, 46 px vertical |
| Content Area | x=64..1216, y=46..674 |

## III. Visual Theme

### Theme Style

- **Mode**: pyramid
- **Visual style**: data-journalism
- **Theme**: Shanghai Jiao Tong red data report
- **Tone**: technical, evidence-led, concise, confident

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | Main canvas |
| Secondary background | #F6F3F0 | Soft evidence bands |
| Primary | #C8161D | SJTU red, conclusions and primary series |
| Accent | #D4AF37 | Baseline and selected emphasis |
| Secondary accent | #4E79A7 | Secondary curriculum series |
| Body text | #202124 | Main text |
| Secondary text | #646A73 | Captions and notes |
| Divider | #D8D5D0 | Hairlines and boundaries |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | strong modern sans | Microsoft YaHei | Arial | sans-serif |
| Body | neutral readable sans | Microsoft YaHei | Arial | sans-serif |
| Data | lining numerals | Arial | Arial | sans-serif |

- **Title stack**: Microsoft YaHei, Arial
- **Body stack**: Microsoft YaHei, Arial
- **Data stack**: Arial, Microsoft YaHei

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 24 |
| Title | 42 |
| Subtitle | 30 |
| Lead | 28 |
| Annotation | 18 |
| Footnote | 15 |
| Data | 28 |

## V. Layout Principles

### Deck-wide Direction

- **Hierarchy direction**: assertion title → hero evidence → concise implication
- **Composition tendency**: charts and simulation frames act as the page spine, with restrained evidence bands
- **Cross-page continuity**: thin red top rule, page number, consistent red/gray/blue/gold data semantics
- **Spacing posture**: open on framing pages, dense but structured on evidence pages
- **Spacing anchors**: page margin 64 px; block gap 24 px; column gutter 32 px; corner radius 12 px; body leading 34 px

## VI. Icon Usage Specification

- **Primary bundled library**: tabler-outline
- **Stroke Width**: 2

| Icon Path | Suitable Scenarios |
| --- | --- |
| tabler-outline/car | vehicle task |
| tabler-outline/route | curriculum and route |
| tabler-outline/chart-line | training metrics |
| tabler-outline/alert-triangle | failure analysis |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Image pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| behavior_cloning_training.png | 2000×867 | 2.31 | BC training evidence | Chart image | full-width evidence plate | no-crop | user | Existing | generated from project logs | embedded | local |
| low_density_training_dynamics.png | 2000×867 | 2.31 | Low-density process | Chart image | full-width evidence plate | no-crop | user | Existing | generated from checkpoint metrics | embedded | local |
| high_density_training_dynamics.png | 2000×867 | 2.31 | High-density process | Chart image | full-width evidence plate | no-crop | user | Existing | generated from checkpoint metrics | embedded | local |
| low_density_curriculum_comparison.png | 2000×800 | 2.50 | Low-density outcome comparison | Chart image | full-width evidence plate | no-crop | user | Existing | generated from checkpoint metrics | embedded | local |
| high_density_curriculum_comparison.png | 2000×800 | 2.50 | High-density outcome comparison | Chart image | full-width evidence plate | no-crop | user | Existing | generated from unified evaluation | embedded | local |
| combined_low_high_outcome_comparison.png | 2000×909 | 2.20 | Combined route comparison | Chart image | full-width evidence plate | no-crop | user | Existing | generated from unified metrics | embedded | hero_page |
| success_seed_1023_last.jpg | 1280×720 | 1.78 | Successful driving example | Simulation frame | wide hero frame with play cue | adaptive | user | Existing | successful episode seed 1023 | none | hero_page |
| collision_seed_1000_last.jpg | 1280×720 | 1.78 | Collision failure example | Simulation frame | left failure frame | adaptive | user | Existing | collision episode seed 1000 | none | local |
| out_of_road_seed_1046_last.jpg | 1280×720 | 1.78 | Out-of-road failure example | Simulation frame | right failure frame | adaptive | user | Existing | out-of-road episode seed 1046 | none | local |

## IX. Content Outline

### Part 1: Task and system

#### Slide 01 - Cover
- **Audience move**: unknown project → know the central question
- **Relationships**: title, subtitle, and curriculum motif establish project identity
- **Composition**: large assertion title with red route motif and compact metadata
- **Title**: MetaDrive 强化学习自动驾驶
- **Core message**: 从模仿学习到课程学习，让车辆在复杂交通中完成闭环驾驶
- **Content**: 项目汇报 / MetaDrive / Behavior Cloning + PPO + Curriculum Learning

#### Slide 02 - What the task looks like
- **Audience move**: abstract task → concrete driving experience
- **Relationships**: successful frame demonstrates the task before definitions
- **Composition**: dominant simulation frame with a play affordance and three task facts
- **Title**: 任务是在随机道路与交通中安全到达终点
- **Core message**: Ego Car must steer, accelerate and brake from observations until destination or failure
- **Content**: 随机地图 · 连续控制 · 到达/碰撞/出界终止
- **Images**: success_seed_1023_last.jpg

#### Slide 03 - Observation and action
- **Audience move**: see driving → understand agent interface
- **Relationships**: observations feed policy; policy emits steering and longitudinal control
- **Composition**: left sensor stack → center policy → right two control channels
- **Title**: 155 维观测映射为 2 维连续控制
- **Core message**: policy fuses navigation, lane, ego state and traffic sensing
- **Content**: 导航与车道 / 车辆状态 / 激光雷达与邻车 / steering / throttle-brake

#### Slide 04 - Method pipeline
- **Audience move**: know interface → understand training strategy
- **Relationships**: IDM demonstrations precede BC; BC precedes PPO; difficulty increases from no traffic to low and high density
- **Composition**: horizontal curriculum ladder with four stages and outcome arrows
- **Title**: BC 提供驾驶先验，PPO 在逐级交通中继续优化
- **Core message**: curriculum prevents the policy from learning all driving and interaction skills at once
- **Content**: IDM expert → Behavior Cloning → No Traffic PPO → Low Density PPO → High Density PPO

### Part 2: Learning evidence

#### Slide 05 - Behavior cloning
- **Audience move**: know pipeline → trust the initial policy
- **Relationships**: validation loss shows convergence; action distribution shows coverage
- **Composition**: full-width BC figure with a compact interpretation band
- **Title**: 130,005 个专家样本让策略先学会基本驾驶动作
- **Core message**: validation MSE drops to 0.0070 over 30 epochs
- **Content**: 300 trajectories / 155-D observations / 2-D actions
- **Images**: behavior_cloning_training.png

#### Slide 06 - Why curriculum learning
- **Audience move**: trust BC → understand the difficulty schedule
- **Relationships**: each stage adds one new source of uncertainty while retaining prior capability
- **Composition**: three difficulty columns with traffic density and learning objective
- **Title**: 逐级增加交通密度，把驾驶与交互学习拆开
- **Core message**: no traffic stabilizes road following; low density introduces avoidance; high density stresses intersections
- **Content**: 无交通：路线跟随 / 低密度：基础避让 / 高密度：路口冲突决策

#### Slide 07 - Low-density training dynamics
- **Audience move**: understand curriculum → inspect optimization behavior
- **Relationships**: two PPO routes and the BC-only baseline are compared across training steps
- **Composition**: chart image dominates with one caution note
- **Title**: 无交通预训练提高低密度上限，但检查点仍有波动
- **Core message**: curriculum route repeatedly exceeds the BC and direct-PPO baselines
- **Images**: low_density_training_dynamics.png

#### Slide 08 - Low-density final comparison
- **Audience move**: see fluctuations → retain final low-density result
- **Relationships**: success, collision and out-of-road are compared across three routes
- **Composition**: left-to-right grouped outcome comparison with headline takeaway
- **Title**: 低密度成功率由 45% 提升至 85%
- **Core message**: no-traffic curriculum raises success while reducing both collision and departure
- **Images**: low_density_curriculum_comparison.png

#### Slide 09 - High-density training dynamics
- **Audience move**: know low-density gain → inspect high-density learning
- **Relationships**: three PPO curricula and BC-only baseline are compared up to 400k
- **Composition**: chart image dominates with evaluation-protocol note
- **Title**: 高密度前 400k 步中，逐级课程更早达到较高成功率
- **Core message**: direct training remains unstable while curriculum transfers useful behavior
- **Images**: high_density_training_dynamics.png

#### Slide 10 - Unified high-density evaluation
- **Audience move**: inspect process → accept comparable final result
- **Relationships**: three routes share identical 100-seed evaluation protocol
- **Composition**: full-width outcome comparison with one red takeaway
- **Title**: 逐级课程在统一测试中达到 51% 成功率
- **Core message**: success rises from 22% to 51%, primarily by reducing out-of-road failures
- **Images**: high_density_curriculum_comparison.png

#### Slide 11 - Combined comparison
- **Audience move**: know separate results → compare all outcome dimensions directly
- **Relationships**: left low density and right high density share success/collision/out-of-road grouping
- **Composition**: one dual-panel evidence figure
- **Title**: 课程学习的主要收益是提升成功并减少出界
- **Core message**: collision remains the high-density bottleneck even after curriculum learning
- **Images**: combined_low_high_outcome_comparison.png

### Part 3: Failure cases and conclusion

#### Slide 12 - Failure diagnosis
- **Audience move**: know aggregate result → understand remaining failure mechanism
- **Relationships**: success, collision and out-of-road differ in intersection risk and route completion
- **Composition**: three outcome columns with risk numbers and causal interpretation
- **Title**: 路口冲突而非路线跟随成为高密度主要瓶颈
- **Core message**: collision peak intersection risk 0.697 is roughly twice success 0.346
- **Content**: Success risk 0.346 / Collision risk 0.697 / Out-of-road risk 0.332

#### Slide 13 - Success and failure videos
- **Audience move**: understand diagnosis → see concrete behavior
- **Relationships**: successful crossing contrasts with collision and out-of-road failures
- **Composition**: one hero success frame above two smaller failure frames with play cues
- **Title**: 成功策略能完成路口通过，失败集中在冲突与避让过度
- **Core message**: examples connect aggregate metrics to observable driving behavior
- **Images**: success_seed_1023_last.jpg; collision_seed_1000_last.jpg; out_of_road_seed_1046_last.jpg

#### Slide 14 - Conclusion
- **Audience move**: see examples → retain findings and next action
- **Relationships**: three findings support one next-step priority
- **Composition**: three conclusion statements and one red next-step band
- **Title**: 课程学习有效，下一步应专攻高密度路口交互
- **Core message**: retain driving skill while learning proactive gap selection and conflict resolution
- **Content**: BC establishes prior / curriculum improves success / intersection collision remains / next: risk-aware interaction objective

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: conclusion first, explain real metrics and evaluation protocol without inventing claims
- **Total duration**: 8–10 minutes
- **Notes style**: formal but conversational
- **Presentation purpose**: course defense and project explanation
