/**
 * 公共交通分析页面的交互功能
 */

// 全局变量
let map = null;         // 百度地图实例
let projectMarker = null; // 项目位置标记
let stationMarkers = []; // 站点标记集合
let searchCircle = null; // 搜索范围圆圈
let currentPosition = null; // 当前选中位置
let stationsData = [];   // 站点数据
let analysisResults = null; // 分析结果对象，用于导出报告

// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('公共交通分析页面加载完成');
    
    // 初始化事件监听
    initEventListeners();
    
    // 自动加载项目信息
    loadProjectInfo();
});

/**
 * 初始化所有事件监听器
 */
function initEventListeners() {
    // 搜索位置按钮
    const searchLocationBtn = document.getElementById('searchLocationBtn');
    if (searchLocationBtn) {
        searchLocationBtn.addEventListener('click', searchProjectLocation);
    }
    
    // 搜索附近站点按钮
    const searchStationsBtn = document.getElementById('searchStations');
    if (searchStationsBtn) {
        searchStationsBtn.addEventListener('click', searchNearbyStations);
    }
    
    // 导出报告按钮 - 修复导出报告按钮的事件监听
    const exportReportBtns = document.querySelectorAll('button');
    exportReportBtns.forEach(btn => {
        if (btn.textContent.includes('导出报告')) {
            btn.id = 'exportReportBtn'; // 设置ID以便于后续操作
            btn.addEventListener('click', exportReport);
        }
    });
}

/**
 * 加载项目信息
 */
