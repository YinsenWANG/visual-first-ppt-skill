# ImageGen 插画工作流与提示词

## 1. 为何使用原创插画

插画对抽象概念、组织协作、不同岗位和技术系统的类比有更强的记忆点。不能因为 PowerPoint 原生形状可编辑，就把全部视觉变成几何卡片。

但插画不是装饰指标：以**解释场景或形成品牌气质**为前提。某张精确工程图若不需要插画，应当让图充分利用版面。

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

保持一组风格的主体抽象程度、线条感和颜色关系一致；也要避免每页长得一模一样。

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

1. 先生成全套封面与最重要的概念插画，验证风格是否统一。
2. 根据每个页面的布局指定不同的主体位置和留白方向。
3. 检查畸形的手、怪异面部、伪字母、无意义的 UI、过于复杂的装饰。
4. 有瑕疵的图重新生成或裁切，不把劣质图强行塞进课件。
5. 标题、数字、引文、技术符号都放在 PPT 的文本或可编辑图形中。
6. 四套系列课件应有独立的主视觉，但可以共享视觉语言或角色设定。

## 5. 用户参考图的使用

- 从参考图提取风格，如人物比例、边缘处理、色块、配色、背景和留白。
- 不要逐图复制参考中的人物身份、姿态、构图和细节。
- 已有真实版权素材，按允许的使用方式处理；不要在没有授权时搬运第三方品牌专属视觉资产。
- 如果没有图像生成能力，诚实说明，并使用能力范围内的视觉替代。
