/**
 * 公共交通分析报告生成工具
 * 用于分析项目周边公共交通情况，生成符合《绿色建筑评价标准》的分析报告
 */

// 定义全局变量
window.mapObj = null;
window.projectMarker = null;
window.stationMarkers = [];
window.stationCircle = null;
window.stations = [];
window.selectedProjectPoint = null;
window.analysisResults = null;
window.projectData = {
    name: '',
    location: '',
    coordinates: null
};

// 定义绿色建筑标准的评价等级和分值
const greenBuildingStandard = {
    // 按照《绿色建筑评价标准》GB/T 50378-2019 第5.2.2条
    publicTransportation: {
        description: "场地人行出入口到达公共交通站点的步行距离不大于500m，或到达轨道交通站的步行距离不大于800m。",
        criteria: [
            { type: "公交站", maxDistance: 500, score: 6 },
            { type: "轨道交通站", maxDistance: 800, score: 10 }
        ]
    }
};

// 监听来自父页面的消息
window.addEventListener('message', function(event) {
    // 只处理来自父窗口的消息
    if (event.source !== window.parent) return;
    
    console.log('收到来自父窗口的消息:', event.data);
    
    // 处理项目信息消息
    if (event.data && event.data.type === 'projectInfo') {
        const projectInfo = event.data.data;
        console.log('收到项目信息:', projectInfo);
        
        if (projectInfo.projectId) {
            // 更新UI显示和存储项目ID
            document.getElementById("projectId").value = projectInfo.projectId;
            console.log('设置项目ID:', projectInfo.projectId);
            
            // 如果有项目名称，直接显示
            if (projectInfo.projectName) {
                document.getElementById("projectName").textContent = projectInfo.projectName;
                
                // 更新全局项目数据
                window.projectData.name = projectInfo.projectName;
            }
            
            // 获取项目详细信息
            getProjectData(projectInfo.projectId).then(data => {
                if (data) {
                    console.log('获取到项目详细信息:', data);
                    window.projectData = data;
                    document.getElementById("projectName").textContent = data.name;
                    document.getElementById("projectLocation").value = data.location || '';
                    
                    // 如果有地址，尝试查找位置
                    if (data.location) {
                        searchLocation(data.location);
                    }
                }
            }).catch(error => {
                console.error('获取项目详细信息失败:', error);
            });
        }
        
        // 向父页面发送准备就绪消息
        window.parent.postMessage({ type: 'iframeReady' }, '*');
    }
});

// 定义百度地图API加载完成后的回调函数
window.baiduMapLoaded = function() {
    console.log('百度地图API加载完成回调被触发');
    startApp();
};

