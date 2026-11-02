<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 课程答辩教师与同学
- objective: 用真实训练与评估证据说明行为克隆和课程学习如何提升复杂交通闭环驾驶能力
- core_message: 行为克隆提供驾驶先验，逐级课程学习在高密度交通中取得最高成功率并减少出界

## mode
- mode: pyramid

## visual_style
- visual_style: data-journalism

## colors
- background: #FFFFFF
- secondary_bg: #F6F3F0
- primary: #C8161D
- accent: #D4AF37
- secondary_accent: #4E79A7
- body_text: #202124
- secondary_text: #646A73
- divider: #D8D5D0
- surface: #F6F3F0
- grid: #E5E2DE

## typography
- font_family: Microsoft YaHei, Arial
- title_family: Microsoft YaHei, Arial
- body_family: Microsoft YaHei, Arial
- data_family: Arial, Microsoft YaHei
- body: 24
- title: 42
- subtitle: 30
- lead: 28
- annotation: 18
- footnote: 15
- data: 28

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: tabler-outline/car, tabler-outline/route, tabler-outline/chart-line, tabler-outline/alert-triangle

## images
- p02-success: images/success_seed_1023_last.jpg | source=user | crop=adaptive
- p05-bc: images/behavior_cloning_training.png | source=user | crop=no-crop
- p07-low-train: images/low_density_training_dynamics.png | source=user | crop=no-crop
- p08-low-compare: images/low_density_curriculum_comparison.png | source=user | crop=no-crop
- p09-high-train: images/high_density_training_dynamics.png | source=user | crop=no-crop
- p10-high-compare: images/high_density_curriculum_comparison.png | source=user | crop=no-crop
- p11-combined: images/combined_low_high_outcome_comparison.png | source=user | crop=no-crop
- p13-collision: images/collision_seed_1000_last.jpg | source=user | crop=adaptive
- p13-out: images/out_of_road_seed_1046_last.jpg | source=user | crop=adaptive

## page_rhythm
- P01: anchor
- P02: anchor
- P03: dense
- P04: dense
- P05: dense
- P06: breathing
- P07: dense
- P08: dense
- P09: dense
- P10: dense
- P11: dense
- P12: dense
- P13: anchor
- P14: anchor

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
- 不提 V1–V4 (user)
