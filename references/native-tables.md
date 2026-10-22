# 现代原生表格

采用已获认可的浅色表头、白底、细横线，见 [表格示例](../assets/slide-examples/table.png)。保留原生 PowerPoint Table，不用截图覆盖，不把每个格子拆成难维护的文本框。

## 样式参数

| 部位 | 参数 |
| --- | --- |
| 表头背景 | `#F2F6FF` |
| 表头文字 | `#1D438D`，加粗 |
| 表头下沿 | `#356CF5`，约 1.35 pt / 1.8 px |
| 正文背景 | `#FFFFFF`，默认关闭交替色带 |
| 正文文字 | `#273244` |
| 第一列 | `#1D438D`，适度加粗 |
| 行分隔 | `#E1E8F2`，约 0.6 pt / 0.8 px |
| 纵线与外框 | 无线或极弱 |
| 成功与重点数值 | 深青绿 `#087F78` |
| 待补充 / 异常提醒 | 深橙 `#B95C29` |
| 待审批 / 判断 | 紫色 `#6E49E8` |

语义色只用在确有含义的字段，并配状态文字；不自动把所有百分比都当成功指标。标签左对齐；需要比较的数值用一致的右对齐或小数对齐，保持列内一致。

1280 × 720 画布可参考 12–16 px 内边距、21–25 px 表格字。优化已有表格时先保留列宽、行高、字号和文本，只有可读性确需改变时才调整。内容过多优先另页或移入 Notes。

## 原生对象设置示例

以下 API 形态在本案例运行过，使用前核对当前工具文档。字体、字号和语义字段从当前课件读取。

```javascript
table.styleOptions = {
  headerRow: false, totalRow: false,
  firstColumn: false, lastColumn: false,
  bandedRows: false, bandedColumns: false,
};
table.borders.assign({ fill: '#FFFFFF', width: 0.4, style: 'solid' });
for (let row = 0; row < table.rowCount; row++) {
  for (let col = 0; col < table.columnCount; col++) {
    const cell = table.getCell(row, col);
    cell.fill = row === 0 ? '#F2F6FF' : '#FFFFFF';
    cell.text.style = {
      typeface: chosenFont, fontSize: chosenSize,
      color: row === 0 || col === 0 ? '#1D438D' : '#273244',
      bold: row === 0 || col === 0,
      alignment: 'left', verticalAlignment: 'middle',
      insets: chosenPadding, autoFit: 'none',
    };
  }
  table.cells.block({
    row, column: 0, rowCount: 1, columnCount: table.columnCount,
  }).assign({ borders: { bottom: {
    width: row === 0 ? 1.8 : 0.8,
    color: row === 0 ? '#356CF5' : '#E1E8F2',
  } } });
}
```

此示例边框宽度为像素参数，按当前工具单位转换。含局部富文本时保留必要强调，不盲目覆盖语义。

## 隐藏的主题影响

旧 PPT 的 `tableStyleId` 可能叠加主题网格、行带或特殊边框。关闭色带、设置 cell.fill 后仍要检查最终渲染，尤其是意外绿色、黑色或粗框线。

需要中性样式时先检查原包 `ppt/tableStyles.xml`。此次无样式无网格 ID 为 `{2D5ABB26-0587-4C30-8999-92F81FD0307C}`；只在目标包已有该定义，或通过当前工具正确创建样式时使用，不能向任意课件硬写 ID。

## 保护其他内容

优先使用可靠的原生局部编辑。若全量导出影响未编辑内容，可先原生编辑生成 donor，再只移植 `<a:tbl>` 元素。

提供的 [preserve_table_styles.py](../scripts/preserve_table_styles.py) 只适合**文字、合并、行列尺寸、数量与顺序不变的纯文本原生表格样式修改**，不是通用 OOXML 编辑器。调用与限制见 [编辑与交付](editing-and-delivery.md)。
