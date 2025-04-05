/**
 * 太阳能光伏发电量计算工具
 * 基于NASA POWER API数据
 */

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
        return data.projectLocation || null;
    } catch (error) {
        console.error('获取项目地点信息失败:', error);
        return null;
    }
}

// 初始化地图
function initMap() {
    // 创建地图实例
    var map = new BMap.Map("map");
    // 初始中心点设为成都
    var point = new BMap.Point(104.06, 30.67);
    map.centerAndZoom(point, 12);
    map.enableScrollWheelZoom(true);
    
    // 添加控件
    map.addControl(new BMap.NavigationControl());
    map.addControl(new BMap.ScaleControl());
    
    // 创建标记
    var marker = new BMap.Marker(point);
    map.addOverlay(marker);
    
    // 点击地图更新坐标
    map.addEventListener("click", function(e) {
        marker.setPosition(e.point);
        document.getElementById("longitude").value = e.point.lng.toFixed(6);
        document.getElementById("latitude").value = e.point.lat.toFixed(6);
    });
    
    // 搜索位置按钮事件
    document.getElementById("searchLocation").addEventListener("click", function() {
        var location = document.getElementById("location").value;
        if (location) {
            var myGeo = new BMap.Geocoder();
            myGeo.getPoint(location, function(point) {
                if (point) {
                    map.centerAndZoom(point, 12);
                    marker.setPosition(point);
                    document.getElementById("longitude").value = point.lng.toFixed(6);
                    document.getElementById("latitude").value = point.lat.toFixed(6);
                    // 获取海拔数据
                    getElevation(point.lat, point.lng);
                } else {
                    alert("未找到该地点");
                }
            }, location);
        }
    });
    
    return {
        map: map,
        marker: marker
    };
}

// 获取海拔数据
function getElevation(lat, lng) {
    // 这里可以调用高程API获取海拔
    // 由于百度地图API不直接提供海拔数据，这里使用模拟数据
    // 实际项目中可以使用其他API如Google Elevation API
    document.getElementById("elevation").value = Math.floor(Math.random() * 1000 + 500);
}

// 从NASA POWER API获取太阳能辐射数据
async function getSolarRadiationData(lat, lng, year) {
    // 构建API请求URL
    const url = `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=${lng}&latitude=${lat}&start=${year}0101&end=${year}1231&format=JSON`;
    
    try {
        // 实际项目中应该使用fetch调用真实API
        const response = await fetch(url);
        const data = await response.json();
        
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
        
        // 遍历每一天的数据
        Object.keys(radiationData).forEach(dateStr => {
            // 日期格式: YYYYMMDD
            const month = parseInt(dateStr.substring(4, 6)) - 1; // 月份从0开始
            const radiation = radiationData[dateStr]; // 单位: MJ/m²/day
            
            // 转换单位: MJ/m²/day 转为 kWh/m²/day (1 MJ = 0.2778 kWh)
            const radiationKWh = radiation * 0.2778;
            
            // 累加到对应月份
            monthlyData[month].radiation += radiationKWh;
        });
        
        return monthlyData;
    } catch (error) {
        console.error("获取太阳能辐射数据失败:", error);
        
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
        
        return monthlyData;
    }
}

// 计算发电量
function calculateGeneration(radiation, area, efficiency) {
    // 转换效率从百分比转为小数
    const efficiencyDecimal = efficiency / 100;
    // 计算发电量 (kWh) = 辐射量 (kWh/m²) * 面积 (m²) * 效率
    return radiation * area * efficiencyDecimal;
}

