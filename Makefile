# Makefile for Followup project

.PHONY: help install install-dev test coverage lint format type-check clean all

# 默认目标
.DEFAULT_GOAL := help

# 帮助信息
help:
	@echo "Followup 项目管理命令"
	@echo ""
	@echo "使用方法: make [target]"
	@echo ""
	@echo "可用目标:"
	@echo "  install       - 安装项目依赖"
	@echo "  install-dev   - 安装开发依赖"
	@echo "  test          - 运行所有测试"
	@echo "  coverage      - 运行测试并生成覆盖率报告"
	@echo "  lint          - 运行代码风格检查"
	@echo "  format        - 格式化代码"
	@echo "  type-check    - 运行类型检查"
	@echo "  clean         - 清理临时文件"
	@echo "  all           - 运行所有检查和测试"
	@echo "  pre-commit    - 安装pre-commit hooks"

# 安装项目依赖
install:
	pip install -e .

# 安装开发依赖
install-dev:
	pip install -e ".[dev]"

# 安装pre-commit hooks
pre-commit:
	pre-commit install

# 运行测试
test:
	pytest

# 运行测试并生成覆盖率报告
coverage:
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "覆盖率报告已生成: htmlcov/index.html"

# 代码风格检查
lint:
	flake8 src tests scripts
	@echo "✓ Flake8 检查通过"

# 格式化代码
format:
	isort src tests scripts
	black src tests scripts
	@echo "✓ 代码已格式化"

# 类型检查
type-check:
	mypy src
	@echo "✓ 类型检查通过"

# 运行所有检查
all: format lint type-check test
	@echo "✓ 所有检查通过"

# 清理临时文件
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✓ 清理完成"
