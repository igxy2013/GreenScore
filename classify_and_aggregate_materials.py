import pandas as pd
import re
import os # 保留 os 用于 os.path.exists

# --- 从图片规则提取的分类字典 ---
# (与之前的版本相同，这里省略以保持简洁)
classification_rules = {
    "主体及围护结构工程用材 Q1": {
        "预拌混凝土": {"keywords": ["混凝土"], "exclude": ["预拌砂浆"]},
        "预拌砂浆": {"keywords": ["砂浆", "胶粘剂", "抹面砂浆", "自流平", "饰面砂浆", "石膏类浆"]},
        "砌体材料": {"keywords": ["砌块", "砖"]},
        "石材": {"keywords": ["石材", "人造石"]},
        "防水密封材料": {"keywords": ["防水卷材", "防水涂料", "建筑密封胶", "刚性防水材料"]},
        "保温隔热材料": {"keywords": ["保温材料", "保温板", "保温装饰一体化板"]},
        "混凝土结构构件": {"keywords": ["混凝土构件"]}, # 需要更具体的关键词
        "钢结构构件": {"keywords": ["钢结构"]}, # 需要更具体的关键词
        "木结构构件": {"keywords": ["原木", "复合木", "重组材", "木结构"]},
        "轻钢龙骨": {"keywords": ["轻钢龙骨"]}, # 需要区分用途
        "节能门窗": {"keywords": ["门窗"]}, # 假设所有门窗都节能，可能需要更细化
        "遮阳制品": {"keywords": ["遮阳"]},
        "建筑幕墙": {"keywords": ["玻璃幕墙"]},
        "墙板": {"keywords": ["墙板", "外墙板", "内隔墙板"]},
        "其他类_Q1": {"keywords": ["铝合金模板", "支架", "钢质防火门", "吊顶系统", "吊顶龙骨", "采暖/照明功能模块"]}, # 包含多个小类
    },
    "装饰装修工程用材 Q2": {
        "墙面涂料": {"keywords": ["涂料", "外墙漆", "内墙漆", "腻子"]},
        "装配式集成墙面": {"keywords": ["集成墙面"]},
        "壁纸（布）": {"keywords": ["壁纸", "墙布"]},
        "建筑装饰板": {"keywords": ["装饰板"], "exclude": ["无机装饰板材", "泡沫铝板", "镁质装饰材料", "保温装饰一体板"]},
        "装修用木制品": {"keywords": ["木制品", "木质地板", "木地板"]},
        "石膏装饰材料": {"keywords": ["石膏板", "石膏线条", "穿孔石膏板", "石膏装饰"]},
        "抗菌净化材料": {"keywords": ["空气净化材料", "抗菌材料"]}, # 关键词可能不全
        "建筑陶瓷制品": {"keywords": ["瓷砖", "陶瓷"]},
        "地坪材料": {"keywords": ["弹性地板", "树脂地坪", "无机地坪", "地坪涂装"]},
        "卫生洁具": {"keywords": ["洁具", "坐便器", "卫浴", "水龙头"]}, # 关键词可能不全
        "其他类_Q2": {"keywords": ["结构结构加固胶", "金属复合装饰材料", "智能坐便器", "人造石材", "集成式卫浴", "木塑制品", "防火涂料"]}, # 包含多个小类
    },
    "机电安装工程用材 Q3": {
        "管材管件": {"keywords": ["管材", "管件", "给水管", "排水管", "塑料管"]},
        "LED照明产品": {"keywords": ["LED", "灯具", "照明"]},
        "电线电缆": {"keywords": ["电线", "电缆"]},
        "新风净化设备及其系统": {"keywords": ["空调机组", "新风系统", "净化设备", "控制器", "计量设备"]},
        "采暖空调设备及其系统": {"keywords": ["空调", "风机盘管", "风管", "水泵", "供暖散热器", "组合式空调机组", "冷热水设备", "冷却塔", "风机盘管机组"]},
        "热泵产品及其系统": {"keywords": ["热泵", "地源热泵", "空气源热泵", "控制器", "计量设备"]},
        "辐射供暖供冷设备及其系统": {"keywords": ["供暖散热器", "冷热水设备", "冷却塔", "联供设备", "计量设备"]},
        "一体化生活污水处理设备": {"keywords": ["污水处理"]},
        "太阳能光伏发电系统": {"keywords": ["光伏组件", "逆变器"]},
        "其他类_Q3": {"keywords": ["水嘴", "建筑用阀门", "净水设备", "软化设备", "油脂分离器", "中水处理设备", "建筑用蓄能装置", "采光系统"]}, # 包含多个小类
    },
    "室外工程用材 Q4": {
        "雨水收集回用系统": {"keywords": ["雨水处理", "雨水收集"]},
        "透水铺装材料": {"keywords": ["透水砖", "透水混凝土", "透水铺装"]}, # 关键词可能不全
        "屋顶绿化材料": {"keywords": ["屋顶绿化"]}, # 关键词可能不全
        "机械式停车设备": {"keywords": ["停车设备"]},
        "其他类_Q4": {"keywords": ["园林用木竹材料", "建筑垃圾处置系统", "一体化预制泵站", "设备隔振降噪装置"]}, # 包含多个小类
    }
}

