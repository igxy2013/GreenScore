/**
 * 太阳能光伏发电量计算工具
 * 基于NASA POWER API数据
 */

// 定义全局变量，用于存储地图对象
window.mapObj = null;

// 定义百度地图API加载完成后的回调函数
window.baiduMapLoaded = function() {
    console.log('百度地图API加载完成回调被触发');
    startApp();
};

// 获取项目地点信息
async function getProjectLocation(projectId) {
    if (!projectId) return null;
    
    try {
        // 调用API获取项目信息
        const response = await fetch(`/api/project_info?project_id=${projectId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        // 返回项目地点
        console.log('获取到项目地点信息:', data);
        return data.项目地点 || null;
    } catch (error) {
        console.error('获取项目地点信息失败:', error);
        return null;
    }
}

// 获取当前项目ID和标准信息
function getProjectInfo() {
    try {
        // 直接从当前页面获取项目ID和标准
        const projectIdElement = document.getElementById('current-project-id');
        const projectStandardElement = document.getElementById('current-project-standard');
        
        if (projectIdElement) {
            return {
                projectId: projectIdElement.value,
                projectStandard: projectStandardElement ? projectStandardElement.value : ''
            };
        }
    } catch (e) {
        console.error('获取项目信息失败:', e);
    }
    return { projectId: null, projectStandard: null };
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
        map.centerAndZoom(point, 15);
        map.enableScrollWheelZoom(false);
        map.disableScrollWheelZoom(); // 使用更强制的禁用方法
        
        // 设置地图区域的鼠标样式为默认箭头
        document.getElementById("map").style.cursor = "default";
        
        // 修改DOM事件监听器，只在特定情况下阻止滚轮事件，允许正常页面滚动
        const mapContainer = document.getElementById("map");
        mapContainer.addEventListener('wheel', function(e) {
            // 只有在按下Ctrl键时才阻止事件（模拟缩放操作）
            // 或者如果用户似乎正在尝试缩放地图（例如使用触控板的捏合手势）
            if (e.ctrlKey || e.deltaMode === 0 && Math.abs(e.deltaY) < 10) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
            // 正常滚动页面时不干预，事件会自然冒泡
        }, { passive: false });
        
        // 添加鼠标按下事件，防止拖拽滚动页面
        mapContainer.addEventListener('mousedown', function(e) {
            // 阻止地图区域的鼠标按下事件冒泡，避免拖拽地图时影响页面滚动
            e.stopPropagation();
        });
        
        // 添加控件
        map.addControl(new BMap.NavigationControl());
        map.addControl(new BMap.ScaleControl());
        
        // 创建自定义图标 - 使用代理API加载图标，确保不直接访问百度服务器
        var myIcon = new BMap.Icon("/api/map_proxy?service_path=images/marker_red.png", new BMap.Size(39, 50), {
            anchor: new BMap.Size(10, 27)  // 调整锚点位置到图标中心
        });
        
        // 创建标记，使用自定义图标
        var marker = new BMap.Marker(point, {icon: myIcon});
        map.addOverlay(marker);

        // 初始化海拔显示为待选择
        document.getElementById("elevation").textContent = "请选择或搜索位置";
        
        // 点击地图更新坐标和地点信息
        map.addEventListener("click", function(e) {
            marker.setPosition(e.point);
            document.getElementById("longitude").textContent = e.point.lng.toFixed(6);
            document.getElementById("latitude").textContent = e.point.lat.toFixed(6);
            
            // 使用逆地理编码获取地点名称
            var geoc = new BMap.Geocoder();
            geoc.getLocation(e.point, function(rs){
                if (rs) {
                    var addComp = rs.addressComponents;
                    var location = addComp.province + addComp.city + addComp.district + addComp.street + addComp.streetNumber;
                    document.getElementById("location").value = location;
                    
                    // 获取海拔数据
                    getElevation(e.point.lat, e.point.lng);
                }
            });
        });
        
        // 搜索位置按钮事件
        document.getElementById("searchLocation").addEventListener("click", async function() {
            var locationValue = document.getElementById("location").value;
            if (locationValue) {
                // 显示加载提示
                const annualRadiationEl = document.getElementById("annualRadiation");
                const annualGenerationEl = document.getElementById("annualGeneration");
                const resultsEl = document.getElementById("results");

                annualRadiationEl.textContent = "查询中...";
                annualGenerationEl.textContent = "查询中...";
                // 确保在开始查询时，如果之前有图表，先清除或显示加载状态
                if (window.radiationChart && typeof window.radiationChart.destroy === 'function') {
                    window.radiationChart.destroy();
                }
                if (window.generationChart && typeof window.generationChart.destroy === 'function') {
                    window.generationChart.destroy();
                }
                // 清空图表容器，或者放一个加载指示器
                document.getElementById('radiationChart').innerHTML = '';
                document.getElementById('generationChart').innerHTML = '';

                resultsEl.style.display = "grid";

                var myGeo = new BMap.Geocoder();
                // Promisify BMap.Geocoder.getPoint
                const getPointPromise = (locationAddr) => {
                    return new Promise((resolve, reject) => {
                        myGeo.getPoint(locationAddr, function(point) {
                            if (point) {
                                resolve(point);
                            } else {
                                reject(new Error("未找到该地点: " + locationAddr));
                            }
                        }/*, city*/); // The third argument for getPoint is city, often same as location for broader search
                    });
                };

                try {
                    const point = await getPointPromise(locationValue);
                    
                    map.centerAndZoom(point, 15);
                    // 确保地图禁用滚轮缩放功能
                    map.enableScrollWheelZoom(false); 
                    map.disableScrollWheelZoom();
                    
                    marker.setPosition(point);
                    document.getElementById("longitude").textContent = point.lng.toFixed(6);
                    document.getElementById("latitude").textContent = point.lat.toFixed(6);
                    
                    // 获取海拔数据 (already async, can run in parallel or awaited if needed before solar)
                    getElevation(point.lat, point.lng); 
                    
                    const year = document.getElementById("year").value;
                    
                    // 调用 getSolarRadiationData 并等待结果
                    const monthlyData = await getSolarRadiationData(point.lat, point.lng, year);
                    
                    // 获取计算发电量所需的参数
                    const panelAreaInput = document.getElementById('panelArea');
                    const systemEfficiencyInput = document.getElementById('systemEfficiency');
                    const panelConversionEfficiencyInput = document.getElementById('panelConversionEfficiency');

                    let panelArea = parseFloat(panelAreaInput.value);
                    if (isNaN(panelArea) || panelArea <= 0) {
                        // alert("请输入有效的光伏板面积 (大于0的数字)。");
                        // panelAreaInput.focus();
                        // annualRadiationEl.textContent = "数据错误"; // Or revert to initial state
                        // annualGenerationEl.textContent = "数据错误";
                        // resultsEl.style.display = "none"; // Hide results if input is invalid
                        // return; 
                        // For now, let's proceed with a default or let updateCharts handle it if area is 0
                         panelArea = 0; // Or a sensible default, or rely on updateCharts to show 0 generation
                    }
                    
                    const systemEfficiency = parseFloat(systemEfficiencyInput.value) || 80; // Default from HTML
                    const panelConversionEfficiency = parseFloat(panelConversionEfficiencyInput.value) || 22;
                    
                    // 更新图表和年度数据，updateCharts 内部会处理DOM更新
                    updateCharts(monthlyData, panelArea, systemEfficiency, panelConversionEfficiency);

                } catch (error) {
                    console.error("搜索位置或获取太阳能数据时出错:", error);
                    alert(error.message || "处理请求时发生错误，请稍后重试。");
                    annualRadiationEl.textContent = "--"; // Revert to initial state or error state
                    annualGenerationEl.textContent = "--";
                    resultsEl.style.display = "none"; // Hide results on error
                }
            } else {
                alert("请输入项目地点进行查询。");
            }
        });
        
        return {
            map: map,
            marker: marker
        };
    } catch (error) {
        console.error('初始化地图时出错:', error);
        const mapContainer = document.getElementById("map");
        if (mapContainer) {
            mapContainer.innerHTML = `<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图初始化错误: ${error.message}</div>`;
        }
        return null;
    }
}

// 获取海拔数据
async function getElevation(lat, lng) {
    // 显示加载状态
    document.getElementById("elevation").textContent = '正在获取...';
    
    try {
        // 使用Open-Elevation API获取真实海拔数据
        // 这是一个开源的海拔数据服务，提供全球海拔数据
        const url = `/api/elevation?lat=${lat}&lng=${lng}`;
        
        // 调用后端代理API，避免CORS问题
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`API响应错误: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.elevation !== undefined) {
            // 显示真实海拔数据
            document.getElementById("elevation").textContent = data.elevation.toFixed(0) + ' m';
            return;
        } 
        
        // 如果后端API失败，尝试其他方法获取海拔
        // 使用Google Maps Elevation API (需要代理以避免客户端暴露API密钥)
        const googleUrl = `/api/google_elevation?lat=${lat}&lng=${lng}`;
        const googleResponse = await fetch(googleUrl);
        
        if (!googleResponse.ok) {
            throw new Error(`Google API响应错误: ${googleResponse.status}`);
        }
        
        const googleData = await googleResponse.json();
        
        if (googleData.elevation !== undefined) {
            document.getElementById("elevation").textContent = googleData.elevation.toFixed(0) + ' m';
            return;
        }
        
        throw new Error('无法获取真实海拔数据');
    } catch (error) {
        console.error('获取海拔数据失败:', error);
        document.getElementById("elevation").textContent = '获取失败';
        
        // 添加重试按钮
        const elevationElement = document.getElementById("elevation");
        if (!elevationElement.nextElementSibling || !elevationElement.nextElementSibling.classList.contains('retry-button')) {
            const retryButton = document.createElement('button');
            retryButton.textContent = '重试';
            retryButton.className = 'ml-2 px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 retry-button';
            retryButton.onclick = () => getElevation(lat, lng);
            elevationElement.parentNode.appendChild(retryButton);
        }
    }
}

