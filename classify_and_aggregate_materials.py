import pandas as pd
import re
import requests # 需要导入 requests
import os       # 需要导入 os 来读取环境变量
import json     # 需要导入 json 来处理 API 请求/响应
import traceback # 导入 traceback

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

# 提取所有二级指标名称作为LLM的目标类别
all_secondary_categories = []
for primary, secondaries in classification_rules.items():
    all_secondary_categories.extend(secondaries.keys())
# 添加"未分类"作为可能的输出
all_secondary_categories.append("未分类")
target_categories_set = set(all_secondary_categories) # 使用集合进行快速查找

# --- Ollama 配置 ---
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwq") # <--- 修改这里

def classify_material_with_ollama(material_name, target_categories):
    """使用本地Ollama LLM对单个材料名称进行分类"""
    if not isinstance(material_name, str) or not material_name.strip():
        return "未分类"

    # 构建Prompt
    prompt = f"""任务：将以下建筑材料名称分类到最合适的预定义二级指标中。
材料名称：'{material_name}'

预定义的二级指标类别：
{', '.join(target_categories)}

请严格从上述类别中选择一个最匹配的，并仅返回该类别的名称。如果无法找到合适的分类，请返回 "未分类"。

分类结果："""

    # 构建Ollama API请求体
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False, # 我们需要一次性获取完整响应
        "options": {
            "temperature": 0.1, # 低温确保更确定的输出
             "num_predict": 50 # 限制最大生成词数，避免过长回复
        }
    }

    try:
        print(f"向 Ollama 发送请求: 模型={OLLAMA_MODEL}, 材料='{material_name}'")
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30) # 设置30秒超时
        response.raise_for_status() # 如果HTTP状态码是4xx或5xx，则抛出异常

        response_data = response.json()

        # 提取模型响应并清理
        classification_result = response_data.get("response", "").strip()
        print(f"Ollama 原始响应: '{classification_result}'")

        # 进一步清理，移除可能的引用符号或多余文字
        # 尝试找到最接近的类别名称
        best_match = "未分类"
        highest_similarity = 0 # (可选：如果需要更复杂的匹配)

        # 简单匹配：检查返回结果是否直接是类别之一
        if classification_result in target_categories:
             best_match = classification_result
        else:
            # 尝试在返回结果中查找类别名称（可能包含额外文字）
             found_cat = next((cat for cat in target_categories if cat in classification_result), None)
             if found_cat:
                 best_match = found_cat
                 print(f"从响应 '{classification_result}' 中提取到类别: '{best_match}'")
             else:
                 print(f"警告: Ollama 返回的 '{classification_result}' 不在预定义类别中，且无法提取有效类别。标记为 '未分类'。")
                 best_match = "未分类" # 如果清理后仍不在类别中，则标记为未分类

        return best_match

    except requests.exceptions.RequestException as e:
        print(f"调用 Ollama API 时出错: {e}")
        print(f"无法连接到 Ollama API ({OLLAMA_API_URL}) 或请求失败。请确保 Ollama 服务正在运行，并且网络连接正常。")
        return "未分类" # API 调用失败时返回未分类
    except json.JSONDecodeError as e:
        print(f"解析 Ollama 响应时出错: {e}")
        print(f"原始响应内容: {response.text}")
        return "未分类"
    except Exception as e:
        print(f"分类过程中发生未知错误 for '{material_name}': {e}")
        print(traceback.format_exc())
        return "未分类" # 其他未知错误

