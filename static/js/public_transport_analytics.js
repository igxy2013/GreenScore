            // --- 公共交通分析JS ---
            let currentMapProvider = 'baidu'; // 默认百度
            let baiduMapInstance = null;
            let gaodeMapInstance = null;
            let lastSearchResults = []; // 存储上次搜索结果，用于导出

            // --- 地图API Key ---
            let baiduApiKey = null;
            let gaodeApiKey = null; // 需要从后端获取

            // --- 切换地图提供商 ---
            function switchMapProvider(provider) {
                if (provider === currentMapProvider) return;

                console.log(`切换地图提供商从 ${currentMapProvider} 到 ${provider}`);
                currentMapProvider = provider;
                lastSearchResults = []; // 清空上次结果
                document.getElementById('result-body').innerHTML = '';
                document.getElementById('result-count').innerHTML = '';
                document.getElementById('export-btn').disabled = true;

                // 更新标签页样式
                document.querySelectorAll('.map-tab').forEach(tab => tab.classList.remove('active', 'text-primary', 'border-primary', 'border-b-2'));
                document.querySelectorAll('.map-tab').forEach(tab => tab.classList.add('text-gray-500', 'hover:text-primary'));
                const activeTab = document.getElementById(`${provider}-tab`);
                if (activeTab) {
                    activeTab.classList.add('active', 'text-primary', 'border-primary', 'border-b-2');
                    activeTab.classList.remove('text-gray-500', 'hover:text-primary');
                }

                // 显示/隐藏地图容器
                document.getElementById('baidu-map-container').style.display = provider === 'baidu' ? 'block' : 'none';
                document.getElementById('gaode-map-container').style.display = provider === 'gaode' ? 'block' : 'none';

                // 初始化地图 (如果尚未初始化)
                if (provider === 'baidu' && !baiduMapInstance) {
                    loadBaiduMapScript();
                } else if (provider === 'gaode' && !gaodeMapInstance) {
                    loadGaodeMapScript(); 
                }

                // 清除地图上的覆盖物 (如果地图已初始化)
                if (baiduMapInstance && provider === 'baidu') {
                    baiduMapInstance.clearOverlays();
                }
                if (gaodeMapInstance && provider === 'gaode') {
                    gaodeMapInstance.clearMap();
                }
                
                // 重新绑定搜索按钮事件监听器
                const searchBtn = document.getElementById('search-btn');
                if (searchBtn) {
                    // 移除所有现有的事件监听器
                    const newSearchBtn = searchBtn.cloneNode(true);
                    searchBtn.parentNode.replaceChild(newSearchBtn, searchBtn);
                    
                    // 添加新的事件监听器
                    newSearchBtn.addEventListener('click', searchAddress);
                }
                
                // 重新绑定地址输入框回车事件
                const addressInput = document.getElementById('address');
                if (addressInput) {
                    // 移除所有现有的事件监听器
                    const newAddressInput = addressInput.cloneNode(true);
                    addressInput.parentNode.replaceChild(newAddressInput, addressInput);
                    
                    // 添加新的事件监听器
                    newAddressInput.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            searchAddress();
                        }
                    });
                }
                
                // 保存用户选择到localStorage
                localStorage.setItem('preferred_map_provider', provider);
            }

            // --- 加载百度地图API (已有) ---
            function loadBaiduMapScript() {
                console.log("开始加载百度地图API");
                
                // 检查BMap对象是否已存在
                if (typeof BMap !== 'undefined') {
                    console.log("BMap对象已存在，直接初始化地图");
                    setTimeout(() => {
                        try {
                            initBaiduMap();
                        } catch (e) {
                            console.error("延迟初始化百度地图失败:", e);
                        }
                    }, 500); // 添加延迟，确保BMap完全加载
                    return;
                }

                // 添加全局错误处理，捕获"Cannot read properties of undefined (reading 'hc')"错误
                window.onerror = function(message, source, lineno, colno, error) {
                    console.error("全局错误:", message, "来源:", source, "行号:", lineno);
                    if (message.includes("Cannot read properties of undefined") && message.includes("hc")) {
                        console.error("捕获到百度地图初始化错误，尝试重新加载");
                        setTimeout(() => {
                            loadBaiduMapScript();
                        }, 1000);
                        return true; // 阻止默认错误处理
                    }
                    return false; // 允许其他错误正常处理
                };

                // 获取API密钥
                fetch('/api/map_api_key')
                    .then(response => {
            if (!response.ok) {
                    // 如果后端代理返回错误，尝试读取错误信息
                return response.json().then(err => {
                    throw new Error(err.error || `后端代理错误: ${response.status}`)
                }).catch(() => {
                    // 如果无法解析 JSON 错误信息，抛出通用错误
                    throw new Error(`后端代理请求失败: ${response.status}`)
                });
            }
            return response.json(); // 假设API返回JSON而不是Blob
        })
        .then(data => {
            if (!data || !data.api_key) {
                throw new Error("API返回中没有百度地图密钥");
            }
            
            // 获取到API密钥后，加载百度地图脚本
            baiduApiKey = data.api_key;
            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = `https://api.map.baidu.com/api?v=3.0&ak=${baiduApiKey}&callback=initBaiduMap`;
            script.onerror = function() {
                console.error("直接加载百度地图API失败，尝试使用代理");
                // 使用后端代理
                const proxyScript = document.createElement('script');
                proxyScript.type = 'text/javascript';
                proxyScript.src = `/api/map_js_api?v=3.0&callback=initBaiduMap`;
                document.body.appendChild(proxyScript);
            };
            document.body.appendChild(script);
        })
        .catch(error => {
            console.error('获取API密钥或加载地图脚本失败:', error);
            const mapContainer = document.getElementById('baidu-map-container');
            if (mapContainer) {
                mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图加载失败: ${error.message}</div>`;
            }
        });
    }
    
    // --- 加载高德地图API ---
    function loadGaodeMapScript() {
        console.log("开始加载高德地图API");
        
        // 检查AMap对象是否已存在
        if (typeof AMap !== 'undefined') {
            console.log("AMap对象已存在，直接初始化地图");
            setTimeout(() => {
                try {
                    initGaodeMap();
                } catch (e) {
                    console.error("延迟初始化高德地图失败:", e);
                }
            }, 500); // 添加延迟，确保AMap完全加载
            return;
        }
        
        // 获取高德地图API密钥
        fetch('/api/gaode_map_api_key')
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || `后端代理错误: ${response.status}`);
                    }).catch(() => {
                        throw new Error(`后端代理请求失败: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.api_key) {
                    throw new Error("API返回中没有高德地图密钥");
                }
                
                // 获取到API密钥后，加载高德地图脚本
                gaodeApiKey = data.api_key;
                
                // 创建script标签
                const script = document.createElement('script');
                script.type = 'text/javascript';
                script.src = `https://webapi.amap.com/maps?v=2.0&key=${gaodeApiKey}&callback=initGaodeMap`;
                script.onerror = function() {
                    console.error("加载高德地图API失败");
                    const mapContainer = document.getElementById('gaode-map-container');
                    if (mapContainer) {
                        mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">高德地图API加载失败</div>`;
                    }
                };
                document.body.appendChild(script);
                
                // 如有安全码，也添加
                if (data.security_js_code) {
                    const secScript = document.createElement('script');
                    secScript.type = 'text/javascript';
                    secScript.text = data.security_js_code;
                    document.head.appendChild(secScript);
                }
            })
            .catch(error => {
                console.error('获取高德地图API密钥或加载脚本失败:', error);
                const mapContainer = document.getElementById('gaode-map-container');
                if (mapContainer) {
                    mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">高德地图加载失败: ${error.message}</div>`;
                }
            });
    }
    
    // 初始化高德地图函数
    function initGaodeMap() {
        try {
            console.log("正在初始化高德地图...");
            // 确保地图容器存在
            const mapContainer = document.getElementById('gaode-map-container');
            if (!mapContainer) {
                throw new Error("高德地图容器不存在");
            }
            
            // 创建地图实例
            const map = new AMap.Map('gaode-map-container', {
                zoom: 15,  // 与百度地图保持一致
                center: [104.065735, 30.659462], // 成都中心点
                viewMode: '2D'
            });
            
            // 保存到全局变量
            gaodeMapInstance = map;
            
            // 添加地图控件 - 使用新版本的控件创建方式
            AMap.plugin(['AMap.Scale', 'AMap.ToolBar'], function(){
                // 添加比例尺
                const scale = new AMap.Scale();
                map.addControl(scale);
                
                // 添加工具条
                const toolBar = new AMap.ToolBar();
                map.addControl(toolBar);
            });
            
            // 确保地图容器可见
            mapContainer.style.display = "block";
            
            console.log("高德地图初始化成功");
        } catch (error) {
            console.error("初始化高德地图失败:", error);
            const mapContainer = document.getElementById('gaode-map-container');
            if (mapContainer) {
                mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">高德地图初始化失败: ${error.message}</div>`;
                mapContainer.style.display = "block"; // 确保错误信息可见
            }
        }
    }
    
    // 初始化百度地图函数
    function initBaiduMap() {
        try {
            console.log("正在初始化百度地图...");
            // 确保地图容器存在
            const mapContainer = document.getElementById('baidu-map-container');
            if (!mapContainer) {
                throw new Error("地图容器不存在");
            }
            
            // 创建地图实例
            const map = new BMap.Map('baidu-map-container');
            // 保存到全局变量
            baiduMapInstance = map;
            window.map = map; // 为了兼容现有代码
            
            // 初始中心点 (成都)
            const point = new BMap.Point(104.065735, 30.659462);
            map.centerAndZoom(point, 17);
            
            // 创建标记并添加到地图中
            const marker = new BMap.Marker(point);
            map.addOverlay(marker);
            
            // 禁用滚轮缩放
            map.disableScrollWheelZoom();
            
            // 添加地图控件
            map.addControl(new BMap.NavigationControl());
            map.addControl(new BMap.ScaleControl());
            
            // 为搜索按钮添加事件监听器
            const searchBtn = document.getElementById('search-btn');
            if (searchBtn) {
                searchBtn.addEventListener('click', searchAddress);
            }
            
            // 监听地址输入框回车事件
            const addressInput = document.getElementById('address');
            if (addressInput) {
                addressInput.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        searchAddress();
                    }
                });
            }
            
            console.log("百度地图初始化成功");
            
            // 确保地图容器可见
            mapContainer.style.display = "block";
        } catch (error) {
            console.error("初始化百度地图失败:", error);
            const mapContainer = document.getElementById('baidu-map-container');
            if (mapContainer) {
                mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图初始化失败: ${error.message}</div>`;
                mapContainer.style.display = "block"; // 确保错误信息可见
            }
        }
    }
    
    // 搜索地址函数
    function searchAddress() {
        const address = document.getElementById('address').value.trim();
        if (!address) {
            alert("请输入地址");
            return;
        }
        
        console.log("搜索地址:", address);
        // 显示加载状态
        document.getElementById('loading').style.display = 'block';
        
        if (currentMapProvider === 'baidu') {
            searchBaiduMap(address);
        } else if (currentMapProvider === 'gaode') {
            // 高德地图搜索逻辑
            searchGaodeMap(address);
        }
    }
    
    // 搜索百度地图
    function searchBaiduMap(address) {
        if (!baiduMapInstance) {
            alert("地图未初始化，请刷新页面重试");
            document.getElementById('loading').style.display = 'none';
            return;
        }
        
        try {
            // 创建地址解析器实例
            const myGeo = new BMap.Geocoder();
            
            // 将地址解析结果显示在地图上，并调整地图视野
            myGeo.getPoint(address, function(point) {
                if (point) {
                    baiduMapInstance.clearOverlays();
                    baiduMapInstance.centerAndZoom(point, 15);
                    const marker = new BMap.Marker(point);
                    baiduMapInstance.addOverlay(marker);
                    
                    // 显示500米半径圆圈
                    const circle = new BMap.Circle(point, 500, {
                        strokeColor: "red",
                        strokeWeight: 2,
                        strokeOpacity: 0.8,
                        fillColor: "red",
                        fillOpacity: 0.1
                    });
                    baiduMapInstance.addOverlay(circle);
                    
                    // 存储圆圈信息用于后续导出
                    window.circleInfo = {
                        center: {
                            lng: point.lng,
                            lat: point.lat
                        },
                        radius: 500
                    };
                    
                    // 存储中心点和缩放级别
                    window.center = {
                        lng: point.lng,
                        lat: point.lat
                    };
                    window.zoom = 15;
                    window.address = address;
                    
                    // 搜索周边公交站
                    searchNearbyTransit(point);
                } else {
                    alert("未找到该地址");
                    document.getElementById('loading').style.display = 'none';
                }
            }, address);
        } catch (error) {
            console.error("搜索地址失败:", error);
            document.getElementById('loading').style.display = 'none';
            alert("搜索地址时出错: " + error.message);
        }
    }
    
    // 搜索周边公交站
    function searchNearbyTransit(point) {
        try {
            // 清空原有覆盖物
            baiduMapInstance.clearOverlays();
            
            // 添加中心点标记
            const marker = new BMap.Marker(point);
            baiduMapInstance.addOverlay(marker);
            
            // 显示800米半径圆圈
            const circle = new BMap.Circle(point, 800, {
                strokeColor: "red",
                strokeWeight: 2,
                strokeOpacity: 0.8,
                fillColor: "red",
                fillOpacity: 0.1
            });
            baiduMapInstance.addOverlay(circle);
            
            // 存储圆圈信息用于后续导出
            window.circleInfo = {
                center: {
                    lng: point.lng,
                    lat: point.lat
                },
                radius: 800
            };
            
            // 创建周边搜索实例
            const local = new BMap.LocalSearch(baiduMapInstance, {
                renderOptions: { 
                    map: baiduMapInstance, 
                    autoViewport: false,
                    selectFirstResult: false
                },
                pageCapacity: 100,
                onSearchComplete: function(results) {
                    document.getElementById('loading').style.display = 'none';
                    
                    if (!results || results.getNumPois() === 0) {
                        document.getElementById('result-count').textContent = '未找到周边公交站点，正在尝试搜索地铁站...';
                        // 继续搜索地铁站
                        searchSubwayStations(point);
                        return;
                    }
                    
                    // 处理搜索结果
                    processSearchResults(results, point, "公交站");
                    
                    // 继续搜索地铁站
                    searchSubwayStations(point);
                },
                onError: function(error) {
                    document.getElementById('loading').style.display = 'none';
                    console.error("搜索周边公交站点失败:", error);
                    alert("搜索周边公交站点失败，请重试");
                }
            });
            
            // 搜索周边800米内的公交站
            local.searchNearby('公交站', point, 800);
        } catch (error) {
            console.error("搜索周边公交站失败:", error);
            document.getElementById('loading').style.display = 'none';
            alert("搜索周边公交站时出错: " + error.message);
        }
    }
    
    // 搜索地铁站
    function searchSubwayStations(point) {
        try {
            const local = new BMap.LocalSearch(baiduMapInstance, {
                renderOptions: { 
                    map: baiduMapInstance, 
                    autoViewport: false,
                    selectFirstResult: false
                },
                pageCapacity: 50,
                onSearchComplete: function(results) {
                    if (!results || results.getNumPois() === 0) {
                        const resultCount = document.getElementById('result-count');
                        const currentText = resultCount.textContent || '';
                        
                        if (currentText.includes('未找到周边公交站点')) {
                            resultCount.textContent = '未找到周边800米内的公交站和地铁站，请尝试其他地点';
                        } else {
                            // 如果已经找到了公交站，但没有地铁站
                            // 不需要更新文本
                        }
                        return;
                    }
                    
                    // 处理搜索结果，合并到现有结果
                    processSearchResults(results, point, "地铁站", true);
                },
                onError: function(error) {
                    console.error("搜索周边地铁站点失败:", error);
                }
            });
            
            // 搜索周边800米内的地铁站
            local.searchNearby('地铁站', point, 800);
        } catch (error) {
            console.error("搜索周边地铁站失败:", error);
        }
    }
    
    // 处理搜索结果
    function processSearchResults(results, centerPoint, stationType = "公交站", appendResults = false) {
        try {
            // 初始化结果数组（如果需要附加结果，则不初始化）
            if (!appendResults) {
                window.stations = [];
                window.markers = [];
                
                // 添加中心点标记
                window.markers.push({
                    lng: centerPoint.lng,
                    lat: centerPoint.lat,
                    isCenter: true
                });
                
                // 清空结果表格
                const resultBody = document.getElementById('result-body');
                resultBody.innerHTML = '';
            }
            
            // 获取所有POI点，兼容不同格式的搜索结果
            let pois = [];
            if (results.getPois && typeof results.getPois === 'function') {
                // 直接使用 getPois 方法
                pois = results.getPois();
            } else if (results.Ar && Array.isArray(results.Ar)) {
                // 某些版本的百度地图API使用 Ar 数组
                pois = results.Ar;
            } else if (results.Ir && Array.isArray(results.Ir)) {
                // 某些版本使用 Ir 数组
                pois = results.Ir;
            } else if (results instanceof Array) {
                // 结果本身是数组
                pois = results;
            } else if (results.Ha && Array.isArray(results.Ha)) {
                // 查找可能的其他属性名
                pois = results.Ha;
            } else if (Array.isArray(results._pois)) {
                // 查找可能的其他属性名
                pois = results._pois;
            } else {
                // 遍历所有属性，查找可能的POI数组
                for (let key in results) {
                    if (Array.isArray(results[key]) && results[key].length > 0 && results[key][0].title) {
                        pois = results[key];
                        break;
                    }
                }
                
                if (pois.length === 0) {
                    console.error("无法识别的搜索结果格式:", results);
                    throw new Error("无法解析搜索结果，不支持的格式");
                }
            }
            
            // 如果没有找到结果
            if (pois.length === 0) {
                const resultCount = document.getElementById('result-count');
                if (!appendResults) {
                    resultCount.textContent = `未找到800米内的${stationType}`;
                }
                return;
            }
            
            // 获取现有结果数量作为索引起点
            const startIndex = window.stations ? window.stations.length : 0;
            
            // 更新结果计数
            const resultCount = document.getElementById('result-count');
            if (!appendResults) {
                resultCount.textContent = `共找到 ${pois.length} 个${stationType}`;
            } else {
                // 附加新结果数量
                const currentCount = parseInt(resultCount.textContent.match(/\d+/) || [0])[0];
                resultCount.textContent = `共找到 ${currentCount + pois.length} 个交通站点 (包括 ${startIndex} 个公交站和 ${pois.length} 个地铁站)`;
            }
            
            // 处理每个POI
            pois.forEach((poi, index) => {
                // 获取坐标点
                let poiPoint;
                if (poi.point) {
                    poiPoint = poi.point;
                } else if (poi.location) {
                    poiPoint = poi.location;
                } else if (poi.latLng) {
                    poiPoint = new BMap.Point(poi.latLng.lng, poi.latLng.lat);
                } else if (poi.lng && poi.lat) {
                    poiPoint = new BMap.Point(poi.lng, poi.lat);
                } else {
                    console.warn("无法获取POI坐标:", poi);
                    return; // 跳过这个POI
                }
                
                // 计算与中心点的距离
                const distance = baiduMapInstance.getDistance(
                    new BMap.Point(centerPoint.lng, centerPoint.lat),
                    poiPoint
                ).toFixed(0);
                
                // 获取POI名称
                const title = poi.title || poi.name || poi.address || "未知站点";
                
                // 获取详细信息
                const details = poi.address || poi.addressDetail || poi.province + poi.city || "无详细信息";
                
                // 创建表格行
                const row = document.createElement('tr');
                
                // 添加单元格
                row.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${startIndex + index + 1}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${title}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${stationType}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${distance}</td>
                    <td class="px-4 py-2 text-sm text-gray-900">${details}</td>
                `;
                
                // 添加行到表格
                const resultBody = document.getElementById('result-body');
                resultBody.appendChild(row);
                
                // 添加到站点数组
                window.stations.push({
                    index: startIndex + index + 1,
                    name: title,
                    type: stationType,
                    distance: distance,
                    detail: details,
                    location: {
                        lng: poiPoint.lng,
                        lat: poiPoint.lat
                    }
                });
                
                // 添加到标记数组
                window.markers.push({
                    lng: poiPoint.lng,
                    lat: poiPoint.lat,
                    stationIndex: startIndex + index + 1,
                    stationType: stationType
                });
                
                // 选择图标颜色（公交站红色，地铁站蓝色）
                const iconColor = stationType === "地铁站" ? "blue" : "red";
                
                // 在地图上添加标记
                const marker = new BMap.Marker(
                    poiPoint,
                    {
                        icon: new BMap.Symbol(BMap_Symbol_SHAPE_POINT, {
                            scale: 1,
                            fillColor: iconColor,
                            fillOpacity: 0.8
                        })
                    }
                );
                
                // 添加标记标签
                const label = new BMap.Label(startIndex + index + 1, {
                    offset: new BMap.Size(0, 0),
                    position: poiPoint
                });
                label.setStyle({
                    color: 'white',
                    backgroundColor: 'transparent',
                    border: 'none',
                    fontSize: '12px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    zIndex: 999
                });
                marker.setLabel(label);
                
                baiduMapInstance.addOverlay(marker);
            });
            
            // 启用导出按钮
            document.getElementById('export-btn').disabled = false;
            
            // 添加导出按钮点击事件
            document.getElementById('export-btn').onclick = executeMapScreenshot;
            
            // 如果搜索的是地铁站（意味着搜索已经完成），则生成结论
            if (stationType === "地铁站" || (window.stations && window.stations.length > 0)) {
                // 生成结论，会自动更新结论预览
                generateConclusion();
            }
            
        } catch (error) {
            console.error("处理搜索结果失败:", error);
            console.log("搜索结果对象:", results);
            alert("处理搜索结果时出错: " + error.message);
        }
    }
    
    // 修改搜索周边公交站和地铁站的函数，增加更好的错误处理
    function searchNearbyTransit(point) {
        try {
            // 清空原有覆盖物
            baiduMapInstance.clearOverlays();
            
            // 添加中心点标记
            const marker = new BMap.Marker(point);
            baiduMapInstance.addOverlay(marker);
            
            // 显示800米半径圆圈
            const circle = new BMap.Circle(point, 800, {
                strokeColor: "red",
                strokeWeight: 2,
                strokeOpacity: 0.8,
                fillColor: "red",
                fillOpacity: 0.1
            });
            baiduMapInstance.addOverlay(circle);
            
            // 存储圆圈信息用于后续导出
            window.circleInfo = {
                center: {
                    lng: point.lng,
                    lat: point.lat
                },
                radius: 800
            };
            
            // 创建周边搜索实例
            const local = new BMap.LocalSearch(baiduMapInstance, {
                renderOptions: { 
                    map: baiduMapInstance, 
                    autoViewport: false,
                    selectFirstResult: false
                },
                pageCapacity: 100,
                onSearchComplete: function(results) {
                    document.getElementById('loading').style.display = 'none';
                    
                    // 检查搜索结果有效性
                    if (!results || typeof results !== 'object' || 
                        (typeof results.getNumPois === 'function' && results.getNumPois() === 0)) {
                        document.getElementById('result-count').textContent = '未找到周边公交站点，正在尝试搜索地铁站...';
                        // 继续搜索地铁站
                        searchSubwayStations(point);
                        return;
                    }
                    
                    // 处理搜索结果
                    processSearchResults(results, point, "公交站");
                    
                    // 继续搜索地铁站
                    searchSubwayStations(point);
                },
                onError: function(error) {
                    document.getElementById('loading').style.display = 'none';
                    console.error("搜索周边公交站点失败:", error);
                    // 尝试继续搜索地铁站，不要立即警告用户
                    searchSubwayStations(point);
                }
            });
            
            // 搜索周边800米内的公交站
            local.searchNearby('公交站', point, 800);
        } catch (error) {
            console.error("搜索周边公交站失败:", error);
            document.getElementById('loading').style.display = 'none';
            alert("搜索周边公交站时出错: " + error.message);
        }
    }
    
    // 修改搜索地铁站函数，增加更好的错误处理
    function searchSubwayStations(point) {
        try {
            const local = new BMap.LocalSearch(baiduMapInstance, {
                renderOptions: { 
                    map: baiduMapInstance, 
                    autoViewport: false,
                    selectFirstResult: false
                },
                pageCapacity: 50,
                onSearchComplete: function(results) {
                    // 检查搜索结果的有效性
                    if (!results || typeof results !== 'object' || 
                        (typeof results.getNumPois === 'function' && results.getNumPois() === 0)) {
                        const resultCount = document.getElementById('result-count');
                        const currentText = resultCount.textContent || '';
                        
                        if (currentText.includes('未找到周边公交站点')) {
                            resultCount.textContent = '未找到周边800米内的公交站和地铁站，请尝试其他地点';
                        } else {
                            // 如果已经找到了公交站，但没有地铁站，保持原文本
                        }
                        return;
                    }
                    
                    // 处理搜索结果，合并到现有结果
                    processSearchResults(results, point, "地铁站", true);
                },
                onError: function(error) {
                    console.error("搜索周边地铁站点失败:", error);
                    // 仅记录错误，不需要提示用户
                }
            });
            
            // 搜索周边800米内的地铁站
            local.searchNearby('地铁站', point, 800);
        } catch (error) {
            console.error("搜索周边地铁站失败:", error);
            // 仅记录错误，不需要提示用户
        }
    }

    // 创建地图截图函数
    function createMapScreenshot() {
        return new Promise((resolve, reject) => {
            try {
                console.log("开始创建地图截图");
                // 获取当前使用的地图容器
                const mapContainerId = currentMapProvider === 'baidu' ? 'baidu-map-container' : 'gaode-map-container';
                const mapContainer = document.getElementById(mapContainerId);
                
                if (!mapContainer) {
                    throw new Error(`地图容器 ${mapContainerId} 不存在`);
                }
                
                // 使用html2canvas对地图容器进行截图
                html2canvas(mapContainer, {
                    useCORS: true,
                    allowTaint: true,
                    logging: false,
                    scale: 1,
                    backgroundColor: "#ffffff"
                }).then(canvas => {
                    console.log("地图截图成功");
                    // 转换为图片数据URL
                    const imgData = canvas.toDataURL('image/png');
                    resolve(imgData);
                }).catch(error => {
                    console.error("html2canvas截图失败:", error);
                    // 截图失败时创建备用的截图
                    const fallbackCanvas = document.createElement('canvas');
                    const width = 800;
                    const height = 600;
                    fallbackCanvas.width = width;
                    fallbackCanvas.height = height;
                    const ctx = fallbackCanvas.getContext('2d');
                    
                    // 绘制背景
                    ctx.fillStyle = '#F5F5F5';
                    ctx.fillRect(0, 0, width, height);
                    
                    // 绘制地址文本
                    ctx.fillStyle = '#333333';
                    ctx.font = 'bold 16px Microsoft YaHei, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText(`地址: ${window.address || '未指定地址'}`, width/2, height/3);
                    
                    // 绘制圆圈表示搜索范围
                    ctx.strokeStyle = 'red';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(width/2, height/2, 100, 0, 2 * Math.PI);
                    ctx.stroke();
                    
                    // 绘制中心点
                    ctx.fillStyle = 'red';
                    ctx.beginPath();
                    ctx.arc(width/2, height/2, 5, 0, 2 * Math.PI);
                    ctx.fill();
                    
                    // 在底部添加说明
                    ctx.fillStyle = '#666666';
                    ctx.font = '14px Microsoft YaHei, sans-serif';
                    ctx.fillText('注: 截图生成失败，此为示例图。', width/2, height*2/3);
                    
                    // 添加站点数量说明
                    if (window.stations && window.stations.length) {
                        ctx.fillText(`周边800米内共找到 ${window.stations.length} 个公共交通站点`, width/2, height*2/3 + 24);
                    }
                    
                    // 返回备用图片数据
                    resolve(fallbackCanvas.toDataURL('image/png'));
                });
            } catch (error) {
                console.error("创建地图截图失败:", error);
                reject(error);
            }
        });
    }

    // 执行地图截图
    function executeMapScreenshot() {
        // 显示加载状态
        document.getElementById('loading').style.display = 'block';
        
        // 生成结论
        const conclusion = generateConclusion();
        
        createMapScreenshot().then(mapImageData => {
            // 检查图片数据是否有效
            if (!mapImageData || mapImageData.length < 1000) {
                console.error("生成的地图截图数据无效或过小");
                throw new Error("地图截图生成失败");
            }
            
            console.log("地图截图数据生成完成，准备发送到后端");
            
            // 准备要发送的数据
            const requestData = {
                address: window.address,
                stations: window.stations || [],
                mapImage: mapImageData,
                mapInfo: {
                    center: window.center || { lng: 0, lat: 0 },
                    zoom: window.zoom || 15,
                    markers: window.markers || [],
                    circle: window.circleInfo || { radius: 800 }
                },
                // 添加项目ID参数，从URL获取
                project_id: new URLSearchParams(window.location.search).get('project_id'),
                // 添加评分结论
                conclusion: conclusion
            };
            
            // 确保所有站点都有详细信息字段
            if (requestData.stations && requestData.stations.length > 0) {
                console.log("处理站点详细信息字段...");
                requestData.stations = requestData.stations.map((station, index) => {
                    // 记录原始站点数据
                    console.log(`原始站点数据 ${index + 1}:`, JSON.stringify(station));
                    
                    // 确保所有重要字段都存在
                    const normalizedStation = {
                        index: station.index || (index + 1),
                        name: station.name || '未知站点',
                        type: station.type || '公交站',
                        distance: station.distance || '0',
                        // 优先使用detail字段，如果没有则使用其他可能的字段
                        detail: station.detail || 
                               station.address || 
                               station.addressDetail || 
                               station.description || 
                               station.info || 
                               '无详细信息',
                        location: station.location || { lng: 0, lat: 0 }
                    };
                    
                    // 记录标准化后的站点数据
                    console.log(`标准化后的站点数据 ${index + 1}:`, JSON.stringify(normalizedStation));
                    
                    return normalizedStation;
                });
                
                console.log(`处理后的站点数据: 共${requestData.stations.length}个站点`);
                if (requestData.stations.length > 0) {
                    console.log(`第一个站点完整数据:`, JSON.stringify(requestData.stations[0]));
                    console.log(`字段检查 - name: ${requestData.stations[0].name}, type: ${requestData.stations[0].type}, distance: ${requestData.stations[0].distance}, detail: ${requestData.stations[0].detail}`);
                }
            }
            
            console.log("开始发送数据到后端生成报告");
            
            // 发送数据到后端
            fetch('/api/fill_transport_report_template', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                if (!response.ok) {
                    console.error(`服务器响应错误: ${response.status} ${response.statusText}`);
                    throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // 隐藏加载中
                document.getElementById('loading').style.display = 'none';
                
                if (data.success) {
                    console.log('成功收到报告生成响应:', data);
                    
                    // 创建下载链接 - 确保使用正确的属性名称
                    const link = document.createElement('a');
                    // 检查两种可能的属性名
                    const downloadUrl = data.download_url || data.downloadUrl;
                    
                    if (!downloadUrl) {
                        console.error('响应中缺少下载链接:', data);
                        alert('生成报告失败: 服务器未返回下载链接');
                        return;
                    }
                    
                    // 显示成功消息
                    alert('公共交通分析报告生成成功，即将开始下载');
                    
                    // 设置下载文件名
                    const fileName = `公共交通查询结果_${window.address || '地址'}_${new Date().toLocaleDateString().replace(/\//g, '-')}.docx`;
                    link.href = downloadUrl;
                    link.download = fileName;
                    
                    // 触发下载
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                } else {
                    console.error('生成报告失败:', data.message);
                    alert('生成报告失败: ' + (data.message || '未知错误'));
                }
            })
            .catch(error => {
                // 隐藏加载中
                document.getElementById('loading').style.display = 'none';
                console.error('API请求失败:', error);
                alert('导出失败: ' + error.message);
            });
        }).catch(error => {
            // 隐藏加载中
            document.getElementById('loading').style.display = 'none';
            console.error('地图截图创建失败:', error);
            alert('地图截图创建失败: ' + error.message);
        });
    }

    // 加载百度地图API
    loadBaiduMapScript();

    // 全局函数，供百度地图API回调
    window.initBaiduMap = initBaiduMap;
    
    // 根据规范生成结论
    function generateConclusion() {
        // 初始化结论对象
        const conclusion = {
            score6_1_2: "不符合", // 6.1.2条规范结论
            score6_2_1_1: 0,      // 6.2.1条第1点得分
            score6_2_1_2: 0,      // 6.2.1条第2点得分
            totalScore: 0,        // 6.2.1条总得分
            distanceText: "",     // 距离描述
            routesText: "",       // 线路描述
            closestBusDistance: 9999, // 最近公交站距离
            closestMetroDistance: 9999, // 最近地铁站距离
            busStationCount: 0,   // 公交站数量
            metroStationCount: 0, // 地铁站数量
            busLines: new Set(),  // 公交线路集合
            metroLines: new Set() // 地铁线路集合
        };
        
        // 检查是否有站点数据
        if (!window.stations || window.stations.length === 0) {
            return {
                result6_1_2: "不符合规范6.1.2要求，场地人行出入口500m内未检测到公共交通站点。",
                result6_2_1: "不符合规范6.2.1要求，场地周边未检测到公共交通站点，总得分为0分。",
                totalScore: 0
            };
        }
        
        // 遍历所有站点，找出最近的公交站和地铁站
        window.stations.forEach(station => {
            const distance = parseInt(station.distance, 10);
            
            // 统计不同类型站点
            if (station.type === "公交站") {
                conclusion.busStationCount++;
                if (distance < conclusion.closestBusDistance) {
                    conclusion.closestBusDistance = distance;
                }
                
                // 暂时将公交站名作为线路添加
                conclusion.busLines.add(station.name);
            } else if (station.type === "地铁站") {
                conclusion.metroStationCount++;
                if (distance < conclusion.closestMetroDistance) {
                    conclusion.closestMetroDistance = distance;
                }
                
                // 暂时将地铁站名作为线路添加
                conclusion.metroLines.add(station.name);
            }
        });
        
        // 评价6.1.2：场地人行出入口500m内是否有公共交通站点
        if (conclusion.closestBusDistance <= 500 || conclusion.closestMetroDistance <= 500) {
            conclusion.score6_1_2 = "符合";
        }
        
        // 评价6.2.1第1点
        if (conclusion.closestBusDistance <= 300 || conclusion.closestMetroDistance <= 500) {
            conclusion.score6_2_1_1 = 4;
        } else if (conclusion.closestBusDistance <= 500 || conclusion.closestMetroDistance <= 800) {
            conclusion.score6_2_1_1 = 2;
        }
        
        // 评价6.2.1第2点
        // 统计800m范围内的公交线路数，简单起见，我们假设每个站点代表一条不同线路
        const totalLines = conclusion.busLines.size + conclusion.metroLines.size;
        if (totalLines >= 2) {
            conclusion.score6_2_1_2 = 4;
        }
        
        // 计算总分
        conclusion.totalScore = conclusion.score6_2_1_1 + conclusion.score6_2_1_2;
        
        // 生成距离描述文本
        if (conclusion.closestBusDistance < 9999) {
            conclusion.distanceText += `最近公交站距离为${conclusion.closestBusDistance}m`;
        }
        if (conclusion.closestMetroDistance < 9999) {
            if (conclusion.distanceText) conclusion.distanceText += "，";
            conclusion.distanceText += `最近地铁站距离为${conclusion.closestMetroDistance}m`;
        }
        
        // 生成线路描述文本
        const busStationList = Array.from(conclusion.busLines).slice(0, 3).join("、");
        const metroStationList = Array.from(conclusion.metroLines).slice(0, 3).join("、");
        
        if (conclusion.busStationCount > 0) {
            conclusion.routesText += `周边800m内有${conclusion.busStationCount}个公交站`;
            if (busStationList) {
                conclusion.routesText += `（包括${busStationList}${conclusion.busLines.size > 3 ? "等" : ""}）`;
            }
        }
        
        if (conclusion.metroStationCount > 0) {
            if (conclusion.routesText) conclusion.routesText += "，";
            conclusion.routesText += `有${conclusion.metroStationCount}个地铁站`;
            if (metroStationList) {
                conclusion.routesText += `（包括${metroStationList}${conclusion.metroLines.size > 3 ? "等" : ""}）`;
            }
        }
        
        // 合成最终结论
        const result = {
            result6_1_2: `${conclusion.score6_1_2}规范6.1.2要求。${conclusion.distanceText}。`,
            result6_2_1: `按照规范6.2.1评分，总得分为${conclusion.totalScore}分，其中：
- ${conclusion.distanceText}，得${conclusion.score6_2_1_1}分；
- ${conclusion.routesText}，总计${totalLines}条线路，得${conclusion.score6_2_1_2}分。`,
            totalScore: conclusion.totalScore
        };
        
        // 更新结论预览
        updateConclusionPreview(result);
        
        return result;
    }
    
    // 更新结论预览区域
    function updateConclusionPreview(conclusion) {
        // 获取结论预览区域元素
        const previewContainer = document.getElementById('conclusion-preview');
        const conclusion612 = document.getElementById('conclusion-6-1-2');
        const conclusion621 = document.getElementById('conclusion-6-2-1');
        const totalScore = document.getElementById('conclusion-total-score');
        const statusIndicator612 = document.getElementById('status-indicator-6-1-2');
        const statusIndicator621 = document.getElementById('status-indicator-6-2-1');
        
        // 更新内容
        conclusion612.textContent = conclusion.result6_1_2;
        conclusion621.textContent = conclusion.result6_2_1;
        totalScore.textContent = conclusion.totalScore + ' 分';
        
        // 设置6.1.2规范状态指示器颜色
        if (conclusion.result6_1_2.includes('符合')) {
            statusIndicator612.classList.add('bg-green-500');
            statusIndicator612.classList.remove('bg-red-500');
        } else {
            statusIndicator612.classList.add('bg-red-500');
            statusIndicator612.classList.remove('bg-green-500');
        }
        
        // 设置6.2.1规范状态指示器颜色
        if (conclusion.totalScore >= 4) {
            statusIndicator621.classList.add('bg-green-500');
            statusIndicator621.classList.remove('bg-yellow-500', 'bg-red-500');
        } else if (conclusion.totalScore >= 2) {
            statusIndicator621.classList.add('bg-yellow-500');
            statusIndicator621.classList.remove('bg-green-500', 'bg-red-500');
        } else {
            statusIndicator621.classList.add('bg-red-500');
            statusIndicator621.classList.remove('bg-green-500', 'bg-yellow-500');
        }
        
        // 设置总分颜色
        if (conclusion.totalScore >= 6) {
            totalScore.classList.add('text-green-600');
            totalScore.classList.remove('text-yellow-600', 'text-red-600');
        } else if (conclusion.totalScore >= 2) {
            totalScore.classList.add('text-yellow-600');
            totalScore.classList.remove('text-green-600', 'text-red-600');
        } else {
            totalScore.classList.add('text-red-600');
            totalScore.classList.remove('text-green-600', 'text-yellow-600');
        }
        
        // 显示预览区域
        previewContainer.classList.remove('hidden');
    }
    
    // 页面加载时，恢复用户上次选择的地图提供商
    document.addEventListener('DOMContentLoaded', function() {
        // 从localStorage获取上次选择的地图提供商
        const preferredMapProvider = localStorage.getItem('preferred_map_provider');
        
        // 如果有保存的选择且不是当前的地图提供商，则切换
        if (preferredMapProvider && preferredMapProvider !== currentMapProvider) {
            console.log('恢复用户上次选择的地图提供商:', preferredMapProvider);
            setTimeout(() => {
                switchMapProvider(preferredMapProvider);
            }, 1000); // 稍微延迟，确保页面已完全加载
        }
    });

    // 全局函数，供高德地图API回调
    window.initGaodeMap = initGaodeMap;
    
    // 搜索高德地图
    function searchGaodeMap(address) {
        if (!gaodeMapInstance) {
            alert("高德地图未初始化，请刷新页面重试");
            document.getElementById('loading').style.display = 'none';
            return;
        }
        
        try {
            // 创建高德地图地理编码实例
            AMap.plugin('AMap.Geocoder', function() {
                const geocoder = new AMap.Geocoder();
                
                // 将地址解析成经纬度
                geocoder.getLocation(address, function(status, result) {
                    if (status === 'complete' && result.info === 'OK') {
                        // 获取第一个地址的位置
                        const location = result.geocodes[0].location;
                        
                        // 清空地图上现有标记
                        gaodeMapInstance.clearMap();
                        
                        // 设置地图中心点和缩放级别
                        gaodeMapInstance.setCenter([location.lng, location.lat]);
                        gaodeMapInstance.setZoom(15);
                        
                        // 添加标记
                        const marker = new AMap.Marker({
                            position: [location.lng, location.lat],
                            map: gaodeMapInstance
                        });
                        
                        // 显示800米半径圆
                        const circle = new AMap.Circle({
                            center: [location.lng, location.lat],
                            radius: 800,
                            strokeColor: "#FF0000",
                            strokeOpacity: 0.8,
                            strokeWeight: 2,
                            fillColor: "#FF0000",
                            fillOpacity: 0.1,
                            map: gaodeMapInstance
                        });
                        
                        // 存储中心点信息用于后续导出
                        window.center = {
                            lng: location.lng,
                            lat: location.lat
                        };
                        window.zoom = 15;
                        window.address = address;
                        
                        // 存储圆圈信息用于后续导出
                        window.circleInfo = {
                            center: {
                                lng: location.lng,
                                lat: location.lat
                            },
                            radius: 800
                        };
                        
                        // 搜索周边公交站
                        searchGaodeNearbyTransit(location);
                    } else {
                        console.error("高德地图地址解析失败:", result);
                        alert("未找到该地址");
                        document.getElementById('loading').style.display = 'none';
                    }
                });
            });
        } catch (error) {
            console.error("高德地图搜索地址失败:", error);
            document.getElementById('loading').style.display = 'none';
            alert("搜索地址时出错: " + error.message);
        }
    }

    // 搜索高德地图周边公交站
    function searchGaodeNearbyTransit(location) {
        try {
            // 清空现有标记（保留中心点和圆圈）
            gaodeMapInstance.clearMap();
            
            // 重新添加中心点标记
            const marker = new AMap.Marker({
                position: [location.lng, location.lat],
                map: gaodeMapInstance
            });
            
            // 重新添加800米半径圆圈
            const circle = new AMap.Circle({
                center: [location.lng, location.lat],
                radius: 800,
                strokeColor: "#FF0000",
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: "#FF0000",
                fillOpacity: 0.1,
                map: gaodeMapInstance
            });
            
            // 初始化 AMap.PlaceSearch
            AMap.plugin(['AMap.PlaceSearch'], function() {
                // 创建公交站点搜索实例
                const placeSearch = new AMap.PlaceSearch({
                    pageSize: 50,
                    type: '公交车站|地铁站',
                    pageIndex: 1,
                    city: '全国',
                    radius: 800,
                    autoFitView: false
                });
                
                // 周边搜索
                placeSearch.searchNearBy('', [location.lng, location.lat], 800, function(status, result) {
                    document.getElementById('loading').style.display = 'none';
                    
                    if (status === 'complete' && result.info === 'OK') {
                        const pois = result.poiList.pois;
                        
                        if (!pois || pois.length === 0) {
                            document.getElementById('result-count').textContent = '未找到周边800米内的公交站和地铁站，请尝试其他地点';
                            return;
                        }
                        
                        // 处理搜索结果
                        processGaodeSearchResults(pois, location);
                    } else {
                        console.error("高德地图搜索周边公交站失败:", result);
                        document.getElementById('result-count').textContent = '未找到周边公交站点';
                    }
                });
            });
        } catch (error) {
            console.error("高德地图搜索周边公交站失败:", error);
            document.getElementById('loading').style.display = 'none';
            alert("搜索周边公交站时出错: " + error.message);
        }
    }

    // 处理高德地图搜索结果
    function processGaodeSearchResults(pois, centerLocation) {
        try {
            // 初始化结果数组
            window.stations = [];
            window.markers = [];
            
            // 添加中心点标记
            window.markers.push({
                lng: centerLocation.lng,
                lat: centerLocation.lat,
                isCenter: true
            });
            
            // 清空结果表格
            const resultBody = document.getElementById('result-body');
            resultBody.innerHTML = '';
            
            // 更新结果计数
            const resultCount = document.getElementById('result-count');
            resultCount.textContent = `共找到 ${pois.length} 个交通站点`;
            
            // 处理每个POI
            pois.forEach((poi, index) => {
                // 获取坐标点
                const poiLocation = poi.location;
                
                // 计算与中心点的距离（高德API返回的距离单位为米）
                const distance = poi.distance;
                
                // 获取类型名称
                const typeName = poi.type.includes('地铁') ? '地铁站' : '公交站';
                
                // 获取POI名称和地址
                const title = poi.name || "未知站点";
                const details = poi.address || "无详细信息";
                
                // 创建表格行
                const row = document.createElement('tr');
                
                // 添加单元格
                row.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${index + 1}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${title}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${typeName}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${distance}</td>
                    <td class="px-4 py-2 text-sm text-gray-900">${details}</td>
                `;
                
                // 添加行到表格
                resultBody.appendChild(row);
                
                // 添加到站点数组
                window.stations.push({
                    index: index + 1,
                    name: title,
                    type: typeName,
                    distance: distance,
                    detail: details,
                    location: {
                        lng: poiLocation.lng,
                        lat: poiLocation.lat
                    }
                });
                
                // 添加到标记数组
                window.markers.push({
                    lng: poiLocation.lng,
                    lat: poiLocation.lat,
                    stationIndex: index + 1,
                    stationType: typeName
                });
                
                // 选择图标颜色（公交站红色，地铁站蓝色）
                const iconColor = typeName === "地铁站" ? "#1890FF" : "#FF0000";
                
                // 在地图上添加标记
                const marker = new AMap.Marker({
                    position: [poiLocation.lng, poiLocation.lat],
                    map: gaodeMapInstance,
                    content: `<div style="background-color: ${iconColor}; color: white; border-radius: 50%; width: 20px; height: 20px; line-height: 20px; text-align: center; font-size: 12px;">${index + 1}</div>`
                });
            });
            
            // 启用导出按钮
            document.getElementById('export-btn').disabled = false;
            
            // 添加导出按钮点击事件
            document.getElementById('export-btn').onclick = executeMapScreenshot;
            
        } catch (error) {
            console.error("处理高德地图搜索结果失败:", error);
            document.getElementById('result-count').textContent = '处理搜索结果时出错';
        }
    }
    