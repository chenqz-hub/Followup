# 患者分组处理脚本使用说明

本项目包含两个专用的患者数据处理脚本，分别用于不同的患者组：

## 📋 脚本概览

### 1. `process_PCI_patients.py` - PCI组患者处理脚本
**适用于：** PCI（经皮冠状动脉介入治疗）组患者

**特点：**
- 支持更多随访时间点（1, 3, 6, 12, 18, 30, 42, 54, 66, 90个月等）
- 自动识别PCI组特有的列名：
  - `随访期间主要心血管不良事件1`
  - `心血管事件1`
- 自动解析事件编码：
  - 1 = 心源性死亡
  - 2 = 非致死性心肌梗死
  - 3 = 靶病变血运重建
  - 4 = 心衰发作
  - 5 = 心绞痛
  - 6 = 因心脏病入院
- 详细的事件类型统计输出

**默认输入文件：** `extracted_PSM186_PCI_cases_20251104_222503_随访表1_20251106_121852.xlsx`

### 2. `process_CAG_patients.py` - CAG组患者处理脚本
**适用于：** CAG（冠状动脉造影）组患者

**特点：**
- 支持标准随访时间点（3, 6, 12, 24, 36, 60个月等）
- 识别CAG组标准列名：
  - `随访期间心血管不良事件1`
  - `如有不良事件，何事件1`
- 兼容原有的事件识别逻辑

**默认输入文件：** `extracted_PSM93_cases_20251104_221914_随访表1_20251106_121718.xlsx`

## 🚀 使用方法

### 基本使用

1. **打开对应的脚本文件**
   - PCI组患者 → 打开 `process_PCI_patients.py`
   - CAG组患者 → 打开 `process_CAG_patients.py`

2. **修改配置（如需要）**
   
   找到脚本中的"配置区域"：
   ```python
   # ====== 配置区域 ======
   # 1. 设置Excel文件路径
   excel_file = r"你的文件路径.xlsx"
   
   # 2. 设置终点事件类型
   endpoint = 'death'  # 可修改为其他终点
   # =====================
   ```

3. **运行脚本**
   ```bash
   python process_PCI_patients.py
   # 或
   python process_CAG_patients.py
   ```

### 终点事件类型选项

修改 `endpoint` 参数可以改变生存分析的终点事件：

| 终点类型 | 说明 | 适用场景 |
|---------|------|---------|
| `'death'` | 死亡（默认） | 总生存分析 |
| `'mace'` | 主要不良心血管事件 | MACE复合终点（死亡+MI+血运重建） |
| `'mi'` | 心肌梗死 | MI专项分析 |
| `'angina'` | 心绞痛 | 心绞痛发作分析 |
| `'heart_failure'` | 心力衰竭 | 心衰分析 |
| `'revascularization'` | 血运重建 | 再次血运重建分析 |
| `'hospitalization'` | 住院 | 因心脏病住院分析 |
| `'any_event'` | 任何事件 | 无事件生存分析 |

**示例：** 如果要分析PCI组患者"首次因心脏病住院"的时间：
```python
endpoint = 'hospitalization'
```

## 📊 输出文件

### 1. Excel完整输出
**文件名格式：** `longitudinal_[组别]_output_[时间戳].xlsx`

**内容：** 56列详细数据
- 患者基本信息（ID、年龄、性别、入组日期等）
- 随访信息（最晚随访日期、随访月数、随访天数）
- **首次事件信息**：
  - `first_event_type` - 首次事件类型
  - `first_event_date` - 首次事件日期
  - `days_to_first_event` - 距入组天数
- **各类事件详细信息**：
  - `first_angina_date`, `first_angina_time_point` - 首次心绞痛
  - `first_hospitalization_date`, `first_hospitalization_time_point` - 首次住院
  - `first_mi_date`, `first_mi_time_point` - 首次心肌梗死
  - `first_heart_failure_date`, `first_heart_failure_time_point` - 首次心衰
  - `first_revascularization_date` - 首次血运重建
  - `first_death_date` - 死亡日期
- 冠脉相关检查/治疗信息
- 生存分析字段（`survival_time_days`, `event_occurred`）

### 2. CSV生存数据集
**文件名格式：** `survival_[组别]_[时间戳].csv`

**内容：** 用于Cox回归/Kaplan-Meier分析的精简数据集
- `patient_id` - 患者ID
- `survival_time_days` - 生存时间（天）
- `event_occurred` - 事件是否发生（0=删失, 1=事件）
- `endpoint_event` - 使用的终点事件类型
- `age` - 年龄
- `gender` - 性别
- `group_name` - 分组
- `enrollment_date` - 入组日期

