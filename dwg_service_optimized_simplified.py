import os
import logging
import time
from dwg_client_simplified import DwgServiceClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedDwgService:
    """
    优化的DWG服务集成模块
    整合缓存和批处理，提供统一的高性能接口
    """
    
    def __init__(self, api_url=None, api_key=None):
        """初始化优化的DWG服务"""
        # 从环境变量获取配置
        self.max_workers = int(os.environ.get('DWG_MAX_WORKERS', '4'))
        self.batch_size = int(os.environ.get('DWG_BATCH_SIZE', '5'))
        self.use_cache = os.environ.get('DWG_USE_CACHE', 'true').lower() == 'true'
        
        # 初始化客户端
        self.client = DwgServiceClient(api_url, api_key)
        
        # 缓存存储
        self.cache = {}
        
        logger.info(f"优化服务初始化完成: 最大线程数={self.max_workers}, "
                   f"批处理大小={self.batch_size}, 使用缓存={self.use_cache}")
    
    def update_attributes(self, template_file, attribute_data, use_cache=None):
        """
        更新DWG文件属性
        
        Args:
            template_file: DWG模板文件对象或路径
            attribute_data: 属性数据列表
            use_cache: 是否使用缓存，默认使用全局设置
            
        Returns:
            (success, result): 成功状态和结果数据
        """
        # 确定是否使用缓存
        should_use_cache = self.use_cache if use_cache is None else use_cache
        
        # 如果启用缓存，先检查缓存
        if should_use_cache:
            # 生成缓存键
            try:
                cache_key = f"{template_file}:{hash(str(attribute_data))}"
                if cache_key in self.cache:
                    logger.info("使用缓存结果")
                    return True, self.cache[cache_key]
            except:
                logger.warning("生成缓存键失败，不使用缓存")
        
        # 调用客户端更新属性
        start_time = time.time()
        success, result = self.client.update_dwg_attributes(template_file, attribute_data)
        elapsed_time = time.time() - start_time
        
        # 记录性能指标
        logger.info(f"属性更新完成，耗时: {elapsed_time:.2f}秒, 成功: {success}")
        
        # 如果成功且启用缓存，存入缓存
        if success and should_use_cache:
            try:
                cache_key = f"{template_file}:{hash(str(attribute_data))}"
                self.cache[cache_key] = result
                
                # 如果缓存过大，清理最早的条目
                max_cache_size = 50
                if len(self.cache) > max_cache_size:
                    # 简单策略：直接清除一半的缓存
                    keys_to_remove = list(self.cache.keys())[:len(self.cache)//2]
                    for key in keys_to_remove:
                        del self.cache[key]
                    logger.info(f"缓存清理完成，当前缓存大小: {len(self.cache)}")
            except:
                logger.warning("存入缓存失败")
        
        return success, result
    
    def batch_update(self, tasks):
        """
        批量更新DWG文件属性
        
        Args:
            tasks: 任务列表，每个任务为 (template_file, attribute_data) 元组
            
        Returns:
            处理结果列表，每个元素为 (success, result, template_file)
        """
        results = []
        total_tasks = len(tasks)
        
        logger.info(f"开始批量处理 {total_tasks} 个任务")
        start_time = time.time()
        
        # 逐个处理任务
        for i, (template_file, attribute_data) in enumerate(tasks):
            logger.info(f"处理任务 {i+1}/{total_tasks}: {template_file}")
            
            # 如果启用缓存，先检查缓存
            if self.use_cache:
                try:
                    cache_key = f"{template_file}:{hash(str(attribute_data))}"
                    if cache_key in self.cache:
                        logger.info(f"使用缓存结果: {template_file}")
                        results.append((True, self.cache[cache_key], template_file))
                        continue
                except:
                    pass
            
            # 没有缓存结果，调用客户端
            success, result = self.client.update_dwg_attributes(template_file, attribute_data)
            results.append((success, result, template_file))
            
            # 如果成功且启用缓存，存入缓存
            if success and self.use_cache:
                try:
                    cache_key = f"{template_file}:{hash(str(attribute_data))}"
                    self.cache[cache_key] = result
                except:
                    pass
        
        elapsed_time = time.time() - start_time
        logger.info(f"批量处理完成，总耗时: {elapsed_time:.2f}秒")
        
        return results
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")

# 创建默认实例
optimized_dwg_service = OptimizedDwgService()

# 使用示例
"""
# 单个文件处理
success, result = optimized_dwg_service.update_attributes(
    'template.dwg',
    [{"field": "项目名称", "value": "绿色建筑示例项目"}]
)

# 批量处理
tasks = [
    ('template1.dwg', [{"field": "项目名称", "value": "项目1"}]),
    ('template2.dwg', [{"field": "项目名称", "value": "项目2"}]),
    ('template3.dwg', [{"field": "项目名称", "value": "项目3"}])
]
results = optimized_dwg_service.batch_update(tasks)

# 清空缓存
optimized_dwg_service.clear_cache()
""" 