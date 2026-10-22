# Storyboard 与制作 Brief 模板

## A. Presentation Brief

```yaml
presentation:
  action: "create | enrich | restyle"
  input_version: "最新批准的 PPTX 或来源版本"
  title: ""
  objective: "听完希望观众知道/相信/采取的行动"
  audience: ""
  mode: "live_training | live_keynote | report | self_reading | technical | workshop"
  duration_minutes: null
  target_slides: null   # 用户未指定则根据章节与密度估计，不机械压页
  language: "zh-CN"
  output: ["pptx"]
  speaker_notes: true
  editable_technical_diagrams: true
visual:
  style: "modern_flat_vector | brand_guided | custom"
  reference_images: []
  palette: "auto"
  imagegen: "proactive_when_useful"
  imagegen_intensity: "balanced"  # restrained | balanced | illustration_rich
constraints:
  mandatory_content: []
  prohibited_content: []
  verified_sources: []
  preserve_on_edit: []  # 文字、数据、Notes、页序、插画或其他未请求修改的对象
```

这是 Agent 的内部记录格式，不要要求用户必须填写表单。

## B. 每页卡片（Slide Card）

| 字段 | 填写提示 |
|---|---|
| 编号 | 例如 08 |
| 章节 | 例如 02 / 案例验证 |
| 页面角色 | 封面 / 章节 / 观点 / 对比 / 架构 / 流程 / 数据 / Demo / 总结 / 封底 |
| 核心结论 | 完整的一句话，观众应记住什么 |
| 屏幕文字 | 精简后的可见内容；现场模式尽量只留一行观点与少量标签 |
| 主要视觉 | ImageGen 插画 / 原生图表 / 真实截图 / 可编辑流程 / 问题页 |
| 视觉结构 | 例如左标题+右图、全屏结构图、上下布局 |
| 讲解备注 | 概念、背景、例子、误区和过渡 |
| 时间 | 预计讲授/展示时长 |
| 数据依据 | 资料文件、用户明确提供的事实或注明示意数据 |
| 本页教学任务 | 理解原理 / 做出选择 / 执行步骤 / 定位异常 / 验收结果 |
| 覆盖来源 | 此页及 Notes 补足了原始资料中的哪些重要知识 |

## C. 短页数演示与完整课件的结构区别

- 4–6 页：仍应明确开场、核心内容与结束，可将章节标识融入标题页。
- 7–15 页：建议独立封面、内容章节、总结和封底；必要时独立分隔。
- 16 页以上：章节分隔页通常有明显价值，每章有自己的视觉起承转合。
- 系列课件：每套独立封面、章节、总结、封底；共享系统风格，不共享完全相同的内容主视觉。

这些是建议，不是硬性页数配额；用户的明确结构要求优先。

## D. 单页信息密度检查例子

原始文字：

> 事件驱动系统通常包括事件源、事件传输、订阅处理者、状态存储、重试机制、死信队列等组件，它的主要优势包括解耦、实时性和可扩展性，但同时需要考虑事件幂等性、重复投递和失败恢复。

**现场幻灯片只呈现：**

标题：`事件驱动，让工作自行开始`

主视觉：`事件 → 消息 → Agent/处理器 → 结果`，下方小标签 `状态 · 重试 · 幂等`

详细解释：放在 Speaker Notes；不要把段落、六大组件和三项优势同时塞入页面。

## E. 用户要求更深入时

上面的概念图只回答“怎样被触发”。需要实施深度时，可增加独立的“重复事件如何安全处理”页，用原生流程呈现业务主键、查询当前状态、允许的下一步与验收结果；再用一个回执丢失案例演示。

内部覆盖对照可记录 `来源主题 / 当前缺口 / 页面锚点 / Notes 或演示 / 验收依据`。不要把所有新增知识都塞入概念图，也不要只扩写备注而让课堂上看不到新增内容。详见 [教学深度](teaching-depth.md)。