**可直接导入R或SPSS进行生存分析！**

## 📈 运行示例

### PCI组示例输出
```
PCI Patient Longitudinal Followup Data Processing
======================================================================

Step 1: Loading Excel file...
  OK: Loaded 10 sheets

Step 2: Importing and merging longitudinal data...
  OK: Imported 186 patient records

Step 3: Processing with 'death' endpoint...
  OK: Processed 186 records (0 errors)

  Event distribution:
    angina: 57 (30.6%)
    death: 1 (0.5%)
    hospitalization: 65 (34.9%)
    no_event: 63 (33.9%)

Step 4: Exporting results...
  OK: Excel exported to output/longitudinal_pci186_output_20251208_194221.xlsx
      Total columns: 56
      Total records: 186
  OK: Survival CSV exported to output/survival_pci186_20251208_194221.csv

  Detailed event breakdown:
    Angina: 66 patients
    Hospitalization: 119 patients
    Death: 1 patients

Processing completed!
```

### CAG组示例输出
```
CAG Patient Longitudinal Followup Data Processing
======================================================================

Step 1: Loading Excel file...
  OK: Loaded 6 sheets

Step 2: Importing and merging longitudinal data...
  OK: Imported 93 patient records

Step 3: Processing with 'death' endpoint...
  OK: Processed 93 records (0 errors)

  Event distribution:
    angina: 2 (2.2%)
    heart_failure: 4 (4.3%)
    no_event: 87 (93.5%)

Step 4: Exporting results...
  OK: Excel exported to output/longitudinal_psm93_output_20251208_194233.xlsx
      Total columns: 56
      Total records: 93
  OK: Survival CSV exported to output/survival_psm93_20251208_194233.csv

Processing completed!
```

## 🔧 高级用法

### 1. 批量处理多个文件
创建一个批处理脚本：
```python
from process_PCI_patients import process_pci_patients

files = [
    r"D:\data\PCI_batch1.xlsx",
    r"D:\data\PCI_batch2.xlsx",
]

for file in files:
    process_pci_patients(file, endpoint='any_event')
```

### 2. 比较不同终点
```python
from process_PCI_patients import process_pci_patients

endpoints = ['death', 'mace', 'hospitalization', 'any_event']

for ep in endpoints:
    print(f"\n处理终点: {ep}")
    process_pci_patients(your_file, endpoint=ep)
```

## ❓ 常见问题

### Q: 如何知道我的数据是PCI组还是CAG组？
**A:** 查看Excel文件名：
- 包含 "PCI" → 使用 `process_PCI_patients.py`
- 包含 "CAG" 或 "PSM" 且没有PCI → 使用 `process_CAG_patients.py`

### Q: 如果我的表格有不同的列名怎么办？
**A:** 系统支持多种列名变体。如果仍不识别，可以在 `src/longitudinal_importer.py` 的 `FIELD_MAPPING` 中添加新的列名映射。

### Q: 为什么有些患者显示"no_event"？
**A:** 可能原因：
1. 该患者在随访期内确实没有发生所选的终点事件
2. 数据中该患者的事件信息缺失或编码不规范

### Q: 如何理解"first_event_type"和具体事件日期列的关系？
**A:** 
- `first_event_type` 显示的是**最早发生**的事件类型
- 具体事件日期列（如`first_angina_date`）显示该**特定类型**事件的首次发生时间
- 一个患者可能在不同时间点发生多种事件

**例如：**
- Patient 1695:
  - `first_event_type`: hospitalization（首次事件是住院）
  - `first_hospitalization_date`: 2020-05-14
  - `first_angina_date`: 2021-05-25（后来又发生了心绞痛）

## 📝 注意事项

1. **文件路径使用绝对路径**，避免相对路径导致的文件找不到问题
2. **输出文件会自动添加时间戳**，不会覆盖之前的结果
3. **所有输出文件保存在 `output/` 目录下**
4. **Excel和CSV文件的列顺序可能不同**，但包含相同的数据
5. **事件统计可能包含"多重计数"**：一个患者可能在多个时间点发生不同类型的事件

## 🆘 获取帮助

如有问题，请查看：
1. `README.md` - 项目整体说明
2. `QUICKSTART.md` - 快速入门指南
3. `src/longitudinal_importer.py` - 数据导入逻辑
4. `src/longitudinal_processor.py` - 事件处理逻辑
