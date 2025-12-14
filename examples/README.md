# 示例脚本目录

此目录包含几个示例脚本，演示如何使用随访数据处理工具。

## 示例列表

### 1. `example_create_sample_data.py`
**目的**: 创建用于测试的示例患者数据

**运行**:
```bash
python examples/example_create_sample_data.py
```

**输出**: 在 `data/` 目录下创建 `sample_patients.csv` 文件，包含50条示例患者记录

**说明**:
- 约50%的患者有随访事件
- 某些患者有多个事件
- 包含各种事件类型

### 2. `example_basic_usage.py`
**目的**: 演示工具的基本使用

**运行**:
```bash
python examples/example_basic_usage.py
```

**说明**:
- 演示如何加载配置
- 如何导入患者数据
- 如何处理事件
- 如何显示处理结果

### 3. `example_complete_workflow.py`
**目的**: 演示完整的工作流程

**运行**:
```bash
python examples/example_complete_workflow.py
```

**说明**:
- 完整的从导入到导出的流程
- 包含数据统计和验证
- 显示详细的处理摘要

## 使用步骤

1. **首先创建示例数据**:
   ```bash
   python examples/example_create_sample_data.py
   ```

2. **更新配置文件** (`config/config.yaml`):
   ```yaml
   data_source:
     type: "csv"
     connection_string: "data/sample_patients.csv"
   
   output:
     format: "excel"
     output_dir: "output"
   ```

3. **运行完整工作流程**:
   ```bash
   python examples/example_complete_workflow.py
   ```

4. **查看结果**:
   - 随访数据在 `output/` 目录下
   - 日志在 `logs/` 目录下

## 自定义示例

您可以根据自己的需要修改这些示例脚本：

- 改变数据源类型（SQLite, Excel等）
- 修改事件类型和字段映射
- 添加自定义的数据验证
- 扩展统计分析功能