// 从NASA POWER API获取太阳能辐射数据
async function getSolarRadiationData(lat, lng, year) {
    // 构建API请求URL
    const url = `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=${lng}&latitude=${lat}&start=${year}0101&end=${year}1231&format=JSON`;
    
    try {
        console.log(`正在从NASA POWER API获取数据，经度: ${lng}, 纬度: ${lat}, 年份: ${year}`);
        
        // 设置请求超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000); // 20秒超时
        
        // 实际项目中应该使用fetch调用真实API
        const response = await fetch(url, {
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'GreenScore-SolarCalculator/1.0'
            }
        });
        
        // 清除超时计时器
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`NASA API响应错误: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // 验证API返回的数据结构
        if (!data || !data.properties || !data.properties.parameter || !data.properties.parameter.ALLSKY_SFC_SW_DWN) {
            console.error('NASA API返回的数据结构不符合预期:', data);
            throw new Error('NASA API返回的数据结构不完整');
        }
        
        // 处理NASA POWER API返回的数据
        // API返回的是每日数据，需要转换为月度数据
        const monthNames = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"];
        const daysInMonth = [31, year % 4 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        
        // 初始化月度数据数组
        const monthlyData = monthNames.map((month, index) => ({
            month: month,
            radiation: 0,
            days: daysInMonth[index]
        }));
        
        // 从API响应中提取数据
        const radiationData = data.properties.parameter.ALLSKY_SFC_SW_DWN;
        
        // 检查radiationData是否为空对象
        if (Object.keys(radiationData).length === 0) {
            console.error('NASA API返回的辐射数据为空');
            throw new Error('未找到辐射数据');
        }
        
        console.log(`成功获取NASA数据，收到${Object.keys(radiationData).length}天的记录`);
        
        // 遍历每一天的数据
        Object.keys(radiationData).forEach(dateStr => {
            // 日期格式: YYYYMMDD
            const month = parseInt(dateStr.substring(4, 6)) - 1; // 月份从0开始
            const radiation = radiationData[dateStr]; // 单位: kWh/m²/day (直接使用,无需转换)
            
            // 处理无效数据
            if (isNaN(radiation) || radiation < 0) {
                console.warn(`日期${dateStr}的辐射数据无效: ${radiation}`);
                return; // 跳过无效数据
            }
            
            // 累加到对应月份 (单位已是 kWh/m²/day)
            monthlyData[month].radiation += radiation;
        });
        
        console.log('月度数据处理完成', monthlyData);
        return monthlyData;
    } catch (error) {
        console.error("获取太阳能辐射数据失败:", error);
        
        // 处理特定错误类型
        if (error.name === 'AbortError') {
            console.error("NASA API请求超时");
            alert("NASA数据请求超时，将使用模拟数据进行计算");
        } else if (error.message.includes('NASA API返回的数据结构不完整')) {
            console.error("NASA API数据结构错误");
            alert("NASA数据格式异常，将使用模拟数据进行计算");
        } else {
            alert("获取NASA辐射数据失败，将使用模拟数据进行计算");
        }
        
        // 如果API调用失败，返回模拟数据
        const monthlyData = [
            { month: "一月", radiation: 85.2, days: 31 },
            { month: "二月", radiation: 92.4, days: 28 },
            { month: "三月", radiation: 120.3, days: 31 },
            { month: "四月", radiation: 135.6, days: 30 },
            { month: "五月", radiation: 155.8, days: 31 },
            { month: "六月", radiation: 162.4, days: 30 },
            { month: "七月", radiation: 170.2, days: 31 },
            { month: "八月", radiation: 165.7, days: 31 },
            { month: "九月", radiation: 140.3, days: 30 },
            { month: "十月", radiation: 115.6, days: 31 },
            { month: "十一月", radiation: 90.4, days: 30 },
            { month: "十二月", radiation: 80.5, days: 31 }
        ];
        
        console.log('使用模拟数据继续计算', monthlyData);
        return monthlyData;
    }
}

// 计算发电量
function calculateGeneration(radiation, area, systemEfficiency, panelConversionEfficiencyInput) {
    // systemEfficiency: 系统综合效率 (%)
    // panelConversionEfficiencyInput: 光伏组件转换效率 (%)

    const systemEfficiencyDecimal = systemEfficiency / 100;
    const panelConversionEfficiencyDecimal = panelConversionEfficiencyInput / 100; 
    
    // 计算发电量 (kWh) = 辐射量 (kWh/m²) * 面积 (m²) * 光伏组件转换效率 * 系统综合效率
    return radiation * area * panelConversionEfficiencyDecimal * systemEfficiencyDecimal;
}

// 更新图表
function updateCharts(monthlyData, area, efficiency, panelConversionEfficiency) {
    const months = monthlyData.map(item => item.month);
    const radiationValues = monthlyData.map(item => item.radiation);
    const generationValues = monthlyData.map(item => calculateGeneration(item.radiation, area, efficiency, panelConversionEfficiency));
    
    // 计算年度总值
    const annualRadiation = radiationValues.reduce((sum, val) => sum + val, 0);
    const annualGeneration = generationValues.reduce((sum, val) => sum + val, 0);
    
    // 更新显示
    document.getElementById("annualRadiation").textContent = annualRadiation.toFixed(2);
    document.getElementById("annualGeneration").textContent = annualGeneration.toFixed(2);
    
    // 显示结果区域
    document.getElementById("results").style.display = "grid";
    
    // 清除旧图表 - 使用更健壮的实现
    try {
        if (window.radiationChart && typeof window.radiationChart.destroy === 'function') {
            window.radiationChart.destroy();
        } else if (window.radiationChart) {
            console.warn('辐射图表实例存在但没有destroy方法');
            window.radiationChart = null;
        }
    } catch (err) {
        console.error('销毁旧的辐射图表时出错:', err);
        window.radiationChart = null;
    }
    
    try {
        if (window.generationChart && typeof window.generationChart.destroy === 'function') {
            window.generationChart.destroy();
        } else if (window.generationChart) {
            console.warn('发电量图表实例存在但没有destroy方法');
            window.generationChart = null;
        }
    } catch (err) {
        console.error('销毁旧的发电量图表时出错:', err);
        window.generationChart = null;
    }
    
    // 辐射量图表
    const radiationCtx = document.getElementById('radiationChart').getContext('2d');
    window.radiationChart = new Chart(radiationCtx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [{
                label: '月度太阳能辐射量 (kWh/m²)',
                data: radiationValues,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // 发电量图表
    const generationCtx = document.getElementById('generationChart').getContext('2d');
    window.generationChart = new Chart(generationCtx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [{
                label: '月度发电量 (kWh)',
                data: generationValues,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    return {
        annualRadiation,
        annualGeneration,
        monthlyData: monthlyData.map((item, index) => ({
            ...item,
            generation: generationValues[index],
            dailyAvg: item.radiation / item.days
        }))
    };
}

// 更新月度数据表格
function updateMonthlyTable(monthlyData) {
    const tableBody = document.getElementById("monthlyTableBody");
    tableBody.innerHTML = "";
    
    monthlyData.forEach(item => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.month}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.radiation.toFixed(2)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.generation.toFixed(2)}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.dailyAvg.toFixed(2)}</td>
        `;
        tableBody.appendChild(row);
    });
    
    // 显示月度数据表格
    document.getElementById("monthlyData").style.display = "block";
}

