/**
 * 中国建筑气候区划查询工具
 * 用于根据省份和城市查询相应的气候区划
 */

// 检查是否已经加载
if (typeof window.climateZoneInitialized === 'undefined') {
    // 定义全局变量存储气候区划数据
    window.climateZonesData = window.climateZonesData || [];

    // 加载气候区划数据
    function loadClimateZones() {
        // 如果数据已经加载，不再重复加载
        if (window.climateZonesData.length > 0) {
            console.log('气候区划数据已加载，跳过');
            return;
        }
        
        fetch('/static/json/climate_zones.json')
            .then(response => response.json())
            .then(data => {
                window.climateZonesData = data;
                console.log('气候区划数据加载完成');
            })
            .catch(error => {
                console.error('加载气候区划数据失败:', error);
            });
    }

    // 页面加载完成后执行
    document.addEventListener('DOMContentLoaded', loadClimateZones);

    /**
     * 根据省份和城市查询气候区划
     * @param {string} province - 省份名称
     * @param {string} city - 城市名称
     * @returns {Object|null} - 返回匹配的气候区划信息，未找到则返回null
     */
    function getClimateZone(province, city) {
        if (!window.climateZonesData || window.climateZonesData.length === 0) {
            console.warn('气候区划数据尚未加载');
            return null;
        }

        // 精确匹配省份和城市
        let result = window.climateZonesData.find(item => 
            item.省 === province && item.地级市 === city
        );

        // 如果没有找到精确匹配，尝试只匹配城市
        if (!result) {
            result = window.climateZonesData.find(item => 
                item.地级市 === city
            );
        }

        return result;
    }

    /**
     * 根据省份获取所有城市
     * @param {string} province - 省份名称
     * @returns {Array} - 返回该省份的所有城市列表
     */
    function getCitiesByProvince(province) {
        if (!window.climateZonesData || window.climateZonesData.length === 0) {
            console.warn('气候区划数据尚未加载');
            return [];
        }

        const cities = window.climateZonesData
            .filter(item => item.省 === province)
            .map(item => item.地级市);
        
        return cities;
    }

    /**
     * 获取所有省份列表
     * @returns {Array} - 返回所有省份列表（去重）
     */
    function getAllProvinces() {
        if (!window.climateZonesData || window.climateZonesData.length === 0) {
            console.warn('气候区划数据尚未加载');
            return [];
        }

        const provinces = [...new Set(window.climateZonesData.map(item => item.省))];
        return provinces;
    }

    /**
     * 自动填充气候区划信息
     * @param {string} provinceSelector - 省份选择器ID
     * @param {string} citySelector - 城市选择器ID
     * @param {string} zoneSelector - 气候区划输出元素ID
     */
    function autoFillClimateZone(provinceSelector, citySelector, zoneSelector) {
        const provinceElement = document.getElementById(provinceSelector);
        const cityElement = document.getElementById(citySelector);
        const zoneElement = document.getElementById(zoneSelector);
        
        if (!provinceElement || !cityElement || !zoneElement) {
            console.warn('未找到指定的表单元素');
            return;
        }
        
        // 当省份或城市变化时更新气候区划
        function updateClimateZone() {
            const province = provinceElement.value;
            const city = cityElement.value;
            
            if (province && city) {
                const zoneInfo = getClimateZone(province, city);
                if (zoneInfo) {
                    zoneElement.value = `${zoneInfo.分区名称}(${zoneInfo.气候区划})`;
                } else {
                    zoneElement.value = '';
                }
            } else {
                zoneElement.value = '';
            }
        }
        
        // 监听省份和城市变化事件
        provinceElement.addEventListener('change', () => {
            // 更新城市下拉列表
            const cities = getCitiesByProvince(provinceElement.value);
            cityElement.innerHTML = '<option value="">请选择城市</option>';
            cities.forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                cityElement.appendChild(option);
            });
            
            updateClimateZone();
        });
        
        cityElement.addEventListener('change', updateClimateZone);
    }

    // 将函数暴露到全局命名空间
    window.climateZoneUtils = {
        getClimateZone,
        getCitiesByProvince,
        getAllProvinces,
        autoFillClimateZone,
        loadClimateZones
    };

    // 标记脚本已初始化
    window.climateZoneInitialized = true;
    console.log('climate_zone.js 初始化完成');
} else {
    console.log('climate_zone.js 已经加载，跳过重复初始化');
} 