# 安装和环境配置指南

## 环境要求

- **Python 版本**: 3.8 或更高
- **操作系统**: Windows, Linux, macOS
- **磁盘空间**: ~500MB（包括虚拟环境）

## 安装步骤

### 步骤 1: 创建虚拟环境（推荐）

**Windows**：
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS**：
```bash
python3 -m venv venv
source venv/bin/activate
```

### 步骤 2: 升级 pip

```bash
python -m pip install --upgrade pip
```

### 步骤 3: 安装项目及依赖

**仅安装基础依赖**（运行程序）：
```bash
pip install -e .
```

**安装所有依赖**（包括开发工具）：
```bash
pip install -e ".[dev]"
```

### 步骤 4: 验证安装

```bash
# 检查Python版本
python --version

# 检查关键包
python -c "import pandas; import pydantic; print('✓ 依赖安装成功')"

# 运行测试验证
pytest tests/ -v
```

## 依赖详解

### 核心依赖

```
pandas>=1.3.0          # 数据表格处理
numpy>=1.21.0          # 数值计算
openpyxl>=3.6.0        # Excel文件操作
python-dateutil>=2.8.2 # 日期解析
pyyaml>=5.4.0          # YAML配置解析
pydantic>=1.8.0        # 数据验证
```

### 开发依赖（可选）

```
pytest>=6.2.0          # 单元测试框架
pytest-cov>=2.12.0     # 测试覆盖率报告
black>=21.0            # 代码格式化
flake8>=3.9.0          # 代码质量检查
mypy>=0.910            # 静态类型检查
```

## 常见安装问题

### 问题 1: pip 命令找不到

**症状**：`pip: 命令未找到`

**解决**：
```bash
# 使用python -m调用pip
python -m pip install ...
```

### 问题 2: 虚拟环境激活失败

**症状**：激活脚本后仍无效

**解决**：
```bash
# 确保在正确的目录
cd d:\git\Followup

# 重新激活虚拟环境
# Windows
venv\Scripts\activate.bat

# Linux/macOS
source venv/bin/activate
```

### 问题 3: pandas 或其他包安装缓慢

**症状**：安装进行缓慢或超时

**解决**：使用清华或阿里云 pip 镜像源
```bash
pip install -i https://pypi.tsinghua.edu.cn/simple -e .
```

### 问题 4: openpyxl 版本冲突

**症状**：`openpyxl` 版本冲突错误

**解决**：
```bash
pip install --upgrade openpyxl
```

## 版本检查

安装后验证各个包的版本：

```bash
pip list | grep -E "pandas|numpy|pydantic|pyyaml|openpyxl|pytest"
```

**预期输出示例**：
```
numpy                    1.21.0
openpyxl                 3.6.0
pandas                   1.3.0
pydantic                 1.8.0
pyyaml                   5.4.0
pytest                   6.2.0
```

## 离线安装（可选）

如果无法连接到互联网，可以在有网的机器上下载依赖：

```bash
# 下载所有依赖到本地目录
pip download -r requirements.txt -d ./packages

# 然后在离线机器上安装
pip install --no-index --find-links=./packages -e .
```

## 生成依赖列表

```bash
# 生成当前环境的依赖列表
pip freeze > requirements.txt

# 仅生成项目依赖（不包括过渡依赖）
pip freeze --exclude-editable | grep -v "^-e" > requirements.txt
```

## 虚拟环境管理

### 查看虚拟环境信息

```bash
# Windows
python -c "import sys; print(sys.prefix)"

# Linux/macOS
which python
```

### 删除虚拟环境

```bash
# Windows
rmdir /s venv

# Linux/macOS
rm -rf venv
```

### 创建新的虚拟环境

```bash
python -m venv venv_new
venv_new\Scripts\activate  # Windows
source venv_new/bin/activate  # Linux/macOS
```

## Docker 安装（可选）

如果您使用 Docker，可以创建 Dockerfile：

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -e .

CMD ["python", "-m", "src.main"]
```

构建和运行：
```bash
docker build -t followup-processor .
docker run -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output followup-processor
```

## 使用 Conda（可选）

如果使用 Conda：

```bash
# 创建环境
conda create -n followup python=3.10

# 激活环境
conda activate followup

# 安装依赖
pip install -e .
```

## 升级依赖

### 升级单个包
```bash
pip install --upgrade pandas
```

### 升级所有包
```bash
pip list --outdated
pip install --upgrade [package_name]
```

## 卸载

```bash
# 卸载项目和依赖
pip uninstall followup-processor pandas pydantic pyyaml -y

# 或直接删除虚拟环境
rm -rf venv
```

## IDE 配置

### Visual Studio Code

1. **安装Python扩展**
   - 搜索 "Python" 并安装 Microsoft 官方扩展

2. **配置Python解释器**
   - Ctrl+Shift+P
   - 输入 "Python: Select Interpreter"
   - 选择 `./venv/bin/python` (Linux/Mac) 或 `./venv/Scripts/python.exe` (Windows)

3. **配置测试**
   - Ctrl+Shift+P
   - 输入 "Python: Configure Tests"
   - 选择 "pytest"
   - 选择 "tests" 目录

### PyCharm

1. **设置解释器**
   - File → Settings → Project → Python Interpreter
   - 选择现有环境，指向虚拟环境

2. **配置测试框架**
   - File → Settings → Tools → Python Integrated Tools
   - 测试框架选择 "pytest"

## 故障排除

### 症状：`ModuleNotFoundError: No module named 'pandas'`

**解决**：
```bash
# 检查虚拟环境是否激活
which python  # 应显示虚拟环境路径

# 重新安装包
pip install pandas
```

### 症状：`Permission denied` 错误

**解决**：
```bash
# 使用虚拟环境避免权限问题
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 症状：旧版本包仍在使用

**解决**：
```bash
# 清除pip缓存并重新安装
pip cache purge
pip install --force-reinstall -e .
```

## 性能优化

### 加快导入速度

如果导入速度慢，可以：

1. **使用更快的 pip 镜像**
   ```bash
   pip install -i https://pypi.org/simple/ pandas
   ```

2. **并行安装**
   ```bash
   pip install --retries 5 -e .
   ```

## 下一步

安装完成后：

1. 阅读 `QUICKSTART.md` 了解快速开始
2. 运行示例脚本验证安装
3. 查看 `README.md` 了解完整文档

## 支持和帮助

- **官方文档**: https://docs.python.org/3/
- **Pandas**: https://pandas.pydata.org/
- **Pydantic**: https://pydantic-docs.helpmanual.io/
- **PyYAML**: https://pyyaml.org/
- **pytest**: https://docs.pytest.org/

---

**最后更新**: 2024年
**维护者**: CAD Research Team
