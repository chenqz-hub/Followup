"""
CAG组患者纵向随访数据处理脚本
适用于CAG组患者的标准表格格式（如PSM93）
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog

# Set paths
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / 'src'))

# Import modules
from config import Config
from longitudinal_importer import LongitudinalDataImporter
from longitudinal_processor import LongitudinalEventProcessor
import pandas as pd


def select_excel_file(default_path: str = None) -> str:
    """
    打开文件选择对话框，让用户选择Excel文件
    
    Args:
        default_path: 默认文件路径（可选）
    
    Returns:
        选择的文件路径，如果取消则返回None
    """
    root = Tk()
    root.withdraw()  # 隐藏主窗口
    root.attributes('-topmost', True)  # 窗口置顶
    
    # 设置初始目录
    initial_dir = str(project_root / 'data')
    if default_path and Path(default_path).exists():
        initial_dir = str(Path(default_path).parent)
    
    file_path = filedialog.askopenfilename(
        title='选择CAG组患者数据文件',
        initialdir=initial_dir,
        filetypes=[
            ('Excel files', '*.xlsx *.xls'),
            ('All files', '*.*')
        ]
    )
    
    root.destroy()
    return file_path if file_path else None


def process_cag_patients(excel_file_path: str, endpoint: str = 'death'):
    """
    处理CAG组患者数据
    
    Args:
        excel_file_path: Excel文件路径
        endpoint: 终点事件类型
            - 'death': 死亡（默认）
            - 'mace': 主要不良心血管事件（死亡+MI+血运重建）
            - 'mi': 心肌梗死
            - 'angina': 心绞痛
            - 'heart_failure': 心衰
            - 'revascularization': 血运重建
            - 'hospitalization': 住院
            - 'any_event': 任何事件
    
    Returns:
        bool: 处理是否成功
    """
    
    print("="*70)
    print("CAG Patient Longitudinal Followup Data Processing")
    print("="*70)
    
    # Step 1: Load Excel file
    print("\nStep 1: Loading Excel file...")
    print(f"  File: {excel_file_path}")
    
    importer = LongitudinalDataImporter()
    if not importer.load_excel_file(excel_file_path):
        print("  ERROR: Failed to load Excel file")
        return False
    
    print(f"  OK: Loaded {len(importer.sheet_data)} sheets")
    
    # Step 2: Import and merge longitudinal data
    print("\nStep 2: Importing and merging longitudinal data...")
    longitudinal_records = importer.import_longitudinal_data()
    
    if not longitudinal_records:
        print("  ERROR: No data imported")
        return False
    
    print(f"  OK: Imported {len(longitudinal_records)} patient records")
    
    # Display sample
    if longitudinal_records:
        sample = longitudinal_records[0]
        print(f"\n  Sample patient {sample.patient_id}:")
        print(f"    Enrollment: {sample.enrollment_date}")
        print(f"    Timepoints: {len(sample.time_points)}")
        print(f"    Latest followup: {sample.latest_followup_date}")
    
    # Step 3: Process with specified endpoint
    print(f"\nStep 3: Processing with '{endpoint}' endpoint...")
    processor = LongitudinalEventProcessor(endpoint=endpoint)
    
    try:
        followup_records = processor.process_batch(longitudinal_records)
        print(f"  OK: Processed {len(followup_records)} records (0 errors)")
    except Exception as e:
        print(f"  ERROR: Processing failed: {e}")
        return False
    
    # Event statistics
    print("\n  Event distribution:")
    event_counts = {}
    for record in followup_records:
        event_type = record.first_event_type or 'no_event'
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    for event_type, count in sorted(event_counts.items()):
        percentage = (count / len(followup_records)) * 100
        print(f"    {event_type}: {count} ({percentage:.1f}%)")
    
    # Step 4: Export results
    print("\nStep 4: Exporting results...")
    
    # Convert to dictionary list
    output_data = [record.to_flattened_dict() for record in followup_records]
    
    # Extract file identifier from input filename
    input_filename = Path(excel_file_path).stem
    file_identifier = "cag"
    if "PSM" in input_filename:
        # Extract PSM93 or similar
        import re
        match = re.search(r'PSM\d+', input_filename)
        if match:
            file_identifier = match.group(0).lower()
    
    # Output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to Excel
    try:
        df = pd.DataFrame(output_data)
        
        excel_file = f"longitudinal_{file_identifier}_output_{timestamp}.xlsx"
        excel_path = output_dir / excel_file
        df.to_excel(str(excel_path), sheet_name='Followup Data', index=False)
        
        print(f"  OK: Excel exported to output/{excel_file}")
        print(f"      Total columns: {len(df.columns)}")
        print(f"      Total records: {len(output_data)}")
    except Exception as e:
        print(f"  ERROR: Excel export failed: {e}")
        return False
    
    # Export survival dataset CSV
    try:
        survival_cols = [
            'patient_id',
            'patient_name',
            'birthday',
            'age',
            'gender',
            'group_name',
            'enrollment_date',
            'survival_time_days',
            'event_occurred',
            'endpoint_event'
        ]
        
        existing_cols = [c for c in survival_cols if c in df.columns]
        survival_df = df[existing_cols].copy()
        
        survival_file = f"survival_{file_identifier}_{timestamp}.csv"
        survival_path = output_dir / survival_file
        survival_df.to_csv(str(survival_path), index=False)
        
        print(f"  OK: Survival CSV exported to output/{survival_file}")
    except Exception as e:
        print(f"  WARNING: Failed to export survival CSV: {e}")
    
    print("\n" + "="*70)
    print("Processing completed!")
    print("="*70)
    
    return True


def main():
    """主函数 - CAG组患者数据处理"""
    
    # ====== 配置区域 ======
    # 1. 设置Excel文件路径（默认路径，可通过对话框修改）
    default_excel_file = r"d:\git\Followup\data\extracted_PSM93_cases_20251104_221914_随访表1_20251106_121718.xlsx"
    
    # 2. 设置终点事件类型
    # 可选值: 'death', 'mace', 'mi', 'angina', 'heart_failure', 
    #         'revascularization', 'hospitalization', 'any_event'
    endpoint = 'death'
    
    # =====================
    
    print("\n" + "="*70)
    print("CAG Patient Data Processing - File Selection")
    print("="*70)
    print("\n请选择要处理的Excel文件...")
    
    # 打开文件选择对话框
    excel_file = select_excel_file(default_excel_file)
    
    if not excel_file:
        print("\n❌ 未选择文件，程序退出。")
        return False
    
    print(f"\n✅ 已选择文件: {excel_file}")
    
    # 检查文件是否存在
    if not Path(excel_file).exists():
        print(f"\nERROR: File not found: {excel_file}")
        return False
    
    # 处理数据
    success = process_cag_patients(excel_file, endpoint)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