// 创建模态窗口图表
function createModalCharts(monthlyData, area, efficiency, panelConversionEfficiency) {
    console.log('开始创建模态窗口图表');
    const months = monthlyData.map(item => item.month);
    const radiationValues = monthlyData.map(item => item.radiation);
    const generationValues = monthlyData.map(item => calculateGeneration(item.radiation, area, efficiency, panelConversionEfficiency));
    
    // 检查是否存在Canvas元素
    const radiationCanvas = document.getElementById('modalRadiationChart');
    const generationCanvas = document.getElementById('modalGenerationChart');
    
    if (!radiationCanvas) {
        console.error('找不到模态窗口辐射图表canvas!');
        return;
    }
    
    if (!generationCanvas) {
        console.error('找不到模态窗口发电量图表canvas!');
        return;
    }
    
    console.log('找到模态窗口Canvas元素');
    
    // 安全地销毁旧图表
    try {
        if (window.modalRadiationChart && typeof window.modalRadiationChart.destroy === 'function') {
            window.modalRadiationChart.destroy();
            console.log('已销毁旧的辐射图表');
        } else if (window.modalRadiationChart) {
            console.warn('辐射图表实例存在但没有destroy方法');
            // 重置图表变量
            window.modalRadiationChart = null;
        }
    } catch (err) {
        console.error('销毁旧的辐射图表时出错:', err);
        // 重置图表变量
        window.modalRadiationChart = null;
    }
    
    try {
        if (window.modalGenerationChart && typeof window.modalGenerationChart.destroy === 'function') {
            window.modalGenerationChart.destroy();
            console.log('已销毁旧的发电量图表');
        } else if (window.modalGenerationChart) {
            console.warn('发电量图表实例存在但没有destroy方法');
            // 重置图表变量
            window.modalGenerationChart = null;
        }
    } catch (err) {
        console.error('销毁旧的发电量图表时出错:', err);
        // 重置图表变量
        window.modalGenerationChart = null;
    }
    
    // 确保canvas处于干净状态，尺寸合适
    const setCanvasSize = (canvas) => {
        const parent = canvas.parentElement;
        if (parent) {
            // 设置正确的高度
            canvas.style.height = '200px';
            canvas.height = 200;
            canvas.width = parent.offsetWidth || 400;
            canvas.style.width = '100%';
            
            // 清除画布
            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
    };
    
    setCanvasSize(radiationCanvas);
    setCanvasSize(generationCanvas);
    
    // 创建新图表
    try {
        // 辐射量图表
        const radiationCtx = radiationCanvas.getContext('2d');
        console.log('创建辐射图表');
        window.modalRadiationChart = new Chart(radiationCtx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: '月度太阳能辐射量 (kWh/m²)',
                    data: radiationValues,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 10,
                            padding: 6,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        titleFont: {
                            size: 11
                        },
                        bodyFont: {
                            size: 10
                        }
                    }
                }
            }
        });
        
        // 发电量图表
        const generationCtx = generationCanvas.getContext('2d');
        console.log('创建发电量图表');
        window.modalGenerationChart = new Chart(generationCtx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: '月度发电量 (kWh)',
                    data: generationValues,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 10
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            boxWidth: 10,
                            padding: 6,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        titleFont: {
                            size: 11
                        },
                        bodyFont: {
                            size: 10
                        }
                    }
                }
            }
        });
        
        // 确保图表正确渲染，使用短延迟触发更新
        setTimeout(() => {
            if (window.modalRadiationChart && typeof window.modalRadiationChart.update === 'function') {
                window.modalRadiationChart.update();
                console.log('辐射图表已更新');
            }
            
            if (window.modalGenerationChart && typeof window.modalGenerationChart.update === 'function') {
                window.modalGenerationChart.update();
                console.log('发电量图表已更新');
            }
        }, 100);
        
    } catch (err) {
        console.error('创建图表时出错:', err);
        showErrorInModal('创建图表时出错: ' + err.message);
        return;
    }
    
    // 填充模态窗口的表格
    fillModalTable(monthlyData);
    
    console.log('模态窗口图表创建完成');
}