// 获取项目信息
async function getProjectData(projectId) {
    if (!projectId) return null;
    
    try {
        console.log('正在获取项目数据，项目ID:', projectId);
        // 调用API获取项目信息
        const response = await fetch(`/api/project_info?project_id=${projectId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        console.log('获取到项目信息:', data);
        return {
            name: data.name || '未命名项目',
            location: data.location || '',
            coordinates: null // 初始时坐标为空，需要通过地图定位获取
        };
    } catch (error) {
        console.error('获取项目信息失败:', error);
        return {
            name: '未命名项目',
            location: '',
            coordinates: null
        };
    }
}

// 初始化地图
function initMap() {
    // 如果BMap不存在，显示提示信息并返回null
    if (typeof BMap === 'undefined') {
        console.error('百度地图API未加载成功，无法初始化地图');
        // 在地图容器中显示错误信息
        const mapContainer = document.getElementById("map");
        if (mapContainer) {
            mapContainer.innerHTML = '<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图API加载失败，请刷新页面重试</div>';
        }
        return null;
    }
    
    console.log('初始化地图组件');
    
    try {
        // 创建地图实例
        var map = new BMap.Map("map");
        // 初始中心点设为成都
        var point = new BMap.Point(104.06, 30.67);
        map.centerAndZoom(point, 12);
        map.enableScrollWheelZoom(true);
        
        // 设置地图区域的鼠标样式为默认箭头
        document.getElementById("map").style.cursor = "default";
        
        // 添加控件
        map.addControl(new BMap.NavigationControl());
        map.addControl(new BMap.ScaleControl());
        
        // 创建项目标记图标
        var projectIcon = new BMap.Icon("/api/map_proxy?service_path=images/marker_red.png", new BMap.Size(39, 50), {
            anchor: new BMap.Size(19, 50) // 锚点设置为图标底部中心
        });
        
        // 创建项目位置标记，初始位置为地图中心
        var marker = new BMap.Marker(point, {icon: projectIcon});
        map.addOverlay(marker);
        window.projectMarker = marker;
        
        // 定义站点图标
        var stationIcon = new BMap.Icon("/api/map_proxy?service_path=images/info.png", new BMap.Size(20, 20), {
            anchor: new BMap.Size(10, 10) // 锚点设置为图标中心
        });
        window.stationIcon = stationIcon;
        
        // 点击地图更新项目坐标
        map.addEventListener("click", function(e) {
            // 更新项目标记位置
            marker.setPosition(e.point);
            window.selectedProjectPoint = e.point;
            
            // 更新坐标显示
            document.getElementById("projectCoordinates").textContent = `${e.point.lng.toFixed(6)}, ${e.point.lat.toFixed(6)}`;
            
            // 清除之前的站点标记和分析结果
            clearStations();
            clearAnalysisResults();
            
            // 使用逆地理编码获取地点名称
            var geoc = new BMap.Geocoder();
            geoc.getLocation(e.point, function(rs){
                if (rs) {
                    var addComp = rs.addressComponents;
                    var location = addComp.province + addComp.city + addComp.district + addComp.street + addComp.streetNumber;
                    document.getElementById("projectLocation").value = location;
                    
                    // 更新项目位置信息
                    window.projectData.location = location;
                    window.projectData.coordinates = {
                        lng: e.point.lng,
                        lat: e.point.lat
                    };
                }
            });
        });
        
        return map;
    } catch (error) {
        console.error('初始化地图时出错:', error);
        const mapContainer = document.getElementById("map");
        if (mapContainer) {
            mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图初始化错误: ${error.message}</div>`;
        }
        return null;
    }
}

// 清除站点标记
function clearStations() {
    // 清除站点标记
    if (window.stationMarkers && window.stationMarkers.length > 0) {
        window.stationMarkers.forEach(marker => {
            window.mapObj.removeOverlay(marker);
        });
        window.stationMarkers = [];
    }
    
    // 清除搜索范围圆圈
    if (window.stationCircle) {
        window.mapObj.removeOverlay(window.stationCircle);
        window.stationCircle = null;
    }
    
    // 清空站点数据和列表
    window.stations = [];
    document.getElementById("stationList").innerHTML = '<div class="text-gray-500 text-center py-8">请点击"搜索附近站点"按钮查询公交站点</div>';
    document.getElementById("stationCount").textContent = "未搜索到站点";
}

// 清除分析结果
function clearAnalysisResults() {
    document.getElementById("analysisResult").innerHTML = '<div class="text-gray-500 text-center py-8">请先搜索附近站点进行分析</div>';
    document.getElementById("scoreResult").classList.add("hidden");
    document.getElementById("exportReport").disabled = true;
}

