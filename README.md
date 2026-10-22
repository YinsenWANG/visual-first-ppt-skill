# Visual-first PPT Skill

一套可复用的演示文稿制作 Skill，适用于课程、演讲、技术分享、产品介绍、路演与汇报。支持从资料新建、沿用风格增补知识，以及表格和局部版式优化。

**内容深、页面清、图表可编辑。** 知识深度、单页信息密度与总页数分别设计；增加原理、决策、案例、异常与验收证据，同时保留讲述空间。

## 使用

将本仓库放入支持 Agent Skills 的工具所识别的 Skill 目录，文件夹建议命名为 `visual-first-ppt`。入口为 [SKILL.md](SKILL.md)，调用名称保持 `$visual-first-ppt`。

新建课件：

> 使用 $visual-first-ppt，根据这份讲义制作现场培训课件。用统一风格的原创插画和可编辑技术图表，保留完整讲师备注，完成渲染检查并交付 PPTX。

补充知识：

> 沿用当前 PPT 的视觉风格，依据原始资料补足知识深度。增加原理、判断依据、实施细节、异常与案例，需要时新增页面，并同步更新 Notes 和授课时间。

优化表格：

> 使用 $visual-first-ppt，把表格改成浅色表头、白底细线的现代样式，突出关键数值与状态，保留原有文字、数据、备注和其他页面内容。

无需填写固定表单；页数、课时、配色和结构由任务决定。

## 工作方式

- **教学深度**：原始资料与嵌入表格建立覆盖对照；重要知识进入页面、Notes 或演示。关键推理不能全部藏进备注。
- **视觉表达**：ImageGen 用于人物和场景；文字、数字、架构、流程和表格采用原生组件。已认可插画在增补时优先复用。
- **现代图表**：浅色表头、细横线、深色语义强调；检查旧表格主题带来的隐藏网格和色带。
- **局部修改**：保留最新批准稿的其他内容；样式导出有副作用时可用受限的原生表格移植工具。
- **交付检查**：实际渲染修改页，核对整体节奏、内容、Notes、可编辑性和文件完整性。

## 视觉示例

以下是完成课件后的渲染示例，用于理解布局与风格，不是整页图片模板。新课件的标题、图形与表格仍应原生可编辑。

![封面布局](assets/slide-examples/cover.png)
![带失败反馈的原生工作流](assets/slide-examples/workflow.png)
![现代原生表格](assets/slide-examples/table.png)

## 文件说明

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | 模式选择、核心规则和按需阅读入口 |
| [agents/openai.yaml](agents/openai.yaml) | Skill 列表展示与调用示例 |
| [Storyboard](references/storyboard-template.md) | Brief、内容覆盖和逐页卡片 |
| [教学深度](references/teaching-depth.md) | 资料增补、页面与备注分工、时间安排 |
| [视觉系统](references/visual-system.md) | 配色、字号、网格与原生技术图 |
| [ImageGen 工作流](references/imagegen-playbook.md) | 插画规划、提示词与复用原则 |
| [原生表格](references/native-tables.md) | 表格样式参数与主题陷阱 |
| [编辑与交付](references/editing-and-delivery.md) | 局部保留、渲染与文件检查 |
| [QA 清单](references/qa-checklist.md) | 内容、视觉、原生对象与最终产物验收 |
| [现场教学示例](examples/live-training-example.md) | 从概念扩展到决策、案例与演示 |
| [表格样式保留工具](scripts/preserve_table_styles.py) | 只移植经过原生工具编辑的表格样式 |

`assets/style-references/` 保留早期版本的参考图，用于风格分析；不将其作为新的插画复刻或对外使用。`assets/slide-examples/` 展示本次完成的课件布局，其中课程标题、时间与示例数字不构成通用模板要求。

## 可选工具与验证

核心 Skill 不绑定演示文稿库或操作系统；制作时使用当前可用的原生编辑、图像生成和渲染工具。表格移植辅助脚本只需 Python 3 标准库，适用于文字、合并、行列尺寸与顺序不变的纯文本原生表格。它不会替代原生编辑或视觉检查。

运行脚本测试：

```bash
python3 -m unittest discover -s tests -v
```

有 skill-creator 的环境还可使用其 `quick_validate.py` 检查 Skill 元数据。脚本用法和拒绝条件见 [编辑与交付](references/editing-and-delivery.md)。