// 填充模态窗口的表格
function fillModalTable(monthlyData) {
    console.log('开始填充模态窗口表格，数据:', monthlyData);
    
    // 获取两个表格的tbody元素
    const tableBody1 = document.getElementById("modalMonthlyTableBody1"); // 1-6月
    const tableBody2 = document.getElementById("modalMonthlyTableBody2"); // 7-12月
    
    if (!tableBody1 || !tableBody2) {
        console.error('找不到模态窗口表格体!', {
            tableBody1: document.getElementById("modalMonthlyTableBody1"),
            tableBody2: document.getElementById("modalMonthlyTableBody2"),
            monthlyModalExists: !!document.getElementById("monthlyModal")
        });
        // 如果找不到表格体，尝试延迟重试一次
        setTimeout(() => {
            const retryTableBody1 = document.getElementById("modalMonthlyTableBody1");
            const retryTableBody2 = document.getElementById("modalMonthlyTableBody2");
            if (retryTableBody1 && retryTableBody2) {
                console.log('延迟后找到表格体，重新填充');
                fillModalTableImpl(monthlyData, retryTableBody1, retryTableBody2);
            } else {
                console.error('延迟后仍找不到表格体，放弃填充');
            }
        }, 500);
        return;
    }
    
    fillModalTableImpl(monthlyData, tableBody1, tableBody2);
}

