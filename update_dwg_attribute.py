import win32com.client
import os
import time
from typing import Optional
import pythoncom

def get_acad_application(max_retries: int = 3, retry_delay: float = 2.0) -> Optional[object]:
    # 初始化COM安全设置
    try:
        pythoncom.CoInitialize()
    except:
        pass

    for attempt in range(max_retries):
        try:
            # 尝试获取已运行的AutoCAD实例
            acad = win32com.client.GetActiveObject("AutoCAD.Application")
            return acad
        except Exception:
            try:
                # 如果没有运行的实例，尝试启动新实例
                acad = win32com.client.Dispatch("AutoCAD.Application")
                acad.Visible = True  # 设置为可见
                time.sleep(3)  # 增加等待时间确保应用程序完全初始化
                # 尝试访问Documents集合以确保应用程序已准备就绪
                try:
                    _ = acad.Documents
                except:
                    time.sleep(2)  # 如果失败，额外等待
                return acad
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"尝试连接AutoCAD失败 ({attempt + 1}/{max_retries})，等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    print(f"无法连接到AutoCAD应用程序: {str(e)}")
                    print("请确保：")
                    print("1. AutoCAD已正确安装且以管理员权限运行")
                    print("2. AutoCAD没有处于未响应状态")
                    print("3. 您有足够的权限运行AutoCAD")
                    print("4. DCOM设置允许程序访问AutoCAD")
                    return None
    return None

def update_attribute_text(template_path: str, output_path: str, attributes: dict[str, str]):
    # 检查文件是否存在
    template_path = os.path.abspath(template_path)
    output_path = os.path.abspath(output_path)
    
    if not os.path.exists(template_path):
        print(f"模板文件不存在: {template_path}")
        return

    # 初始化COM安全设置
    try:
        pythoncom.CoInitialize()
    except:
        pass

    # 获取AutoCAD应用程序实例
    acad = get_acad_application()
    if not acad:
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        return
    
    doc = None
    try:
        try:
            # 打开DWG文件
            try:
                doc = acad.Documents.Open(template_path)
                time.sleep(1)  # 等待文档完全加载
                if not doc:
                    print("无法打开DWG文件")
                    return
            except Exception as e:
                print(f"打开DWG文件时出错: {str(e)}")
                return
                
            # 获取所有块引用
            try:
                model_space = doc.ModelSpace
                if not model_space:
                    print("无法访问模型空间")
                    return
                    
                block_refs = [item for item in model_space if item.ObjectName == "AcDbBlockReference" and item.HasAttributes]
                
                # 记录已更新的属性
                updated_attributes = set()
                
                for entity in block_refs:
                    try:
                        # 遍历所有属性
                        for attrib in entity.GetAttributes():
                            # 检查标签名称是否在需要更新的属性字典中
                            tag_name = attrib.TagString
                            if tag_name in attributes:
                                # 更新文字内容
                                attrib.TextString = attributes[tag_name]
                                updated_attributes.add(tag_name)
                    except Exception as e:
                        print(f"处理实体属性时出错: {str(e)}")
                        continue
                
                # 检查是否所有属性都已更新
                for tag_name in attributes:
                    if tag_name not in updated_attributes:
                        print(f"警告: 未找到属性标签 '{tag_name}'")
                
                # 保存修改后的文件
                doc.SaveAs(output_path)
                print(f'已成功更新属性块文字，保存到: {output_path}')
                
            except Exception as e:
                print(f'访问模型空间时出错: {str(e)}')
            
        except Exception as e:
            print(f'操作DWG文件时出错: {str(e)}')
    finally:
        # 确保文档被关闭和资源被释放
        try:
            if doc:
                doc.Close()
        except:
            pass
        try:
            pythoncom.CoUninitialize()
        except:
            pass
