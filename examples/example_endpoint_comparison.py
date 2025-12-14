"""
示例：比较不同终点事件的生存分析结果

演示如何使用不同的终点事件（death, MACE, MI, angina等）
"""

import sys
from pathlib import Path

# 添加父目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
from config import Config
from longitudinal_importer import LongitudinalDataImporter
from longitudinal_processor import LongitudinalEventProcessor


def process_with_endpoint(file_path: str, endpoint: str) -> pd.DataFrame:
    """
    使用指定终点事件处理数据
    
    Args:
        file_path: Excel文件路径
        endpoint: 终点事件类型 (death/mace/mi/angina/heart_failure/revascularization/hospitalization/any_event)
    
    Returns:
        包含生存分析结果的DataFrame
    """
    # 加载配置
    config = Config()
    
    # 导入数据
    importer = LongitudinalDataImporter()
    importer.load_excel_file(file_path)
    patient_records = importer.import_longitudinal_data()
    
    # 使用指定终点处理
    processor = LongitudinalEventProcessor(endpoint=endpoint)
    followup_records = []
    for patient_record in patient_records:
        try:
            followup_record = processor.process_followup(patient_record)
            followup_records.append(followup_record)
        except Exception as e:
            print(f"处理患者{patient_record.patient_id}时出错: {e}")
    
    # 转换为DataFrame
    data = [record.to_flattened_dict() for record in followup_records]
    df = pd.DataFrame(data)
    
    return df


def compare_endpoints():
    """比较不同终点事件的结果"""
    
    file_path = project_root / "data" / "extracted_PSM93_cases_20251104_221914_随访表1_20251106_121718.xlsx"
    
    # 定义要测试的终点事件
    endpoints = {
        'death': 'Death',
        'mace': 'MACE',
        'mi': 'MI',
        'angina': 'Angina',
        'heart_failure': 'Heart Failure',
        'revascularization': 'Revascularization',
        'hospitalization': 'Hospitalization',
        'any_event': 'Any Event'
    }
    
    print("\n" + "="*80)
    print("Comparison of Different Survival Analysis Endpoints")
    print("="*80)
    
    results = {}
    
    for endpoint_code, endpoint_name in endpoints.items():
        print(f"\nProcessing endpoint: {endpoint_name} ({endpoint_code})...")
        df = process_with_endpoint(str(file_path), endpoint_code)
        
        # 统计结果
        total = len(df)
        events = df['event_occurred'].sum() if 'event_occurred' in df.columns else 0
        censored = total - events
        event_rate = events / total * 100 if total > 0 else 0
        mean_survival = df['survival_time_days'].mean() if 'survival_time_days' in df.columns else 0
        
        results[endpoint_name] = {
            'endpoint_code': endpoint_code,
            'total': total,
            'events': events,
            'censored': censored,
            'event_rate': event_rate,
            'mean_survival_days': mean_survival
        }
        
        print(f"  OK: Total={total}, Events={events} ({event_rate:.1f}%), Censored={censored}, Mean survival={mean_survival:.1f} days")
    
    # 生成对比表
    print("\n" + "="*80)
    print("Summary Table")
    print("="*80)
    print(f"{'Endpoint':<20} {'Total':<8} {'Events':<8} {'Rate %':<10} {'Mean Days':<12}")
    print("-"*80)
    
    for endpoint_name, stats in results.items():
        print(f"{endpoint_name:<20} {stats['total']:<8} {stats['events']:<8} "
              f"{stats['event_rate']:>6.1f}%    {stats['mean_survival_days']:>10.1f}")
    
    print("\n" + "="*80)
    print("Notes:")
    print("  - death: Only death as endpoint")
    print("  - MACE: Major Adverse Cardiovascular Event (death + MI + revascularization)")
    print("  - any_event: Any adverse event as endpoint (most inclusive)")
    print("="*80)


if __name__ == "__main__":
    compare_endpoints()