// 实际填充表格的函数
function fillModalTableImpl(monthlyData, tableBody1, tableBody2) {
    console.log('填充表格实现，数据条数:', monthlyData.length);
    
    // 清空表格
    tableBody1.innerHTML = "";
    tableBody2.innerHTML = "";
    
    if (!monthlyData || monthlyData.length === 0) {
        console.error('没有数据可以填充到表格');
        return;
    }
    
    // 确保数据按照月份顺序排序
    const monthsOrder = {
        "一月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6, 
        "七月": 7, "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12
    };
    
    const monthlyDataSorted = [...monthlyData].sort((a, b) => {
        return monthsOrder[a.month] - monthsOrder[b.month];
    });
    
    console.log('排序后的数据:', monthlyDataSorted.map(m => m.month));
    
    // 遍历排序后的数据，分别填充到左右两个表格
    monthlyDataSorted.forEach(item => {
        const monthNum = monthsOrder[item.month];
        
        if (!monthNum) {
            console.warn('无法识别的月份:', item.month);
            return;
        }
        
        // 创建行元素而不是使用HTML字符串
        const row = document.createElement('tr');
        
        // 月份单元格
        const monthCell = document.createElement('td');
        monthCell.className = "px-2 py-2 whitespace-nowrap text-sm text-gray-900";
        monthCell.textContent = item.month;
        row.appendChild(monthCell);
        
        // 太阳能辐射量单元格
        const radiationCell = document.createElement('td');
        radiationCell.className = "px-2 py-2 whitespace-nowrap text-sm text-gray-900 text-right";
        radiationCell.textContent = item.radiation.toFixed(2);
        row.appendChild(radiationCell);
        
        // 发电量单元格
        const generationCell = document.createElement('td');
        generationCell.className = "px-2 py-2 whitespace-nowrap text-sm text-gray-900 text-right";
        generationCell.textContent = item.generation.toFixed(2);
        row.appendChild(generationCell);
        
        // 日均辐射量单元格
        const dailyAvgCell = document.createElement('td');
        dailyAvgCell.className = "px-2 py-2 whitespace-nowrap text-sm text-gray-900 text-right";
        dailyAvgCell.textContent = item.dailyAvg.toFixed(2);
        row.appendChild(dailyAvgCell);
        
        // 根据月份判断填充到哪个表格
        if (monthNum <= 6) {
            // 1-6月填充到左侧表格
            tableBody1.appendChild(row);
        } else {
            // 7-12月填充到右侧表格
            tableBody2.appendChild(row);
        }
    });
    
    console.log('模态窗口表格填充完成，左侧行数:', tableBody1.children.length, '右侧行数:', tableBody2.children.length);
}

// 关闭模态窗口按钮事件
function setupModalCloseEvents() {
    console.log('正在设置模态窗口关闭事件');
    
    // 关闭按钮事件
    const closeModalBtn = document.getElementById("closeMonthlyModal");
    if (closeModalBtn) {
        console.log('找到关闭模态窗口按钮:', closeModalBtn);
        
        // 移除可能存在的旧事件监听器，避免重复绑定
        closeModalBtn.removeEventListener("click", hideMonthlyModal);
        
        // 添加新的事件监听器
        closeModalBtn.addEventListener("click", function(e) {
            console.log('关闭模态窗口按钮被点击');
            e.preventDefault();
            e.stopPropagation();
            hideMonthlyModal();
        });
    } else {
        console.warn("未找到关闭模态窗口按钮元素，将继续尝试");
    }
    
    // 底部关闭按钮事件
    const bottomCloseBtn = document.getElementById("bottomCloseModalBtn");
    if (bottomCloseBtn) {
        console.log('找到底部关闭模态窗口按钮:', bottomCloseBtn);
        
        // 移除可能存在的旧事件监听器
        bottomCloseBtn.removeEventListener("click", hideMonthlyModal);
        
        // 添加新的事件监听器
        bottomCloseBtn.addEventListener("click", function(e) {
            console.log('底部关闭模态窗口按钮被点击');
            e.preventDefault();
            hideMonthlyModal();
        });
    } else {
        console.warn("未找到底部关闭模态窗口按钮元素");
    }
    
    // 点击模态窗口背景时关闭
    const monthlyModal = document.getElementById("monthlyModal");
    if (monthlyModal) {
        // 移除可能存在的旧事件监听器，避免重复绑定
        monthlyModal.removeEventListener("click", modalBackgroundClick);
        
        // 添加新的事件监听器
        monthlyModal.addEventListener("click", modalBackgroundClick);
    } else {
        console.warn("未找到模态窗口元素，将继续尝试");
    }
}

// 处理模态窗口背景点击
function modalBackgroundClick(e) {
    console.log('模态窗口区域被点击', e.target.id, e.currentTarget.id);
    if (e.target === e.currentTarget) {
        console.log('点击了模态窗口背景，关闭模态窗口');
        hideMonthlyModal();
    }
}

// 显示模态窗口
function showMonthlyModal() {
    console.log('显示模态窗口');
    const modal = document.getElementById("monthlyModal");
    console.log('模态窗口元素:', modal);
    if (!modal) {
        console.error('找不到模态窗口元素！');
        return;
    }
    
    // 临时隐藏年度结果卡片
    const resultsElement = document.getElementById("results");
    if (resultsElement && resultsElement.style.display !== "none") {
        console.log('临时隐藏年度结果卡片');
        resultsElement.setAttribute("data-previous-display", resultsElement.style.display); // 保存当前显示状态
        resultsElement.style.display = "none";
    }
    
    console.log('模态窗口当前类名:', modal.className);
    modal.style.display = 'flex';  // 使用flex而不是block，以便应用居中样式
    modal.classList.remove("hidden");
    console.log('移除hidden类后的类名:', modal.className);
    
    // 避免页面滚动
    document.body.style.overflow = "hidden";
    
    // 每次显示模态窗口时，都重新设置关闭事件
    setupModalCloseEvents();
}

