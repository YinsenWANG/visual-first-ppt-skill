# Visual-first PPT Skill

一套可复用的演示文稿制作 Skill，适用于课程、演讲、技术分享、产品介绍、路演与汇报。

## 直接使用

将本文件夹放入支持 Agent Skills 的工具所识别的 Skill 目录，并启用该 Skill。入口文件为 `SKILL.md`。

然后直接提出需求，例如：

> 请使用 visual-first-ppt，基于下面的培训讲义制作两套现场课件。每套独立封面、章节分隔、总结和封底。每页只呈现一个观点；保留完整讲师备注；多用 ImageGen 生成统一风格的极简人物插画，技术架构和表格使用可编辑原生元素。完成渲染质检并交付 PPTX。

无需填写固定表单；Agent 会根据任务理解目标、受众、风格与交付形式。

## 文件说明

- `SKILL.md`：入口指令、触发条件和完整工作流。
- `references/storyboard-template.md`：任务 Brief、逐页卡片和密度控制。
- `references/visual-system.md`：默认视觉系统、版式与技术图规范。
- `references/imagegen-playbook.md`：插画规划与生成提示词。
- `references/qa-checklist.md`：内容、视觉、文件和渲染验收。
- `examples/live-training-example.md`：可复用的现场授课示例。
- `assets/style-references/`：可选的示例风格图。来自用户提供的参考图，只供内部风格分析，不应直接作为新的 PPT 插画复刻或对外发布。可替换为自己的品牌示例。

## 核心观点

- 不是减少页数，而是降低单页信息密度。
- 独立 PPT 具有封面、章节、总结和封底。
- 现场 PPT 是视觉锚点，知识细节进讲师备注。
- ImageGen 生成场景和人物插画；原生图形表达准确流程、数字和架构。
- 必须渲染检查，不以 PPTX 保存成功代替实际完成。
