# 开发指南

## 环境设置

### 1. 克隆仓库
```bash
git clone <repository-url>
cd Followup
```

### 2. 创建虚拟环境
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. 安装依赖
```bash
# 安装项目依赖
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

### 4. 设置pre-commit hooks
```bash
pre-commit install
```

## 代码质量工具

### 代码格式化 (Black)
```bash
# 格式化所有代码
black src tests scripts

# 检查但不修改
black --check src tests scripts
```

### 代码风格检查 (Flake8)
```bash
flake8 src tests scripts
```

### 类型检查 (Mypy)
```bash
mypy src
```

### 导入排序 (isort)
```bash
# 排序导入
isort src tests scripts

# 检查但不修改
isort --check-only src tests scripts
```

### 运行所有检查
```bash
# 使用pre-commit运行所有检查
pre-commit run --all-files
```

## 测试

### 运行所有测试
```bash
pytest
```

### 运行特定测试文件
```bash
pytest tests/test_config.py
```

### 运行带覆盖率报告的测试
```bash
pytest --cov=src --cov-report=html
# 查看报告: open htmlcov/index.html
```

### 运行特定测试
```bash
pytest tests/test_config.py::TestConfig::test_load_from_dict
```

## 项目结构

```
Followup/
├── src/                      # 源代码（包）
│   ├── __init__.py          # 包初始化，导出公共API
│   ├── config.py            # 配置管理
│   ├── logger.py            # 日志系统
│   ├── data_models.py       # 数据模型（Pydantic）
│   ├── data_importer.py     # 数据导入
│   ├── data_exporter.py     # 数据导出
│   ├── event_processor.py   # 事件处理
│   ├── longitudinal_*.py    # 纵向数据处理
│   └── py.typed             # 类型检查标记
├── tests/                    # 测试代码
│   ├── conftest.py          # pytest配置和fixtures
│   ├── test_*.py            # 测试文件
├── scripts/                  # 运行脚本
├── config/                   # 配置文件
├── data/                     # 数据目录（被忽略）
├── output/                   # 输出目录（被忽略）
├── logs/                     # 日志目录（被忽略）
├── pyproject.toml           # 项目配置
├── .pre-commit-config.yaml  # Pre-commit配置
├── .flake8                  # Flake8配置
└── .gitignore               # Git忽略文件
```

## 代码规范

### Python风格
- 遵循 PEP 8
- 使用 Black 进行代码格式化（行长100）
- 使用 type hints 注解类型
- 编写清晰的 docstrings

### Docstring格式
使用Google风格的docstring：

```python
def function_name(param1: str, param2: int) -> bool:
    """
    简短描述函数功能
    
    更详细的描述（如需要）
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
    
    Returns:
        返回值描述
    
    Raises:
        ValueError: 何时抛出此异常
    
    Example:
        >>> function_name("test", 42)
        True
    """
    pass
```

### 导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地应用/库导入

使用isort自动排序。

### 提交信息规范
使用传统提交格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 发布流程

### 1. 更新版本号
编辑 `pyproject.toml` 中的版本号

### 2. 更新CHANGELOG
记录此版本的变更

### 3. 创建标签
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 4. 构建分发包
```bash
python -m build
```

## 常见问题

### 导入错误
如果遇到导入错误，确保：
1. 虚拟环境已激活
2. 项目以可编辑模式安装：`pip install -e .`
3. src目录在Python路径中

### 测试失败
1. 确保所有依赖已安装：`pip install -e ".[dev]"`
2. 检查配置文件路径
3. 查看详细错误信息：`pytest -v`

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

确保：
- 所有测试通过
- 代码格式符合规范
- 添加了必要的测试
- 更新了文档