// 启动应用
function startApp() {
    // 初始化地图
    window.mapObj = initMap();
    if (!window.mapObj) {
        console.error('地图初始化失败');
        return;
    }
    
    try {
        // 获取项目信息
        const projectId = document.getElementById("projectId")?.value;
        
        if (projectId) {
            console.log(`使用项目ID: ${projectId}`);
            getProjectData(projectId).then(data => {
                if (data) {
                    window.projectData = data;
                    document.getElementById("projectName").textContent = data.name;
                    
                    // 设置项目地址并确保输入框可用
                    const locationInput = document.getElementById("projectLocation");
                    locationInput.value = data.location || '';
                    locationInput.readOnly = false;
                    locationInput.disabled = false;
                    
                    // 如果有地址，尝试查找位置
                    if (data.location) {
                        searchLocation(data.location);
                    }
                }
            }).catch(error => {
                console.error('获取项目数据失败:', error);
                document.getElementById("projectName").textContent = "未关联项目或加载失败";
                
                // 确保输入框可用
                const locationInput = document.getElementById("projectLocation");
                locationInput.readOnly = false;
                locationInput.disabled = false;
            });
        } else {
            console.log('未找到项目ID，使用独立模式');
            document.getElementById("projectName").textContent = "未关联项目";
            
            // 确保输入框可用
            const locationInput = document.getElementById("projectLocation");
            locationInput.readOnly = false;
            locationInput.disabled = false;
        }
    } catch (error) {
        console.error('启动应用时出错:', error);
        document.getElementById("projectName").textContent = "未关联项目或加载失败";
        
        // 确保输入框可用
        const locationInput = document.getElementById("projectLocation");
        locationInput.readOnly = false;
        locationInput.disabled = false;
    }
    
    // 绑定搜索位置按钮事件
    document.getElementById("searchLocation").addEventListener("click", function() {
        const location = document.getElementById("projectLocation").value;
        if (location) {
            searchLocation(location);
        } else {
            alert("请输入项目地址");
        }
    });
    
    // 绑定输入框回车事件
    document.getElementById("projectLocation").addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            const location = this.value;
            if (location) {
                searchLocation(location);
            } else {
                alert("请输入项目地址");
            }
        }
    });
    
    // 绑定搜索站点按钮事件
    document.getElementById("searchStations").addEventListener("click", function() {
        if (!window.selectedProjectPoint) {
            alert("请先选择或搜索项目位置");
            return;
        }
        
        const radius = parseInt(document.getElementById("searchRadius").value);
        searchNearbyStations(window.selectedProjectPoint, radius);
    });
    
    // 绑定导出报告按钮事件
    document.getElementById("exportReport").addEventListener("click", function() {
        if (!window.analysisResults) {
            alert("请先完成公共交通分析");
            return;
        }
        
        generateReport();
    });
}

// 搜索位置函数
function searchLocation(address) {
    if (!address || !window.mapObj) return;
    
    const myGeo = new BMap.Geocoder();
    myGeo.getPoint(address, function(point) {
        if (point) {
            window.mapObj.centerAndZoom(point, 15);
            window.projectMarker.setPosition(point);
            window.selectedProjectPoint = point;
            
            // 更新坐标显示
            document.getElementById("projectCoordinates").textContent = `${point.lng.toFixed(6)}, ${point.lat.toFixed(6)}`;
            
            // 更新项目位置信息
            window.projectData.location = address;
            window.projectData.coordinates = {
                lng: point.lng,
                lat: point.lat
            };
            
            // 清除之前的站点标记和分析结果
            clearStations();
            clearAnalysisResults();
        } else {
            alert("未找到该地址，请尝试更详细的地址信息");
        }
    }, "");
}

// 搜索附近公交站点
function searchNearbyStations(point, radius) {
    if (!point || !window.mapObj) return;
    
    // 清除之前的站点标记和分析结果
    clearStations();
    clearAnalysisResults();
    
    // 添加搜索范围圆形
    const circle = new BMap.Circle(point, radius, {
        strokeColor: "blue",
        strokeWeight: 2,
        strokeOpacity: 0.3,
        fillColor: "blue",
        fillOpacity: 0.1
    });
    window.mapObj.addOverlay(circle);
    window.stationCircle = circle;
    
    // 显示加载中
    document.getElementById("stationList").innerHTML = '<div class="text-gray-500 text-center py-8"><i class="ri-loader-2-line animate-spin text-xl mr-2"></i>正在搜索附近站点...</div>';
    
    // 使用百度地图POI搜索
    const search = new BMap.LocalSearch(window.mapObj, {
        onSearchComplete: function(results) {
            // 处理搜索结果
            processSearchResults(results, point);
        },
        pageCapacity: 50
    });
    
    // 搜索公交站点和地铁站
    search.searchNearby(['公交站', '地铁站'], point, radius);
}

