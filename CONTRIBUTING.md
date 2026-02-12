# 贡献指南

感谢您对本项目的关注！我们欢迎任何形式的贡献。

## 贡献方式

### 报告问题
- 使用GitHub Issues报告bug
- 清晰描述问题和复现步骤
- 包含相关的日志和错误信息
- 说明您的环境（Python版本、操作系统等）

### 提出新功能
- 在Issues中描述功能需求
- 说明使用场景和预期效果
- 讨论实现方案

### 提交代码
1. **Fork项目**
2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **编写代码**
   - 遵循项目代码规范
   - 添加必要的测试
   - 更新相关文档
4. **运行测试**
   ```bash
   make all
   ```
5. **提交更改**
   ```bash
   git commit -m "feat: add amazing feature"
   ```
6. **推送分支**
   ```bash
   git push origin feature/your-feature-name
   ```
7. **创建Pull Request**

## 代码规范

### 开发环境设置
```bash
# 克隆您fork的仓库
git clone https://github.com/your-username/Followup.git
cd Followup

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装开发依赖
pip install -e ".[dev]"

# 设置pre-commit hooks
pre-commit install
```

### 代码风格
- 遵循PEP 8规范
- 使用Black格式化代码（行长100）
- 使用Flake8检查代码风格
- 使用isort排序导入

### 类型注解
- 为函数参数和返回值添加类型注解
- 使用Mypy进行类型检查
- 复杂类型使用typing模块

### 文档字符串
使用Google风格的docstring：
```python
def process_data(input_path: str, output_path: str) -> bool:
    """
    处理数据文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
    
    Returns:
        处理是否成功
    
    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 数据格式错误
    """
```

### 测试
- 为新功能编写测试
- 确保测试覆盖率不降低
- 运行所有测试确保通过
- 测试文件命名：`test_*.py`
- 测试类命名：`Test*`
- 测试方法命名：`test_*`

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_config.py

# 查看覆盖率
pytest --cov=src --cov-report=html
```

### 提交信息
使用约定式提交格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型(type):**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构代码
- `test`: 测试相关
- `chore`: 构建/工具链相关

**示例:**
```
feat(importer): add support for JSON data source

- Implement JSONDataSource class
- Add tests for JSON import
- Update documentation

Closes #123
```

## Pull Request流程

### 提交前检查
- [ ] 代码通过所有测试
- [ ] 代码风格检查通过
- [ ] 类型检查通过
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] CHANGELOG.md已更新

### PR描述模板
```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新

## 变更说明
<!-- 简要描述本次变更 -->

## 相关Issue
Closes #(issue编号)

## 测试
<!-- 描述测试情况 -->
- [ ] 添加了新测试
- [ ] 更新了现有测试
- [ ] 所有测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的文档
- [ ] 更新了CHANGELOG
```

### Review流程
1. 至少一名维护者审核
2. 所有讨论需要解决
3. CI检查必须通过
4. 获得批准后合并

## 项目结构

理解项目结构有助于更好地贡献：

```
src/                    # 核心代码包
├── config.py          # 配置管理
├── data_models.py     # 数据模型
├── data_importer.py   # 数据导入
├── data_exporter.py   # 数据导出
├── event_processor.py # 事件处理
└── logger.py          # 日志系统

tests/                  # 测试代码
├── conftest.py        # pytest配置
└── test_*.py          # 测试文件

docs/                   # 文档
scripts/                # 运行脚本
config/                 # 配置文件
```

## 开发建议

### 添加新功能
1. 在Issues中讨论功能设计
2. 创建feature分支
3. 实现功能（保持小步提交）
4. 编写测试
5. 更新文档
6. 提交PR

### 修复Bug
1. 在Issues中报告bug
2. 创建bugfix分支
3. 编写测试重现bug
4. 修复bug
5. 确保测试通过
6. 提交PR

### 改进文档
- 修正错别字和语法错误
- 添加示例和说明
- 改进代码注释
- 更新README和指南

## 社区准则

### 行为准则
- 尊重所有贡献者
- 提供建设性反馈
- 专注于技术讨论
- 保持友好和专业

### 沟通
- 使用GitHub Issues讨论问题
- PR中清晰表达意图
- 及时回复评论和反馈

## 许可证

贡献的代码将在MIT许可证下发布。

## 问题？

如有疑问，请：
- 查看[开发文档](docs/DEVELOPMENT.md)
- 在Issues中提问
- 联系项目维护者

再次感谢您的贡献！
