"""
一键式随访数据处理流程

从原始大文件中自动提取随访表Sheet并处理。
支持从包含多个Sheet的原始文件中提取"*随访表1"的Sheet，
重组为标准格式后进行纵向随访数据处理。

使用方法：
    python scripts/extract_and_process.py [原始文件路径.xlsx]

    如果不提供参数，会弹出文件选择对话框
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog, messagebox
import pandas as pd

# Set paths
project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from src.longitudinal_importer import LongitudinalDataImporter
from src.longitudinal_processor import LongitudinalEventProcessor
from src.logger import setup_logger


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
    logger = setup_logger("extract_followup")

    logger.info(f"\n正在读取原始文件: {input_file}")
    logger.info(f"文件大小: {input_file.stat().st_size / (1024*1024):.1f} MB")

    # 读取Excel文件
    logger.info("\n加载Excel文件 (这可能需要几分钟)...")
    xls = pd.ExcelFile(input_file)

    logger.info(f"文件共有 {len(xls.sheet_names)} 个sheet")

    # 找到所有包含"随访表1"的sheet
    followup_sheets = [name for name in xls.sheet_names if "随访表1" in name]
    logger.info(f"\n找到 {len(followup_sheets)} 个随访表1 sheet:")
    for i, name in enumerate(followup_sheets, 1):
        time_point = extract_time_point_from_sheet_name(name)
        logger.info(f"  {i}. {name} -> {time_point}")

    # 读取并重新组织数据
    logger.info("\n开始提取数据...")
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sheet_name in followup_sheets:
            logger.info(f"  处理: {sheet_name}")

            # 读取数据
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # 提取时间点作为新的sheet名称
            time_point = extract_time_point_from_sheet_name(sheet_name)

            # 清理sheet名称 (Excel sheet名称不能超过31字符)
            if len(time_point) > 31:
                time_point = time_point[:31]

            # 保存到新文件
            df.to_excel(writer, sheet_name=time_point, index=False)
            logger.info(f"    -> 导出为: {time_point} ({len(df)} 行)")

    logger.info(f"\n✓ 提取完成!")
    logger.info(f"输出文件: {output_file}")
    logger.info(f"输出文件大小: {output_file.stat().st_size / 1024:.1f} KB")


def select_excel_file() -> str:
    """打开文件选择对话框"""
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="选择原始数据文件（包含多个随访表Sheet）",
        initialdir=str(project_root / "data" / "raw"),
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
    )

    root.destroy()
    return file_path if file_path else None


def process_extracted_file(excel_file_path: str, patient_group: str = "CAG") -> bool:
    """
    处理提取后的文件

    Args:
        excel_file_path: 提取后的Excel文件路径
        patient_group: 患者组类型 (CAG/PCI)

    Returns:
        bool: 处理是否成功
    """
    logger = setup_logger("process_followup")

    logger.info("=" * 60)
    logger.info("开始处理纵向随访数据")
    logger.info(f"文件: {excel_file_path}")
    logger.info(f"患者组: {patient_group}")
    logger.info("=" * 60)

    try:
        # 1. 导入数据
        logger.info("\n步骤 1/3: 导入数据")
        importer = LongitudinalDataImporter()
        if not importer.load_excel_file(excel_file_path):
            logger.error("❌ 加载文件失败")
            return False
        logger.info(f"✅ 成功导入 {len(importer.sheet_data)} 个时间点的数据")

        # 2. 导入纵向数据
        logger.info("\n步骤 2/3: 导入纵向患者记录")
        longitudinal_records = importer.import_longitudinal_data()
        logger.info(f"✅ 成功导入 {len(longitudinal_records)} 条患者记录")

        # 3. 处理事件
        logger.info("\n步骤 3/3: 处理事件数据")
        processor = LongitudinalEventProcessor(endpoint="death")
        followup_records = processor.process_batch(longitudinal_records)
        logger.info(f"✅ 成功处理 {len(followup_records)} 条随访记录")

        # 4. 导出结果
        logger.info("\n步骤 4/4: 导出结果")
        output_data = [record.to_flattened_dict() for record in followup_records]
        df_output = pd.DataFrame(output_data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "output"
        output_dir.mkdir(exist_ok=True)

        # 导出完整Excel
        output_filename = f"{patient_group}_followup_results_{timestamp}.xlsx"
        output_path = output_dir / output_filename
        df_output.to_excel(output_path, index=False, engine="openpyxl")
        logger.info(f"✅ Excel已导出: {output_filename}")

        # 导出生存分析CSV
        survival_filename = f"survival_{patient_group}_{timestamp}.csv"
        try:
            survival_cols = [
                "patient_id",
                "patient_name",
                "birthday",
                "age",
                "gender",
                "group_name",
                "enrollment_date",
                "survival_time_days",
                "event_occurred",
                "endpoint_event",
            ]
            existing_cols = [c for c in survival_cols if c in df_output.columns]
            survival_df = df_output[existing_cols].copy()

            survival_path = output_dir / survival_filename
            survival_df.to_csv(survival_path, index=False)
            logger.info(f"✅ 生存分析CSV已导出: {survival_filename}")
        except Exception as e:
            logger.warning(f"⚠️ 生存分析CSV导出失败: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ 处理完成！")
        logger.info("=" * 60)
        logger.info(f"输出文件:")
        logger.info(f"  - {output_filename}")
        logger.info(f"  - {survival_filename}")
        logger.info(f"患者数量: {len(followup_records)}")

        # 统计信息
        has_event = sum(1 for r in followup_records if r.first_event_date is not None)
        logger.info(f"\n统计:")
        logger.info(f"  - 总患者数: {len(followup_records)}")
        logger.info(
            f"  - 发生事件: {has_event} ({has_event/len(followup_records)*100:.1f}%)"
        )
        logger.info(f"  - 无事件: {len(followup_records) - has_event}")
        
        # 详细事件分布
        logger.info(f"\n详细事件分布:")
        event_details = {
            "心绞痛": df_output["first_angina_date"].notna().sum() if "first_angina_date" in df_output.columns else 0,
            "住院": df_output["first_hospitalization_date"].notna().sum() if "first_hospitalization_date" in df_output.columns else 0,
            "心肌梗死": df_output["first_mi_date"].notna().sum() if "first_mi_date" in df_output.columns else 0,
            "心衰": df_output["first_heart_failure_date"].notna().sum() if "first_heart_failure_date" in df_output.columns else 0,
            "血运重建": df_output["first_revascularization_date"].notna().sum() if "first_revascularization_date" in df_output.columns else 0,
            "死亡": df_output["first_death_date"].notna().sum() if "first_death_date" in df_output.columns else 0,
        }
        for event_name, count in event_details.items():
            if count > 0:
                logger.info(f"  - {event_name}: {count} 例")

        return True

    except Exception as e:
        logger.error(f"\n❌ 处理失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger = setup_logger("extract_and_process")

    logger.info("\n" + "=" * 60)
    logger.info("随访表自动提取和处理工具")
    logger.info("=" * 60)

    # 获取源文件路径
    if len(sys.argv) > 1:
        source_file = sys.argv[1]
    else:
        logger.info("\n请选择包含随访表Sheet的原始Excel文件...")
        source_file = select_excel_file()

    if not source_file:
        logger.warning("未选择文件，程序退出")
        return

    if not Path(source_file).exists():
        logger.error(f"文件不存在: {source_file}")
        return

    # 检测患者组类型
    patient_group = "CAG"  # 默认
    filename = Path(source_file).name.upper()
    if "PCI" in filename:
        patient_group = "PCI"
    elif "CAG" in filename:
        patient_group = "CAG"
    else:
        # 询问用户
        root = Tk()
        root.withdraw()
        response = messagebox.askquestion(
            "患者组类型",
            "这是 PCI 组患者吗？\n\n是 = PCI组\n否 = CAG组",
            icon="question",
        )
        patient_group = "PCI" if response == "yes" else "CAG"
        root.destroy()

    logger.info(f"\n识别为: {patient_group} 组")

    # 步骤1: 提取随访表Sheet
    logger.info("\n" + "=" * 60)
    logger.info("步骤 1/2: 从原始文件提取随访表1数据")
    logger.info("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source_path = Path(source_file)
    output_filename = f"extracted_{source_path.stem}_{timestamp}.xlsx"
    extracted_file = project_root / "data" / "raw" / output_filename

    try:
        extract_followup_sheets(Path(source_file), extracted_file)
    except Exception as e:
        logger.error(f"\n提取失败: {e}")
        input("\n按回车键退出...")
        return

    # 步骤2: 处理提取后的文件
    logger.info("\n" + "=" * 60)
    logger.info("步骤 2/2: 处理数据并生成输出")
    logger.info("=" * 60)

    success = process_extracted_file(str(extracted_file), patient_group=patient_group)

    if success:
        logger.info("\n🎉 全部完成！")

        # 询问是否保留中间文件
        root = Tk()
        root.withdraw()
        keep_file = messagebox.askquestion(
            "保留中间文件？",
            f"是否保留提取的临时文件？\n\n{extracted_file}\n\n"
            f"（文件已保存在 data/raw/ 目录，可用于后续处理）",
            icon="question",
        )
        root.destroy()

        if keep_file == "no":
            try:
                extracted_file.unlink()
                logger.info(f"已删除临时文件: {extracted_file}")
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
    else:
        logger.error("\n处理失败")

    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
