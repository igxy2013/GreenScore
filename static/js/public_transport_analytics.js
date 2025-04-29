            // --- 公共交通分析JS ---
            let currentMapProvider = 'baidu'; // 默认百度
            let baiduMapInstance = null;
            let gaodeMapInstance = null;
            let lastSearchResults = []; // 存储上次搜索结果，用于导出

            // --- 地图API Key ---
            let baiduApiKey = null;
            let gaodeApiKey = null; // 需要从后端获取
            window.securityJsCode = null; // 添加安全码全局变量

    // 确保DOM完全加载后再执行
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOMContentLoaded: 页面DOM加载完成');
        
        // 使用setTimeout给浏览器一些时间完全渲染DOM
        setTimeout(function() {
            // 检查当前页面是否需要地图功能
            const baiduMapContainer = document.getElementById('baidu-map-container');
            const gaodeMapContainer = document.getElementById('gaode-map-container');
            
            // 查找公共交通分析标题
            let transportAnalysisTitle = false;
            const h1Elements = document.querySelectorAll('h1.text-center');
            for (let i = 0; i < h1Elements.length; i++) {
                if (h1Elements[i].textContent.includes('公共交通站点分析')) {
                    transportAnalysisTitle = true;
                    break;
                }
            }
            
            // 检查是否是公共交通分析页面
            const isTransportPage = Boolean(
                baiduMapContainer || 
                gaodeMapContainer || 
                transportAnalysisTitle ||
                window.location.href.includes('public_transport_analysis') ||
                document.querySelector('[id="transport-project-id"]')
            );
            
            console.log('页面检测: 是否为公共交通分析页面:', isTransportPage);
            console.log('检查地图容器状态:');
            console.log('百度地图容器:', baiduMapContainer ? '已找到' : '未找到');
            console.log('高德地图容器:', gaodeMapContainer ? '已找到' : '未找到');
            
            // 如果不是公共交通分析页面，则不需要初始化地图
            if (!isTransportPage) {
                console.log('当前页面不是公共交通分析页面，跳过地图初始化');
                return;
            }
            
            // 如果页面上没有地图容器，也不需要初始化地图功能
            if (!baiduMapContainer && !gaodeMapContainer) {
                console.log('当前页面不需要地图功能，跳过初始化');
                return;
            }
            
            console.log('检测到地图容器，初始化地图功能');
            
            // 确保容器可见
            if (baiduMapContainer) {
                baiduMapContainer.style.display = 'block';
                console.log('百度地图容器设为可见');
            }
            
            // 初始化首选地图提供商
            const preferredProvider = localStorage.getItem('preferred_map_provider') || 'baidu';
            console.log('首选地图提供商:', preferredProvider);
            switchMapProvider(preferredProvider);

            // --- 新增：为应用得分按钮添加事件监听器 ---
            const applyBtn = document.getElementById('apply-score-btn');
            if (applyBtn) {
                applyBtn.addEventListener('click', applyTransportScoresToProject);
                console.log('已为应用得分按钮添加点击事件监听器');
            } else {
                console.warn('未找到应用得分按钮 (apply-score-btn)');
            }
            // --- 结束新增 ---
        }, 500); // 延迟500毫秒，确保DOM完全渲染
    });
    
    // 处理页面加载完成后的初始化
    window.addEventListener('load', function() {
        console.log('页面完全加载完成，包括所有图片和资源');
        // 检查百度地图容器
        const baiduMapContainer = document.getElementById('baidu-map-container');
        if (baiduMapContainer && currentMapProvider === 'baidu' && !baiduMapInstance) {
            console.log('页面加载完成后再次尝试初始化百度地图');
            loadBaiduMapScript();
        }
    });

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
        // 在任何操作前检查是否处于含有地图的页面
        if (!document.getElementById('baidu-map-container')) {
            // 如果容器不存在，静默返回，不记录错误
            console.log("当前页面不包含百度地图容器，不需要加载地图API");
            return;
        }
        
        console.log("开始加载百度地图API");
        
        // 先检查地图容器是否存在，不存在则不需要加载地图API
        const mapContainer = document.getElementById('baidu-map-container');
        if (!mapContainer) {
            console.log("百度地图容器不存在，可能当前页面不需要地图功能");
            return; // 安静地退出，不产生错误
        } else {
            console.log("找到百度地图容器元素:", mapContainer);
            // 确保地图容器可见
            mapContainer.style.display = "block";
        }
        
        // 检查BMap对象是否已存在
        if (typeof BMap !== 'undefined') {
            console.log("BMap对象已存在，直接初始化地图");
            setTimeout(() => {
                try {
                    initBaiduMap();
                } catch (e) {
                    console.error("延迟初始化百度地图失败:", e);
                    // 显示错误信息
                    if (mapContainer) {
                        mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图初始化失败: ${e.message}</div>`;
                    }
                }
            }, 500); // 添加延迟，确保BMap完全加载
            return;
        }

        // 添加全局错误处理，捕获"Cannot read properties of undefined"错误
        window.onerror = function(message, source, lineno, colno, error) {
            console.error("全局错误:", message, "来源:", source, "行号:", lineno);
            if (message.includes("Cannot read properties of undefined") || message.includes("地图容器不存在")) {
                console.error("捕获到百度地图初始化错误，尝试重新加载");
                setTimeout(() => {
                    // 清空容器并重试
                    if (mapContainer) {
                        mapContainer.innerHTML = '';
                    }
                    loadBaiduMapScriptWithHardcodedKey();
                }, 1000);
                return true; // 阻止默认错误处理
            }
            return false; // 允许其他错误正常处理
        };

        // 尝试先使用后端API获取密钥
        fetch('/api/map_api_key')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`后端代理请求失败: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.api_key) {
                    throw new Error("API返回中没有百度地图密钥");
                }
                
                console.log("成功从API获取百度地图密钥");
                
                // 再次检查容器是否存在（可能在API请求期间页面结构发生变化）
                if (!document.getElementById('baidu-map-container')) {
                    console.log("API请求返回后，百度地图容器已不存在，不继续加载");
                    return;
                }
                
                // 获取到API密钥后，加载百度地图脚本
                baiduApiKey = data.api_key;
                loadScriptWithKey(baiduApiKey);
            })
            .catch(error => {
                console.error('获取API密钥失败，尝试使用硬编码密钥:', error);
                
                // 再次检查容器是否存在
                if (!document.getElementById('baidu-map-container')) {
                    console.log("API请求失败后，百度地图容器已不存在，不继续加载");
                    return;
                }
                
                loadBaiduMapScriptWithHardcodedKey();
            });
    }
    
    // 使用硬编码密钥加载百度地图（作为备选方案）
    function loadBaiduMapScriptWithHardcodedKey() {
        console.log("使用硬编码密钥加载百度地图");
        // 使用.env中配置的密钥作为备选
        const hardcodedKey = "J6UW18n9sxCMtrxTkjpLE3JkU8pfw3bL";
        baiduApiKey = hardcodedKey;
        loadScriptWithKey(hardcodedKey);
    }
    
    // 使用给定的密钥加载百度地图脚本
    function loadScriptWithKey(apiKey) {
        console.log("使用密钥加载百度地图脚本:", apiKey);
        
        // 检查容器是否存在 - 如果不存在，可能是当前页面不需要地图
        const mapContainer = document.getElementById('baidu-map-container');
        if (!mapContainer) {
            console.log("百度地图容器不存在，可能当前页面不需要地图功能");
            return; // 安静地退出，不产生错误
        }
        
        // 创建脚本元素
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = `https://api.map.baidu.com/api?v=3.0&ak=${apiKey}&callback=initBaiduMap`;
        script.onerror = function() {
            console.error("直接加载百度地图API失败，尝试使用代理");
            // 使用后端代理
            const proxyScript = document.createElement('script');
            proxyScript.type = 'text/javascript';
            proxyScript.src = `/api/map_js_api?v=3.0&callback=initBaiduMap`;
            // 确保document.body存在
            if (document.body) {
                document.body.appendChild(proxyScript);
                console.log("通过代理添加百度地图脚本");
            } else {
                console.error("document.body不存在，无法添加脚本");
                // 显示错误信息
                if (mapContainer) {
                    mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图加载失败: document.body不存在</div>`;
                }
            }
        };
        
        // 确保document.body存在
        if (document.body) {
            document.body.appendChild(script);
            console.log("已添加百度地图脚本到document.body");
        } else {
            console.error("document.body不存在，无法添加脚本");
            // 显示错误信息
            if (mapContainer) {
                mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图加载失败: document.body不存在</div>`;
            }
        }
    }
    
    // --- 加载高德地图API ---
    function loadGaodeMapScript() {
        console.log("开始加载高德地图API");
        
        // 先检查地图容器是否存在，不存在则不需要加载地图API
        const mapContainer = document.getElementById('gaode-map-container');
        if (!mapContainer) {
            console.log("高德地图容器不存在，不加载地图API");
            return;
        }
        
        // 检查AMap对象是否已存在
        if (typeof AMap !== 'undefined') {
            console.log("AMap对象已存在，直接初始化地图");
            setTimeout(() => {
                try {
                    initGaodeMap();
                } catch (e) {
                    console.error("延迟初始化高德地图失败:", e);
                    // 显示错误信息
                    if (mapContainer) {
                        mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">高德地图初始化失败: ${e.message}</div>`;
                    }
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
                
                // 保存API密钥
                gaodeApiKey = data.api_key;
                
                try {
                    // 检查是否已有安全设置
                    if (!window._AMapSecurityConfig) {
                        // 直接创建安全配置对象
                        window._AMapSecurityConfig = {
                            securityJsCode: data.security_js_code || '',
                            serviceHost: data.service_host || "https://lbs.amap.com"
                        };
                        console.log("已创建高德地图安全配置对象");
                    }
                    
                    // 加载高德地图主脚本
                    loadAMapMainScript(gaodeApiKey);
                } catch (e) {
                    console.error("设置高德地图安全码失败:", e);
                    // 失败后仍尝试加载主脚本
                    loadAMapMainScript(gaodeApiKey);
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
    
    // 加载高德地图主脚本的函数
    function loadAMapMainScript(apiKey) {
        console.log("开始加载高德地图主脚本");
        
        // 检查是否已存在脚本
        const existingScript = document.querySelector('script[src*="webapi.amap.com/maps"]');
        if (existingScript) {
            console.log("高德地图脚本已存在，不重复加载");
            // 如果AMap对象已存在，则初始化地图
            if (typeof AMap !== 'undefined') {
                setTimeout(() => {
                    try {
                        initGaodeMap();
                    } catch (e) {
                        console.error("尝试初始化高德地图失败:", e);
                    }
                }, 500);
            }
            return;
        }
        
        // 创建script标签
        const script = document.createElement('script');
        script.type = 'text/javascript';
        // 添加必要的插件到URL中，预先加载所需插件
        script.src = `https://webapi.amap.com/maps?v=2.0&key=${apiKey}&callback=initGaodeMap&plugin=AMap.Geocoder,AMap.PlaceSearch,AMap.Scale,AMap.ToolBar`;
        
        // 添加加载错误处理
        script.onerror = function() {
            console.error("加载高德地图API失败");
            const mapContainer = document.getElementById('gaode-map-container');
            if (mapContainer) {
                mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">高德地图API加载失败</div>`;
            }
        };
        
        // 添加到文档中加载脚本
        // 确保document.body存在
        if (document.body) {
            document.body.appendChild(script);
            console.log("高德地图脚本标签已添加到文档");
        } else {
            console.error("document.body不存在，无法添加高德地图脚本");
        }
    }
    
    // --- 初始化百度地图函数
    function initBaiduMap() {
        try {
            console.log("正在初始化百度地图...");
            
            // 确保地图容器存在并可见
            const mapContainer = document.getElementById('baidu-map-container');
            if (!mapContainer) {
                console.error("初始化失败：百度地图容器元素不存在！");
                throw new Error("地图容器不存在");
            }
            
            console.log("地图容器状态：", {
                id: mapContainer.id,
                display: mapContainer.style.display,
                height: mapContainer.style.height || mapContainer.offsetHeight + 'px',
                width: mapContainer.style.width || mapContainer.offsetWidth + 'px'
            });
            
            // 确保容器可见
            mapContainer.style.display = "block";
            
            // 检查BMap对象是否存在
            if (typeof BMap === 'undefined') {
                console.error("初始化失败：BMap对象未定义！");
                throw new Error("百度地图API未加载");
            }
            
            console.log("BMap对象已存在，开始创建地图实例");
            
            try {
                // 创建地图实例
                console.log("创建BMap.Map实例...");
                const map = new BMap.Map('baidu-map-container');
                console.log("地图实例创建成功");
                
                // 保存到全局变量
                baiduMapInstance = map;
                window.map = map; // 为了兼容现有代码
                
                // 初始中心点 (成都)
                const point = new BMap.Point(104.065735, 30.659462);
                map.centerAndZoom(point, 15);
                
                // 创建标记并添加到地图中
                const marker = new BMap.Marker(point);
                baiduMapInstance.addOverlay(marker);
                
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
                
                // 添加地图点击事件
                map.addEventListener('click', function(e) {
                    // 显示加载中
                    const loadingElement = document.getElementById('loading');
                    if (loadingElement) {
                        loadingElement.style.display = 'block';
                    }
                    
                    // 清除原有覆盖物
                    map.clearOverlays();
                    
                    // 添加新的标记
                    const newPoint = new BMap.Point(e.point.lng, e.point.lat);
                    const newMarker = new BMap.Marker(newPoint);
                    map.addOverlay(newMarker);
                    
                    // 反向地理编码获取地址
                    const geoCoder = new BMap.Geocoder();
                    geoCoder.getLocation(newPoint, function(result) {
                        if (result && result.address) {
                            // 更新地址输入框
                            const addressInput = document.getElementById('address');
                            if (addressInput) {
                                addressInput.value = result.address;
                            }
                            
                            // 保存地址信息
                            window.address = result.address;
                            
                            // 保存中心点
                            window.center = {
                                lng: newPoint.lng,
                                lat: newPoint.lat
                            };
                            
                            // 搜索周边公交站
                            searchNearbyTransit(newPoint);
                        } else {
                            const loadingElement = document.getElementById('loading');
                            if (loadingElement) {
                                loadingElement.style.display = 'none';
                            }
                            alert("无法获取该位置的地址信息");
                        }
                    });
                });
                
                console.log("百度地图初始化成功");
                
            } catch (innerError) {
                console.error("创建地图实例时发生错误:", innerError);
                throw innerError;
            }
            
        } catch (error) {
            console.error("初始化百度地图失败:", error);
            const mapContainer = document.getElementById('baidu-map-container');
            if (mapContainer) {
                // 显示错误信息给用户
                mapContainer.innerHTML = `
                    <div class="flex flex-col items-center justify-center h-full bg-gray-100 p-5">
                        <div class="text-red-500 font-bold mb-2">地图初始化失败</div>
                        <div class="text-gray-700 text-sm mb-4">原因: ${error.message}</div>
                        <button class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark" 
                                onclick="retryLoadBaiduMap()">
                            重试加载地图
                        </button>
                    </div>`;
                mapContainer.style.display = "block"; // 确保错误信息可见
            }
            // 设置一个全局重试函数
            window.retryLoadBaiduMap = function() {
                const container = document.getElementById('baidu-map-container');
                if (container) {
                    container.innerHTML = '';
                    container.style.display = 'block';
                }
                loadBaiduMapScriptWithHardcodedKey();
            };
        }
    }
    
    // --- 初始化高德地图函数
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
                viewMode: '2D',
                scrollWheel: false // 禁用鼠标滚轮缩放
            });
            
            // 保存到全局变量
            gaodeMapInstance = map;
            
            // 禁用滚轮缩放
            map.setStatus({scrollWheel: false});
            
            // 添加地图控件 - 使用新版本的控件创建方式
            AMap.plugin(['AMap.Scale', 'AMap.ToolBar', 'AMap.Geocoder', 'AMap.PlaceSearch'], function(){
                // 添加比例尺
                const scale = new AMap.Scale();
                map.addControl(scale);
                
                // 添加工具条
                const toolBar = new AMap.ToolBar();
                map.addControl(toolBar);
                
                // 初始化地理编码服务，用于后续点击事件
                const geocoder = new AMap.Geocoder({
                    city: "全国", // 城市，默认"全国"
                    radius: 1000 // 范围，默认1000米
                });
                
                // 添加地图点击事件
                map.on('click', function(e) {
                    // 显示加载中
                    document.getElementById('loading').style.display = 'block';
                    
                    // 清除地图上现有标记
                    map.clearMap();
                    
                    // 添加新的标记
                    const marker = new AMap.Marker({
                        position: [e.lnglat.getLng(), e.lnglat.getLat()],
                        map: map
                    });
                    
                    // 逆地理编码，获取地址信息
                    geocoder.getAddress([e.lnglat.getLng(), e.lnglat.getLat()], function(status, result) {
                        if (status === 'complete' && result.info === 'OK') {
                            // 获取地址
                            const address = result.regeocode.formattedAddress;
                            
                            // 更新地址输入框
                            const addressInput = document.getElementById('address');
                            if (addressInput) {
                                addressInput.value = address;
                            }
                            
                            // 保存地址信息
                            window.address = address;
                            
                            // 保存中心点
                            window.center = {
                                lng: e.lnglat.getLng(),
                                lat: e.lnglat.getLat()
                            };
                            
                            // 搜索周边公交站
                            searchGaodeNearbyTransit(location);
                        } else {
                            document.getElementById('loading').style.display = 'none';
                            console.error("高德地图逆地理编码失败:", result);
                            alert("无法获取该位置的地址信息");
                        }
                    });
                });
                
                console.log("高德地图插件加载成功：AMap.Scale, AMap.ToolBar, AMap.Geocoder, AMap.PlaceSearch");
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
            
            // 添加中心点标记，使用更大的图标
            const centerIcon = new BMap.Icon("/api/map_proxy?service_path=images/marker_red.png", new BMap.Size(39, 50), {
                anchor: new BMap.Size(20, 50)  // 调整锚点位置
            });
            const marker = new BMap.Marker(point, {icon: centerIcon});
            baiduMapInstance.addOverlay(marker);
            
            // 显示800米半径圆圈
            const circle = new BMap.Circle(point, 800, {
                strokeColor: "red",
                strokeWeight: 3,  // 增加线宽
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
            
            // 创建存储所有站点的数组
            window.allStations = [];
            
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
                    
                    // 处理搜索结果，但不直接渲染，而是存储在 window.allStations
                    collectSearchResults(results, point, "公交站");
                    
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
                    // 检查搜索结果的有效性
                    if (!results || typeof results !== 'object' || 
                        (typeof results.getNumPois === 'function' && results.getNumPois() === 0)) {
                        
                        // 如果没有地铁站但有公交站
                        if (window.allStations && window.allStations.length > 0) {
                            // 处理收集的所有站点
                            processCombinedResults(point);
                        } else {
                            // 如果没有找到任何站点
                            const resultCount = document.getElementById('result-count');
                            resultCount.textContent = '未找到周边800米内的公交站和地铁站，请尝试其他地点';
                        }
                        return;
                    }
                    
                    // 收集地铁站搜索结果
                    collectSearchResults(results, point, "地铁站");
                    
                    // 处理所有收集的站点（公交站+地铁站）
                    processCombinedResults(point);
                },
                onError: function(error) {
                    console.error("搜索周边地铁站点失败:", error);
                    // 如果至少有公交站，仍然处理结果
                    if (window.allStations && window.allStations.length > 0) {
                        processCombinedResults(point);
                    }
                }
            });
            
            // 搜索周边800米内的地铁站
            local.searchNearby('地铁站', point, 800);
        } catch (error) {
            console.error("搜索周边地铁站失败:", error);
            // 如果至少有公交站，仍然处理结果
            if (window.allStations && window.allStations.length > 0) {
                processCombinedResults(point);
            }
        }
    }
    
    // 收集搜索结果但不渲染
    function collectSearchResults(results, centerPoint, stationType) {
        try {
            // 获取所有POI点，兼容不同格式的搜索结果
            let pois = [];
            if (results.getPois && typeof results.getPois === 'function') {
                pois = results.getPois();
            } else if (results.Ar && Array.isArray(results.Ar)) {
                pois = results.Ar;
            } else if (results.Ir && Array.isArray(results.Ir)) {
                pois = results.Ir;
            } else if (results instanceof Array) {
                pois = results;
            } else if (results.Ha && Array.isArray(results.Ha)) {
                pois = results.Ha;
            } else if (Array.isArray(results._pois)) {
                pois = results._pois;
            } else {
                for (let key in results) {
                    if (Array.isArray(results[key]) && results[key].length > 0 && results[key][0].title) {
                        pois = results[key];
                        break;
                    }
                }
                
                if (pois.length === 0) {
                    console.error("无法识别的搜索结果格式:", results);
                    return;
                }
            }
            
            // 如果没有找到结果
            if (pois.length === 0) {
                return;
            }
            
            // 处理所有POI
            pois.forEach(poi => {
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
                const distance = parseInt(baiduMapInstance.getDistance(
                    new BMap.Point(centerPoint.lng, centerPoint.lat),
                    poiPoint
                ).toFixed(0), 10);
                
                // 获取POI名称
                const title = poi.title || poi.name || poi.address || "未知站点";
                
                // 获取详细信息
                const details = poi.address || poi.addressDetail || poi.province + poi.city || "无详细信息";
                
                // 添加到所有站点数组
                window.allStations.push({
                    poi,
                    poiPoint,
                    distance,
                    title,
                    details,
                    stationType
                });
            });
            
        } catch (error) {
            console.error("收集搜索结果失败:", error);
        }
    }
    
    // 处理合并后的站点结果
    function processCombinedResults(centerPoint) {
        try {
            if (!window.allStations) {
                window.allStations = [];
            }
            
            // 按距离排序所有站点
            window.allStations.sort((a, b) => a.distance - b.distance);
            
            // 统计原始总数
            const originalCount = window.allStations.length;
            const busStationsCount = window.allStations.filter(s => s.stationType === "公交站").length;
            const metroStationsCount = window.allStations.filter(s => s.stationType === "地铁站").length;
            
            // 只取最近的10个站点
            const displayStations = window.allStations.slice(0, 10);
            
            // 初始化结果数组
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
            
            // 更新结果计数
            const resultCount = document.getElementById('result-count');
            if (originalCount > 10) {
                resultCount.textContent = `共找到 ${originalCount} 个交通站点 (包括 ${busStationsCount} 个公交站和 ${metroStationsCount} 个地铁站)，显示最近的 10 个`;
            } else {
                resultCount.textContent = `共找到 ${originalCount} 个交通站点 (包括 ${busStationsCount} 个公交站和 ${metroStationsCount} 个地铁站)`;
            }
            
            // 处理选定的站点
            displayStations.forEach((station, index) => {
                // 创建表格行
                const row = document.createElement('tr');
                
                
                // 添加单元格
                row.innerHTML = `
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${index + 1}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${station.title}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${station.stationType}</td>
                    <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">${station.distance}</td>
                    <td class="px-4 py-2 text-sm text-gray-900">${station.details}</td>
                `;
                
                // 添加行到表格
                resultBody.appendChild(row);
                
                // 添加到站点数组
                window.stations.push({
                    index: index + 1,
                    name: station.title,
                    type: station.stationType,
                    distance: station.distance.toString(), // 确保是字符串
                    detail: station.details,
                    location: {
                        lng: station.poiPoint.lng,
                        lat: station.poiPoint.lat
                    }
                });
                
                // 添加到标记数组
                window.markers.push({
                    lng: station.poiPoint.lng,
                    lat: station.poiPoint.lat,
                    stationIndex: index + 1,
                    stationType: station.stationType
                });
                
                // 选择图标颜色（公交站红色，地铁站蓝色）
                const iconColor = station.stationType === "地铁站" ? "blue" : "red";
                
                // 在地图上添加标记
                const marker = new BMap.Marker(
                    station.poiPoint,
                    {
                        icon: new BMap.Symbol(BMap_Symbol_SHAPE_POINT, {
                            scale: 1,
                            fillColor: iconColor,
                            fillOpacity: 0.8
                        })
                    }
                );
                
                // 添加标记标签
                const label = new BMap.Label(index + 1, {
                    offset: new BMap.Size(0, 0),
                    position: station.poiPoint
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
            document.getElementById('apply-score-btn').disabled = false; // <-- 启用应用得分按钮
            
            // 添加导出按钮点击事件
            document.getElementById('export-btn').onclick = executeMapScreenshot;
            
            // 生成评价结论
            generateConclusion();
            
        } catch (error) {
            console.error("处理合并搜索结果失败:", error);
            console.log("站点数据:", window.allStations);
            alert("处理搜索结果时出错: " + error.message);
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
            
            // 在遍历所有站点之前对其按距离排序
            const processablePois = pois.map(poi => {
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
                    return null; // 跳过这个POI
                }
                
                // 计算与中心点的距离
                const distance = parseInt(baiduMapInstance.getDistance(
                    new BMap.Point(centerPoint.lng, centerPoint.lat),
                    poiPoint
                ).toFixed(0), 10);
                
                return {
                    poi,
                    poiPoint,
                    distance
                };
            }).filter(item => item !== null);
            
            // 按距离排序
            processablePois.sort((a, b) => a.distance - b.distance);
            
            // 记录原始数量
            const originalCount = processablePois.length;
            
            // 无论是否为附加结果，只保留前10个站点
            let displayedPois = processablePois;
            if (processablePois.length > 10) {
                displayedPois = processablePois.slice(0, 10);
            }
            
            // 获取现有结果数量作为索引起点
            const startIndex = window.stations ? window.stations.length : 0;
            
            // 更新结果计数
            const resultCount = document.getElementById('result-count');
            if (!appendResults) {
                // 第一次搜索结果（公交站）
                if (originalCount > 10) {
                    resultCount.textContent = `共找到 ${originalCount} 个${stationType}，显示最近的 10 个`;
                } else {
                    resultCount.textContent = `共找到 ${originalCount} 个${stationType}`;
                }
            } else {
                // 这是地铁站搜索结果，也限制为10个
                // 计算公交站数量
                const busStations = window.stations.filter(s => s.type === "公交站").length;
                
                // 总数 = 已有的公交站 + 这次找到的地铁站
                const totalStations = busStations + originalCount;
                
                if (originalCount > 0) {
                    if (originalCount > 10) {
                        resultCount.textContent = `共找到 ${totalStations} 个交通站点 (包括 ${busStations} 个公交站和 ${originalCount} 个地铁站)，显示最近的站点`;
                    } else {
                        resultCount.textContent = `共找到 ${totalStations} 个交通站点 (包括 ${busStations} 个公交站和 ${originalCount} 个地铁站)`;
                    }
                } else {
                    // 没找到地铁站
                    resultCount.textContent = `共找到 ${busStations} 个公交站，周边800米内无地铁站`;
                }
            }
            
            // 处理每个POI
            displayedPois.forEach(({poi, poiPoint, distance}, index) => {
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
                resultBody.appendChild(row);
                
                // 添加到站点数组
                window.stations.push({
                    index: startIndex + index + 1,
                    name: title,
                    type: stationType,
                    distance: distance.toString(), // 确保是字符串
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
            document.getElementById('apply-score-btn').disabled = false; // <-- 启用应用得分按钮
            
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
            
            // 添加中心点标记，使用更大的图标
            const centerIcon = new BMap.Icon("/api/map_proxy?service_path=images/marker_red.png", new BMap.Size(39, 50), {
                anchor: new BMap.Size(10, 20)  // 调整锚点位置
            });
            const marker = new BMap.Marker(point, {icon: centerIcon});
            baiduMapInstance.addOverlay(marker);
            
            // 显示800米半径圆圈
            const circle = new BMap.Circle(point, 800, {
                strokeColor: "red",
                strokeWeight: 3,  // 增加线宽
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
            
            // 创建存储所有站点的数组
            window.allStations = [];
            
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
                    
                    // 处理搜索结果，但不直接渲染，而是存储在 window.allStations
                    collectSearchResults(results, point, "公交站");
                    
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
                        
                        // 如果没有地铁站但有公交站
                        if (window.allStations && window.allStations.length > 0) {
                            // 处理收集的所有站点
                            processCombinedResults(point);
                        } else {
                            // 如果没有找到任何站点
                            const resultCount = document.getElementById('result-count');
                            resultCount.textContent = '未找到周边800米内的公交站和地铁站，请尝试其他地点';
                        }
                        return;
                    }
                    
                    // 收集地铁站搜索结果
                    collectSearchResults(results, point, "地铁站");
                    
                    // 处理所有收集的站点（公交站+地铁站）
                    processCombinedResults(point);
                },
                onError: function(error) {
                    console.error("搜索周边地铁站点失败:", error);
                    // 如果至少有公交站，仍然处理结果
                    if (window.allStations && window.allStations.length > 0) {
                        processCombinedResults(point);
                    }
                }
            });
            
            // 搜索周边800米内的地铁站
            local.searchNearby('地铁站', point, 800);
        } catch (error) {
            console.error("搜索周边地铁站失败:", error);
            // 如果至少有公交站，仍然处理结果
            if (window.allStations && window.allStations.length > 0) {
                processCombinedResults(point);
            }
        }
    }



    // 执行地图截图前先检查地图状态
    function executeMapScreenshot() {
        // 显示加载状态
        document.getElementById('loading').style.display = 'block';
        
        // 生成结论
        const conclusion = generateConclusion();
        
        // 尝试从剪贴板获取图片
        tryGetImageFromClipboard().then(clipboardImage => {
            if (clipboardImage) {
                console.log("成功从剪贴板获取图片，直接使用");
                performScreenshotCapture(conclusion, clipboardImage);
            } else {
                console.log("剪贴板中没有图片，使用正常截图流程");
                // 检查是否使用高德地图，如果是，使用静态图API
                if (currentMapProvider === 'gaode' && gaodeMapInstance) {
                    // 使用高德地图静态图API
                    createGaodeStaticMap().then(staticMapImageData => {
                        performScreenshotCapture(conclusion, staticMapImageData);
                    }).catch(error => {
                        console.error("创建高德静态地图失败，回退到普通截图:", error);
                        checkMapTilesAndCapture(conclusion);
                    });
                } else {
                    // 百度地图或其他情况使用普通截图
                    checkMapTilesAndCapture(conclusion);
                }
            }
        }).catch(error => {
            console.error("获取剪贴板图片失败:", error);
            // 回退到正常截图流程
            if (currentMapProvider === 'gaode' && gaodeMapInstance) {
                createGaodeStaticMap().then(staticMapImageData => {
                    performScreenshotCapture(conclusion, staticMapImageData);
                }).catch(error => {
                    console.error("创建高德静态地图失败，回退到普通截图:", error);
                    checkMapTilesAndCapture(conclusion);
                });
            } else {
                checkMapTilesAndCapture(conclusion);
            }
        });
    }
    
    // 从剪贴板获取图片
    async function tryGetImageFromClipboard() {
        try {
            // 首先检查是否已通过粘贴事件保存了剪贴板图片
            if (window.clipboardImageData) {
                console.log("使用之前通过粘贴事件保存的剪贴板图片");
                return window.clipboardImageData;
            }
            
            // 检查剪贴板API是否可用
            if (!navigator.clipboard || !navigator.clipboard.read) {
                console.warn("浏览器不支持Clipboard API读取功能");
                return null;
            }
            
            // 读取剪贴板内容
            const clipboardItems = await navigator.clipboard.read();
            console.log("读取到剪贴板项目:", clipboardItems.length);
            
            // 查找图片类型
            for (const clipboardItem of clipboardItems) {
                // 检查是否有图片类型
                const imageTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
                
                // 找到支持的图片类型
                let foundImageType = null;
                for (const imageType of imageTypes) {
                    if (clipboardItem.types.includes(imageType)) {
                        foundImageType = imageType;
                        break;
                    }
                }
                
                if (foundImageType) {
                    console.log("在剪贴板中找到图片类型:", foundImageType);
                    // 获取图片数据
                    const blob = await clipboardItem.getType(foundImageType);
                    console.log("获取到剪贴板图片数据块:", blob.size, "字节");
                    
                    // 转换为Data URL
                    return new Promise((resolve, reject) => {
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    });
                }
            }
            
            console.log("剪贴板中没有找到图片");
            return null;
        } catch (error) {
            console.error("读取剪贴板时出错:", error);
            
            // 如果出错且有权限错误，提示用户
            if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
                alert("需要剪贴板读取权限。请在浏览器设置中允许本网站访问剪贴板，然后重试。或者您可以手动复制地图截图并在页面上按Ctrl+V粘贴。");
            }
            
            return null;
        }
    }
    
    // 检查地图瓦片加载状态，然后执行截图
    function checkMapTilesAndCapture(conclusion) {
        if (currentMapProvider === 'gaode' && gaodeMapInstance) {
            console.log("检查高德地图瓦片加载状态...");
            // 强制刷新地图以确保瓦片加载
            gaodeMapInstance.setStatus({jogEnable: true});
            setTimeout(() => {
                gaodeMapInstance.setStatus({jogEnable: false});
                
                // 延迟执行截图，给瓦片加载时间
                setTimeout(() => {
                    performScreenshotCapture(conclusion);
                }, 1000);
            }, 500);
        } else {
            // 百度地图或其他情况直接截图
            performScreenshotCapture(conclusion);
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
                    logging: true, // 开启日志以便调试
                    scale: window.devicePixelRatio || 2, // 提高清晰度
                    backgroundColor: "#ffffff",
                    willReadFrequently: true,
                    foreignObjectRendering: false, // 禁用foreignObject渲染以避免某些浏览器的兼容性问题
                    ignoreElements: (element) => {
                        // 忽略任何隐藏的元素
                        return element.style.display === 'none';
                    },
                    onclone: (documentClone, element) => {
                        // 在克隆的文档中处理一些特殊情况
                        console.log("文档克隆完成，准备进行截图...");
                        const clonedContainer = documentClone.getElementById(mapContainerId);
                        
                        // 确保克隆的容器可见且尺寸正确
                        if (clonedContainer) {
                            clonedContainer.style.opacity = '1';
                            clonedContainer.style.visibility = 'visible';
                            
                            // 百度地图特殊处理
                            if (currentMapProvider === 'baidu') {
                                // 确保所有百度地图元素可见
                                const mapElements = clonedContainer.querySelectorAll('.BMap_mask, .BMap_shadow, .BMap_circle, .BMap_Marker, .BMap_Overlay, canvas');
                                mapElements.forEach(element => {
                                    if (element) {
                                        element.style.opacity = '1';
                                        element.style.visibility = 'visible';
                                    }
                                });
                                
                                // 特别强调圆形元素的显示
                                const circles = clonedContainer.querySelectorAll('.BMap_circle');
                                circles.forEach(circle => {
                                    if (circle) {
                                        circle.style.strokeOpacity = '1';
                                        circle.style.fillOpacity = '0.2';
                                        circle.style.strokeWidth = '3px';
                                        circle.style.zIndex = '1000';
                                    }
                                });
                            }
                            
                            // 特殊处理高德地图
                            if (currentMapProvider === 'gaode') {
                                // 确保所有地图瓦片和覆盖物都可见
                                const mapTiles = clonedContainer.querySelectorAll('.amap-layer img, .amap-markers img, .amap-overlays div');
                                mapTiles.forEach(tile => {
                                    if (tile) {
                                        tile.style.opacity = '1';
                                        tile.style.visibility = 'visible';
                                    }
                                });
                            }
                        }
                    }
                }).then(canvas => {
                    console.log("地图截图成功，画布尺寸:", canvas.width, "x", canvas.height);
                    // 转换为图片数据URL
                    const imgData = canvas.toDataURL('image/png');
                    resolve(imgData);
                }).catch(error => {
                    console.error("html2canvas截图失败:", error);
                    // 截图失败时创建备用的截图
                    createFallbackImage(resolve);
                });
            } catch (error) {
                console.error("创建地图截图失败:", error);
                // 发生异常时创建备用的截图
                createFallbackImage(resolve);
            }
        });
    }
    
    // 创建备用图片
    function createFallbackImage(resolve) {
        console.log("创建备用地图图片");
        const fallbackCanvas = document.createElement('canvas');
        const width = 800;
        const height = 600;
        fallbackCanvas.width = width;
        fallbackCanvas.height = height;
        const ctx = fallbackCanvas.getContext('2d', { willReadFrequently: true }); // 添加willReadFrequently属性
        
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
                result6_1_2: "不符合《绿色建筑评价标准》（2024版）6.1.2要求，场地人行出入口500m内无公共交通站点。建设单位需提供专用接驳车。",
                result6_2_1: "不符合《绿色建筑评价标准》（2024版）6.2.1要求，场地周边无公共交通站点，总得分为0分。",
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
            result6_1_2: `${conclusion.score6_1_2}《绿色建筑评价标准》（2024版）6.1.2要求。${conclusion.distanceText}。`,
            result6_2_1: `按照《绿色建筑评价标准》（2024版）6.2.1评分，总得分为${conclusion.totalScore}分，其中：
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
        
        
        // 添加地图上的浮动提示
        const mapContainers = [
            document.getElementById('baidu-map-container'),
            document.getElementById('gaode-map-container')
        ];
        
        mapContainers.forEach(container => {
            if (container && !container.querySelector('.map-overlay-tip')) {
                const overlayTip = document.createElement('div');
                overlayTip.className = 'map-overlay-tip';
                overlayTip.style.cssText = 'position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); background-color:rgba(0,0,0,0.6); color:white; padding:8px 12px; border-radius:4px; z-index:1000; pointer-events:none; transition:opacity 0.5s;';
                overlayTip.innerHTML = '点击地图任意位置选择项目地点';
                
                // 创建一个容器用于控制位置
                const tipContainer = document.createElement('div');
                tipContainer.style.cssText = 'position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:999;';
                tipContainer.appendChild(overlayTip);
                container.appendChild(tipContainer);
                
                // 3秒后淡出提示
                setTimeout(() => {
                    overlayTip.style.opacity = '0';
                    // 完全淡出后移除DOM元素
                    setTimeout(() => {
                        try {
                            if (tipContainer.parentNode) {
                                tipContainer.parentNode.removeChild(tipContainer);
                            }
                        } catch (e) {
                            console.error("移除提示元素失败:", e);
                        }
                    }, 500);
                }, 3000);
            }
        });
        
        // 添加剪贴板粘贴支持
        setupClipboardPasteSupport();
    });
    
    // 设置剪贴板粘贴支持
    function setupClipboardPasteSupport() {
        // 1. 创建一个隐藏的粘贴区域
        let pasteArea = document.getElementById('clipboard-paste-area');
        if (!pasteArea) {
            pasteArea = document.createElement('div');
            pasteArea.id = 'clipboard-paste-area';
            pasteArea.contentEditable = true;
            pasteArea.style.cssText = 'position:absolute; left:-9999px; top:-9999px; width:1px; height:1px; opacity:0.01; overflow:hidden;';
            document.body.appendChild(pasteArea);
        }
        
        // 2. 创建一个隐藏的存储粘贴图片的容器
        let clipboardImageContainer = document.getElementById('clipboard-image-container');
        if (!clipboardImageContainer) {
            clipboardImageContainer = document.createElement('div');
            clipboardImageContainer.id = 'clipboard-image-container';
            clipboardImageContainer.style.cssText = 'display:none;';
            document.body.appendChild(clipboardImageContainer);
        }
        
        // 存储剪贴板图片的全局变量
        window.clipboardImageData = null;
        
        // 3. 添加全局粘贴事件监听
        document.addEventListener('paste', function(e) {
            console.log("检测到粘贴操作");
            
            // 如果用户在输入框中粘贴，不拦截
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // 检查是否有图片
            const items = e.clipboardData.items;
            let imageItem = null;
            
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    imageItem = items[i];
                    break;
                }
            }
            
            // 如果有图片，处理它
            if (imageItem) {
                e.preventDefault(); // 阻止默认粘贴行为
                
                const blob = imageItem.getAsFile();
                const reader = new FileReader();
                reader.onload = function(event) {
                    // 保存图片数据
                    window.clipboardImageData = event.target.result;
                    
                    // 清空之前的图片
                    clipboardImageContainer.innerHTML = '';
                    
                    // 显示预览
                    const previewImg = document.createElement('img');
                    previewImg.src = window.clipboardImageData;
                    previewImg.style.cssText = 'max-width: 200px; max-height: 120px; border: 1px solid #ccc; margin: 10px; border-radius: 4px;';
                    
                    // 创建提示文本
                    const infoText = document.createElement('div');
                    infoText.textContent = '已从剪贴板获取地图图片，导出时将优先使用';
                    infoText.style.cssText = 'color: green; font-size: 12px; margin-bottom: 2px;';
                    
                    // 创建清除按钮
                    const clearBtn = document.createElement('button');
                    clearBtn.textContent = '清除图片';
                    clearBtn.className = 'text-sm px-2 py-1 text-gray-600 border border-gray-300 rounded hover:bg-gray-100';
                    clearBtn.onclick = function() {
                        window.clipboardImageData = null;
                        clipboardImageContainer.innerHTML = '';
                        clipboardImageContainer.style.display = 'none';
                    };
                    
                    // 创建预览容器
                    const previewContainer = document.createElement('div');
                    previewContainer.style.cssText = 'display: flex; flex-direction: column; align-items: center; margin: 10px 0;';
                    previewContainer.appendChild(infoText);
                    previewContainer.appendChild(previewImg);
                    previewContainer.appendChild(clearBtn);
                    
                    // 添加到容器
                    clipboardImageContainer.appendChild(previewContainer);
                    clipboardImageContainer.style.display = 'block';
                    
                    // 找到适当的位置显示预览
                    const resultsContainer = document.querySelector('.results-container') || document.getElementById('result-body');
                    if (resultsContainer) {
                        resultsContainer.parentNode.insertBefore(clipboardImageContainer, resultsContainer);
                    } else {
                        // 如果找不到结果容器，就添加到导出按钮旁边
                        const exportBtn = document.getElementById('export-btn');
                        if (exportBtn && exportBtn.parentNode) {
                            exportBtn.parentNode.insertBefore(clipboardImageContainer, exportBtn.nextSibling);
                        } else {
                            // 最后尝试添加到页面底部
                            document.body.appendChild(clipboardImageContainer);
                        }
                    }
                    
                    alert('已获取剪贴板图片，导出时将优先使用此图片作为地图截图');
                };
                reader.readAsDataURL(blob);
            }
        });
    
    }

    // 全局函数，供高德地图API回调
    window.initGaodeMap = initGaodeMap;
    
    // 搜索高德地图
    function searchGaodeMap(address) {
        if (!gaodeMapInstance) {
            console.error("高德地图实例不存在，尝试重新初始化");
            alert("高德地图未初始化，请刷新页面重试");
            document.getElementById('loading').style.display = 'none';
            // 尝试重新加载高德地图
            loadGaodeMapScript();
            return;
        }
        
        try {
            console.log("开始搜索高德地图地址:", address);
            
            // 加载地理编码插件
            AMap.plugin(['AMap.Geocoder'], function() {
                try {
                    console.log("AMap.Geocoder插件加载中");
                    
                    // 创建高德地图地理编码实例
                    const geocoder = new AMap.Geocoder();
                    
                    // 将地址解析成经纬度
                    geocoder.getLocation(address, function(status, result) {
                        console.log("高德地图地址解析结果:", status, result);
                        
                        if (status === 'complete' && result.info === 'OK') {
                            // 获取第一个地址的位置
                            const location = result.geocodes[0].location;
                            console.log("解析到的位置:", location);
                            
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
                            alert("未找到该地址，请输入更精确的地址");
                            document.getElementById('loading').style.display = 'none';
                        }
                    });
                } catch (error) {
                    console.error("创建地理编码实例失败:", error);
                    document.getElementById('loading').style.display = 'none';
                    alert("搜索地址时出错: " + error.message);
                }
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
            console.log("开始搜索高德地图周边公交站:", location);
            
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
            
            // 加载周边搜索插件
            AMap.plugin(['AMap.PlaceSearch'], function() {
                try {
                    console.log("AMap.PlaceSearch插件加载中");
                    
                    // 创建公交站点搜索实例
                    const placeSearch = new AMap.PlaceSearch({
                        pageSize: 50,
                        type: '公交车站|地铁站',
                        pageIndex: 1,
                        city: '全国',
                        radius: 800,
                        autoFitView: false
                    });
                    
                    console.log("开始周边搜索，中心点:", [location.lng, location.lat]);
                    
                    // 周边搜索
                    placeSearch.searchNearBy('', [location.lng, location.lat], 800, function(status, result) {
                        document.getElementById('loading').style.display = 'none';
                        
                        console.log("高德地图周边搜索结果:", status, result);
                        
                        if (status === 'complete' && result.info === 'OK') {
                            const pois = result.poiList.pois;
                            console.log("找到POI数量:", pois ? pois.length : 0);
                            
                            if (!pois || pois.length === 0) {
                                document.getElementById('result-count').textContent = '未找到周边800米内的公交站和地铁站，请尝试其他地点';
                                return;
                            }
                            
                            // 处理搜索结果
                            processGaodeSearchResults(pois, location);
                        } else {
                            console.error("高德地图搜索周边公交站失败:", result);
                            document.getElementById('result-count').textContent = '未找到周边公交站点，请尝试其他地点或切换百度地图';
                        }
                    });
                } catch (error) {
                    console.error("创建周边搜索实例失败:", error);
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('result-count').textContent = '搜索周边公交站点失败，请刷新页面重试';
                }
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
            console.log("处理高德地图搜索结果，共", pois.length, "个POI");
            
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
            if (!resultBody) {
                console.error("未找到结果表格元素 'result-body'");
                return;
            }
            resultBody.innerHTML = '';
            
            // 更新结果计数
            const resultCount = document.getElementById('result-count');
            if (!resultCount) {
                console.error("未找到结果计数元素 'result-count'");
                return;
            }
            
            // 处理有效的POI
            let validPois = pois.filter(poi => poi && poi.location);
            console.log("有效POI数量:", validPois.length);
            
            // 为所有POI添加距离属性(确保为数值类型用于排序)
            validPois.forEach(poi => {
                if (typeof poi.distance === 'string') {
                    poi.distance = parseInt(poi.distance, 10) || 0;
                } else if (typeof poi.distance !== 'number') {
                    poi.distance = 0;
                }
            });
            
            // 按距离排序
            validPois.sort((a, b) => a.distance - b.distance);
            
            // 记录原始数量
            const originalCount = validPois.length;
            
            // 如果POI超过10个，只保留前10个
            if (validPois.length > 10) {
                validPois = validPois.slice(0, 10);
                resultCount.textContent = `共找到 ${originalCount} 个交通站点，显示最近的 10 个`;
            } else {
                resultCount.textContent = `共找到 ${validPois.length} 个交通站点`;
            }
            
            // 处理筛选后的POI
            validPois.forEach((poi, index) => {
                // 获取坐标点
                const poiLocation = poi.location;
                
                // 确保距离始终为字符串类型
                const distance = typeof poi.distance === 'number' ? String(poi.distance) : (poi.distance || '0');
                
                // 获取类型名称
                const typeName = poi.type && poi.type.includes('地铁') ? '地铁站' : '公交站';
                
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
                    distance: distance, // 确保是字符串
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
            const exportBtn = document.getElementById('export-btn');
            const applyScoreBtn = document.getElementById('apply-score-btn'); // <-- 获取应用得分按钮
            if (exportBtn) {
                exportBtn.disabled = false;
                // 添加导出按钮点击事件
                exportBtn.onclick = executeMapScreenshot;
            }
            if (applyScoreBtn) { // <-- 启用应用得分按钮
                applyScoreBtn.disabled = false;
            }
            
            // 生成评价结论
            generateConclusion();
            
        } catch (error) {
            console.error("处理高德地图搜索结果失败:", error);
            document.getElementById('result-count').textContent = '处理搜索结果时出错';
        }
    }
    
    // 执行地图截图并处理后续操作 (改进版)
    function performScreenshotCapture(conclusion, preloadedMapImage = null) {
        // 如果已经有预加载的地图图片(静态图API)，就直接使用
        if (preloadedMapImage) {
            console.log("使用预加载的静态地图图像");
            processMapImageAndSendReport(preloadedMapImage, conclusion);
            return;
        }
        
        // 否则使用html2canvas截图
        createMapScreenshot().then(mapImageData => {
            // 检查图片数据是否有效
            if (!mapImageData || mapImageData.length < 1000) {
                console.error("生成的地图截图数据无效或过小");
                throw new Error("地图截图生成失败");
            }
            
            // 使用截图进行后续处理
            processMapImageAndSendReport(mapImageData, conclusion);
        }).catch(error => {
            // 隐藏加载中
            document.getElementById('loading').style.display = 'none';
            console.error('地图截图创建失败:', error);
            alert('地图截图创建失败: ' + error.message);
        });
    }

        // 处理地图图像并发送报告
        async function processMapImageAndSendReport(mapImageData, conclusion) {
            console.log("地图图像数据生成完成，准备处理报告 (外部JS - 已恢复)"); // 修改标识
            
            // <<< 恢复此函数内的所有逻辑 >>>
            
            try {
                // 显示加载中提示
                document.getElementById('loading').style.display = 'block';
                
                // 获取项目信息
                const urlParams = new URLSearchParams(window.location.search);
                console.log("URL参数:", window.location.search);
                console.log("URL路径:", window.location.pathname);
                
                // 从URL路径中提取项目ID - 格式通常是 /project/{project_id}
                let projectIdFromPath = null;
                const pathMatch = window.location.pathname.match(/\/project\/(\d+)/);
                if (pathMatch && pathMatch[1]) {
                    projectIdFromPath = pathMatch[1];
                }
                console.log("从URL路径提取的项目ID:", projectIdFromPath);
                
                // 从URL参数中获取项目ID
                const projectIdFromUrl = urlParams.get('project_id');
                console.log("从URL参数获取的项目ID:", projectIdFromUrl);
                
                // 从隐藏字段获取项目ID
                const projectIdFromElement = document.getElementById('current-project-id')?.value;
                const transportProjectId = document.getElementById('transport-project-id')?.value;
                console.log("从页面元素获取的项目ID (current-project-id):", projectIdFromElement);
                console.log("从页面元素获取的项目ID (transport-project-id):", transportProjectId);
                
                // 优先使用路径中的ID，然后是URL参数，然后是transport-project-id，最后是current-project-id
                const projectId = projectIdFromPath || projectIdFromUrl || transportProjectId || projectIdFromElement;
                console.log("最终使用的项目ID:", projectId);
                
                let projectInfo = {};
                
                try {
                    if (projectId) {
                        console.log("正在通过API获取项目信息...");
                        const projectInfoResponse = await fetch(`/api/project_info?project_id=${projectId}`);
                        
                        if (projectInfoResponse.ok) {
                            projectInfo = await projectInfoResponse.json();
                            console.log("成功获取项目信息:", projectInfo);
                        } else {
                            console.error("获取项目信息失败:", projectInfoResponse.status, projectInfoResponse.statusText);
                            try {
                                const errorText = await projectInfoResponse.text();
                                console.error("错误详情:", errorText);
                            } catch (e) {
                                console.error("无法获取错误详情:", e);
                            }
                        }
                    } else {
                        alert("未提供项目ID，无法获取项目信息!");
                        return;
                    }
                } catch (error) {
                    console.error("获取项目信息时发生错误:", error);
                }

                // 准备传递给后端的数据
                const data = {
                    address: window.address || '',
                    stations: window.stations || [],
                    mapImage: mapImageData,
                    conclusion: conclusion,
                    project_id: projectId,
                    // 将项目信息整体传递，保留原始结构
                    project_info: projectInfo
                };
                
                console.log("发送到后端的数据:", JSON.stringify(data));
                
                // 发送数据到后端
                const response = await fetch('/generate_transport_report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                // 检查响应内容类型
                const contentType = response.headers.get('Content-Type');
                console.log("响应内容类型:", contentType);
                
                if (response.ok) {
                    // 检查是否是直接文件下载（DOCX文件类型）
                    if (contentType && contentType.includes('application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
                        console.log("接收到直接文件下载响应");
                        // 获取文件名
                        let filename = "公共交通站点分析报告.docx";
                        const contentDisposition = response.headers.get('Content-Disposition');
                        console.log("Content-Disposition头部:", contentDisposition);
                        
                        if (contentDisposition) {
                            // 处理标准格式: attachment; filename="filename.docx"
                            let filenameMatch = contentDisposition.match(/filename="?([^\"]*)"?/i);
                            if (filenameMatch && filenameMatch[1]) {
                                filename = filenameMatch[1];
                            }
                            
                            // 处理UTF-8编码格式: attachment; filename*=UTF-8''encoded-filename
                            filenameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]*)/i);
                            if (filenameMatch && filenameMatch[1]) {
                                try {
                                    // 解码URL编码的文件名
                                    filename = decodeURIComponent(filenameMatch[1]);
                                    console.log("解码后的文件名:", filename);
                                } catch (e) {
                                    console.error("解码文件名失败:", e);
                                }
                            }
                        }
                        
                        // 确保文件名以.docx结尾
                        if (!filename.toLowerCase().endsWith('.docx')) {
                            filename += '.docx';
                        }
                        
                        // 获取文件内容的blob
                        const blob = await response.blob();
                        
                        // 创建下载链接
                        const downloadUrl = window.URL.createObjectURL(blob);
                        const downloadLink = document.createElement('a');
                        downloadLink.href = downloadUrl;
                        downloadLink.download = filename;
                        downloadLink.style.display = 'none';
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        
                        // 清理
                        setTimeout(() => {
                            document.body.removeChild(downloadLink);
                            window.URL.revokeObjectURL(downloadUrl);
                        }, 100);
                        
                        console.log("报告生成成功，正在下载", filename);
                    } else {
                        // 处理JSON响应（兼容旧方式）
                        const result = await response.json();
                        console.log("后端响应:", result);
                        
                        if (result.success && result.file_url) {
                            // 下载报告 - 在新标签页中打开
                            const downloadLink = document.createElement('a');
                            downloadLink.href = result.file_url;
                            downloadLink.target = '_blank';  // 在新标签页打开
                            downloadLink.rel = 'noopener noreferrer';  // 安全性设置
                            downloadLink.click();  // 触发点击
                            console.log("报告生成成功，正在下载...", result.file_url);
                        } else {
                            alert("生成报告失败: " + (result.error || "未知错误"));
                        }
                    }
                } else {
                    console.error("请求失败:", response.status, response.statusText);
                    alert("请求失败，状态码: " + response.status);
                    
                    try {
                        const errorText = await response.text();
                        console.error("错误详情:", errorText);
                    } catch (e) {
                        console.error("无法获取错误详情:", e);
                    }
                }
                
            } catch (error) {
                console.error("生成报告时发生错误 (外部JS - 已恢复):", error);
                 alert("生成报告时发生错误: " + error.message);
            } finally {
                // 隐藏加载中提示
                 document.getElementById('loading').style.display = 'none';
            }
           
        }
    
    // --- 新增：应用得分到项目 --- 
    async function applyTransportScoresToProject() {
        console.log("开始应用公共交通分析得分到项目");
        const applyBtn = document.getElementById('apply-score-btn');
        applyBtn.disabled = true; // 防止重复点击
        applyBtn.textContent = '应用中...';

        try {
            // 1. 获取项目ID
            const projectId = document.getElementById('transport-project-id')?.value || getCurrentProjectId();
            if (!projectId) {
                throw new Error("无法获取当前项目ID");
            }

            // 2. 获取评价结论数据
            const conclusion612Text = document.getElementById('conclusion-6-1-2')?.textContent || '';

            const totalScoreText = document.getElementById('conclusion-total-score')?.textContent || '0 分';
            const is612Achieved = document.getElementById('status-indicator-6-1-2')?.classList.contains('bg-green-500');

            const score621 = parseFloat(totalScoreText.replace(' 分', '')) || 0;
            const isAchieved612 = is612Achieved ? '是' : '否';
            const isAchieved621 = score621 > 0 ? '是' : '否'; // 如果有得分，则视为达标
            const conclusion621Text = score621 > 0 ? '满足要求，详见公共交通站点分析报告' : '';
            console.log("准备更新数据:", {
                projectId,
                clause_6_1_2: { isAchieved: isAchieved612, technicalMeasures: conclusion612Text },
                clause_6_2_1: { score: score621, isAchieved: isAchieved621, technicalMeasures: conclusion621Text }
            });

            // 3. 调用 updateDatabaseScore 更新数据库
            // 更新 6.1.2 (这是一个评价项，没有分数，我们将isAchieved和结论存入)
            await updateDatabaseScore("6.1.2", 0, isAchieved612, conclusion612Text);
            console.log("条文 6.1.2 更新成功");

            // 更新 6.2.1
            await updateDatabaseScore("6.2.1", score621, isAchieved621, conclusion621Text);
            console.log("条文 6.2.1 更新成功");

            Toastify({
                text: '得分已成功应用到项目！',
                duration: 3000,
                gravity: 'top',
                position: 'right',
                style: {
                    background: 'linear-gradient(to right, #00b09b, #96c93d)'
                }
            }).showToast();

        } catch (error) {
            console.error("应用得分到项目时出错:", error);
            Toastify({
                text: `应用得分失败: ${error.message}`,
                duration: 3000,
                gravity: 'top',
                position: 'right',
                style: {
                    background: 'linear-gradient(to right, #ff5f6d, #ffc371)'
                }
            }).showToast();
        } finally {
            applyBtn.disabled = false; // 恢复按钮
            applyBtn.textContent = '应用得分到项目';
        }
    }
    