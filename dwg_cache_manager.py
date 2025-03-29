import os
import time
import logging
import json
import hashlib
from collections import OrderedDict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DwgCacheManager:
    """
    DWG缓存管理器，提供高级缓存功能
    支持LRU缓存策略、缓存过期和缓存大小限制
    """
    
    def __init__(self, max_size=50, ttl=3600, cache_dir=None):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存条目数，默认50
            ttl: 缓存生存时间（秒），默认1小时
            cache_dir: 缓存目录，如果提供则启用磁盘缓存
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache_dir = cache_dir
        
        # 使用OrderedDict实现LRU缓存
        self.memory_cache = OrderedDict()
        
        # 如果提供了缓存目录，确保它存在
        if self.cache_dir and not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logger.info(f"创建缓存目录: {self.cache_dir}")
            except Exception as e:
                logger.error(f"创建缓存目录失败: {str(e)}")
                self.cache_dir = None
        
        logger.info(f"DWG缓存管理器初始化完成，最大缓存: {max_size}项, TTL: {ttl}秒, 缓存目录: {cache_dir or '无'}")
    
    def _generate_key(self, template_file, attribute_data):
        """
        生成缓存键
        
        Args:
            template_file: 模板文件路径
            attribute_data: 属性数据
            
        Returns:
            缓存键字符串
        """
        try:
            # 对模板文件路径使用绝对路径
            if isinstance(template_file, str):
                template_path = os.path.abspath(template_file)
            else:
                # 如果是文件对象，尝试获取名称
                try:
                    template_path = template_file.name
                except AttributeError:
                    template_path = str(id(template_file))
            
            # 对属性数据进行排序和序列化
            attr_json = json.dumps(attribute_data, sort_keys=True)
            
            # 使用MD5生成哈希值
            key_str = f"{template_path}:{attr_json}"
            return hashlib.md5(key_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"生成缓存键失败: {str(e)}")
            # 生成失败时返回一个唯一的时间戳键
            return f"fallback_{time.time()}"
    
    def get(self, template_file, attribute_data):
        """
        从缓存获取结果
        
        Args:
            template_file: 模板文件路径或对象
            attribute_data: 属性数据
            
        Returns:
            缓存的结果或None（如果缓存未命中）
        """
        key = self._generate_key(template_file, attribute_data)
        
        # 首先检查内存缓存
        if key in self.memory_cache:
            entry = self.memory_cache.pop(key)  # 移除并重新添加以更新LRU顺序
            timestamp, value = entry
            
            # 检查是否过期
            if time.time() - timestamp <= self.ttl:
                self.memory_cache[key] = entry  # 放回缓存顶部
                logger.info(f"内存缓存命中: {key[:8]}...")
                return value
            else:
                logger.info(f"缓存已过期: {key[:8]}...")
                # 不放回缓存
                return None
        
        # 如果内存缓存未命中且启用了磁盘缓存，检查磁盘缓存
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    timestamp = cache_data.get('timestamp', 0)
                    value = cache_data.get('value')
                    
                    # 检查是否过期
                    if time.time() - timestamp <= self.ttl:
                        # 添加到内存缓存
                        self.memory_cache[key] = (timestamp, value)
                        # 维护内存缓存大小
                        self._maintain_cache_size()
                        logger.info(f"磁盘缓存命中: {key[:8]}...")
                        return value
                    else:
                        logger.info(f"磁盘缓存已过期: {key[:8]}...")
                        # 删除过期的磁盘缓存
                        try:
                            os.remove(cache_file)
                        except Exception as e:
                            logger.warning(f"删除过期缓存文件失败: {str(e)}")
                except Exception as e:
                    logger.warning(f"读取磁盘缓存失败: {str(e)}")
        
        logger.info(f"缓存未命中: {key[:8]}...")
        return None
    
    def set(self, template_file, attribute_data, value):
        """
        将结果存入缓存
        
        Args:
            template_file: 模板文件路径或对象
            attribute_data: 属性数据
            value: 要缓存的值
        """
        key = self._generate_key(template_file, attribute_data)
        timestamp = time.time()
        
        # 存入内存缓存
        self.memory_cache[key] = (timestamp, value)
        
        # 维护内存缓存大小
        self._maintain_cache_size()
        
        # 如果启用了磁盘缓存，也存入磁盘
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            try:
                cache_data = {
                    'timestamp': timestamp,
                    'value': value
                }
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f)
                logger.info(f"结果已存入磁盘缓存: {key[:8]}...")
            except Exception as e:
                logger.warning(f"写入磁盘缓存失败: {str(e)}")
        
        logger.info(f"结果已存入内存缓存: {key[:8]}...")
    
    def _maintain_cache_size(self):
        """
        维护内存缓存大小，如果超出最大大小，移除最旧的条目
        """
        while len(self.memory_cache) > self.max_size:
            # OrderedDict在Python 3.7+中保持插入顺序
            # popitem(last=False)移除最早插入的项
            oldest_key, _ = self.memory_cache.popitem(last=False)
            logger.debug(f"从缓存中移除最旧条目: {oldest_key[:8]}...")
    
    def clear(self):
        """
        清空缓存
        """
        self.memory_cache.clear()
        
        # 清空磁盘缓存
        if self.cache_dir and os.path.exists(self.cache_dir):
            try:
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.cache'):
                        os.remove(os.path.join(self.cache_dir, filename))
                logger.info("磁盘缓存已清空")
            except Exception as e:
                logger.warning(f"清空磁盘缓存失败: {str(e)}")
        
        logger.info("内存缓存已清空")
    
    def remove(self, template_file, attribute_data):
        """
        从缓存中移除特定条目
        
        Args:
            template_file: 模板文件路径或对象
            attribute_data: 属性数据
        """
        key = self._generate_key(template_file, attribute_data)
        
        # 从内存缓存移除
        if key in self.memory_cache:
            self.memory_cache.pop(key)
            logger.info(f"从内存缓存移除条目: {key[:8]}...")
        
        # 从磁盘缓存移除
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logger.info(f"从磁盘缓存移除条目: {key[:8]}...")
                except Exception as e:
                    logger.warning(f"从磁盘缓存移除条目失败: {str(e)}")

# 创建默认缓存管理器实例
default_cache_manager = DwgCacheManager(
    max_size=int(os.environ.get('DWG_CACHE_SIZE', '50')),
    ttl=int(os.environ.get('DWG_CACHE_TTL', '3600')),
    cache_dir=os.environ.get('DWG_CACHE_DIR')
)