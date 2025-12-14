"""
纵向随访数据处理完整流程 - 英文输出版本，可避免编码问题
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Set paths
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / 'src'))

# Import modules
from config import Config
from longitudinal_importer import LongitudinalDataImporter
from longitudinal_processor import LongitudinalEventProcessor

def main():
    """Main processing flow"""
    
    print("=" * 60)
    print("Longitudinal CAD Patient Followup Data Processing")
    print("=" * 60)
    
    # Step 1: Load configuration
    print("\nStep 1: Loading configuration...")
    try:
        config = Config()
        print("  OK: Configuration loaded")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False
    
    # Step 2: Initialize importer
    print("\nStep 2: Initializing importer...")
    importer = LongitudinalDataImporter()
    
    # Step 3: Load Excel file
    template_file = r"d:\git\Followup\data\extracted_PSM93_cases_20251104_221914_随访表1_20251106_121718.xlsx"
    print(f"\nStep 3: Loading Excel file...")
    print(f"  File: {template_file}")
    
    if not importer.load_excel_file(template_file):
        print("  ERROR: Failed to load Excel file")
        return False
    
    print(f"  OK: Loaded {len(importer.sheet_data)} sheets")
    for sheet_name in importer.sheet_data.keys():
        print(f"    - {sheet_name}")
    
    # Step 4: Import longitudinal data
    print("\nStep 4: Importing and merging longitudinal data...")
    longitudinal_records = importer.import_longitudinal_data()
    print(f"  OK: Imported {len(longitudinal_records)} patient records")
    
    if not longitudinal_records:
        print("  ERROR: No data imported")
        return False
    
    # Display summary
    print("\n  First 3 patient summaries:")
    for i, record in enumerate(longitudinal_records[:3], 1):
        print(f"    {i}. Patient {record.patient_id}: "
              f"enrolled {record.enrollment_date}, "
              f"latest followup {record.latest_followup_date} ({record.latest_followup_months}M), "
              f"{record.days_to_latest_followup} days follow-up")
    
    # Step 5: Initialize event processor
    print("\nStep 5: Initializing event processor...")
    # You can change the endpoint here:
    # - 'death': 死亡（默认）
    # - 'mace': 主要不良心血管事件（死亡+MI+血运重建）
    # - 'mi': 心肌梗死
    # - 'angina': 心绞痛
    # - 'heart_failure': 心衰
    # - 'revascularization': 血运重建
    # - 'hospitalization': 住院
    # - 'any_event': 任何事件
    endpoint = 'death'  # Change this to your desired endpoint
    processor = LongitudinalEventProcessor(endpoint=endpoint)
    print(f"  Using endpoint: {endpoint}")
    
    # Step 6: Process events
    print("\nStep 6: Identifying events and calculating metrics...")
    followup_records = processor.process_batch(longitudinal_records)
    print(f"  OK: Processed {len(followup_records)} followup records")
    
    # Event statistics
    print("\n  Event distribution:")
    event_counts = {}
    for record in followup_records:
        event_type = record.first_event_type or 'no_event'
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    for event_type, count in sorted(event_counts.items()):
        percentage = (count / len(followup_records)) * 100
        print(f"    {event_type}: {count} ({percentage:.1f}%)")
    
    # Step 7: Export results
    print("\nStep 7: Exporting results...")
    
    import pandas as pd
    
    # Convert to dictionary list
    output_data = [record.to_flattened_dict() for record in followup_records]
    
    # Output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"longitudinal_followup_output_{timestamp}.xlsx"
    output_path = project_root / "output" / output_file
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Export to Excel
    try:
        df = pd.DataFrame(output_data)
        df.to_excel(str(output_path), sheet_name='Followup Data', index=False)
        print(f"  OK: Results exported to output/{output_file}")
        print(f"      Total records: {len(output_data)}")
    except Exception as e:
        print(f"  ERROR: Export failed: {e}")
        return False

    # Additionally export a survival dataset CSV for Cox/regression analysis
    try:
        survival_cols = [
            'patient_id',
            'survival_time_days',
            'event_occurred',
            'age',
            'gender',
            'group_name',
            'enrollment_date'
        ]

        # Keep only the columns that actually exist in the dataframe
        existing_cols = [c for c in survival_cols if c in df.columns]
        survival_df = df[existing_cols].copy()

        survival_file = f"survival_dataset_{timestamp}.csv"
        survival_path = project_root / "output" / survival_file
        survival_df.to_csv(str(survival_path), index=False)
        print(f"  OK: Survival dataset exported to output/{survival_file}")
    except Exception as e:
        print(f"  WARNING: Failed to export survival CSV: {e}")
    
    # Step 8: Display sample output
    print("\nStep 8: Sample output data:")
    if followup_records:
        sample = followup_records[0]
        print(f"  Patient {sample.patient_id}:")
        print(f"    Enrollment date: {sample.enrollment_date}")
        print(f"    Latest followup date: {sample.latest_followup_date}")
        print(f"    Days to latest followup: {sample.days_to_latest_followup}")
        print(f"    First event type: {sample.first_event_type}")
        print(f"    First event date: {sample.first_event_date}")
        print(f"    Days to first event: {sample.days_to_first_event}")
        print(f"    Followup status: {sample.total_followup_status}")
    
    print("\n" + "=" * 60)
    print("Processing completed successfully!")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