# --- 规则分类函数 ---
def classify_material_rule_based(material_name, rules):
    """使用预定义规则对材料名称进行分类"""
    if not isinstance(material_name, str): return "未分类"
    material_name_lower = material_name.lower().strip()
    if not material_name_lower: return "未分类" # 处理空字符串

    # 特殊处理轻钢龙骨
    if "轻钢龙骨" in material_name:
        if "墙体" in material_name or "隔墙" in material_name: return "轻钢龙骨"
        elif "吊顶" in material_name or "顶棚" in material_name: return "轻钢龙骨"
        else: return "轻钢龙骨" # 默认也归类

    # 尝试精确匹配二级指标名称 (去除_Qx后缀)
    for primary_cat, secondary_cats in rules.items():
        for secondary_cat, _ in secondary_cats.items():
            clean_secondary_cat = re.sub(r'_Q\d$', '', secondary_cat)
            if clean_secondary_cat == material_name_lower: return secondary_cat

    # 基于关键词匹配
    best_match = "未分类"
    match_found = False
    for primary_cat, secondary_cats in rules.items():
        for secondary_cat, details in secondary_cats.items():
            keywords = details.get("keywords", [])
            excludes = details.get("exclude", [])
            # 检查是否包含排除词
            excluded = any(ex.lower() in material_name_lower for ex in excludes)
            if excluded: continue
            # 检查是否包含任一关键词
            if any(kw.lower() in material_name_lower for kw in keywords):
                best_match = secondary_cat
                match_found = True
                break # 找到第一个匹配的就跳出内层循环
        if match_found: break # 找到匹配的就跳出外层循环
    return best_match

