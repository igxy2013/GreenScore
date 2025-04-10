# 使用utf-8编码修复app.py中的编码问题
with open('app.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 删除之前添加的有问题的代码
if '# 添加获取高德地图API密钥的API端点' in content:
    content_parts = content.split('# 添加获取高德地图API密钥的API端点')
    content = content_parts[0]

# 添加正确编码的代码
new_code = '''
# 添加获取高德地图API密钥的API端点
@app.route("/api/gaode_map_api_key", methods=["GET"])
def get_gaode_map_api_key():
    try:
        # 从环境变量获取高德地图API密钥和安全密钥
        api_key = os.environ.get("GAODE_MAP_AK")
        security_js_code = os.environ.get("GAODE_MAP_SEC_CODE")
        
        if not api_key or not security_js_code:
            return jsonify({"error": "高德地图API密钥未配置"}), 500
        
        # 返回API密钥和安全密钥
        return jsonify({
            "api_key": api_key,
            "security_js_code": security_js_code
        })
    except Exception as e:
        app.logger.error(f"获取高德地图API密钥时出错: {str(e)}")
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500
'''

# 写回文件
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content + new_code) 