import json
import traceback

def debug_stations():
    """调试站点数据中detail字段的问题"""
    print("开始调试站点详细信息问题...")
    
    # 模拟前端生成的站点数据
    sample_stations = [
        {
            "index": 1,
            "name": "测试站点1",
            "type": "公交站",
            "distance": "300",
            "detail": "这是测试站点1的详细信息",
            "location": {"lng": 116.123, "lat": 39.456}
        },
        {
            "index": 2,
            "name": "测试站点2",
            "type": "地铁站",
            "distance": "500",
            # 没有detail字段，但有address字段
            "address": "这是测试站点2的地址信息",
            "location": {"lng": 116.234, "lat": 39.567}
        },
        {
            "index": 3,
            "name": "测试站点3",
            "type": "公交站",
            "distance": "400",
            # 既没有detail也没有address字段
            "location": {"lng": 116.345, "lat": 39.678}
        }
    ]
    
    print("\n模拟站点数据:")
    for s in sample_stations:
        print(f"  {s['name']}: {s}")
    
    # 测试如何从站点数据中提取详细信息
    print("\n提取的详细信息:")
    for idx, station in enumerate(sample_stations):
        # 正确的提取方式
        detail = station.get('detail', station.get('address', '无详细信息'))
        
        # 当前代码中的提取方式
        old_detail = station.get('address', '无详细信息')
        
        print(f"站点 {idx+1}: {station.get('name', '')}")
        print(f"  - 正确提取: {detail}")
        print(f"  - 当前提取: {old_detail}")
        print(f"  - 字段存在: detail={'detail' in station}, address={'address' in station}")
    
    print("\n调试结论:")
    print("1. 前端代码将站点详细信息保存在'detail'字段中")
    print("2. 后端代码之前只查找'address'字段，未检查'detail'字段")
    print("3. 修复方案: 优先使用'detail'字段，如果不存在再尝试'address'字段")
    print("4. 已修改代码: cells[4].text = station.get('detail', station.get('address', '无详细信息'))")

if __name__ == "__main__":
    try:
        debug_stations()
    except Exception as e:
        print(f"调试过程中出错: {e}")
        print(traceback.format_exc()) 