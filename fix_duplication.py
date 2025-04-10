# 使用utf-8编码修复app.py中的重复路由问题
with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 只保留第一个路由定义，删除所有重复的定义
occurrences = content.count('@app.route("/api/gaode_map_api_key"')
if occurrences > 1:
    # 找到第一个定义的位置
    first_pos = content.find('@app.route("/api/gaode_map_api_key"')
    # 找到第一个定义的结束位置（寻找函数定义结束）
    func_start = content.find('def get_gaode_map_api_key():', first_pos)
    # 找到函数体
    func_body_start = content.find(':', func_start) + 1
    # 找到下一个路由定义（或文件结尾）
    next_route = content.find('@app.route', func_body_start)
    if next_route == -1:
        next_route = len(content)
    
    # 保留第一个定义，删除其他所有定义
    cleaned_content = content[:next_route]
    
    # 删除所有后续定义
    remaining = content[next_route:]
    while '@app.route("/api/gaode_map_api_key"' in remaining:
        route_start = remaining.find('@app.route("/api/gaode_map_api_key"')
        next_route = remaining.find('@app.route', route_start + 1)
        if next_route == -1:
            next_route = len(remaining)
        remaining = remaining[:route_start] + remaining[next_route:]
    
    # 合并清理后的内容
    cleaned_content += remaining
    
    # 写回文件
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"已删除 {occurrences - 1} 个重复的路由定义")
else:
    print("没有发现重复的路由定义") 