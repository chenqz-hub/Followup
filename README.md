# Follow-up Data Processing Tool

## 概述

这是一个用于从冠心病（CAD）数据库中自动提取患者随访信息的工具。它能够：

- 从多种数据源（SQLite、CSV、Excel）导入患者数据
- 自动识别和分类患者事件（死亡、心肌梗死、脑卒中等）
- 计算首次事件距离入组时间的天数
- 生成规范化的随访数据表格（CSV或Excel格式）
- **[新增]** 支持纵向数据处理：从多个Excel Sheet合并患者跨月份的随访记录

## 功能特性

### 核心功能

1. **灵活的数据导入**
   - 支持SQLite数据库
   - 支持CSV文件导入
   - 支持Excel文件导入
   - 支持纵向数据（多Sheet）导入
   - 自动处理缺失数据和数据格式转换

2. **智能事件识别**
   - 多种事件类型配置（死亡、MI、脑卒中、血运重建等）
   - 支持多个数据源字段映射到同一事件类型
   - 优先级管理：同一天内的多个事件可按优先级选择
   - **[新增]** 纵向事件追踪：从多个时间点识别首次事件

3. **日期处理**
   - 支持多种日期格式自动识别
   - Excel日期码自动转换
   - 无效日期的智能处理（跳过、用NULL填充、用今天填充）

4. **灵活的导出**
   - CSV格式导出
   - Excel格式导出（带自动列宽调整）
   - 包含统计摘要

5. **完整的日志系统**
   - 日志文件自动轮转
   - 控制台和文件双输出
   - 详细的处理过程记录

### 纵向数据处理（新增）

支持从多个Excel Sheet中合并纵向患者数据：

- **多时间点支持**: 3月、6月、12月、36月、60月、84月随访
- **智能合并**: 按患者ID自动合并来自不同Sheet的数据
- **动态最晚随访**: 识别每个患者的最晚有效随访时间点（不使用固定时间点）
- **纵向事件追踪**: 从多个时间点识别患者的首次事件
- **随访状态判断**: 自动分类患者的随访状态（完全/充分/不完全/失访）

详见：[纵向数据处理指南](LONGITUDINAL_README.md)

### 软件工程最佳实践

- **模块化设计**：清晰的职责分离（数据导入、事件处理、数据导出）
- **配置驱动**：使用YAML配置文件，便于定制
- **数据验证**：使用Pydantic进行数据模型验证
- **完整的测试**：单元测试覆盖核心功能
- **错误处理**：详细的异常捕获和日志记录
- **代码规范**：遵循PEP 8，包含完整的文档字符串

## 项目结构

```
Followup/
├── src/                          # 源代码目录
│   ├── __init__.py              # 包初始化文件
│   ├── main.py                  # 主程序入口
│   ├── config.py                # 配置管理模块
│   ├── logger.py                # 日志系统模块
│   ├── data_models.py           # 数据模型定义
│   ├── event_processor.py       # 事件处理核心模块
│   ├── data_importer.py         # 数据导入模块
│   ├── data_exporter.py         # 数据导出模块
│   ├── longitudinal_models.py         # [新]纵向数据模型
│   ├── longitudinal_importer.py       # [新]纵向数据导入器
│   └── longitudinal_processor.py      # [新]纵向事件处理器
├── config/
│   └── config.yaml              # 主配置文件
├── tests/                        # 测试目录
│   ├── test_config.py           # 配置管理测试
│   ├── test_data_models.py      # 数据模型测试
│   ├── test_event_processor.py  # 事件处理器测试
│   └── simple_test.py           # [新]纵向数据测试
├── examples/                     # 示例脚本
│   ├── example_*.py             # 各种示例
│   └── run_longitudinal_processing.py  # [新]纵向处理完整示例
├── data/                         # 数据目录（输入数据存放处）
├── output/                       # 输出目录（处理结果）
├── logs/                         # 日志目录
├── LONGITUDINAL_README.md        # [新]纵向数据处理详细指南
├── pyproject.toml               # 项目配置和依赖
└── README.md                    # 说明文档（本文件）
```

## 安装

### 前置要求

- Python 3.8+
- pip 或 conda

### 步骤

1. 克隆仓库或进入项目目录

2. 创建虚拟环境（可选但推荐）：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. 安装依赖：
   ```bash
   pip install -e .
   ```

4. 安装开发依赖（用于运行测试）：
   ```bash
   pip install -e ".[dev]"
   ```

## 快速开始

### 1. 准备数据

将数据放在 `data/` 目录下，支持的格式：

**SQLite数据库**：
```
data/cad_database.db
```

**CSV文件**：
```
data/patients.csv
```

**Excel文件**：
```
data/patients.xlsx
```

### 2. 配置

编辑 `config/config.yaml` 文件：

```yaml
# 配置数据源
data_source:
  type: "csv"  # 或 "excel", "sqlite"
  connection_string: "data/patients.csv"

# 配置输出
output:
  format: "excel"  # 或 "csv"
  output_dir: "output"
```

### 3. 运行

```bash
python -m src.main config/config.yaml
```

或直接运行：

```bash
python src/main.py
```

### 4. 查看结果

处理完成后，随访数据表格会保存在 `output/` 目录下，文件名格式为：
```
followup_data_YYYYMMDD_HHMMSS.xlsx
```

### 纵向数据处理 （新增）

如果你有多个Sheet的纵向数据（不同时间点的随访记录），使用以下方式：

```bash
python examples/run_longitudinal_processing.py
```

这将：
1. 从模板Excel文件加载6个Sheet（3M、6M、12M、36M、60M、84M）
2. 按患者ID合并数据
3. 识别每个患者的最晚随访时间点
4. 识别首次发生的事件
5. 导出汇总结果到Excel文件