def classify_and_aggregate(excel_path, use_llm=True): # 添加 use_llm 参数
    """
    读取Excel文件，进行二级指标分类（可选LLM），并汇总每个二级指标的工程量。

    Args:
        excel_path (str): Excel文件的路径.
        use_llm (bool): 是否使用LLM进行分类，默认为True.

    Returns:
        pandas.Series: 以二级指标为索引，总工程量为值的Series.
                       返回 None 如果找不到必要的列或文件。
    """
    try:
        # 指定第三行为表头 (0-based index 2)
        df = pd.read_excel(excel_path, header=2)
    except FileNotFoundError:
        print(f"错误: 文件 '{excel_path}' 未找到.")
        return None
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None

    # --- 查找项目名称列 ---
    possible_name_cols = ['项目名称', '材料名称', '名称', '项目编码'] # 可能的列名
    name_col = None
    for col in possible_name_cols:
        if col in df.columns:
            name_col = col
            break
    if name_col is None:
        print(f"错误: 找不到项目名称列 (尝试过: {', '.join(possible_name_cols)}).")
        return None
    print(f"使用列 '{name_col}' 作为建材名称.")

    # --- 查找工程量列 ---
    possible_quantity_cols = ['工程量', '数量', '合计数量', 'Quantity'] # 可能的列名
    quantity_col = None
    for col in possible_quantity_cols:
        if col in df.columns:
            quantity_col = col
            break
    if quantity_col is None:
        print(f"错误: 找不到工程量列 (尝试过: {', '.join(possible_quantity_cols)}).")
        return None
    print(f"使用列 '{quantity_col}' 作为工程量.")

    # --- 数据类型转换和填充 ---
    # 确保工程量列是数值类型，非数值转为NaN，然后填充为0
    df[quantity_col] = pd.to_numeric(df[quantity_col], errors='coerce').fillna(0)
    # 确保项目名称列是字符串，填充空值为""
    # 确保项目名称列是字符串，填充空值为""，并去除首尾空格
    df[name_col] = df[name_col].astype(str).fillna("").str.strip()


    # --- 应用分类 ---
    if use_llm:
        print(f"使用 Ollama LLM ({OLLAMA_MODEL} @ {OLLAMA_API_URL}) 进行分类...")
        # 应用 LLM 分类函数
        # 使用 apply 逐行调用，对于大量数据可能会慢
        # TODO: 考虑实现批量调用 Ollama API 以提高性能
        df['二级指标'] = df[name_col].apply(lambda x: classify_material_with_ollama(x, target_categories_set))
    else:
        # 使用原始的基于规则的分类（需要原始的 classify_material 函数）
        print("使用基于规则的方法进行分类...")
        # 在这里保留或导入原始的 classify_material 函数
        # 假设原始函数名为 classify_material_rule_based
        def classify_material_rule_based(material_name, rules):
            """根据规则对单个材料名称进行分类（原始逻辑）"""
            if not isinstance(material_name, str): return "未分类"
            material_name_lower = material_name.lower()
            if "轻钢龙骨" in material_name:
                if "墙体" in material_name or "隔墙" in material_name: return "轻钢龙骨"
                elif "吊顶" in material_name or "顶棚" in material_name: return "轻钢龙骨"
                else: return "轻钢龙骨"
            for primary_cat, secondary_cats in rules.items():
                for secondary_cat, _ in secondary_cats.items():
                    clean_secondary_cat = re.sub(r'_Q\d$', '', secondary_cat)
                    if clean_secondary_cat == material_name_lower: return secondary_cat
            best_match = "未分类"
            match_found = False
            for primary_cat, secondary_cats in rules.items():
                for secondary_cat, details in secondary_cats.items():
                    keywords = details.get("keywords", [])
                    excludes = details.get("exclude", [])
                    excluded = any(ex.lower() in material_name_lower for ex in excludes)
                    if excluded: continue
                    if any(kw.lower() in material_name_lower for kw in keywords):
                        best_match = secondary_cat
                        match_found = True
                        break
                if match_found: break
            return best_match

        df['二级指标'] = df[name_col].apply(lambda x: classify_material_rule_based(x, classification_rules))

    # --- 过滤掉未分类的项 ---
    # 在过滤前打印未分类的材料名称，帮助调试
    unclassified_items = df[df['二级指标'] == "未分类"][name_col].tolist()
    if unclassified_items:
        print(f"\n以下 {len(unclassified_items)} 项未能分类:")
        # 只打印前 10 个未分类项，避免过多输出
        for item in unclassified_items[:10]:
            print(f"- {item}")
        if len(unclassified_items) > 10:
            print(f"... (还有 {len(unclassified_items) - 10} 项)")

    classified_df = df[df['二级指标'] != "未分类"].copy()

    # --- 按二级指标分组并汇总工程量 ---
    # 在汇总前打印分类结果的分布
    print("\n分类结果统计:")
    print(classified_df['二级指标'].value_counts())

    if not classified_df.empty:
        aggregated_quantities = classified_df.groupby('二级指标')[quantity_col].sum()
        print("\n汇总结果:")
        print(aggregated_quantities)
        return aggregated_quantities
    else:
        print("\n没有找到可分类的材料或所有材料均未成功分类。")
        return pd.Series(dtype=float) # 返回一个空的Series

# --- 使用示例 (可选，用于直接测试此脚本) ---
if __name__ == "__main__":
    # 请将 'path/to/your/excel/file.xlsx' 替换为实际的文件路径进行测试
    excel_file_path = '示例工程量清单.xlsx' # <--- 替换为你的 Excel 文件路径

    if os.path.exists(excel_file_path):
        print(f"\n--- 测试使用 Ollama LLM 分类 ---")
        results_llm = classify_and_aggregate(excel_file_path, use_llm=True)
        if results_llm is not None:
            print("\nLLM 分类汇总完成。")

        # print(f"\n--- 测试使用基于规则的分类 ---")
        # results_rules = classify_and_aggregate(excel_file_path, use_llm=False)
        # if results_rules is not None:
        #     print("\n规则分类汇总完成。")
    else:
        print(f"\n测试文件 '{excel_file_path}' 不存在，请提供有效的Excel文件路径以进行测试。")
