# 快速开始指南

本指南帮助您快速上手 Followup 随访数据处理工具。

## 安装

### 前提条件
- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

#### 1. 克隆仓库（或下载源码）
```bash
git clone <repository-url>
cd Followup
```

#### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -e .
```

## 基本使用

### 1. 准备数据

将您的患者数据准备为以下格式之一：
- Excel文件 (.xlsx)
- CSV文件 (.csv)
- SQLite数据库 (.db)

数据应包含：
- 患者ID
- 入组日期
- 事件日期字段（如死亡日期、心梗日期等）

### 2. 配置文件

创建或修改 `config/config.yaml`：

```yaml
# 数据源配置
data_source:
  type: "csv"  # 或 "sqlite", "excel"
  connection_string: "data/raw/patients.csv"

# 患者字段配置
patient:
  enrollment_date_field: "enrollment_date"
  patient_id_field: "patient_id"

# 事件配置
events:
  types:
    death:
      field_names: ["death_date"]
      priority: 1
    mi:
      field_names: ["mi_date"]
      priority: 2

# 输出配置
output:
  format: "excel"  # 或 "csv"
  file_path: "output/followup_results.xlsx"
```

### 3. 运行处理

#### 使用Python模块
```bash
python -m src.main config/config.yaml
```

#### 使用脚本（带GUI文件选择）
```bash
python scripts/followup_data_processor.py
```

### 4. 查看结果

结果文件将保存在 `output/` 目录中，包含：
- 患者ID
- 入组日期
- 首次事件类型
- 首次事件日期
- 事件距入组天数

## 示例

### 示例1：处理CSV数据

**数据文件** (`data/raw/patients.csv`):
```csv
patient_id,enrollment_date,death_date,mi_date
P001,2020-01-01,2021-06-15,
P002,2020-02-01,,2021-03-10
P003,2020-03-01,,
```

**配置** (`config/config.yaml`):
```yaml
data_source:
  type: "csv"
  connection_string: "data/raw/patients.csv"

patient:
  enrollment_date_field: "enrollment_date"
  patient_id_field: "patient_id"

events:
  types:
    death:
      field_names: ["death_date"]
      priority: 1
    mi:
      field_names: ["mi_date"]
      priority: 2

output:
  format: "excel"
  file_path: "output/followup_results.xlsx"
```

**运行**:
```bash
python -m src.main config/config.yaml
```

**输出结果**:
```
patient_id  enrollment_date  first_event_type  first_event_date  days_to_first_event
P001        2020-01-01       death            2021-06-15        531
P002        2020-02-01       mi               2021-03-10        403
P003        2020-03-01       None             None              None
```

### 示例2：处理纵向数据

对于多时间点的随访数据（如3月、6月、12月随访），使用纵向数据处理脚本：

```bash
python scripts/followup_data_processor.py
```

然后：
1. 选择包含多个Sheet的Excel文件
2. 程序自动识别不同时间点的随访数据
3. 合并数据并计算首次事件

## 常见问题

### Q: 日期格式不正确怎么办？
A: 程序支持多种日期格式，包括：
- ISO格式：2020-01-01
- 中文格式：2020年1月1日
- Excel日期码（自动转换）

### Q: 如何处理缺失数据？
A: 配置文件中设置 `date_handling` 选项：
```yaml
date_handling:
  invalid_date_action: "skip"  # 或 "null", "today"
```

### Q: 如何查看详细处理日志？
A: 日志文件保存在 `logs/` 目录中，可以查看详细的处理过程和错误信息。

### Q: 支持哪些事件类型？
A: 支持任意自定义事件类型，在配置文件的 `events.types` 中定义即可。

## 进阶功能

### 纵向数据处理
详见：[纵向数据处理指南](LONGITUDINAL_README.md)

### 自定义事件处理
详见：[README.md](README.md) 的高级配置部分

### 批量处理
可以编写脚本批量处理多个数据文件

## 下一步

- 阅读完整的 [README.md](README.md)
- 查看 [开发文档](docs/DEVELOPMENT.md)（如需二次开发）
- 浏览示例数据和配置

## 获取帮助

如遇问题：
1. 查看 [常见问题](README.md#常见问题)
2. 查看日志文件
3. 在GitHub Issues中提问

祝使用愉快！