详细说明和配置选项见：[纵向数据处理指南](LONGITUDINAL_README.md)

## 配置说明

### 数据源配置 (`data_source`)

```yaml
data_source:
  type: "sqlite"              # 数据源类型: sqlite, csv, excel
  connection_string: "data/cad_database.db"  # 数据库路径或文件路径
```

### 患者字段配置 (`patient`)

```yaml
patient:
  enrollment_date_field: "enrollment_date"  # 入组日期字段名
  patient_id_field: "patient_id"           # 患者ID字段名
```

### 事件类型配置 (`events`)

事件类型配置定义了如何识别和分类患者事件：

```yaml
events:
  types:
    death:
      field_names: ["death_date", "patient_death"]  # 多个可能的字段名
      priority: 1  # 优先级，数字越小优先级越高
    
    myocardial_infarction:
      field_names: ["mi_date", "first_mi_date"]
      priority: 2
    
    # 添加更多事件类型...
```

### 处理配置 (`processing`)

```yaml
processing:
  skip_invalid_records: true              # 是否跳过无效记录
  fill_missing_values: true               # 是否填补缺失值
  invalid_date_handling: "skip"           # skip, fill_with_null, fill_with_today
  max_days_from_enrollment: 36500         # 最大合理的事件天数差（约100年）
```

### 输出配置 (`output`)

```yaml
output:
  format: "excel"              # 输出格式: csv, excel
  output_dir: "output"         # 输出目录
  filename_prefix: "followup_data"  # 输出文件名前缀
  include_details: true        # 是否包含详细信息
```

### 日志配置 (`logging`)

```yaml
logging:
  level: "INFO"                # 日志级别: DEBUG, INFO, WARNING, ERROR
  log_dir: "logs"              # 日志目录
  max_log_size: 10485760       # 单个日志文件最大大小（字节）
  backup_count: 5              # 备份日志文件数量
```

## 输入数据格式要求

### 必需字段

| 字段名 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `patient_id` | 字符串 | 患者唯一标识 | "P001", "CAD-2020-001" |
| `enrollment_date` | 日期 | 患者入组日期 | "2020-01-15", "2020/01/15" |

### 可选的事件字段

根据配置，可以包含以下事件字段：

| 字段名 | 说明 |
|------|------|
| `death_date` | 患者死亡日期 |
| `mi_date`, `first_mi_date` | 心肌梗死发生日期 |
| `stroke_date`, `first_stroke_date` | 脑卒中发生日期 |
| `revascularization_date` | 血运重建日期 |
| `hospitalization_date` | 住院日期 |

## 输出格式说明

### 输出表格列

| 列名 | 说明 | 示例 |
|------|------|------|
| `patient_id` | 患者ID | "P001" |
| `enrollment_date` | 入组日期 | "2020-01-15" |
| `first_event_type` | 首次事件类型 | "myocardial_infarction" |
| `first_event_date` | 首次事件日期 | "2021-01-15" |
| `days_to_first_event` | 首次事件距离入组时间的天数 | 365 |
| `event_count` | 患者的总事件数 | 3 |
| `notes` | 备注 | "" |
| `processing_timestamp` | 处理时间戳 | "2024-01-15T10:30:00" |

### 统计摘要

处理完成后，日志中会显示统计摘要：

```
=== 导出摘要 ===
文件路径: output/followup_data_20240115_103000.xlsx
总患者数: 1000
有事件患者数: 850
无事件患者数: 150
总事件数: 1200
事件类型分布: {'myocardial_infarction': 450, 'death': 250, 'stroke': 300, 'revascularization': 200}
```

## 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
pytest tests/test_event_processor.py -v
```

### 生成测试覆盖率报告

```bash
pytest tests/ --cov=src --cov-report=html
```

这会在 `htmlcov/` 目录下生成HTML格式的覆盖率报告。

## 日志文件位置

日志文件存放在 `logs/` 目录下，文件名格式为：
```
followup_processor_YYYYMMDD.log
```

每个日志文件大小限制为10MB，超出后会自动轮转。

## 常见问题

### Q: 日期格式不被识别
A: 工具支持多种常见日期格式。如果您的日期格式不被识别，可以：
1. 在 `src/event_processor.py` 中的 `date_formats` 列表添加新格式
2. 或将日期转换为支持的格式后再导入

### Q: 某些患者没有事件
A: 这是正常的，随访表中会显示 `first_event_type` 为 NULL。这可能表示：
- 患者在随访期间没有发生任何事件
- 数据中没有对应的事件字段
- 事件日期缺失或格式无效

### Q: 如何自定义事件类型
A: 编辑 `config/config.yaml` 中的 `events.types` 部分，添加新的事件类型和对应的字段映射。

### Q: 导出的数据格式是什么
A: 默认导出为Excel格式（.xlsx），可在配置中改为CSV格式。

## 扩展指南

### 添加新的事件类型

1. 在 `config/config.yaml` 中添加事件定义：
```yaml
events:
  types:
    new_event:
      field_names: ["new_event_field", "alternative_field"]
      priority: 7
```

2. 数据导入时包含相应的字段即可

### 添加新的数据源

1. 在 `src/data_importer.py` 中创建新的 `DataSource` 子类
2. 在 `DataImporter.create_source()` 方法中添加对应的处理逻辑
3. 在配置中指定新的数据源类型

### 自定义日期解析格式

在 `src/event_processor.py` 的 `_parse_date()` 方法中添加新的日期格式。

## 性能考虑

- 对于包含数千条患者记录的数据集，处理通常需要几秒到几十秒
- 内存使用量主要取决于患者记录数量
- 日志文件会自动轮转，不会无限增长

## 许可证

MIT License

## 支持和联系

如有问题或建议，请联系 CAD Research Team。