function loadProjectInfo() {
    // 获取页面上隐藏的项目ID
    const projectId = document.getElementById('projectId')?.value;
    
    if (!projectId) {
        console.warn('未找到项目ID，尝试从父窗口获取');
        // 尝试从父窗口获取项目信息
        const projectInfo = getFallbackProjectInfo();
        
        // 更新项目地址
        if (projectInfo.location && document.getElementById('projectLocation')) {
            document.getElementById('projectLocation').value = projectInfo.location;
        }
        
        // 确保地图仍然初始化，即使获取项目信息失败
        if (!map) {
            window.baiduMapLoaded = function() {
                initMap();
                
                // 如果备用信息中有坐标，使用这些坐标
                if (projectInfo.latitude && projectInfo.longitude) {
                    setProjectLocation(
                        projectInfo.longitude,
                        projectInfo.latitude,
                        projectInfo.name || '项目位置'
                    );
                } else if (projectInfo.location) {
                    // 如果有地址但没有坐标，尝试搜索地址
                    setTimeout(() => {
                        searchProjectLocation();
                    }, 1000);
                }
            };
            
            if (window.BMap) {
                window.baiduMapLoaded();
            }
        }
        return;
    }
    
    console.log(`尝试获取项目ID: ${projectId} 的信息`);
    
    // 设置请求超时
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
    
    // 使用项目详情页面API获取项目JSON数据
    fetch(`/api/project_info?project_id=${projectId}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'GreenScore-PublicTransportAnalysis/1.0'
        },
        credentials: 'same-origin',
        signal: controller.signal
    })
    .then(async response => {
        // 清除超时计时器
        clearTimeout(timeoutId);
        
        console.log(`获取到响应，状态码: ${response.status}`);
        
        // 检查响应状态
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`项目ID ${projectId} 不存在`);
            }
            throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
        }
        
        // 检查内容类型
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('text/html')) {
            console.warn('服务器返回了HTML页面而不是JSON数据，可能是认证问题，尝试继续处理');
        }
        
        // 获取响应文本
        const text = await response.text();
        
        // 如果响应内容为空，返回一个默认的空对象而不是抛出错误
        if (!text || text.trim() === '') {
            console.warn('服务器返回了空响应，使用默认空对象');
            return {};
        }
        
        // 尝试解析为 JSON
        try {
            return JSON.parse(text);
        } catch (e) {
            console.error("无法解析的响应内容:", text.substring(0, 150) + "...");
            console.warn("尝试使用默认空对象继续");
            // 返回空对象而不是抛出错误，允许代码继续执行
            return {};
        }
    })
    .then(data => {
        console.log('成功解析项目数据:', data);
        
        // 检查API返回格式，更灵活地处理各种情况
        if (data && data.success === false) {
            console.warn('API返回失败状态:', data.message);
            // 不直接抛出错误，而是记录警告并尝试继续处理
            // 如果有message字段，记录警告
            if (data.message) {
                console.warn('API返回提示: ' + data.message);
            }
            // 尝试继续处理，可能有部分可用数据
        }
        
        // 确保数据格式正确 (从API返回的项目数据通常在data字段中)
        let projectData = data.data || data.project || data.projectLocation || data;
        
        // 增强数据格式验证和容错处理
        if (!projectData) {
            console.warn('API返回的数据中没有找到项目信息，尝试使用原始数据');
            projectData = data; // 尝试使用原始数据
        }
        
        // 检查projectData是否为对象类型
        if (typeof projectData !== 'object') {
            console.warn('项目数据不是对象类型，尝试创建默认对象');
            projectData = { name: '未知项目' };
        }
        
        // 确保至少有基本的项目信息
        if (!projectData.name) {
            console.warn('项目数据中没有名称信息，使用默认名称');
            projectData.name = '未命名项目';
        }
        
        // 更新项目地址 - 增强容错处理
        const projectLocation = document.getElementById('projectLocation');
        if (projectLocation) {
            // 检查location是否存在且为非空字符串
            if (projectData.location && typeof projectData.location === 'string' && projectData.location.trim() !== '') {
                projectLocation.value = projectData.location;
            } else {
                console.warn('项目地址信息不完整或无效');
                // 保留输入框现有值，如果有的话
            }
        }
        
        // 检查坐标信息是否有效
        const hasValidCoordinates = (
            projectData.latitude && !isNaN(parseFloat(projectData.latitude)) &&
            projectData.longitude && !isNaN(parseFloat(projectData.longitude))
        );
        
        // 如果有有效的坐标信息，初始化地图
        if (hasValidCoordinates) {
            console.log(`使用项目坐标: 经度=${projectData.longitude}, 纬度=${projectData.latitude}`);
            // 确保地图API已加载
            window.baiduMapLoaded = function() {
                initMap();
                // 设置项目位置
                setProjectLocation(
                    parseFloat(projectData.longitude), 
                    parseFloat(projectData.latitude), 
                    projectData.name || '项目位置'
                );
            };
            
            // 如果百度地图已加载则直接初始化
            if (window.BMap) {
                window.baiduMapLoaded();
            } else {
                console.log('百度地图API尚未加载，等待回调...');
            }
        } else {
            // 没有坐标信息，则在地图加载后自动搜索地址
            window.baiduMapLoaded = function() {
                initMap();
                // 如果有地址信息，自动搜索
                if (projectData.location) {
                    setTimeout(() => {
                        searchProjectLocation();
                    }, 1000);
                }
            };
            
            // 如果百度地图已加载则直接初始化
            if (window.BMap) {
                window.baiduMapLoaded();
            } else {
                console.log('百度地图API尚未加载，等待回调...');
            }
        }
    })
    .catch(error => {
        // 清除超时计时器（以防在catch中未清除）
        clearTimeout(timeoutId);
        
        // 处理特定错误类型
        if (error.name === 'AbortError') {
            console.error("获取项目信息请求超时");
        } else {
            console.error('获取项目信息失败:', error);
        }
        
        // 使用备用方法：从页面上直接获取项目地址
        const fallbackInfo = getFallbackProjectInfo();
        
        if (fallbackInfo.location && document.getElementById('projectLocation')) {
            document.getElementById('projectLocation').value = fallbackInfo.location;
        }
        
        // 确保地图仍然初始化，即使获取项目信息失败
        if (!map && window.BMap) {
            window.baiduMapLoaded = function() {
                initMap();
                
                // 如果备用信息中有坐标，使用这些坐标
                if (fallbackInfo.latitude && fallbackInfo.longitude) {
                    setProjectLocation(
                        fallbackInfo.longitude,
                        fallbackInfo.latitude,
                        fallbackInfo.name || '项目位置'
                    );
                } else if (fallbackInfo.location) {
                    // 如果有地址但没有坐标，尝试搜索地址
                    setTimeout(() => {
                        searchProjectLocation();
                    }, 1000);
                }
            };
            
            if (window.BMap) {
                window.baiduMapLoaded();
            }
        }
    });
}

/**
 * 从页面上获取备用的项目信息
 * 这是一种应急方案，当API调用失败时使用
 */
function getFallbackProjectInfo() {
    try {
        // 尝试从页面中获取项目地址和坐标
        let location = '';
        let latitude = null;
        let longitude = null;
        
        // 首先尝试从当前页面获取
        const currentPageLocation = document.querySelector('.project-location, .location');
        if (currentPageLocation) {
            location = currentPageLocation.textContent.trim();
        }
        
        // 尝试从页面上的隐藏字段获取坐标
        const latField = document.querySelector('input[name="latitude"], #latitude');
        const lngField = document.querySelector('input[name="longitude"], #longitude');
        
        if (latField && !isNaN(parseFloat(latField.value))) {
            latitude = parseFloat(latField.value);
        }
        
        if (lngField && !isNaN(parseFloat(lngField.value))) {
            longitude = parseFloat(lngField.value);
        }
        
        // 如果当前页面没有找到，尝试从父页面获取
        if ((!name || !location) && window.parent && window.parent.document) {
            try {
                const projectNameElement = window.parent.document.querySelector('.project-name');
                if (projectNameElement && !name) {
                    name = projectNameElement.textContent.trim();
                }
                
                const locationElement = window.parent.document.querySelector('.project-location');
                if (locationElement && !location) {
                    location = locationElement.textContent.trim();
                }
                
                // 如果没有找到项目名称，尝试其他可能的选择器
                if (!name) {
                    const possibleNameElements = [
                        window.parent.document.querySelector('.project-title'),
                        window.parent.document.querySelector('h1'),
                        window.parent.document.querySelector('title')
                    ];
                    
                    for (const element of possibleNameElements) {
                        if (element && element.textContent) {
                            name = element.textContent.trim();
                            if (name) break;
                        }
                    }
                }
                
                // 尝试从父页面获取坐标
                if (latitude === null || longitude === null) {
                    const parentLatField = window.parent.document.querySelector('input[name="latitude"], #latitude, .latitude');
                    const parentLngField = window.parent.document.querySelector('input[name="longitude"], #longitude, .longitude');
                    
                    if (parentLatField && !isNaN(parseFloat(parentLatField.value || parentLatField.textContent))) {
                        latitude = parseFloat(parentLatField.value || parentLatField.textContent);
                    }
                    
                    if (parentLngField && !isNaN(parseFloat(parentLngField.value || parentLngField.textContent))) {
                        longitude = parseFloat(parentLngField.value || parentLngField.textContent);
                    }
                }
            } catch (innerError) {
                console.warn('访问父窗口DOM时出错:', innerError);
                // 内部错误不会中断整个函数
            }
        }
        
        // 如果仍然没有找到名称，使用URL中可能包含的信息
        if (!name) {
            try {
                const urlParams = new URLSearchParams(window.location.search);
                const projectIdFromUrl = urlParams.get('project_id');
                if (projectIdFromUrl) {
                    name = `项目 #${projectIdFromUrl}`;
                    
                    // 尝试从localStorage获取该项目的缓存信息
                    try {
                        const cachedProject = localStorage.getItem(`project_${projectIdFromUrl}`);
                        if (cachedProject) {
                            const projectData = JSON.parse(cachedProject);
                            if (projectData.name) name = projectData.name;
                            if (projectData.location) location = projectData.location;
                            if (projectData.latitude) latitude = projectData.latitude;
                            if (projectData.longitude) longitude = projectData.longitude;
                        }
                    } catch (storageError) {
                        console.warn('从localStorage获取缓存项目信息失败:', storageError);
                    }
                }
            } catch (urlError) {
                console.warn('从URL获取项目ID失败:', urlError);
            }
        }
        
        // 如果仍然没有找到位置信息，尝试使用默认位置（如成都市中心）
        if (!location && !latitude && !longitude) {
            console.warn('未找到位置信息，使用默认位置');
            location = '成都市';
            latitude = 30.67;
            longitude = 104.06;
        }
        
        console.log('获取到备用项目信息:', { name, location, latitude, longitude });
        return { name, location, latitude, longitude };
    } catch (e) {
        console.error('获取备用项目信息失败:', e);
        return { name: '未知项目', location: '成都市', latitude: 30.67, longitude: 104.06 };
    }
}