// 隐藏模态窗口
function hideMonthlyModal() {
    console.log('隐藏模态窗口');
    const modal = document.getElementById("monthlyModal");
    if (!modal) {
        console.error('找不到模态窗口元素！');
        return;
    }
    
    console.log('隐藏前模态窗口类名:', modal.className);
    modal.style.display = 'none';  // 直接设置display为none
    modal.classList.add("hidden");
    console.log('隐藏后模态窗口类名:', modal.className);
    
    // 恢复之前隐藏的年度结果卡片
    const resultsElement = document.getElementById("results");
    if (resultsElement && resultsElement.hasAttribute("data-previous-display")) {
        console.log('恢复年度结果卡片显示');
        const previousDisplay = resultsElement.getAttribute("data-previous-display");
        if (previousDisplay && previousDisplay !== "none") {
            resultsElement.style.display = previousDisplay;
        }
        resultsElement.removeAttribute("data-previous-display");
    }
    
    // 恢复页面滚动
    document.body.style.overflow = "";
    
    console.log('模态窗口已成功隐藏');
}

// 在模态窗口中显示加载状态
function showLoadingInModal(message = "加载中...") {
    console.log('显示模态窗口加载状态:', message);
    
    // 查找可能存在的loading元素，如果不存在则创建
    let loadingElem = document.getElementById("modalLoading");
    if (!loadingElem) {
        loadingElem = document.createElement("div");
        loadingElem.id = "modalLoading";
        loadingElem.className = "absolute inset-0 flex items-center justify-center bg-white bg-opacity-80 z-10";
        loadingElem.innerHTML = `
            <div class="text-center">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary mb-2"></div>
                <p class="text-gray-700 font-medium" id="modalLoadingText">${message}</p>
            </div>
        `;
        
        // 将loading元素添加到模态窗口内容区域
        const modalContent = document.querySelector("#monthlyModal > div");
        if (modalContent) {
            modalContent.appendChild(loadingElem);
        }
    } else {
        // 更新已有loading元素的消息
        const textElem = loadingElem.querySelector("#modalLoadingText");
        if (textElem) textElem.textContent = message;
        loadingElem.style.display = "flex";
    }
}

// 隐藏模态窗口中的加载状态
function hideLoadingInModal() {
    console.log('隐藏模态窗口加载状态');
    const loadingElem = document.getElementById("modalLoading");
    if (loadingElem) {
        loadingElem.style.display = "none";
    }
}

