#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动从原始大文件中提取随访表1数据

此脚本直接从原始数据文件中提取所有"随访表1" sheet，
并重新组织成适合longitudinal处理流程的格式。

使用方法:
    python extract_followup_sheets.py [input_file] [output_file]

如果不提供参数，将使用默认路径。
"""

import sys
import re
from pathlib import Path
from datetime import datetime

import pandas as pd


def extract_time_point_from_sheet_name(sheet_name: str) -> str:
    """
    从sheet名称中提取时间点信息

    例如: '第三个月随访_CAGSFB1_627CAG随访表1' -> '3个月'
          '第12个月随访_CAGSFB1_627CAG随访表1' -> '12个月'
    """
    # 中文数字到阿拉伯数字的映射
    chinese_to_arabic = {
        "一": "1",
        "二": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
        "十": "10",
    }

    # 尝试匹配"第X个月"或"第X月" (阿拉伯数字)
    match = re.search(r"第(\d+)个?月", sheet_name)
    if match:
        months = match.group(1)
        return f"{months}个月"

    # 尝试匹配中文数字 "第X个月" 或 "第X月"
    for chinese, arabic in chinese_to_arabic.items():
        # 匹配 "第三个月" 或 "第三月"
        match = re.search(rf"第{chinese}个?月", sheet_name)
        if match:
            return f"{arabic}个月"

    # 如果是personal或其他格式，返回sheet名称
    return sheet_name


def extract_followup_sheets(input_file: Path, output_file: Path) -> None:
    """
    从原始文件中提取所有随访表1数据并保存

    Args:
        input_file: 原始Excel文件路径
        output_file: 输出Excel文件路径
    """
    print(f"\n正在读取原始文件: {input_file}")
    print(f"文件大小: {input_file.stat().st_size / (1024*1024):.1f} MB")

    # 读取Excel文件
    print("\n加载Excel文件 (这可能需要几分钟)...")
    xls = pd.ExcelFile(input_file)

    print(f"文件共有 {len(xls.sheet_names)} 个sheet")

    # 找到所有包含"随访表1"的sheet
    followup_sheets = [name for name in xls.sheet_names if "随访表1" in name]
    print(f"\n找到 {len(followup_sheets)} 个随访表1 sheet:")
    for i, name in enumerate(followup_sheets, 1):
        time_point = extract_time_point_from_sheet_name(name)
        print(f"  {i}. {name} -> {time_point}")

    # 读取并重新组织数据
    print("\n开始提取数据...")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sheet_name in followup_sheets:
            print(f"  处理: {sheet_name}")

            # 读取数据
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # 提取时间点作为新的sheet名称
            time_point = extract_time_point_from_sheet_name(sheet_name)

            # 清理sheet名称 (Excel sheet名称不能超过31字符)
            if len(time_point) > 31:
                time_point = time_point[:31]

            # 保存到新文件
            df.to_excel(writer, sheet_name=time_point, index=False)
            print(f"    -> 导出为: {time_point} ({len(df)} 行)")

    print(f"\n✓ 提取完成!")
    print(f"输出文件: {output_file}")
    print(f"输出文件大小: {output_file.stat().st_size / 1024:.1f} KB")


def detect_patient_group(filename: str) -> str:
    """
    从文件名中识别患者组类型
    
    Args:
        filename: 文件名
        
    Returns:
        患者组类型: "PCI" 或 "CAG"
    """
    filename_upper = filename.upper()
    if "PCI" in filename_upper:
        return "PCI"
    elif "CAG" in filename_upper:
        return "CAG"
    return "Unknown"


def main():
    """主函数"""
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    
    # 从命令行参数获取路径（如果提供）
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        # 没有提供参数，默认使用CAG组文件
        default_input = data_dir / "20250924  CAG 组.xlsx"
        input_file = default_input

    # 验证输入文件存在
    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        print(f"\n提示: 请指定输入文件路径，例如:")
        print(f'  python scripts/extract_followup_sheets.py "data/raw/20250924  PCI组.xlsx"')
        sys.exit(1)

    # 自动识别患者组类型并生成输出文件名
    patient_group = detect_patient_group(input_file.name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        # 根据患者组类型生成输出文件名
        output_filename = f"extracted_{patient_group}_followup_{timestamp}.xlsx"
        output_file = data_dir / output_filename

    # 验证输入文件存在
    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)

    # 确保输出目录存在
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 显示处理信息
    print(f"\n{'='*60}")
    print(f"随访表自动提取工具")
    print(f"{'='*60}")
    print(f"输入文件: {input_file.name}")
    print(f"患者组: {patient_group}")
    print(f"输出文件: {output_file.name}")
    print(f"{'='*60}")

    # 提取数据
    try:
        extract_followup_sheets(input_file, output_file)
        print(f"\n现在可以使用以下脚本处理提取的数据:")
        print(f"  python scripts/followup_data_processor.py")
        print(f"  (然后选择文件: {output_file.name})")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
