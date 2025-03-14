#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import Project, db

def calculate_per_capita_land_score(total_land_area, residential_units, climate_zone, average_floors):
    """
    计算人均居住用地指标得分
    """
    # 参数验证
    if not total_land_area or total_land_area <= 0:
        print('总用地面积必须大于0')
        return {'score': 0, 'rating': '无效数据', 'perCapitaLand': 0}
    
    if not residential_units or residential_units <= 0:
        print('住宅户数必须大于0')
        return {'score': 0, 'rating': '无效数据', 'perCapitaLand': 0}
    
    # 计算总人数 (每户平均3.2人)
    average_person_per_unit = 3.2
    total_population = residential_units * average_person_per_unit
    
    # 计算人均居住用地面积(平方米/人)
    per_capita_land = total_land_area / total_population
    
    # 标准化气候区划
    normalized_climate_zone = climate_zone.upper().replace('Ⅰ', 'I').replace('Ⅱ', 'II').replace('Ⅲ', 'III').replace('Ⅳ', 'IV').replace('Ⅴ', 'V').replace('Ⅵ', 'VI')
    
    # 标准化平均层数
    if isinstance(average_floors, str):
        if '3层及以下' in average_floors or '3层以下' in average_floors:
            floor_range = 3
        elif '4-6层' in average_floors or '4~6层' in average_floors:
            floor_range = 5
        elif '7-9层' in average_floors or '7~9层' in average_floors:
            floor_range = 8
        elif '10-18层' in average_floors or '10~18层' in average_floors:
            floor_range = 15
        elif '19层及以上' in average_floors or '19层以上' in average_floors:
            floor_range = 20
        else:
            # 默认为中等层数
            floor_range = 10
    else:
        floor_range = int(average_floors)
    
    # 根据评分规则计算得分
    score = 0
    rating = ''
    
    # 根据气候区划和平均层数确定评分标准
    if normalized_climate_zone in ['I', 'VI']:
        # I、VI气候区
        if floor_range <= 3:
            if per_capita_land <= 33:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 36:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 4 <= floor_range <= 6:
            if per_capita_land <= 29:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 32:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 7 <= floor_range <= 9:
            if per_capita_land <= 21:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 22:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 10 <= floor_range <= 18:
            if per_capita_land <= 17:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 19:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        else:  # 19层及以上
            if per_capita_land <= 12:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 13:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
    elif normalized_climate_zone in ['II', 'V']:
        # II、V气候区
        if floor_range <= 3:
            if per_capita_land <= 33:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 36:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 4 <= floor_range <= 6:
            if per_capita_land <= 27:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 30:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 7 <= floor_range <= 9:
            if per_capita_land <= 20:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 21:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 10 <= floor_range <= 18:
            if per_capita_land <= 16:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 17:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        else:  # 19层及以上
            if per_capita_land <= 12:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 13:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
    else:
        # III、IV气候区（默认）
        if floor_range <= 3:
            if per_capita_land <= 33:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 36:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 4 <= floor_range <= 6:
            if per_capita_land <= 24:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 27:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 7 <= floor_range <= 9:
            if per_capita_land <= 19:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 20:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        elif 10 <= floor_range <= 18:
            if per_capita_land <= 15:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 16:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
        else:  # 19层及以上
            if per_capita_land <= 11:
                score = 20
                rating = '卓越'
            elif per_capita_land <= 12:
                score = 15
                rating = '优秀'
            else:
                score = 0
                rating = '不达标'
    
    return {
        'score': score,
        'rating': rating,
        'perCapitaLand': round(per_capita_land, 2)
    }

def main():
    # 获取项目ID=21的信息
    project = db.session.query(Project).filter_by(id=21).first()
    
    if not project:
        print("未找到ID为21的项目")
        return
    
    # 打印项目基本信息
    print("\n" + "="*50)
    print("项目信息".center(46))
    print("="*50)
    print(f"项目ID: {project.id}")
    print(f"项目名称: {project.name}")
    print(f"项目编号: {project.code}")
    print(f"建设单位: {project.construction_unit}")
    print(f"设计单位: {project.design_unit}")
    print(f"项目地点: {project.location}")
    print(f"建筑面积: {project.building_area} 平方米")
    print(f"评价标准: {project.standard}")
    print(f"建筑类型: {project.building_type}")
    print(f"建筑气候区划: {project.climate_zone}")
    print(f"星级目标: {project.star_rating_target}")
    print(f"总用地面积: {project.total_land_area} 平方米")
    print(f"总建筑面积: {project.total_building_area} 平方米")
    print(f"地上建筑面积: {project.above_ground_area} 平方米")
    print(f"地下建筑面积: {project.underground_area} 平方米")
    print(f"地下一层建筑面积: {project.underground_floor_area} 平方米")
    print(f"地面停车位数量: {project.ground_parking_spaces}")
    print(f"容积率: {project.plot_ratio}")
    print(f"建筑基底面积: {project.building_base_area} 平方米")
    print(f"建筑密度: {project.building_density}%")
    print(f"绿地面积: {project.green_area} 平方米")
    print(f"绿地率: {project.green_ratio}%")
    print(f"住宅户数: {project.residential_units}")
    print(f"建筑层数: {project.building_floors}")
    print(f"建筑高度: {project.building_height} 米")
    print(f"空调形式: {project.air_conditioning_type}")
    print(f"住宅平均层数: {project.average_floors}")
    print(f"有无垃圾用房: {project.has_garbage_room}")
    print(f"有无电梯或扶梯: {project.has_elevator}")
    print(f"有无地下车库: {project.has_underground_garage}")
    print(f"项目建设情况: {project.construction_type}")
    print(f"有无景观水体: {project.has_water_landscape}")
    print(f"是否为全装修项目: {project.is_fully_decorated}")
    
    # 计算人均居住用地指标得分
    result = calculate_per_capita_land_score(
        project.total_land_area,
        project.residential_units,
        project.climate_zone,
        project.average_floors
    )
    
    # 打印分割线
    print("\n" + "-"*50)
    print("人均居住用地指标评分".center(42))
    print("-"*50)
    
    # 打印计算过程
    print(f"总用地面积: {project.total_land_area} 平方米")
    print(f"住宅户数: {project.residential_units}")
    print(f"每户平均人数: 3.2 人/户")
    print(f"总人数: {project.residential_units * 3.2} 人")
    print(f"人均居住用地面积: {result['perCapitaLand']} 平方米/人")
    print(f"建筑气候区划: {project.climate_zone}")
    print(f"住宅平均层数: {project.average_floors}")
    
    # 打印评分结果
    print("\n" + "*"*50)
    print(f"人均居住用地指标得分: {result['score']} 分")
    print(f"评级: {result['rating']}")
    print("*"*50)

if __name__ == "__main__":
    main() 