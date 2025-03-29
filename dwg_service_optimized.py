import os
import logging
import time
from dwg_client import DwgServiceClient
from dwg_cache_manager import default_cache_manager
from dwg_batch_processor import DwgBatchProcessor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedDwgService:
    """
    优化的DWG服务集成模块
    整合缓存管理、批处理和重试机制，提供统一的高性能接口
    """
    
    def __init__(self, api_url=None, api_key=None):
        """
        初始化优化的DWG服务
        
        Args:
            api_url: DWG服务API地址
            api_key: DWG服务API密钥
        """
        # 从环境变量获取配置
        self.max_workers = int(os.environ.get('DWG_MAX_WORKERS', '4'))
        self.batch_size = int(os.environ.get('DWG_BATCH_SIZE', '5'))
        self.use_cache = os.environ.get('DWG_USE_CACHE', 'true').lower() == 'true'
        
        # 初始化客户端和处理器
        self.client = DwgServiceClient(api_url, api_key)
        self.batch_processor = DwgBatchProcessor(
            max_workers=self.max_workers,
            batch_size=self.batch_size,
            api_url=api_url,
            api_key=api_key
        )
        
        # 使用全局缓存管理器
        self.cache_manager = default_cache_manager
        
        logger.info(f"优化的DWG服务初始化完成，最大工作线程: {self.max_workers}, "
                   f"批处理大小: {self.batch_size}, 使用缓存: {self.use_cache}")
    
    def update_attributes(self, template_file, attribute_data, use_cache=None):
        """
        更新DWG文件属性（优化版）
        
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
            cached_result = self.cache_manager.get(template_file, attribute_data)
            if cached_result:
                logger.info("使用缓存结果")
                return True, cached_result
        
        # 调用客户端更新属性
        start_time = time.time()
        success, result = self.client.update_dwg_attributes(template_file, attribute_data)
        elapsed_time = time.time() - start_time
        
        # 记录性能指标
        logger.info(f"属性更新完成，耗时: {elapsed_time:.2f}秒, 成功: {success}")
        
        # 如果成功且启用缓存，存入缓存
        if success and should_use_cache:
            self.cache_manager.set(template_file, attribute_data, result)
        
        return success, result
    
    def batch_update(self, tasks, auto_process=True):
        """
        批量更新DWG文件属性
        
        Args:
            tasks: 任务列表，每个任务为 (template_file, attribute_data) 元组
            auto_process: 是否自动处理，如果为False则只添加到队列
            
        Returns:
            处理结果列表，每个元素为 (success, result, template_file)
        """
        # 清空之前的队列
        self.batch_processor.clear_queue()
        
        # 添加所有任务
        for template_file, attribute_data in tasks:
            # 如果启用缓存，先检查缓存
            if self.use_cache:
                cached_result = self.cache_manager.get(template_file, attribute_data)
                if cached_result:
                    logger.info(f"使用缓存结果，模板: {template_file}")
                    # 不添加到批处理队列，直接返回缓存结果
                    continue
            
            # 添加到批处理队列
            self.batch_processor.add_task(template_file, attribute_data)
        
        # 如果自动处理，处理所有任务
        if auto_process:
            results = self.batch_processor.process_batch()
            
            # 如果启用缓存，将成功结果存入缓存
            if self.use_cache:
                for success, result, template_file in results:
                    if success:
                        # 从任务中找到对应的属性数据
                        for tf, attr_data in tasks:
                            if tf == template_file:
                                self.cache_manager.set(template_file, attr_data, result)
                                break
            
            return results
        
        return []
    
    def clear_cache(self):
        """
        清空缓存
        """
        self.cache_manager.clear()
        logger.info("DWG服务缓存已清空")
    
    def optimize_get_service_host_ip(self):
        """
        优化获取服务主机IP的过程
        减少不必要的日志和网络请求
        """
        from dwg_client import get_service_host_ip
        
        # 缓存IP地址，避免重复检测
        if not hasattr(self, '_cached_host_ip'):
            self._cached_host_ip = get_service_host_ip()
            self._cached_host_ip_time = time.time()
        else:
            # 检查缓存是否过期（10分钟）
            if time.time() - self._cached_host_ip_time > 600:
                self._cached_host_ip = get_service_host_ip()
                self._cached_host_ip_time = time.time()
        
        return self._cached_host_ip

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