// 处理站点搜索结果
function processSearchResults(results, projectPoint) {
    // 检查结果是否为空
    if (!results || results.getNumPois() === 0) {
        document.getElementById("stationList").innerHTML = '<div class="text-gray-500 text-center py-8">未找到附近站点</div>';
        document.getElementById("stationCount").textContent = "未搜索到站点";
        return;
    }
    
    // 获取所有POI点
    const pois = results.getPois();
    console.log('搜索到的站点:', pois);
    
    // 存储站点数据，包括距离和类型信息
    const stations = pois.map(poi => {
        // 计算距离项目点的直线距离
        const distance = calculateDistance(
            projectPoint.lat, projectPoint.lng,
            poi.point.lat, poi.point.lng
        );
        
        // 判断站点类型 (公交站或地铁站)
        const isSubway = poi.title.includes('地铁') || poi.address.includes('地铁');
        
        return {
            id: poi.uid,
            name: poi.title,
            address: poi.address,
            point: poi.point,
            distance: distance,
            type: isSubway ? '轨道交通站' : '公交站',
            lines: poi.address.split(';') // 简单处理，可能需要更复杂的解析
        };
    });
    
    // 按距离排序
    stations.sort((a, b) => a.distance - b.distance);
    window.stations = stations;
    
    // 添加站点标记到地图
    addStationMarkers(stations);
    
    // 更新站点列表UI
    updateStationsList(stations);
    
    // 分析结果
    analyzeTransportation(stations, projectPoint);
}

// 计算两点间距离（米）
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371000; // 地球半径，单位米
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    return Math.round(distance); // 四舍五入到整数
}

// 添加站点标记到地图
function addStationMarkers(stations) {
    // 清除之前的标记
    window.stationMarkers.forEach(marker => {
        window.mapObj.removeOverlay(marker);
    });
    window.stationMarkers = [];
    
    // 为每个站点添加标记
    stations.forEach(station => {
        // 根据站点类型选择图标
        const icon = new BMap.Icon(
            station.type === '轨道交通站' 
                ? "/api/map_proxy?service_path=images/subway.png" 
                : "/api/map_proxy?service_path=images/bus.png", 
            new BMap.Size(24, 24), 
            { anchor: new BMap.Size(12, 12) }
        );
        
        const marker = new BMap.Marker(station.point, { icon: icon });
        window.mapObj.addOverlay(marker);
        window.stationMarkers.push(marker);
        
        // 添加信息窗口
        const infoWindow = new BMap.InfoWindow(
            `<div style="padding: 8px;">
                <h4 style="margin-top:0;margin-bottom:5px;font-weight:bold;">${station.name}</h4>
                <p style="margin:0;line-height:1.5;">类型: ${station.type}</p>
                <p style="margin:0;line-height:1.5;">距离: ${station.distance}米</p>
                <p style="margin:0;line-height:1.5;">线路: ${station.lines.join(', ')}</p>
            </div>`, 
            { width: 280, title: "站点信息" }
        );
        
        // 点击标记时显示信息窗口
        marker.addEventListener("click", function() {
            this.openInfoWindow(infoWindow);
            
            // 高亮对应的列表项
            highlightStationInList(station.id);
        });
    });
}