# --- 主处理函数 --- #
def classify_and_aggregate(excel_path):
    """
    读取Excel文件，使用pandas提取数据，使用规则进行二级指标分类，
    并汇总每个二级指标的工程量。

    Args:
        excel_path (str): Excel文件的路径.

    Returns:
        pandas.Series: 以二级指标为索引，总工程量为值的Series.
                       返回 None 如果文件读取失败。
                       返回空 Series 如果没有可分类的数据。
    """
    try:
        # 1. 使用 pandas 读取 Excel 数据
        # 指定第三行为表头 (0-based index 2)
        # 同时读取为字符串类型，避免 pandas 自动转换类型
        df = pd.read_excel(excel_path, header=2, dtype=str)
        print(f"成功读取 Excel 文件: {excel_path}")
    except FileNotFoundError:
        print(f"错误: 文件 '{excel_path}' 未找到.")
        return None
    except Exception as e:
        # 捕获 openpyxl 缺失的错误
        if "Missing optional dependency 'openpyxl'" in str(e):
             print("错误：缺少处理 .xlsx 文件所需的 'openpyxl' 库。")
             print("请在您的 Python 环境中运行 'pip install openpyxl' 来安装它。")
        else:
             print(f"读取Excel文件时出错: {e}")
        return None

    # --- 2. 使用 pandas 直接提取工程量数据 ---
    print("\n--- 使用 pandas 直接提取工程量数据 ---")
    # --- 查找项目名称列 ---
    possible_name_cols = ['项目名称', '材料名称', '名称', '项目编码']
    name_col = next((col for col in possible_name_cols if col in df.columns), None)
    if name_col is None:
        print("错误: 在Excel文件中找不到合适的项目名称列 (如 '项目名称', '材料名称', '名称', '项目编码').")
        return None
    print(f"使用列 '{name_col}' 作为建材名称.")

    # --- 查找工程量列 ---
    possible_quantity_cols = ['工程量', '数量', '合计数量', 'Quantity']
    quantity_col = next((col for col in possible_quantity_cols if col in df.columns), None)
    if quantity_col is None:
        print("错误: 在Excel文件中找不到合适的工程量列 (如 '工程量', '数量', '合计数量', 'Quantity').")
        return None
    print(f"使用列 '{quantity_col}' 作为工程量.")

    # --- 数据类型转换和填充 ---
    # 转换为数值，无法转换的设为 NaN，然后填充为 0
    df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce').fillna(0)
    # 确保名称列是字符串，填充 NaN 为空字符串，并去除两端空格
    df[name_col] = df[name_col].astype(str).fillna("").str.strip()

    # 筛选出需要的列，并重命名以保持一致性
    extracted_df = df[[name_col, quantity_col]].copy()
    extracted_df.columns = ['extracted_name', 'extracted_quantity'] # 直接重命名

    # 过滤掉工程量为0或名称为空的行
    extracted_df = extracted_df[extracted_df['extracted_quantity'] > 0]
    extracted_df = extracted_df[extracted_df['extracted_name'] != ""]

    if extracted_df.empty:
        print("错误：使用 Pandas 提取后没有找到有效的材料数据（名称非空且工程量大于0）。")
        return pd.Series(dtype=float) # 返回空 Series

    print(f"Pandas 提取并清理了 {len(extracted_df)} 条有效数据。")

    # --- 3. 应用基于规则的分类 --- #
    material_names_to_classify = extracted_df['extracted_name'].tolist()
    print(f"\n--- 开始对 {len(material_names_to_classify)} 个提取出的材料名称进行基于规则的分类 ---")

    # 应用规则分类函数
    extracted_df['二级指标'] = extracted_df['extracted_name'].apply(
        lambda x: classify_material_rule_based(x, classification_rules)
    )

    # --- 4. 过滤和汇总 --- #
    # 打印未分类的项
    unclassified_items = extracted_df[extracted_df['二级指标'] == "未分类"]
    if not unclassified_items.empty:
        print(f"\n以下 {len(unclassified_items)} 项未能通过规则分类:")
        # 打印前 10 个未分类项的名称和原始工程量
        for index, row in unclassified_items.head(10).iterrows():
            print(f"- {row['extracted_name']} (工程量: {row['extracted_quantity']})")
        if len(unclassified_items) > 10: print(f"... (还有 {len(unclassified_items) - 10} 项)")

    # 过滤掉未分类的项，准备汇总
    classified_df = extracted_df[extracted_df['二级指标'] != "未分类"].copy()

    if classified_df.empty:
        print("\n所有提取到的材料均未能通过规则分类。")
        return pd.Series(dtype=float) # 返回空 Series

    # 打印分类结果统计
    print("\n分类结果统计:")
    print(classified_df['二级指标'].value_counts())

    # 按二级指标分组并汇总工程量 ('extracted_quantity')
    aggregated_quantities = classified_df.groupby('二级指标')['extracted_quantity'].sum()
    print("\n汇总结果:")
    print(aggregated_quantities)
    return aggregated_quantities

# --- 使用示例 (可选，用于直接测试此脚本) ---
if __name__ == "__main__":
    excel_file_path = '示例工程量清单.xlsx' # <--- 替换为你的 Excel 文件路径

    if os.path.exists(excel_file_path):
        print(f"\n--- 执行: 使用 Pandas 提取 + 规则 分类 ---")
        # 调用简化后的函数
        results = classify_and_aggregate(excel_file_path)
        if results is not None:
            if not results.empty:
                print("\nPandas 提取 + 规则 分类 汇总完成。")
            else:
                print("\n处理完成，但没有可汇总的分类数据。")
        else:
            print("\n处理过程中发生错误，未能完成汇总。")
    else:
        print(f"\n错误: 测试文件 '{excel_file_path}' 不存在，请提供有效的Excel文件路径。")
