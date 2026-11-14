# ImageGen 插画工作流与提示词

## 1. 为何使用原创插画

插画对抽象概念、组织协作、不同岗位和技术系统的类比有更强的记忆点。不能因为 PowerPoint 原生形状可编辑，就把全部视觉变成几何卡片。

但插画不是装饰指标：以**解释场景或形成品牌气质**为前提。某张精确工程图若不需要插画，应当让图充分利用版面。

本 Skill 复用的是风格规范。每次制作课件，按当前页面的内容调用 ImageGen 生成所需插图；仓库示例图、风格参考和历史课件均不是固定插图库，不能裁出其中的插画直接用于新课件。

## 2. Illustration Plan

生成之前为每张图记录：

| 属性 | 示例 |
|---|---|
| 使用页面 | 01 封面 |
| 意图 | 表达人与 Agent 一起完成工作 |
| 主体 | 两个人与一个抽象 Agent 元素 |
| 场景 | 共同操作可视化工作台 |
| 构图 | 主体右侧，左侧为标题留白 |
| 纵横比 | 16:9 / 4:3 / 竖向 |
| 视觉风格 | Modern flat vector editorial |
| 调色板 | 蓝、橙、黄、青绿，白背景 |
| 必须避免 | 机器人金属质感、图片文字、密集 UI、畸形手指 |
| 本次生成记录 | 页面稳定键、内容意图、提示词、调用结果与实际生成文件路径 |

保持一组风格的主体抽象程度、线条感和颜色关系一致；也要避免每页长得一模一样。

有满意样稿时，先实际查看其中的插画，记录人物头身比例、全身/半身取景、面部复杂度、阴影、轮廓、道具与画面留白。把代表图作为生成参考，而不只复用风格形容词。人物与 Agent 的协作关系、轻巧全身场景和小型道具，不能在未说明的情况下变成半身商务肖像、厚重桌面和高细节背景。若主题不涉及 Agent，不强加吉祥物。

将首张图放入实际页面，与认可样稿同尺寸检查后再生成同系列其余图片。白色图片背景并不自动等于页面留白；检查有色主体本身的面积与视觉重量。

## 3. 可复用风格提示词

在具体场景前后加入如下风格描述，按主题调整：

> Modern flat vector editorial illustration for a premium presentation. Friendly stylized characters, rounded geometric shapes, crisp flat colors, royal blue, coral orange, bright yellow, teal and soft lavender, clean contemporary product-design aesthetic, minimal details, generous negative space, white or very pale background, cohesive original character design, professional but playful, balanced composition, no photorealism, no 3D rendering, no complex texture, no text, no letters, no labels.

针对右侧主视觉追加：

> Compose primary subjects on the right half, keep the left 40% open with uncluttered negative space for slide title. No typography in the image.

针对概念页：

> A single clearly readable visual metaphor with one focal point, simplified objects, no clutter, no charts or labels baked into the artwork.

针对技术课程：

> Use illustration only to represent the human activity or concept. Leave all architectural nodes, technical labels and arrows to editable PowerPoint elements outside the generated image.

## 4. 生成与验收

1. 将当前页面内容与 Skill 风格描述组合为提示词，实际调用 ImageGen。先生成一张代表插图并入页检查，再生成其余封面与概念插图。
2. 根据每个页面的布局指定不同的主体位置和留白方向。
3. 检查畸形的手、怪异面部、伪字母、无意义的 UI、过于复杂的装饰。
4. 有瑕疵的图重新生成或裁切，不把劣质图强行塞进课件。
5. 标题、数字、引文、技术符号都放在 PPT 的文本或可编辑图形中。
6. 多套系列课件应有独立的主视觉，但可以共享视觉语言或角色设定。
7. 记录本次生成结果与使用页的对应关系，使用工具实际返回的图片文件；不硬编码旧项目路径，不把参考图记作本次生成。输出图片的完整性与风格分别检查，不能要求新插图与参考文件的哈希相同。

## 5. 增补和局部修订

用户已经认可画风时，保留画风与构图语言；新增或重做的插图仍按对应内容调用 ImageGen。新增知识也可通过原生技术图、案例或表格表达，不为凑图片数量添加无关插画。

同一课件只改文字、表格、排版或修复导出时，不重新生成未涉及的插图。继续尚未完成的同一任务时，也沿用本次任务已经生成并验收的图片，避免重试造成随机替换。这一保留规则不适用于新课件套用历史图片；仅用户明确指定复用素材时例外。

## 6. 用户参考图的使用

- 从参考图提取风格，如人物比例、边缘处理、色块、配色、背景和留白。
- 不要逐图复制参考中的人物身份、姿态、构图和细节。
- 已有真实版权素材，按允许的使用方式处理；不要在没有授权时搬运第三方品牌专属视觉资产。
- 如果没有图像生成能力，说明插图生成尚未完成，并继续可做的原生内容与排版；不自动拿仓库图片或旧课件插画充当本次生成结果。
- 参考图无法访问时，只依据可用文字规范执行并说明，不声称已看过图片。
