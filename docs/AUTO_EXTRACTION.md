# 自动提取和处理随访数据工具使用说明

## 概述

本项目提供了从原始大文件直接提取随访数据并处理的一键式解决方案。无需手动整理Excel文件，系统会自动识别、提取并处理所有随访表数据。

## 工作流程

### 原始流程（手动两步）

❌ **之前需要手动操作：**
1. 手动从原始大文件中复制"随访表1"相关的sheet
2. 手动整理成多个时间点的sheet
3. 保存为新文件
4. 运行处理脚本

### 新流程（一键自动化）

✅ **现在只需一步：**
```bash
python scripts/extract_and_process.py
```
或者指定文件：
```bash
python scripts/extract_and_process.py "data/raw/20250924  CAG 组.xlsx"
```

## 使用方法

### 方法1: 一键式处理（推荐）

最简单的方式，从原始文件到最终结果一步到位：

```bash
# Windows PowerShell
python scripts/extract_and_process.py

# 或指定原始文件路径
python scripts/extract_and_process.py "D:\path\to\原始数据.xlsx"
```

**功能：**
1. 自动提取所有"*随访表1" sheet
2. 自动识别并规范化时间点名称（3个月、6个月、12个月等）
3. 自动处理数据并生成宽格式和长格式输出
4. 询问是否保留中间文件

**输出：**
- `output/CAG_followup_results_YYYYMMDD_HHMMSS_wide.xlsx` - 宽格式数据
- `output/CAG_followup_results_YYYYMMDD_HHMMSS_long.xlsx` - 长格式数据
- `data/raw/extracted_CAG_followup_YYYYMMDD_HHMMSS.xlsx` - 中间提取文件（可选保留）

### 方法2: 仅提取数据

如果只想提取数据但暂不处理：

```bash
python scripts/extract_followup_sheets.py [输入文件] [输出文件]
```

**示例：**
```bash
# 使用默认路径
python scripts/extract_followup_sheets.py

# 指定输入和输出文件
python scripts/extract_followup_sheets.py "原始数据.xlsx" "提取后数据.xlsx"
```

**输出：**
- 包含所有随访表1数据的新Excel文件
- Sheet名称已规范化为时间点（3个月、6个月等）

### 方法3: 处理已提取的数据

如果已经有提取好的数据文件：

```bash
python scripts/followup_data_processor.py
```

会弹出文件选择对话框，选择提取后的Excel文件。

## 文件结构说明

### 原始文件结构

原始文件（如 `20250924  CAG 组.xlsx`）包含80个sheet：
- `第三个月随访_CAGSFB1_627CAG随访表1` - 3个月随访数据
- `第六个月随访_CAGSFB1_627CAG随访表1` - 6个月随访数据
- `第12个月随访_CAGSFB1_627CAG随访表1` - 12个月随访数据
- `第36个月随访_CAGSFB1_627CAG随访表1` - 36个月随访数据
- `第60个月随访_CAGSFB1_627CAG随访表1` - 60个月随访数据
- `第84个月随访_CAGSFB1_627CAG随访表1` - 84个月随访数据
- `personal_CAG随访表1` - 个人随访记录
- 其他73个sheet（患者住院阶段数据等）

### 提取后文件结构

提取后的文件只包含随访表1数据，sheet名称已规范化：
- `3个月` - 3个月随访数据
- `6个月` - 6个月随访数据
- `12个月` - 12个月随访数据
- `36个月` - 36个月随访数据
- `60个月` - 60个月随访数据
- `84个月` - 84个月随访数据
- `personal_CAG随访表1` - 个人随访记录

### 输出文件结构

#### 宽格式 (`*_wide.xlsx`)
每个患者一行，包含所有时间点的数据：
- 基本信息：`subjid`, `groupdate`, `groupname` 等
- 各时间点数据：`随访日期_3`, `死亡时间_3`, `事件_3` ...

#### 长格式 (`*_long.xlsx`)
每个患者每个时间点一行：
- 基本信息：`subjid`, `groupdate`
- 时间点：`visit_month`
- 该时间点的所有随访数据

## 脚本说明

### `extract_and_process.py`

**全自动一键式处理脚本**

- 自动提取：从原始大文件中识别并提取所有"随访表1" sheet
- 自动命名：将中文时间点转换为标准格式（"第三个月" → "3个月"）
- 自动处理：调用完整的数据处理流程
- 智能识别：自动检测患者组类型（CAG/PCI）
- 用户友好：提供GUI文件选择和处理选项

### `extract_followup_sheets.py`

**单独的数据提取工具**

- 功能：从原始文件提取所有"随访表1" sheet
- 用途：当只需要提取数据，不需要立即处理时使用
- 输出：格式化的Excel文件，可用于后续处理

### `followup_data_processor.py`

**通用数据处理脚本**

- 功能：处理已经格式化好的多时间点Excel文件
- 自动检测患者组类型
- 生成宽格式和长格式输出

## 常见问题

### Q: 我有多个原始文件需要处理怎么办？

A: 可以使用循环或批处理：
```bash
# Windows PowerShell批量处理
Get-ChildItem "data/raw" -Filter "*CAG*.xlsx" | ForEach-Object {
    python scripts/extract_and_process.py $_.FullName
}
```

### Q: 提取后的中间文件可以删除吗？

A: 可以。程序处理完成后会询问是否保留。如果需要重新处理，建议保留；否则可以删除以节省空间。

### Q: 如果原始文件sheet名称格式不同怎么办？

A: 修改 `extract_time_point_from_sheet_name()` 函数中的正则表达式，或联系开发者添加新的识别规则。

### Q: 处理很慢怎么办？

A: 原始文件很大（73.7 MB），正常情况下：
- 读取文件：1-3分钟
- 提取数据：1-2分钟
- 处理数据：30秒-1分钟
- 总计：约3-6分钟

### Q: 如何验证提取是否正确？

A: 脚本会显示详细日志：
- 原始文件中发现的sheet数量
- 匹配到的"随访表1" sheet列表
- 每个sheet的时间点转换结果
- 提取的数据行数

如果数字不对，请检查原始文件格式。

## 技术细节

### 时间点识别逻辑

1. **阿拉伯数字识别**：`第12个月` → `12个月`
2. **中文数字识别**：`第三个月` → `3个月`
3. **特殊名称保留**：`personal_CAG随访表1` → `personal_CAG随访表1`

### 数据处理流程

```
原始Excel (80 sheets)
    ↓ extract_followup_sheets()
临时Excel (7 sheets, 规范化名称)
    ↓ LongitudinalDataImporter
数据字典 {time_point: DataFrame}
    ↓ LongitudinalFollowupProcessor
宽格式DataFrame + 长格式DataFrame
    ↓ DataExporter
输出文件 (*_wide.xlsx, *_long.xlsx)
```

### 患者组识别

- 文件名包含"PCI" → PCI组
- 文件名包含"CAG" → CAG组  
- 其他情况 → 弹出对话框询问用户

## 相关文档

- [快速开始](QUICKSTART.md) - 项目基本使用
- [开发指南](DEVELOPMENT.md) - 开发环境配置
- [患者分组说明](PATIENT_GROUP_SCRIPTS.md) - 不同患者组的处理方式

## 更新日志

- 2025-02-12: 创建自动提取工具
  - 添加 `extract_followup_sheets.py` 
  - 更新 `extract_and_process.py` 支持新的处理流程
  - 添加中文数字到阿拉伯数字的转换
  - 实现一键式端到端处理