// 在模态窗口中显示错误信息
function showErrorInModal(errorMessage) {
    console.log('显示模态窗口错误:', errorMessage);
    
    // 查找可能存在的error元素，如果不存在则创建
    let errorElem = document.getElementById("modalError");
    if (!errorElem) {
        errorElem = document.createElement("div");
        errorElem.id = "modalError";
        errorElem.className = "p-4 mb-4 text-red-700 bg-red-100 rounded-lg";
        errorElem.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clip-rule="evenodd"></path>
                </svg>
                <span id="modalErrorText">${errorMessage}</span>
            </div>
            <div class="mt-2">
                <button id="modalErrorRetry" class="px-4 py-2 bg-primary text-white text-sm rounded hover:bg-primary-dark">重试</button>
                <button id="modalErrorUseSimulated" class="ml-2 px-4 py-2 bg-gray-500 text-white text-sm rounded hover:bg-gray-600">使用模拟数据</button>
            </div>
        `;
        
        // 将error元素添加到模态窗口内容区域顶部
        const modalContent = document.querySelector("#monthlyModal > div");
        if (modalContent) {
            // 添加在标题栏之后
            const titleBar = modalContent.querySelector(".flex.justify-between");
            if (titleBar && titleBar.nextSibling) {
                modalContent.insertBefore(errorElem, titleBar.nextSibling);
            } else {
                modalContent.appendChild(errorElem);
            }
            
            // 添加重试按钮点击事件
            const retryBtn = errorElem.querySelector("#modalErrorRetry");
            if (retryBtn) {
                retryBtn.addEventListener("click", function() {
                    errorElem.style.display = "none";
                    // 触发月度详细统计按钮的点击事件
                    document.getElementById("calculateMonthly")?.click();
                });
            }
            
            // 添加使用模拟数据按钮点击事件
            const useSimulatedBtn = errorElem.querySelector("#modalErrorUseSimulated");
            if (useSimulatedBtn) {
                useSimulatedBtn.addEventListener("click", function() {
                    errorElem.style.display = "none";
                    // 使用模拟数据创建图表
                    const area = parseFloat(document.getElementById("panelArea")?.value || '0');
                    const systemEfficiency = parseFloat(document.getElementById("systemEfficiency")?.value || '0');
                    const panelConversionEfficiency = parseFloat(document.getElementById("panelConversionEfficiency")?.value || '22');
                    
                    // 创建模拟数据
                    const simulatedData = [
                        { month: "一月", radiation: 85.2, days: 31 },
                        { month: "二月", radiation: 92.4, days: 28 },
                        { month: "三月", radiation: 120.3, days: 31 },
                        { month: "四月", radiation: 135.6, days: 30 },
                        { month: "五月", radiation: 155.8, days: 31 },
                        { month: "六月", radiation: 162.4, days: 30 },
                        { month: "七月", radiation: 170.2, days: 31 },
                        { month: "八月", radiation: 165.7, days: 31 },
                        { month: "九月", radiation: 140.3, days: 30 },
                        { month: "十月", radiation: 115.6, days: 31 },
                        { month: "十一月", radiation: 90.4, days: 30 },
                        { month: "十二月", radiation: 80.5, days: 31 }
                    ].map(item => ({
                        ...item,
                        generation: calculateGeneration(item.radiation, area, systemEfficiency, panelConversionEfficiency),
                        dailyAvg: item.radiation / item.days
                    }));
                    
                    // 显示图表
                    createModalCharts(simulatedData, area, systemEfficiency, panelConversionEfficiency);
                });
            }
        }
    } else {
        // 更新已有error元素的消息
        const textElem = errorElem.querySelector("#modalErrorText");
        if (textElem) textElem.textContent = errorMessage;
        errorElem.style.display = "block";
    }
}

// 调整Canvas元素尺寸
function resizeCanvasElements(radiationCanvas, generationCanvas) {
    // 获取父容器尺寸
    const container1 = radiationCanvas.parentElement;
    const container2 = generationCanvas.parentElement;
    
    if (container1 && container2) {
        // 设置Canvas尺寸与父容器匹配
        const setCanvasSize = (canvas, container) => {
            const rect = container.getBoundingClientRect();
            // 重置Canvas物理尺寸，确保图表正确绘制
            canvas.width = rect.width;
            canvas.height = rect.height;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
        };
        
        setCanvasSize(radiationCanvas, container1);
        setCanvasSize(generationCanvas, container2);
        
        console.log('Canvas元素尺寸已调整为：', {
            辐射图表: { width: radiationCanvas.width, height: radiationCanvas.height },
            发电量图表: { width: generationCanvas.width, height: generationCanvas.height }
        });
        
        // 如果图表已经创建，触发重绘
        if (window.modalRadiationChart && typeof window.modalRadiationChart.resize === 'function') {
            window.modalRadiationChart.resize();
            console.log('辐射图表已重绘');
        }
        
        if (window.modalGenerationChart && typeof window.modalGenerationChart.resize === 'function') {
            window.modalGenerationChart.resize();
            console.log('发电量图表已重绘');
        }
    }
}

// 监听窗口大小变化，调整图表尺寸
window.addEventListener('resize', debounce(function() {
    const radiationCanvas = document.getElementById('modalRadiationChart');
    const generationCanvas = document.getElementById('modalGenerationChart');
    
    if (radiationCanvas && generationCanvas) {
        resizeCanvasElements(radiationCanvas, generationCanvas);
    }
}, 250));

// 导出函数
window.solarCalculator = {
    initMap,
    getSolarRadiationData,
    calculateGeneration,
    updateCharts,
    updateMonthlyTable,
    createModalCharts,
    showMonthlyModal,
    hideMonthlyModal,
    showLoadingInModal,
    hideLoadingInModal,
    showErrorInModal
};

// 添加测试函数到全局对象，方便在控制台调试
window.testModal = {
    // 显示模态窗口的测试函数
    show: function() {
        console.log('测试显示模态窗口');
        const modal = document.getElementById('monthlyModal');
        if (modal) {
            // 设置display为block
            modal.style.display = 'block';
            console.log('已显示模态窗口');
        } else {
            console.error('找不到模态窗口元素');
        }
    },
    
    // 隐藏模态窗口的测试函数
    hide: function() {
        console.log('测试隐藏模态窗口');
        const modal = document.getElementById('monthlyModal');
        if (modal) {
            // 设置display为none
            modal.style.display = 'none';
            console.log('已隐藏模态窗口');
        } else {
            console.error('找不到模态窗口元素');
        }
    },
    
    // 模态窗口状态检查
    status: function() {
        const modal = document.getElementById('monthlyModal');
        if (modal) {
            console.log('模态窗口状态:', {
                元素: modal,
                显示状态: window.getComputedStyle(modal).display,
                类名: modal.className,
                zIndex: window.getComputedStyle(modal).zIndex,
                位置: modal.getBoundingClientRect()
            });
            
            // 检查模态窗口内的图表元素
            const radiationCanvas = document.getElementById('modalRadiationChart');
            const generationCanvas = document.getElementById('modalGenerationChart');
            console.log('图表Canvas元素状态:', {
                辐射图表: radiationCanvas,
                发电量图表: generationCanvas,
                辐射图表宽高: radiationCanvas ? {
                    width: radiationCanvas.width,
                    height: radiationCanvas.height,
                    clientWidth: radiationCanvas.clientWidth,
                    clientHeight: radiationCanvas.clientHeight
                } : null,
                发电量图表宽高: generationCanvas ? {
                    width: generationCanvas.width,
                    height: generationCanvas.height,
                    clientWidth: generationCanvas.clientWidth,
                    clientHeight: generationCanvas.clientHeight
                } : null
            });
        } else {
            console.error('找不到模态窗口元素');
        }
    }
};

// 防抖函数，限制更新频率
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", function() {
    console.log('页面加载完成');
    
    // 检查百度地图API是否已加载完成
    if (typeof BMap !== 'undefined') {
        // 如果已加载，直接启动应用
        console.log('百度地图API已存在，直接启动应用');
        startApp();
    } else {
        console.log('百度地图API尚未加载，等待加载完成');
        // 否则等待百度地图API加载完成后的回调
        // baiduMapLoaded函数将在API加载完成后被调用
        
        // 添加5秒超时保障
        setTimeout(function() {
            if (typeof BMap === 'undefined') {
                console.error('百度地图API加载超时');
                const mapContainer = document.getElementById("map");
                if (mapContainer) {
                    mapContainer.innerHTML = '<div class="flex items-center justify-center h-full bg-gray-100 text-red-500 font-bold">地图API加载超时，请刷新页面重试</div>';
                }
            }
        }, 5000);
    }
    
    // 开始监听DOM变化
    startObserving();
}, 800); // 给足够时间让页面渲染

// 开始监听DOM变化
function startObserving() {
    // 删除高度监听相关代码，只保留窗口大小变化监听
    window.addEventListener('resize', function() {
        console.log('窗口大小变化');
    });
}

// 启动应用主函数
function startApp() {
    console.log('启动应用...');
    
    // 获取项目信息
    const { projectId } = window.getProjectInfo ? window.getProjectInfo() : { projectId: null };
    
    console.log('当前项目ID:', projectId);
    
    // 初始化地图
    window.mapObj = initMap();
    
    // 如果有项目ID，获取项目地点并自动填充
    if (projectId) {
        getProjectLocation(projectId).then(projectLocation => {
            if (projectLocation && window.mapObj) {
                // 填充地点输入框
                const locationInput = document.getElementById("location");
                if (locationInput) {
                    locationInput.value = projectLocation;
                    
                    // 自动触发地点搜索
                    const searchBtn = document.getElementById("searchLocation");
                    if (searchBtn) {
                        searchBtn.click();
                    }
                }
            }
        });
    }
    
    // 年度汇总按钮事件
    const calculateAnnualBtn = document.getElementById("calculateAnnual");
    if (calculateAnnualBtn) {
        calculateAnnualBtn.addEventListener("click", async function() {
            const lat = parseFloat(document.getElementById("latitude")?.textContent || '0');
            const lng = parseFloat(document.getElementById("longitude")?.textContent || '0');
            const year = document.getElementById("year")?.value || '2023';
            const area = parseFloat(document.getElementById("panelArea")?.value || '0');
            const systemEfficiency = parseFloat(document.getElementById("systemEfficiency")?.value || '0');
            const panelConversionEfficiency = parseFloat(document.getElementById("panelConversionEfficiency")?.value || '22');
            
            if (isNaN(lat) || isNaN(lng)) {
                alert("请先选择或输入有效的地理坐标");
                return;
            }
            
            if (isNaN(area) || area <= 0) {
                alert("请输入有效的太阳能光伏板面积");
                return;
            }
            
            if (isNaN(systemEfficiency) || systemEfficiency <= 0 || systemEfficiency > 100) {
                alert("请输入有效的系统综合效率(0-100%)");
                return;
            }
            
            if (isNaN(panelConversionEfficiency) || panelConversionEfficiency < 0 || panelConversionEfficiency > 100) {
                alert("请输入有效的光伏组件转换效率(0-100%)");
                return;
            }
            
            // 获取太阳能辐射数据
            const monthlyData = await getSolarRadiationData(lat, lng, year);
            if (monthlyData) {
                // 更新图表
                const result = updateCharts(monthlyData, area, systemEfficiency, panelConversionEfficiency);
                // 隐藏月度数据表格
                const monthlyDataElem = document.getElementById("monthlyData");
                if (monthlyDataElem) {
                    monthlyDataElem.style.display = "none";
                }
                
                // 自动滚动到页面底部
                setTimeout(() => {
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                }, 100);
            }
        });
    } else {
        console.error("未找到年度汇总按钮元素");
    }
    
    // 月度详细统计按钮事件
    const calculateMonthlyBtn = document.getElementById("calculateMonthly");
    if (calculateMonthlyBtn) {
        calculateMonthlyBtn.addEventListener("click", async function() {
            console.log('点击了月度详细统计按钮');
            const lat = parseFloat(document.getElementById("latitude")?.textContent || '0');
            const lng = parseFloat(document.getElementById("longitude")?.textContent || '0');
            const year = document.getElementById("year")?.value || '2023';
            const area = parseFloat(document.getElementById("panelArea")?.value || '0');
            const systemEfficiency = parseFloat(document.getElementById("systemEfficiency")?.value || '0');
            const panelConversionEfficiency = parseFloat(document.getElementById("panelConversionEfficiency")?.value || '22');
            
            if (isNaN(lat) || isNaN(lng)) {
                alert("请先选择或输入有效的地理坐标");
                return;
            }
            
            if (isNaN(area) || area <= 0) {
                alert("请输入有效的太阳能光伏板面积");
                return;
            }
            
            if (isNaN(systemEfficiency) || systemEfficiency <= 0 || systemEfficiency > 100) {
                alert("请输入有效的系统综合效率(0-100%)");
                return;
            }
            
            if (isNaN(panelConversionEfficiency) || panelConversionEfficiency < 0 || panelConversionEfficiency > 100) {
                alert("请输入有效的光伏组件转换效率(0-100%)");
                return;
            }
            
            // 先显示模态窗口，显示加载状态
            showMonthlyModal();
            
            // 在模态窗口中显示加载中状态
            showLoadingInModal("正在获取数据并处理...");
            
            // 再获取数据并创建图表
            try {
                console.log('开始获取太阳能辐射数据');
                
                // 获取太阳能辐射数据
                const monthlyData = await getSolarRadiationData(lat, lng, year);
                if (!monthlyData || monthlyData.length === 0) {
                    console.error('未获取到太阳能辐射数据');
                    throw new Error('无法获取有效的太阳能辐射数据');
                }
                
                console.log('成功获取太阳能辐射数据', monthlyData);
                
                // 处理数据并计算结果
                const processedData = monthlyData.map((item) => ({
                    ...item,
                    generation: calculateGeneration(item.radiation, area, systemEfficiency, panelConversionEfficiency),
                    dailyAvg: item.radiation / item.days
                }));
                
                // 计算年度总值 - 但不在界面上显示
                const annualRadiation = processedData.reduce((sum, item) => sum + item.radiation, 0);
                const annualGeneration = processedData.reduce((sum, item) => sum + item.generation, 0);
                
                // 不再主动更新年度总值显示，也不显示results区域
                // 仅将数据保存到window对象以备后续使用
                window.lastCalculatedAnnualData = {
                    annualRadiation,
                    annualGeneration
                };
                
                // 清除模态窗口中的加载状态
                hideLoadingInModal();
                
                // 创建模态窗口中的图表
                createModalCharts(processedData, area, systemEfficiency, panelConversionEfficiency);
                
            } catch (err) {
                console.error('月度详细统计处理失败:', err);
                
                // 清除模态窗口中的加载状态
                hideLoadingInModal();
                
                // 显示错误信息但保持模态窗口打开
                showErrorInModal("处理数据时发生错误：" + (err.message || "未知错误"));
            }
        });
    } else {
        console.error("未找到月度详细统计按钮元素");
    }
    
    // 设置模态窗口事件（包括关闭按钮和背景点击关闭）
    setupModalCloseEvents();
    
    // 单日查询按钮事件
    const calculateDailyBtn = document.getElementById("calculateDaily");
    if (calculateDailyBtn) {
        calculateDailyBtn.addEventListener("click", function() {
            alert("单日查询功能正在开发中，敬请期待！");
        });
    }
}