// 更新站点列表UI
function updateStationsList(stations) {
    const stationList = document.getElementById("stationList");
    const stationCount = document.getElementById("stationCount");
    
    // 更新站点计数
    stationCount.textContent = `共找到 ${stations.length} 个站点`;
    
    // 清空列表
    stationList.innerHTML = '';
    
    // 添加站点列表项
    stations.forEach(station => {
        const stationItem = document.createElement('div');
        stationItem.className = 'station-item p-3 border-b border-gray-200 hover:bg-blue-50';
        stationItem.dataset.id = station.id;
        stationItem.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0 mt-1">
                    <i class="ri-${station.type === '轨道交通站' ? 'train' : 'bus'}-line text-lg ${station.type === '轨道交通站' ? 'text-red-500' : 'text-blue-500'}"></i>
                </div>
                <div class="ml-3 flex-grow">
                    <h3 class="text-md font-medium text-gray-900">${station.name}</h3>
                    <p class="text-sm text-gray-600">距离: ${station.distance}米</p>
                    <p class="text-sm text-gray-600">类型: ${station.type}</p>
                </div>
                <div class="flex-shrink-0 text-right">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${station.type === '轨道交通站' ? 'red' : 'blue'}-100 text-${station.type === '轨道交通站' ? 'red' : 'blue'}-800">
                        ${station.type === '轨道交通站' ? '地铁' : '公交'}
                    </span>
                </div>
            </div>
        `;
        
        // 点击列表项时，打开对应的信息窗口
        stationItem.addEventListener('click', function() {
            const stationId = this.dataset.id;
            const station = stations.find(s => s.id === stationId);
            if (station) {
                // 居中到站点并打开信息窗口
                window.mapObj.panTo(station.point);
                const marker = window.stationMarkers[stations.indexOf(station)];
                marker.dispatchEvent(new Event('click'));
                
                // 高亮当前列表项
                highlightStationInList(stationId);
            }
        });
        
        stationList.appendChild(stationItem);
    });
}

// 高亮站点列表中的项目
function highlightStationInList(stationId) {
    // 移除所有高亮
    document.querySelectorAll('.station-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // 添加高亮到对应项
    const targetItem = document.querySelector(`.station-item[data-id="${stationId}"]`);
    if (targetItem) {
        targetItem.classList.add('selected');
        // 滚动到可见区域
        targetItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// 分析公共交通情况
function analyzeTransportation(stations, projectPoint) {
    // 如果没有站点，显示提示并返回
    if (!stations || stations.length === 0) {
        document.getElementById("analysisResult").innerHTML = `
            <div class="text-center py-8">
                <div class="mb-4 text-yellow-500">
                    <i class="ri-error-warning-line text-5xl"></i>
                </div>
                <h3 class="text-lg font-semibold text-gray-800 mb-2">未找到公共交通站点</h3>
                <p class="text-gray-600">在搜索范围内未发现公共交通站点，建议扩大搜索范围或更换项目位置</p>
            </div>
        `;
        return;
    }
    
    // 按类型分组
    const busStations = stations.filter(s => s.type === '公交站');
    const subwayStations = stations.filter(s => s.type === '轨道交通站');
    
    // 获取最近的公交站和地铁站
    const nearestBus = busStations.length > 0 ? busStations[0] : null;
    const nearestSubway = subwayStations.length > 0 ? subwayStations[0] : null;
    
    // 符合条件的站点
    const qualifiedBusStations = busStations.filter(s => s.distance <= greenBuildingStandard.publicTransportation.criteria[0].maxDistance);
    const qualifiedSubwayStations = subwayStations.filter(s => s.distance <= greenBuildingStandard.publicTransportation.criteria[1].maxDistance);
    
    // 生成分析结果
    const analysisResults = {
        totalStations: stations.length,
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
        // 评价结果
        evaluation: {
            hasBusWithin500m: qualifiedBusStations.length > 0,
            hasSubwayWithin800m: qualifiedSubwayStations.length > 0,
            // 按照5.2.2条评价，满足其中一项即可得分
            score: qualifiedBusStations.length > 0 ? greenBuildingStandard.publicTransportation.criteria[0].score :
                  (qualifiedSubwayStations.length > 0 ? greenBuildingStandard.publicTransportation.criteria[1].score : 0),
            result: qualifiedBusStations.length > 0 || qualifiedSubwayStations.length > 0 ? '符合' : '不符合'
        }
    };
    
    // 保存分析结果
    window.analysisResults = analysisResults;
    
    // 更新UI
    updateAnalysisUI(analysisResults);
}

// 更新分析结果UI
function updateAnalysisUI(results) {
    if (!results) return;
    
    const analysisResult = document.getElementById("analysisResult");
    const scoreResult = document.getElementById("scoreResult");
    const scoreContent = document.getElementById("scoreContent");
    const exportButton = document.getElementById("exportReport");
    
    // 构建分析结果HTML
    let html = `
        <div class="bg-gray-50 p-4 rounded-lg mb-4">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">公共交通情况统计</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-white p-4 rounded shadow-sm">
                    <h4 class="font-medium text-blue-800 mb-2">公交站 (${results.busStations.total}个)</h4>
                    <div class="text-sm text-gray-700">
                        <p>500米范围内站点数: <span class="font-medium">${results.busStations.qualified}</span></p>
                        ${results.busStations.nearest ? 
                            `<p>最近站点: <span class="font-medium">${results.busStations.nearest.name}</span></p>
                             <p>最近距离: <span class="font-medium">${results.busStations.nearest.distance}米</span></p>` : 
                            '<p class="text-red-500">未找到公交站</p>'}
                    </div>
                </div>
                <div class="bg-white p-4 rounded shadow-sm">
                    <h4 class="font-medium text-red-800 mb-2">地铁站 (${results.subwayStations.total}个)</h4>
                    <div class="text-sm text-gray-700">
                        <p>800米范围内站点数: <span class="font-medium">${results.subwayStations.qualified}</span></p>
                        ${results.subwayStations.nearest ? 
                            `<p>最近站点: <span class="font-medium">${results.subwayStations.nearest.name}</span></p>
                             <p>最近距离: <span class="font-medium">${results.subwayStations.nearest.distance}米</span></p>` : 
                            '<p class="text-red-500">未找到地铁站</p>'}
                    </div>
                </div>
            </div>
        </div>
        
        <div class="bg-${results.evaluation.result === '符合' ? 'green' : 'red'}-50 p-4 rounded-lg border border-${results.evaluation.result === '符合' ? 'green' : 'red'}-200">
            <h3 class="text-lg font-semibold text-${results.evaluation.result === '符合' ? 'green' : 'red'}-800 mb-2">评价结论</h3>
            <div class="text-${results.evaluation.result === '符合' ? 'green' : 'red'}-700">
                <p class="mb-2"><span class="font-medium">绿色建筑标准5.2.2条:</span> ${greenBuildingStandard.publicTransportation.description}</p>
                <p class="mb-1">500米内公交站: ${results.evaluation.hasBusWithin500m ? '✓ 有' : '✗ 无'}</p>
                <p class="mb-1">800米内地铁站: ${results.evaluation.hasSubwayWithin800m ? '✓ 有' : '✗ 无'}</p>
                <p class="font-medium mt-2">结论: ${results.evaluation.result} ${greenBuildingStandard.publicTransportation.description}</p>
            </div>
        </div>
    `;
    
    // 更新分析结果
    analysisResult.innerHTML = html;
    
    // 更新评分结果
    let scoreHtml = `
        <p class="mb-2"><strong>《绿色建筑评价标准》GB/T 50378-2019</strong></p>
        <p class="mb-2"><strong>第5.2.2条:</strong> ${greenBuildingStandard.publicTransportation.description}</p>
        <p class="mb-2">评分: <strong>${results.evaluation.score}</strong> 分</p>
        <p>评价结果: <strong>${results.evaluation.result}</strong></p>
    `;
    scoreContent.innerHTML = scoreHtml;
    scoreResult.classList.remove("hidden");
    
    // 启用导出按钮
    exportButton.disabled = false;
}

// 生成报告
function generateReport() {
    // 检查是否有分析结果
    if (!window.analysisResults || !window.projectData) {
        alert('缺少必要的分析数据，无法生成报告');
        return;
    }
    
    // 显示正在生成报告的提示
    document.getElementById("exportReport").disabled = true;
    document.getElementById("exportReport").innerHTML = '<i class="ri-loader-2-line animate-spin mr-2"></i>正在生成...';
    
    // 准备报告数据
    const reportData = {
        project: window.projectData,
        analysis: window.analysisResults,
        stations: window.stations.slice(0, 10), // 只取前10个站点
        timestamp: new Date().toISOString()
    };
    
    // 发送请求生成报告
    fetch('/api/generate_transport_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // 报告生成成功
        console.log('报告生成成功:', data);
        
        // 重置按钮状态
        document.getElementById("exportReport").disabled = false;
        document.getElementById("exportReport").innerHTML = '<i class="ri-file-word-line mr-2"></i>生成分析报告';
        
        // 如果有下载链接，进行下载
        if (data.downloadUrl) {
            window.open(data.downloadUrl, '_blank');
        }
    })
    .catch(error => {
        console.error('生成报告失败:', error);
        alert('生成报告失败: ' + error.message);
        
        // 重置按钮状态
        document.getElementById("exportReport").disabled = false;
        document.getElementById("exportReport").innerHTML = '<i class="ri-file-word-line mr-2"></i>生成分析报告';
    });
} 