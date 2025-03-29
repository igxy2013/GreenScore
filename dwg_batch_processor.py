import os
import logging
import concurrent.futures
import time
from dwg_client import DwgServiceClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DwgBatchProcessor:
    """
    DWG文件批处理器，用于批量处理DWG文件属性更新
    支持并行处理和批量提交
    """
    
    def __init__(self, max_workers=4, batch_size=5, api_url=None, api_key=None):
        """
        初始化批处理器
        
        Args:
            max_workers: 最大并行工作线程数
            batch_size: 每批处理的最大文件数
            api_url: DWG服务API地址
            api_key: DWG服务API密钥
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.client = DwgServiceClient(api_url, api_key)
        self.processing_queue = []
        logger.info(f"DWG批处理器初始化完成，最大工作线程: {max_workers}, 批处理大小: {batch_size}")
    
    def add_task(self, template_file, attribute_data):
        """
        添加处理任务到队列
        
        Args:
            template_file: DWG模板文件路径
            attribute_data: 属性数据列表
        """
        self.processing_queue.append((template_file, attribute_data))
        logger.info(f"添加任务到队列，当前队列长度: {len(self.processing_queue)}")
        
        # 如果队列达到批处理大小，自动处理
        if len(self.processing_queue) >= self.batch_size:
            logger.info(f"队列达到批处理大小 {self.batch_size}，自动处理")
            return self.process_batch()
        return None
    
    def process_batch(self):
        """
        处理当前队列中的所有任务
        
        Returns:
            处理结果列表，每个元素为 (success, result, template_file)
        """
        if not self.processing_queue:
            logger.info("处理队列为空，无需处理")
            return []
        
        tasks = self.processing_queue.copy()
        self.processing_queue.clear()
        
        logger.info(f"开始批量处理 {len(tasks)} 个任务")
        start_time = time.time()
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_task = {executor.submit(self._process_single_task, template_file, attribute_data): (template_file, attribute_data) 
                             for template_file, attribute_data in tasks}
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_task):
                template_file, _ = future_to_task[future]
                try:
                    success, result = future.result()
                    results.append((success, result, template_file))
                except Exception as e:
                    logger.error(f"处理任务出错: {str(e)}")
                    results.append((False, {'message': f"处理任务出错: {str(e)}"}, template_file))
        
        elapsed_time = time.time() - start_time
        logger.info(f"批量处理完成，耗时: {elapsed_time:.2f}秒，成功: {sum(1 for s, _, _ in results if s)}/{len(results)}")
        
        return results
    
    def _process_single_task(self, template_file, attribute_data):
        """
        处理单个任务
        
        Args:
            template_file: DWG模板文件路径
            attribute_data: 属性数据列表
            
        Returns:
            (success, result): 处理结果
        """
        logger.info(f"处理任务: {template_file}")
        return self.client.update_dwg_attributes(template_file, attribute_data)
    
    def clear_queue(self):
        """
        清空处理队列
        """
        queue_size = len(self.processing_queue)
        self.processing_queue.clear()
        logger.info(f"清空处理队列，移除了 {queue_size} 个任务")

# 使用示例
"""
# 创建批处理器
batch_processor = DwgBatchProcessor(max_workers=4, batch_size=5)

# 添加任务
for i in range(10):
    template_file = f"template_{i}.dwg"
    attribute_data = [{"field": "项目名称", "value": f"项目{i}"}]
    batch_processor.add_task(template_file, attribute_data)

# 处理剩余任务
results = batch_processor.process_batch()

# 处理结果
for success, result, template_file in results:
    if success:
        print(f"处理成功: {template_file}, {result['message']}")
    else:
        print(f"处理失败: {template_file}, {result['message']}")
"""