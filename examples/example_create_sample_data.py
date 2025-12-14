"""
示例脚本2：创建示例数据
如何生成示例CSV文件用于测试
"""

import csv
from datetime import date, timedelta
import random
from pathlib import Path


def create_sample_data():
    """
    创建示例数据文件
    """
    print("\n" + "="*60)
    print("示例 2: 创建示例数据")
    print("="*60)
    
    # 确保data目录存在
    Path('data').mkdir(exist_ok=True)
    
    # 生成示例患者数据
    output_file = 'data/sample_patients.csv'
    
    # 定义列名
    fieldnames = [
        'patient_id',
        'enrollment_date',
        'age',
        'gender',
        'death_date',
        'mi_date',
        'stroke_date',
        'revascularization_date',
        'hospitalization_date'
    ]
    
    # 生成示例数据
    base_date = date(2020, 1, 1)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(1, 51):  # 生成50条示例患者数据
            enrollment_date = base_date + timedelta(days=i*7)
            
            # 50% 的患者有至少一个事件
            has_event = random.random() < 0.5
            
            row = {
                'patient_id': f'CAD-2020-{i:04d}',
                'enrollment_date': enrollment_date.strftime('%Y-%m-%d'),
                'age': random.randint(40, 80),
                'gender': random.choice(['M', 'F']),
                'death_date': '',
                'mi_date': '',
                'stroke_date': '',
                'revascularization_date': '',
                'hospitalization_date': '',
            }
            
            if has_event:
                # 随机分配事件
                event_type = random.choice([
                    'death_date',
                    'mi_date',
                    'stroke_date',
                    'revascularization_date',
                    'hospitalization_date'
                ])
                
                event_date = enrollment_date + timedelta(days=random.randint(30, 730))
                row[event_type] = event_date.strftime('%Y-%m-%d')
                
                # 某些患者有多个事件
                if random.random() < 0.3:
                    second_event_type = random.choice([
                        'death_date',
                        'mi_date',
                        'stroke_date',
                        'revascularization_date',
                        'hospitalization_date'
                    ])
                    if second_event_type != event_type:
                        second_event_date = event_date + timedelta(days=random.randint(30, 365))
                        row[second_event_type] = second_event_date.strftime('%Y-%m-%d')
            
            writer.writerow(row)
    
    print(f"\n✓ 示例数据已创建: {output_file}")
    print(f"  包含 50 条患者记录，约 50% 的患者有随访事件")
    
    # 显示前几行
    print("\n示例数据预览:")
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < 3:
                print(f"\n  记录 {i+1}:")
                print(f"    患者ID: {row['patient_id']}")
                print(f"    入组日期: {row['enrollment_date']}")
                print(f"    年龄: {row['age']}")
                print(f"    事件: ", end='')
                events = [
                    f for f in fieldnames[4:]
                    if row.get(f)
                ]
                print(", ".join(events) if events else "无")
            else:
                break
    
    print("\n" + "="*60)
    print("✓ 示例 2 完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    create_sample_data()