// 项目名称相关功能已移除

/**
 * 初始化百度地图
 */
function initMap() {
    if (!window.BMap) {
        console.error('百度地图API未加载');
        // 尝试重新加载百度地图API
        const script = document.createElement('script');
        script.src = `/api/map_js_api?v=3.0&callback=initBaiduMap`;
        script.type = 'text/javascript';
        document.head.appendChild(script);
        console.log('尝试重新加载百度地图API...');
        return;
    }
    
    try {
        // 确保BMap.Map是一个构造函数
        if (typeof BMap.Map !== 'function') {
            console.error('BMap.Map不是一个构造函数，百度地图API可能未正确加载');
            return;
        }
        
        // 如果百度地图没有提供checkResize方法，添加一个
        if (!BMap.Map.prototype.checkResize) {
            BMap.Map.prototype.checkResize = function() {
                this.reset();
                this.resize();
                this.enableAutoResize();
            };
        }
        
        // 创建地图实例
        map = new BMap.Map("map");
        
        // 默认中心点成都
        const defaultPoint = new BMap.Point(104.06, 30.67);
        map.centerAndZoom(defaultPoint, 13);
        
        // 添加地图控件
        map.addControl(new BMap.NavigationControl());  // 平移缩放控件
        map.addControl(new BMap.ScaleControl());       // 比例尺控件
        map.enableScrollWheelZoom();                   // 允许滚轮缩放
        
        // 添加地图点击事件
        map.addEventListener("click", function(e) {
            setProjectLocation(e.point.lng, e.point.lat, "选中位置");
        });
        
        console.log('百度地图初始化成功');
    } catch (e) {
        console.error('初始化地图失败:', e);
    }
}