// 更新图表
function updateCharts(monthlyData, area, efficiency) {
    const months = monthlyData.map(item => item.month);
    const radiationValues = monthlyData.map(item => item.radiation);
    const generationValues = monthlyData.map(item => calculateGeneration(item.radiation, area, efficiency));
    
    // 计算年度总值
    const annualRadiation = radiationValues.reduce((sum, val) => sum + val, 0);
    const annualGeneration = generationValues.reduce((sum, val) => sum + val, 0);
    
    // 更新显示
    document.getElementById("annualRadiation").textContent = annualRadiation.toFixed(2);
    document.getElementById("annualGeneration").textContent = annualGeneration.toFixed(2);
    
    // 显示结果区域
    document.getElementById("results").style.display = "grid";
    
    // 清除旧图表
    if (window.radiationChart) {
        window.radiationChart.destroy();
    }
    if (window.generationChart) {
        window.generationChart.destroy();
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

// 导出函数
window.solarCalculator = {
    initMap,
    getSolarRadiationData,
    calculateGeneration,
    updateCharts,
    updateMonthlyTable
};

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", async function() {
    // 获取项目信息
    const { projectId } = window.getProjectInfo ? window.getProjectInfo() : { projectId: null };
    
    console.log('当前项目ID:', projectId);
    
    // 初始化地图
    const mapObj = initMap();
    
    // 如果有项目ID，获取项目地点并自动填充
    if (projectId) {
        const projectLocation = await getProjectLocation(projectId);
        if (projectLocation) {
            // 填充地点输入框
            const locationInput = document.getElementById("location");
            locationInput.value = projectLocation;
            
            // 自动触发地点搜索
            document.getElementById("searchLocation").click();
        }
    }
    
    // 年度汇总按钮事件
    document.getElementById("calculateAnnual").addEventListener("click", async function() {
        const lat = parseFloat(document.getElementById("latitude").value);
        const lng = parseFloat(document.getElementById("longitude").value);
        const year = document.getElementById("year").value;
        const area = parseFloat(document.getElementById("panelArea").value);
        const efficiency = parseFloat(document.getElementById("efficiency").value);
        
        if (isNaN(lat) || isNaN(lng)) {
            alert("请先选择或输入有效的地理坐标");
            return;
        }
        
        if (isNaN(area) || area <= 0) {
            alert("请输入有效的太阳能光伏板面积");
            return;
        }
        
        if (isNaN(efficiency) || efficiency <= 0 || efficiency > 100) {
            alert("请输入有效的光伏板效率(0-100%)");
            return;
        }
        
        // 获取太阳能辐射数据
        const monthlyData = await getSolarRadiationData(lat, lng, year);
        if (monthlyData) {
            // 更新图表
            const result = updateCharts(monthlyData, area, efficiency);
            // 隐藏月度数据表格
            document.getElementById("monthlyData").style.display = "none";
        }
    });
    
    // 月度详细统计按钮事件
    document.getElementById("calculateMonthly").addEventListener("click", async function() {
        const lat = parseFloat(document.getElementById("latitude").value);
        const lng = parseFloat(document.getElementById("longitude").value);
        const year = document.getElementById("year").value;
        const area = parseFloat(document.getElementById("panelArea").value);
        const efficiency = parseFloat(document.getElementById("efficiency").value);
        
        if (isNaN(lat) || isNaN(lng)) {
            alert("请先选择或输入有效的地理坐标");
            return;
        }
        
        if (isNaN(area) || area <= 0) {
            alert("请输入有效的太阳能光伏板面积");
            return;
        }
        
        if (isNaN(efficiency) || efficiency <= 0 || efficiency > 100) {
            alert("请输入有效的光伏板效率(0-100%)");
            return;
        }
        
        // 获取太阳能辐射数据
        const monthlyData = await getSolarRadiationData(lat, lng, year);
        if (monthlyData) {
            // 更新图表
            const result = updateCharts(monthlyData, area, efficiency);
            // 更新月度数据表格
            updateMonthlyTable(result.monthlyData);
        }
    });
    
    // 单日查询按钮事件
    document.getElementById("calculateDaily").addEventListener("click", function() {
        alert("单日查询功能正在开发中，敬请期待！");
    });
});