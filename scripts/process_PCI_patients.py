"""
PCI组患者纵向随访数据处理脚本（scripts/ 版本）
此文件是对根目录脚本的轻微修改：`project_root` 指向仓库根目录。
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog

# Set paths (project root is repo root)
project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

# Import modules
from src.config import Config
from src.longitudinal_importer import LongitudinalDataImporter
from src.longitudinal_processor import LongitudinalEventProcessor
import pandas as pd


def select_excel_file(default_path: str = None) -> str:
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    initial_dir = str(project_root / "data")
    if default_path and Path(default_path).exists():
        initial_dir = str(Path(default_path).parent)
    file_path = filedialog.askopenfilename(
        title="选择PCI组患者数据文件",
        initialdir=initial_dir,
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
    )
    root.destroy()
    return file_path if file_path else None


def process_pci_patients(excel_file_path: str, endpoint: str = "death"):
    # (simplified runner) - core logic uses existing importer/processor
    print("Processing (scripts/process_PCI_patients.py)")
    importer = LongitudinalDataImporter()
    if not importer.load_excel_file(excel_file_path):
        print("ERROR: Failed to load Excel file")
        return False
    longitudinal_records = importer.import_longitudinal_data()
    processor = LongitudinalEventProcessor(endpoint=endpoint)
    followup_records = processor.process_batch(longitudinal_records)
    output_data = [record.to_flattened_dict() for record in followup_records]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(output_data)
    excel_file = f"longitudinal_pci_output_{timestamp}.xlsx"
    excel_path = output_dir / excel_file
    df.to_excel(str(excel_path), sheet_name="Followup Data", index=False)
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
    existing_cols = [c for c in survival_cols if c in df.columns]
    survival_df = df[existing_cols].copy()
    survival_file = f"survival_pci_{timestamp}.csv"
    survival_path = output_dir / survival_file
    survival_df.to_csv(str(survival_path), index=False)
    print(f"Exported: {excel_file}, {survival_file}")
    return True


def main():
    default_excel_file = str(
        project_root
        / "data"
        / "extracted_PSM186_PCI_cases_20251104_222503_随访表1_20251106_121852.xlsx"
    )
    endpoint = "death"
    excel_file = select_excel_file(default_excel_file)
    if not excel_file:
        print("No file selected")
        return False
    return process_pci_patients(excel_file, endpoint)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