/**
 * 设置项目位置
 */
function setProjectLocation(lng, lat, title) {
    if (!map) return;
    
    try {
        // 创建坐标点
        const point = new BMap.Point(lng, lat);
        
        // 清除已有标记
        if (projectMarker) {
            map.removeOverlay(projectMarker);
        }
        
        // 创建新标记
        projectMarker = new BMap.Marker(point);
        map.addOverlay(projectMarker);
        
        // 添加标记信息窗口
        const infoWindow = new BMap.InfoWindow(title);
        projectMarker.addEventListener("click", function() {
            this.openInfoWindow(infoWindow);
        });
        
        // 设置地图中心点
        map.centerAndZoom(point, 15);
        
        // 更新当前位置
        currentPosition = point;
        
        // 更新坐标显示
        updateCoordinatesDisplay(lng, lat);
        
        console.log(`已设置项目位置: ${lng}, ${lat}`);
        return true;
    } catch (e) {
        console.error('设置项目位置失败:', e);
        return false;
    }
}

/**
 * 更新坐标显示
 */
function updateCoordinatesDisplay(lng, lat) {
    const coordsElement = document.getElementById('projectCoordinates');
    if (coordsElement) {
        coordsElement.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
}

/**
 * 搜索项目位置
 */
function searchProjectLocation() {
    if (!map) {
        console.error('地图未初始化');
        return;
    }
    
    // 获取地址输入
    const addressInput = document.getElementById('projectLocation');
    if (!addressInput || !addressInput.value.trim()) {
        alert('请输入项目地址');
        return;
    }
    
    const address = addressInput.value.trim();
    
    // 创建地址解析器
    const myGeo = new BMap.Geocoder();
    
    // 解析地址信息
    myGeo.getPoint(address, function(point) {
        if (point) {
            // 设置项目位置
            const success = setProjectLocation(point.lng, point.lat, address);
            if (success) {
                // 更新当前地址
                addressInput.value = address;
            }
        } else {
            alert('未找到该地址的位置信息');
        }
    }, "中国");
}

/**
 * 搜索附近站点
 */
function searchNearbyStations() {
    if (!map || !currentPosition) {
        alert('请先选择项目位置');
        return;
    }
    
    // 清除已有站点标记
    clearStationMarkers();
    
    // 获取搜索半径
    const radiusSelect = document.getElementById('searchRadius');
    const radius = parseInt(radiusSelect ? radiusSelect.value : 500);
    
    // 显示搜索范围圆圈
    showSearchRadius(currentPosition, radius);
    
    // 创建地点搜索实例
    const searchRequest = {
        location: currentPosition,
        radius: radius,
        onSearchComplete: function(results) {
            // 处理搜索结果
            processStationResults(results, radius);
            
            // 确保布局稳定
            ensureStableLayout();
        },
        pageCapacity: 50
    };
    
    // 创建本地搜索实例
    const localSearch = new BMap.LocalSearch(map, searchRequest);
    
    // 执行公交站点搜索
    localSearch.searchNearby('公交站', currentPosition, radius);
    localSearch.searchNearby('地铁站', currentPosition, radius);
    
    // 显示加载提示
    updateStationList([{
        html: `<div class="text-center py-4">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <div class="mt-2">正在搜索附近站点...</div>
              </div>`
    }]);
}

/**
 * 确保布局稳定
 */
function ensureStableLayout() {
    // 强制地图容器保持原有尺寸
    const mapParent = document.querySelector('.map-parent-container');
    if (mapParent) {
        mapParent.style.width = '60%';
        mapParent.style.minWidth = '60%';
        mapParent.style.maxWidth = '60%';
    }
    
    // 强制侧边栏容器保持尺寸
    const sideContainer = document.querySelector('.side-container');
    if (sideContainer) {
        sideContainer.style.width = '40%';
        sideContainer.style.minWidth = '40%';
        sideContainer.style.maxWidth = '40%';
    }
    
    // 刷新地图大小以适应容器
    if (map) {
        setTimeout(() => {
            map.checkResize();
        }, 300);
    }
}

/**
 * 清除所有站点标记
 */
function clearStationMarkers() {
    // 清除地图上的站点标记
    stationMarkers.forEach(marker => {
        map.removeOverlay(marker);
    });
    stationMarkers = [];
    
    // 清除搜索圆圈
    if (searchCircle) {
        map.removeOverlay(searchCircle);
        searchCircle = null;
    }
    
    // 清空站点数据
    stationsData = [];
}

/**
 * 显示搜索半径圆圈
 */
function showSearchRadius(center, radius) {
    // 清除旧的圆圈
    if (searchCircle) {
        map.removeOverlay(searchCircle);
    }
    
    // 创建新的圆圈
    searchCircle = new BMap.Circle(center, radius, {
        strokeColor: "#1E88E5",
        strokeWeight: 2,
        strokeOpacity: 0.6,
        fillColor: "#1E88E5",
        fillOpacity: 0.1
    });
    
    // 添加到地图
    map.addOverlay(searchCircle);
}

/**
 * 处理站点搜索结果
 */
function processStationResults(results, searchRadius) {
    if (!results || results.getNumPois() === 0) {
        return;
    }
    
    // 获取站点数据
    const pois = results.getPois();
    const newStations = [];
    
    // 站点类型检查，过滤出公交站和地铁站
    const stationTypes = ['公交车站', '公交站', '地铁站', '轻轨站'];
    
    pois.forEach(poi => {
        // 检查是否为公交站或地铁站
        if (!stationTypes.some(type => poi.type.includes(type))) {
            return;
        }
        
        // 计算到项目的距离
        const distance = map.getDistance(currentPosition, poi.point).toFixed(0);
        
        // 如果超出搜索范围，跳过
        if (distance > searchRadius) {
            return;
        }
        
        // 确定站点类型
        let stationType = '公交站';
        if (poi.type.includes('地铁') || poi.title.includes('地铁')) {
            stationType = '地铁站';
        }
        
        // 添加到站点数据中
        const station = {
            name: poi.title,
            type: stationType,
            point: poi.point,
            address: poi.address,
            distance: parseInt(distance)
        };
        
        // 检查是否已存在相同名称的站点
        const existingIndex = stationsData.findIndex(s => s.name === station.name);
        if (existingIndex === -1) {
            stationsData.push(station);
            newStations.push(station);
        }
    });
    
    // 添加新站点的标记
    addStationMarkers(newStations);
    
    // 更新站点列表显示
    updateStationDisplay();
    
    // 分析站点数据
    analyzeStations(stationsData, searchRadius);
}

/**
 * 添加站点标记
 */
function addStationMarkers(stations) {
    stations.forEach(station => {
        // 创建不同颜色的图标
        const iconUrl = station.type === '地铁站' 
            ? '/static/image/metro_icon.png'  // 地铁站图标
            : '/static/image/bus_icon.png';   // 公交站图标
            
        // 如果图标不存在，使用默认标记
        let marker;
        try {
            const icon = new BMap.Icon(iconUrl, new BMap.Size(24, 24));
            marker = new BMap.Marker(station.point, {icon: icon});
        } catch (e) {
            // 使用默认标记
            marker = new BMap.Marker(station.point);
        }
        
        // 添加点击事件
        const infoWindow = new BMap.InfoWindow(
            `<div style="padding: 8px;">
                <h3 style="margin-bottom: 8px; font-weight: bold;">${station.name}</h3>
                <p>类型: ${station.type}</p>
                <p>距离: ${station.distance}米</p>
                <p>地址: ${station.address || '未知'}</p>
            </div>`
        );
        marker.addEventListener("click", function() {
            this.openInfoWindow(infoWindow);
        });
        
        // 添加到地图
        map.addOverlay(marker);
        stationMarkers.push(marker);
    });
}

/**
 * 更新站点显示
 */
function updateStationDisplay() {
    // 更新站点计数
    updateStationCount();
    
    // 按距离排序
    const sortedStations = [...stationsData].sort((a, b) => a.distance - b.distance);
    
    // 更新站点列表
    const stationItems = sortedStations.map(station => ({
        html: `<div class="station-item p-3 border-b border-gray-200 hover:bg-blue-50 transition-colors"
                   data-name="${station.name}" data-lng="${station.point.lng}" data-lat="${station.point.lat}">
                <div class="flex justify-between items-center">
                    <div class="font-medium">${station.name}</div>
                    <div class="text-sm text-gray-600">${station.distance}米</div>
                </div>
                <div class="text-sm text-gray-600 mt-1">
                    <span class="inline-block px-2 py-1 rounded-full text-xs ${
                        station.type === '地铁站' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                    }">${station.type}</span>
                </div>
              </div>`
    }));
    
    updateStationList(stationItems);
    
    // 添加站点项点击事件
    addStationItemClickEvents();
    
    // 确保布局稳定
    ensureStableLayout();
}

/**
 * 更新站点计数
 */
function updateStationCount() {
    const countElement = document.getElementById('stationCount');
    if (!countElement) return;
    
    // 计算不同类型的站点数量
    const busStations = stationsData.filter(s => s.type === '公交站').length;
    const metroStations = stationsData.filter(s => s.type === '地铁站').length;
    
    countElement.innerHTML = `
        <div class="flex justify-between">
            <div>
                共找到 <span class="font-semibold text-blue-600">${stationsData.length}</span> 个站点
            </div>
            <div>
                <span class="inline-block px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700 mr-2">
                    公交站: ${busStations}
                </span>
                <span class="inline-block px-2 py-1 rounded-full text-xs bg-green-100 text-green-700">
                    地铁站: ${metroStations}
                </span>
            </div>
        </div>
    `;
}

/**
 * 更新站点列表
 */
function updateStationList(items) {
    const listElement = document.getElementById('stationList');
    if (!listElement) return;
    
    // 如果没有站点
    if (items.length === 0) {
        listElement.innerHTML = `
            <div class="text-gray-500 text-center py-8">
                未找到附近站点
            </div>
        `;
        return;
    }
    
    // 更新列表内容
    listElement.innerHTML = items.map(item => item.html).join('');
}

/**
 * 添加站点项点击事件
 */
function addStationItemClickEvents() {
    const stationItems = document.querySelectorAll('.station-item');
    
    stationItems.forEach(item => {
        item.addEventListener('click', function() {
            // 移除所有选中样式
            stationItems.forEach(i => i.classList.remove('selected'));
            
            // 添加选中样式
            this.classList.add('selected');
            
            // 获取站点坐标
            const lng = parseFloat(this.dataset.lng);
            const lat = parseFloat(this.dataset.lat);
            const name = this.dataset.name;
            
            // 找到对应的标记
            const point = new BMap.Point(lng, lat);
            const marker = stationMarkers.find(m => {
                return Math.abs(m.getPosition().lng - lng) < 0.0001 && 
                       Math.abs(m.getPosition().lat - lat) < 0.0001;
            });
            
            // 打开信息窗口
            if (marker) {
                // 获取站点数据
                const station = stationsData.find(s => s.name === name);
                if (station) {
                    const infoWindow = new BMap.InfoWindow(
                        `<div style="padding: 8px;">
                            <h3 style="margin-bottom: 8px; font-weight: bold;">${station.name}</h3>
                            <p>类型: ${station.type}</p>
                            <p>距离: ${station.distance}米</p>
                            <p>地址: ${station.address || '未知'}</p>
                        </div>`
                    );
                    marker.openInfoWindow(infoWindow);
                }
            }
            
            // 平移地图
            map.panTo(point);
        });
    });
}

/**
 * 分析站点数据
 */
function analyzeStations(stations, searchRadius) {
    if (!stations || stations.length === 0) {
        showAnalysisResults({
            busStations: { total: 0, qualified: 0, nearest: null },
            subwayStations: { total: 0, qualified: 0, nearest: null },
            evaluation: { result: '不符合', score: 0 }
        });
        
        // 确保布局稳定
        ensureStableLayout();
        return;
    }
    
    // 筛选公交站和地铁站
    const busStations = stations.filter(s => s.type === '公交站');
    const subwayStations = stations.filter(s => s.type === '地铁站');
    
    // 按距离排序
    busStations.sort((a, b) => a.distance - b.distance);
    subwayStations.sort((a, b) => a.distance - b.distance);
    
    // 符合条件的站点数量（公交站500米内，地铁站800米内）
    const qualifiedBusStations = busStations.filter(s => s.distance <= 500);
    const qualifiedSubwayStations = subwayStations.filter(s => s.distance <= 800);
    
    // 最近的站点
    const nearestBus = busStations.length > 0 ? busStations[0] : null;
    const nearestSubway = subwayStations.length > 0 ? subwayStations[0] : null;
    
    // 评价结果（根据绿色建筑评价标准）
    let result = '不符合';
    let score = 0;
    
    // 有效站点数量评价
    if (qualifiedBusStations.length >= 2 || qualifiedSubwayStations.length >= 1) {
        result = '符合';
        score = 8;
    }
    
    // 创建分析结果
    analysisResults = {
        busStations: {
            total: busStations.length,
            qualified: qualifiedBusStations.length,
            nearest: nearestBus
        },
        subwayStations: {
            total: subwayStations.length,
            qualified: qualifiedSubwayStations.length,
            nearest: nearestSubway
        },
        evaluation: {
            result: result,
            score: score
        },
        projectName: document.getElementById('projectNameText')?.textContent || '未命名项目',
        projectLocation: document.getElementById('projectLocation')?.value || '未知地址',
        projectCoordinates: document.getElementById('projectCoordinates')?.textContent || '未知坐标',
        searchRadius: searchRadius,
        timestamp: new Date().toLocaleString('zh-CN')
    };
    
    // 显示分析结果
    showAnalysisResults(analysisResults);
    
    // 确保布局稳定
    ensureStableLayout();
}

/**
 * 显示分析结果
 */
function showAnalysisResults(results) {
    const resultElement = document.getElementById('analysisResult');
    if (!resultElement) return;
    
    // 获取最近的站点信息
    const nearestBus = results.busStations.nearest;
    const nearestSubway = results.subwayStations.nearest;
    
    // 格式化显示内容
    resultElement.innerHTML = `
        <div class="mb-4">
            <div class="flex justify-between items-center mb-2">
                <div class="font-medium">评价结果:</div>
                <div class="px-3 py-1 rounded-full text-sm ${
                    results.evaluation.result === '符合' 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-red-100 text-red-700'
                }">
                    ${results.evaluation.result}
                </div>
            </div>
            <div class="text-sm">
                得分: <span class="font-semibold">${results.evaluation.score}</span> 分
            </div>
        </div>
        
        <div class="border-t pt-4">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <div class="font-medium mb-2">公交站点情况:</div>
                    <div class="text-sm">
                        <div>站点总数: ${results.busStations.total}</div>
                        <div>500米内站点数: ${results.busStations.qualified}</div>
                        <div>最近站点: ${nearestBus ? nearestBus.name : '无'}</div>
                        <div>最近距离: ${nearestBus ? nearestBus.distance + '米' : '无'}</div>
                    </div>
                </div>
                
                <div>
                    <div class="font-medium mb-2">地铁站点情况:</div>
                    <div class="text-sm">
                        <div>站点总数: ${results.subwayStations.total}</div>
                        <div>800米内站点数: ${results.subwayStations.qualified}</div>
                        <div>最近站点: ${nearestSubway ? nearestSubway.name : '无'}</div>
                        <div>最近距离: ${nearestSubway ? nearestSubway.distance + '米' : '无'}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-4 text-xs text-gray-500">
            根据《绿色建筑评价标准》，公共交通条件评分标准：<br>
            - 500米范围内有2个以上公交站点，或800米范围内有轨道交通站点：8分<br>
            - 其它情况：不得分
        </div>
    `;
}

/**
 * 导出公共交通分析报告
 */
function exportReport() {
    // 检查是否有分析结果
    if (!analysisResults) {
        alert('请先搜索附近站点并生成分析结果');
        return;
    }
    
    // 获取项目ID
    const projectId = document.getElementById('projectId').value;
    if (!projectId) {
        alert('未找到项目ID，无法导出报告');
        return;
    }
    
    // 显示加载状态
    const exportBtn = document.getElementById('exportReportBtn');
    if (exportBtn) {
        const originalText = exportBtn.innerHTML;
        exportBtn.innerHTML = '<i class="ri-loader-2-line animate-spin mr-2"></i>导出中...';
        exportBtn.disabled = true;
        
        // 准备要发送的数据
        const reportData = {
            projectId: projectId,
            projectName: analysisResults.projectName,
            projectLocation: analysisResults.projectLocation,
            projectCoordinates: analysisResults.projectCoordinates,
            searchRadius: analysisResults.searchRadius,
            busStations: {
                total: analysisResults.busStations.total,
                qualified: analysisResults.busStations.qualified,
                nearest: analysisResults.busStations.nearest ? {
                    name: analysisResults.busStations.nearest.name,
                    distance: analysisResults.busStations.nearest.distance
                } : null
            },
            subwayStations: {
                total: analysisResults.subwayStations.total,
                qualified: analysisResults.subwayStations.qualified,
                nearest: analysisResults.subwayStations.nearest ? {
                    name: analysisResults.subwayStations.nearest.name,
                    distance: analysisResults.subwayStations.nearest.distance
                } : null
            },
            evaluation: analysisResults.evaluation,
            timestamp: new Date().toISOString()
        };
        
        // 发送请求生成报告
        fetch('/api/export/public_transport_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(reportData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`服务器响应错误: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `公共交通分析报告_${analysisResults.projectName}_${new Date().toLocaleDateString().replace(/\//g, '-')}.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            // 恢复按钮状态
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
        })
        .catch(error => {
            console.error('导出报告失败:', error);
            alert(`导出报告失败: ${error.message}`);
            
            // 恢复按钮状态
            exportBtn.innerHTML = originalText;
            exportBtn.disabled = false;
        });
    } else {
        alert('导出功能初始化失败，请刷新页面重试');
    }
}
