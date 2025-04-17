(function() {
// 省市联动功能
// 只在全局变量未定义时才声明
var provinceData = {};
var cityData = {};
// 用户权限控制状态
var userPermissions = null;
var isFormReadOnly = false;

// 初始化省市数据
document.addEventListener('DOMContentLoaded', function() {
    initializeProvinceCitySelectors();
    
    // 加载用户权限并初始化表单状态
    loadUserPermissions();
});

// 加载用户权限
function loadUserPermissions() {
    const projectIdElement = document.getElementById('project_id');
    if (!projectIdElement) return;
    
    const projectId = projectIdElement.value;
    if (!projectId) return;
    
    fetch(`/api/projects/${projectId}/permissions`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                userPermissions = data.permissions;
                // 根据权限设置表单可编辑状态
                updateFormEditability();
            } else {
                console.warn("获取权限失败:", data.error);
                // 默认设置为只读模式
                setFormReadOnly(true);
            }
        })
        .catch(error => {
            console.error("获取用户权限出错:", error);
            // 出错时默认设置为只读模式
            setFormReadOnly(true);
        });
}

// 根据权限更新表单可编辑状态
function updateFormEditability() {
    if (!userPermissions) {
        setFormReadOnly(true);
        return;
    }
    
    // 检查是否有编辑权限
    const role = userPermissions.role;
    const permissions = userPermissions.permissions;
    
    // 创建者或具有"管理"权限的用户可以编辑
    if (role === '创建者' || permissions === '管理' || permissions === '编辑') {
        setFormReadOnly(false);
        // 添加权限提示
        // showPermissionIndicator(role, permissions, false);
    } else {
        // 其他情况设为只读
        setFormReadOnly(true);
        // 添加权限提示
        // showPermissionIndicator(role, permissions, true);
    }
}

// 显示权限提示信息
function showPermissionIndicator(role, permissions, isReadOnly) {
    // 检查是否已经存在权限提示元素
    let permissionIndicator = document.getElementById('permission-indicator');
    if (!permissionIndicator) {
        // 创建权限提示元素
        permissionIndicator = document.createElement('div');
        permissionIndicator.id = 'permission-indicator';
        permissionIndicator.className = 'fixed top-4 right-4 px-3 py-2 rounded-lg shadow-md z-50 flex items-center space-x-2 text-sm';
        
        // 插入到页面中
        document.body.appendChild(permissionIndicator);
    }
    
    // 设置样式和内容
    if (isReadOnly) {
        permissionIndicator.className = 'fixed top-4 right-4 px-3 py-2 rounded-lg shadow-md z-50 flex items-center space-x-2 text-sm bg-amber-100 text-amber-800 border border-amber-200';
        permissionIndicator.innerHTML = `
            <i class="fas fa-lock"></i>
            <span>只读模式 (角色: ${role}, 权限: ${permissions})</span>
        `;
    } else {
        permissionIndicator.className = 'fixed top-4 right-4 px-3 py-2 rounded-lg shadow-md z-50 flex items-center space-x-2 text-sm bg-green-100 text-green-800 border border-green-200';
        permissionIndicator.innerHTML = `
            <i class="fas fa-edit"></i>
            <span>编辑模式 (角色: ${role}, 权限: ${permissions})</span>
        `;
    }
}

// 设置表单为只读状态
function setFormReadOnly(readOnly) {
    isFormReadOnly = readOnly;
    
    // 获取所有输入元素
    const inputElements = document.querySelectorAll('input, select, textarea');
    inputElements.forEach(element => {
        element.disabled = readOnly;
        
        // 添加视觉提示
        if (readOnly) {
            element.classList.add('bg-gray-100');
            element.classList.add('cursor-not-allowed');
        } else {
            element.classList.remove('bg-gray-100');
            element.classList.remove('cursor-not-allowed');
        }
    });
    
    // 获取所有按钮（除了导航和关闭按钮）
    const buttons = document.querySelectorAll('button:not(.nav-button):not(.close-button)');
    buttons.forEach(button => {
        if (readOnly) {
            // 在只读模式下禁用所有提交和保存按钮
            if (button.type === 'submit' || 
                button.id === 'saveBtn' || 
                button.textContent.includes('保存') || 
                button.textContent.includes('提交') ||
                button.textContent.includes('上传') ||
                button.textContent.includes('添加')) {
                button.disabled = true;
                button.classList.add('opacity-50');
                button.classList.add('cursor-not-allowed');
            }
        } else {
            button.disabled = false;
            button.classList.remove('opacity-50');
            button.classList.remove('cursor-not-allowed');
        }
    });
}

// 初始化省市选择器
function initializeProvinceCitySelectors() {
    const provinceSelect = document.getElementById('province');
    const citySelect = document.getElementById('city');
    const projectLocationInput = document.getElementById('project_location');
    
    // 只在项目表单页面初始化
    if (provinceSelect && citySelect && projectLocationInput) {
        // 设置loading状态，防止抖动
        provinceSelect.innerHTML = '<option value="">加载中...</option>';
        citySelect.innerHTML = '<option value="">请选择城市</option>';
        
        // 加载省市数据
        fetch('/static/json/province_city.json')
            .then(response => response.json())
            .then(data => {
                provinceData = data['86']; // 所有省份
                cityData = data; // 所有城市数据
                
                // 添加省份选项
                let provinceOptions = '<option value="">请选择省份</option>';
                for (let code in provinceData) {
                    provinceOptions += `<option value="${code}">${provinceData[code]}</option>`;
                }
                provinceSelect.innerHTML = provinceOptions;
                
                // 如果有已保存的地址，尝试初始化选择框
                if (projectLocationInput.value) {
                    const parts = projectLocationInput.value.split(' ');
                    if (parts.length > 0) {
                        const provinceName = parts[0];
                        let provinceCode = null;
                        
                        // 查找省份代码
                        for (let code in provinceData) {
                            if (provinceData[code] === provinceName) {
                                provinceCode = code;
                                provinceSelect.value = code;
                                
                                // 加载城市选项
                                const cities = cityData[code] || {};
                                let cityOptions = '<option value="">请选择城市</option>';
                                for (let cityCode in cities) {
                                    cityOptions += `<option value="${cityCode}">${cities[cityCode]}</option>`;
                                }
                                citySelect.innerHTML = cityOptions;
                                
                                // 如果有城市数据，设置选中状态
                                if (parts.length > 1) {
                                    const cityName = parts[1];
                                    for (let cityCode in cities) {
                                        if (cities[cityCode] === cityName) {
                                            citySelect.value = cityCode;
                                            break;
                                        }
                                    }
                                }
                                break;
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('加载省市数据失败:', error);
                provinceSelect.innerHTML = '<option value="">请选择省份</option>';
            });
    }
}

// 更新省市选择
function updateProvinceCity() {
    const provinceSelect = document.getElementById('province');
    const citySelect = document.getElementById('city');
    const projectLocationInput = document.getElementById('project_location');
    const climateZoneSelect = document.getElementById('climate_zone');
    
    if (!provinceSelect || !citySelect || !projectLocationInput) return;
    
    // 如果切换了省份，加载对应的城市
    if (provinceSelect.value && provinceSelect.value !== citySelect.dataset.provinceCode) {
        citySelect.dataset.provinceCode = provinceSelect.value;
        
        // 构建城市选项
        const cities = cityData[provinceSelect.value] || {};
        let cityOptions = '<option value="">请选择城市</option>';
        for (let cityCode in cities) {
            cityOptions += `<option value="${cityCode}">${cities[cityCode]}</option>`;
        }
        citySelect.innerHTML = cityOptions;
        citySelect.value = "";
    }
    
    // 更新地址输入框
    const provinceName = provinceSelect.options[provinceSelect.selectedIndex]?.text || '';
    const cityName = citySelect.options[citySelect.selectedIndex]?.text || '';
    
    let location = [];
    if (provinceName && provinceName !== '请选择省份' && provinceName !== '加载中...') location.push(provinceName);
    if (cityName && cityName !== '请选择城市') location.push(cityName);
    
    projectLocationInput.value = location.join(' ');
    
    // 更新气候区划
    if (climateZoneSelect && provinceName && cityName && 
        provinceName !== '请选择省份' && provinceName !== '加载中...' && 
        cityName !== '请选择城市') {
        
        const zoneInfo = getClimateZone(provinceName, cityName);
        if (zoneInfo) {
            // 设置气候区划选择框的值
            for (let i = 0; i < climateZoneSelect.options.length; i++) {
                if (climateZoneSelect.options[i].value === zoneInfo.气候区划) {
                    climateZoneSelect.selectedIndex = i;
                    break;
                }
            }
        }
    }
}


document.addEventListener('DOMContentLoaded', function() {
    // 初始化表单字段和事件监听器
    initFormFields();
    
    // 添加自动计算得分事件监听器
    setupScoreCalculation();
    
    // 添加载入星级案例按钮事件
    const loadStarCaseBtn = document.getElementById('loadStarCaseBtn');
    if (loadStarCaseBtn) {
        loadStarCaseBtn.addEventListener('click', async function() {
            try {
                // 检查表单是否为只读模式
                if (isFormReadOnly) {
                    alert('您没有编辑权限，无法载入星级案例数据。');
                    return;
                }
                
                // 获取项目ID
                const projectId = document.getElementById('project_id').value;
                if (!projectId) {
                    alert('未找到项目ID，请先保存项目信息');
                    return;
                }

                // 显示加载状态
                const originalText = this.textContent;
                this.textContent = '载入中...';
                this.disabled = true;

                // 调用API获取星级案例数据
                const response = await fetch(`/api/star_case_scores?target_project_id=${projectId}`);
                const data = await response.json();

                // 恢复按钮状态
                this.textContent = originalText;
                this.disabled = false;

                if (data.success) {
                    alert(`成功导入 ${data.data.imported_count} 条星级案例数据！\n标准: ${data.data.standard}\n星级目标: ${data.data.star_rating_target}`);
                } else {
                    alert(`载入失败: ${data.message}`);
                }
            } catch (error) {
                console.error('载入星级案例出错:', error);
                alert('载入星级案例失败: ' + error.message);
                // 恢复按钮状态
                this.textContent = '载入星级案例';
                this.disabled = false;
            }
        });
    }
    
    // 其他初始化逻辑...
});

// 初始化表单字段和事件监听器
function initFormFields() {
    console.log("初始化表单字段...");
    
    // 绑定容积率、建筑密度和绿地率的自动计算
    const totalLandArea = document.getElementById('total_land_area');
    const aboveGroundArea = document.getElementById('above_ground_area');
    const buildingBaseArea = document.getElementById('building_base_area');
    const greenArea = document.getElementById('green_area');
    const plotRatio = document.getElementById('plot_ratio');
    const buildingDensity = document.getElementById('building_density');
    const greenRatio = document.getElementById('green_ratio');
    
    // 当总用地面积和地上建筑面积变化时，自动计算容积率
    if (totalLandArea && aboveGroundArea && plotRatio) {
        const calculatePlotRatio = function() {
            const tla = parseFloat(totalLandArea.value) || 0;
            const aga = parseFloat(aboveGroundArea.value) || 0;
            if (tla > 0 && aga > 0) {
                plotRatio.value = (aga / tla).toFixed(2);
            }
        };
        totalLandArea.addEventListener('change', calculatePlotRatio);
        aboveGroundArea.addEventListener('change', calculatePlotRatio);
    }
    
    // 当总用地面积和建筑基底面积变化时，自动计算建筑密度
    if (totalLandArea && buildingBaseArea && buildingDensity) {
        const calculateBuildingDensity = function() {
            const tla = parseFloat(totalLandArea.value) || 0;
            const bba = parseFloat(buildingBaseArea.value) || 0;
            if (tla > 0 && bba > 0) {
                buildingDensity.value = ((bba / tla) * 100).toFixed(2);
            }
        };
        totalLandArea.addEventListener('change', calculateBuildingDensity);
        buildingBaseArea.addEventListener('change', calculateBuildingDensity);
    }
    
    // 当总用地面积和绿地面积变化时，自动计算绿地率
    if (totalLandArea && greenArea && greenRatio) {
        const calculateGreenRatio = function() {
            const tla = parseFloat(totalLandArea.value) || 0;
            const ga = parseFloat(greenArea.value) || 0;
            if (tla > 0 && ga > 0) {
                greenRatio.value = ((ga / tla) * 100).toFixed(2);
            }
        };
        totalLandArea.addEventListener('change', calculateGreenRatio);
        greenArea.addEventListener('change', calculateGreenRatio);
    }
    
    // 绑定建筑类型变化事件
    const buildingType = document.getElementById('building_type');
    if (buildingType) {
        buildingType.addEventListener('change', function() {
            // 计算得分并更新显示
            calculateAndUpdateScores();
        });
    }
    
    // 设置总建筑面积自动计算
    const totalBuildingArea = document.getElementById('total_building_area');
    const undergroundArea = document.getElementById('underground_area');
    if (aboveGroundArea && undergroundArea && totalBuildingArea) {
        const calculateTotalBuildingArea = function() {
            const aga = parseFloat(aboveGroundArea.value) || 0;
            const ua = parseFloat(undergroundArea.value) || 0;
            totalBuildingArea.value = (aga + ua).toFixed(2);
        };
        aboveGroundArea.addEventListener('change', calculateTotalBuildingArea);
        undergroundArea.addEventListener('change', calculateTotalBuildingArea);
    }
    
    console.log("表单字段初始化完成");
}

// 设置自动计算得分的事件监听器
function setupScoreCalculation() {
    // 在页面加载时计算一次得分
    calculateAndUpdateScores();
    
    // 为相关表单字段添加事件监听器
    const scoreFields = [
        'total_land_area', 'residential_units', 'avg_floors', 'building_type',
        'underground_area', 'first_floor_underground_area', 'above_ground_area',
        'green_area', 'construction_type', 'public_green_space', 'climate_zone',
        'plot_ratio', 'public_building_type', 'green_ratio', 'ground_parking_spaces',
        'has_underground_garage', 'standard_selection'
    ];
    
    scoreFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('change', calculateAndUpdateScores);
        }
    });
}

// 页面加载完成后执行计算和更新
document.addEventListener('DOMContentLoaded', function() {
    calculateAndUpdateScores();
    
    // 监听表单字段变化，重新计算得分
    const formFields = [
        'total_land_area', 'residential_units', 'avg_floors', 'building_type',
        'underground_area', 'first_floor_underground_area', 'above_ground_area',
        'green_area', 'construction_type', 'public_green_space', 'climate_zone',
        'plot_ratio', 'public_building_type', 'green_ratio', 'ground_parking_spaces',
        'has_underground_garage'
    ];
    
    formFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('change', calculateAndUpdateScores);
        }
    });
    
    // 初始化省市选择器
    initProvinceCity();
    
    // 确保绿建得分计算区域可见
    const scoreSection = document.querySelector('.mt-6.bg-white.rounded-lg.shadow-sm.border.border-gray-200.p-4');
    if (scoreSection) {
        scoreSection.style.display = 'block';
    }
    
});

// 计算得分并更新数据库
function calculateAndUpdateScores() {
    //总用地面积
    const totalLandArea = parseFloat(document.getElementById('total_land_area').value) || 0;
    //住宅总套数
    const residentialUnits = parseInt(document.getElementById('residential_units').value) || 0;
    //住宅平均层数
    const averageFloors = document.getElementById('avg_floors').value;
    //建筑类型
    const buildingType = document.getElementById('building_type').value;
    //地下空间面积
    const undergroundArea = parseFloat(document.getElementById('underground_area').value) || 0;
    //地下一层面积
    const undergroundFirstFloor = parseFloat(document.getElementById('first_floor_underground_area').value) || 0;
    //地上面积
    const aboveGroundArea = parseFloat(document.getElementById('above_ground_area').value) || 0;
    //绿化用地面积
    const greenSpaceArea = parseFloat(document.getElementById('green_area').value) || 0;
    //项目类型
    const projectType = document.getElementById('construction_type').value;
    //绿地向公众开放
    const publicGreenSpace = document.getElementById('public_green_space').value;
    //建筑层数
    let floors = 0;
    switch (averageFloors) {
        case "平均3层及以下": floors = 3; break;
        case "平均4-6层": floors = 4; break;
        case "平均7-9层": floors = 7; break;
        case "平均10-18层": floors = 10; break;
        case "平均19层及以上": floors = 19; break;
        default: floors = 0;
    }
    //气候区
    const climateZone = document.getElementById('climate_zone').value;
    //容积率
    const plotRatio = parseFloat(document.getElementById('plot_ratio').value) || 0;
    //公建类型
    const publicBuildingType = document.getElementById('public_building_type').value;
    //绿地率与规划绿地率的比值
    const greenRate = parseFloat(document.getElementById('green_ratio').value) /0.3|| 0;
    //人均集中绿地面积
    const greenArea = parseFloat(document.getElementById('green_area').value)/(residentialUnits*3.2) || 0;
    //地面停车位数量
    const groundParkingCount = parseFloat(document.getElementById('ground_parking_spaces').value) || 0;
    //有无地下车库
    const hasundergroundgarage=document.getElementById('has_underground_garage').value;
    
    // 计算各项得分
    const perCapitaLandScore = calculatePerCapitaLandScore(totalLandArea, residentialUnits, 3.2, climateZone, floors);
    //公建容积率指标得分
    const plotRatioScore = calculatePlotRatioScore(plotRatio, publicBuildingType);
    //地下空间开发利用得分
    const undergroundScore = calculateUndergroundScore(buildingType, undergroundArea, undergroundFirstFloor, aboveGroundArea, totalLandArea);
    //绿化用地指标得分
    const greenSpaceScore = calculateGreenScore(buildingType, greenRate, greenArea, projectType, publicGreenSpace);
    //停车设施得分
    let parkingScore = 0;
    if (hasundergroundgarage === '有') {
        if (buildingType === '居住建筑') {
                parkingScore = calculateParkingScore(buildingType, groundParkingCount, residentialUnits);
        } else if (buildingType === '公共建筑'){
                parkingScore = calculateParkingScore(buildingType, groundParkingCount*34, totalLandArea);
        }
    }
    
    // 更新显示
    document.getElementById('per_capita_land_score').innerHTML = perCapitaLandScore+' 分';
    document.getElementById('plot_ratio_score').innerHTML = plotRatioScore+' 分';
    document.getElementById('underground_score').innerHTML = undergroundScore+' 分';
    document.getElementById('green_space_score').innerHTML = greenSpaceScore+' 分';
    document.getElementById('parking_score').innerHTML = parkingScore+' 分';
    
    // 修改多个条文的得分   
    let standard = document.getElementById('current-project-standard')?.value || '成都市标';
    let projectId = document.getElementById('current-project-id')?.value || document.getElementById('project_id')?.value;
    
    if (!projectId) {
        console.log('未找到项目ID，无法更新得分');
        return;
    }
    
    try {
        if (standard === '成都市标'){
            if (buildingType === '居住建筑'){
                updateDatabaseScore('3.1.2.14', perCapitaLandScore, projectId);
            } else if (buildingType === '公共建筑'){
                updateDatabaseScore('3.1.2.14', plotRatioScore, projectId);
            }
            updateDatabaseScore('3.1.2.15', undergroundScore, projectId);
            updateDatabaseScore('3.1.2.21', greenSpaceScore, projectId);
            updateDatabaseScore('3.1.2.16', parkingScore, projectId);
        }
        else if (standard === '四川省标'){
            if (buildingType === '居住建筑'){
                updateDatabaseScore('3.1.16', perCapitaLandScore, projectId);
            }
            else if (buildingType === '公共建筑'){
                updateDatabaseScore('3.1.16', plotRatioScore, projectId);
            }
            updateDatabaseScore('3.1.17', undergroundScore, projectId);
            updateDatabaseScore('3.1.25', greenSpaceScore, projectId);
            updateDatabaseScore('3.1.18', parkingScore, projectId);
        }
        else if (standard === '国标'){
            if (buildingType === '居住建筑'){
                updateDatabaseScore('7.2.1', perCapitaLandScore, projectId);
            }
            else if (buildingType === '公共建筑'){
                updateDatabaseScore('7.2.1', plotRatioScore, projectId);
            }
            updateDatabaseScore('7.2.2', undergroundScore, projectId);
            updateDatabaseScore('8.2.3', greenSpaceScore, projectId);
            updateDatabaseScore('7.2.3', parkingScore, projectId);
        }
        console.log('得分更新完成');
    } catch (error) {
        console.error('更新得分时出错:', error);
    }
}
        
// 为保存按钮添加点击事件
// 检查是否已绑定事件处理程序
{
    const saveProjectInfoBtn = document.getElementById('saveProjectInfoBtn');
    if (saveProjectInfoBtn) {
        saveProjectInfoBtn.addEventListener('click', function(e) {
            e.preventDefault(); // 阻止表单默认提交
            
            // 检查是否有编辑权限
            if (isFormReadOnly) {
                toast('您没有编辑权限，无法保存项目信息', 'error');
                return;
            }
            
            // 获取表单数据
            const form = this.closest('form');
            const formData = new FormData(form);
            
            // 发送AJAX请求保存数据
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toast('项目信息保存成功', 'success');
                    // 更新页面显示的项目ID
                    if (data.project_id) {
                        document.getElementById('project_id').value = data.project_id;
                    }
                    
                    // 使用直接跳转方式强制从服务器重新加载整个页面
                    setTimeout(() => {
                        const projectId = document.getElementById('project_id').value || data.project_id;
                        window.location.href = `/project/${projectId}`;
                    }, 1000); // 延迟1秒后跳转，让用户看到成功提示
                } else {
                    // 检查是否是权限错误
                    if (data.error && (data.error.includes('权限') || data.error.includes('permission'))) {
                        toast('保存失败: 您没有编辑此项目的权限', 'error');
                        // 更新权限状态
                        setFormReadOnly(true);
                    } else {
                        toast('保存失败: ' + (data.message || data.error || '未知错误'), 'error');
                    }
                }
            })
            .catch(error => {
                console.error('保存项目信息出错:', error);
                toast('保存失败: ' + error.message, 'error');
            });
        });
    }
}
        
// AI提取项目信息相关函数
// 全局变量存储粘贴的图片
// 检查是否已经声明过
if (typeof pastedImage === 'undefined') {
    var pastedImage = null;
}
// 检查是否已经声明过
if (typeof currentTab === 'undefined') {
    var currentTab = 'word'; // 当前激活的标签页
}
    
// 切换标签页
function switchTab(tab) {
    console.log("切换到标签页:", tab);
    currentTab = tab;  // 更新当前标签页状态
    
    // 获取标签页按钮
    const wordTabBtn = document.getElementById('wordTabBtn');
    const imageTabBtn = document.getElementById('imageTabBtn');
    
    // 获取标签页内容
    const wordUploadTab = document.getElementById('wordUploadTab');
    const imageUploadTab = document.getElementById('imageUploadTab');
    
    // 更新标签页按钮样式
    if (tab === 'word') {
        wordTabBtn.classList.add('active');
        imageTabBtn.classList.remove('active');
        
        // 显示Word上传区域，隐藏图片上传区域
        wordUploadTab.classList.remove('hidden');
        wordUploadTab.classList.add('active');
        imageUploadTab.classList.add('hidden');
        imageUploadTab.classList.remove('active');
        
        console.log("Word标签页已激活");
    } else {
        imageTabBtn.classList.add('active');
        wordTabBtn.classList.remove('active');
        
        // 显示图片上传区域，隐藏Word上传区域
        imageUploadTab.classList.remove('hidden');
        imageUploadTab.classList.add('active');
        wordUploadTab.classList.add('hidden');
        wordUploadTab.classList.remove('active');
        
        console.log("图片标签页已激活");
    }
}
    
// 将switchTab函数暴露到全局作用域
window.switchTab = switchTab;

// 清除图片预览
function clearImagePreview(event) {
    // 阻止事件冒泡，防止触发文件选择
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    // 完全清除图片状态
    const previewContainer = document.getElementById('previewContainer');
    const dropAreaText = document.getElementById('dropAreaText');
    const imageFileInput = document.getElementById('imageFileInput');
    const clearImageBtn = document.getElementById('clearImageBtn');
    const imagePreview = document.getElementById('imagePreview');
    
    // 重置图片元素
    previewContainer.classList.add('hidden');
    dropAreaText.classList.remove('hidden');
    clearImageBtn.classList.add('hidden');
    imageFileInput.value = '';
    imagePreview.src = '';
    
    // 清除粘贴的图片数据
    pastedImage = null;
    
    console.log('图片已清除');
}

// 将clearImagePreview函数暴露到全局作用域
window.clearImagePreview = function(event) {
    clearImagePreview(event);  // 调用内部函数
};

// 处理图片预览
function handleImagePreview(file) {
    if (!file || !file.type || !file.type.match('image.*')) {
        alert('请选择图片文件');
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const img = document.getElementById('imagePreview');
        img.src = e.target.result;
        document.getElementById('previewContainer').classList.remove('hidden');
        document.getElementById('dropAreaText').classList.add('hidden');
        document.getElementById('clearImageBtn').classList.remove('hidden');
    };
    reader.readAsDataURL(file);
}
    
// 显示Word文件名
function showWordFileName(file) {
    const fileNameDiv = document.getElementById('wordFileName');
    if (file) {
        fileNameDiv.textContent = `已选择: ${file.name}`;
        fileNameDiv.classList.remove('hidden');
    } else {
        fileNameDiv.classList.add('hidden');
    }
}
    
// 将showAiExtractModal函数和相关函数暴露到全局作用域
window.showAiExtractModal = function() {
    console.log("调用showAiExtractModal函数");
    
    // 检查是否有编辑权限
    if (isFormReadOnly) {
        toast('您没有编辑权限，无法使用AI提取功能', 'error');
        return;
    }
    
    const modal = document.getElementById('aiExtractModal');
    
    if (!modal) {
        console.error("未找到模态框元素!");
        return;
    }
    
    console.log("找到模态框元素，当前类名:", modal.className);
    modal.classList.add('show');
    console.log("添加show类后，类名:", modal.className);
    
    // 重置所有状态
    const extractResult = document.getElementById('extractResult');
    const extractLoading = document.getElementById('extractLoading');
    const applyButton = document.getElementById('applyButton');
    const wordFileInput = document.getElementById('wordFileInput');
    const wordFileName = document.getElementById('wordFileName');
    
    if (extractResult) extractResult.classList.add('hidden');
    if (extractLoading) extractLoading.classList.add('hidden');
    if (applyButton) applyButton.classList.add('hidden');
    if (wordFileInput) wordFileInput.value = '';
    if (wordFileName) wordFileName.classList.add('hidden');
    
    clearImagePreview();
    
    // 添加ESC键监听
    document.addEventListener('keydown', handleEscKeyForModal);
    // 添加粘贴监听
    document.addEventListener('paste', handlePasteImage);
    
    // 初始化文件上传监听
    initFileUploadListeners();
    
    console.log("模态框初始化完成，应该可见");
};

// 其他需要暴露的函数
window.closeAiExtractModal = function() {
    const modal = document.getElementById('aiExtractModal');
    if (!modal) return;
    
    modal.classList.remove('show');
    
    // 强制重置所有状态
    const resetElements = {
        'wordFileInput': el => el.value = '',
        'wordFileName': el => el.classList.add('hidden'),
        'imageFileInput': el => el.value = '',
        'imagePreview': el => el.src = '',
        'previewContainer': el => el.classList.add('hidden'),
        'dropAreaText': el => el.classList.remove('hidden'),
        'clearImageBtn': el => el.classList.add('hidden'),
        'extractResult': el => el.classList.add('hidden'),
        'applyButton': el => el.classList.add('hidden')
    };
    
    // 应用所有重置
    for (const [id, resetFn] of Object.entries(resetElements)) {
        const element = document.getElementById(id);
        if (element) resetFn(element);
    }
    
    // 清除粘贴的图片数据
    pastedImage = null;
    
    // 移除ESC键监听
    document.removeEventListener('keydown', handleEscKeyForModal);
    // 移除粘贴监听
    document.removeEventListener('paste', handlePasteImage);
    
    console.log('模态窗口已关闭，所有状态已重置');
};

// 显示AI提取模态框
function showAiExtractModal() {
    window.showAiExtractModal(); // 调用全局函数
}

// 关闭AI提取模态框
function closeAiExtractModal() {
    window.closeAiExtractModal(); // 调用全局函数
}

// 处理ESC键按下事件
function handleEscKeyForModal(event) {
    if (event.key === 'Escape') {
        closeAiExtractModal();
    }
}
    
// 处理图片粘贴事件
function handlePasteImage(event) {
    // 检查当前标签页是否是图片标签页
    if (currentTab !== 'image') {
        return;
    }
    
    // 检查剪贴板数据
    const items = (event.clipboardData || event.originalEvent.clipboardData).items;
    
    for (let i = 0; i < items.length; i++) {
        if (items[i].kind === 'file') {
            pastedImage = items[i].getAsFile();
            
            // 处理图片预览
            handleImagePreview(pastedImage);
            
            // 阻止默认粘贴行为
            event.preventDefault();
            break;
        }
    }
}
    
// 初始化文件上传监听
function initFileUploadListeners() {
    // Word文件选择
    const wordFileInput = document.getElementById('wordFileInput');
    if (wordFileInput) {
        wordFileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                showWordFileName(this.files[0]);
            } else {
                showWordFileName(null);
            }
        });
    }
    
    // 图片文件选择
    const imageFileInput = document.getElementById('imageFileInput');
    if (imageFileInput) {
        imageFileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                handleImagePreview(this.files[0]);
            }
        });
    }
    
    // 清除图片按钮
    const clearImageBtn = document.getElementById('clearImageBtn');
    if (clearImageBtn) {
        clearImageBtn.addEventListener('click', function(e) {
            clearImagePreview(e);
        });
    }
}
    
// 提取项目信息
function extractProjectInfo() {
    console.log("extractProjectInfo函数被调用");
    
    // 检查是否有编辑权限
    if (isFormReadOnly) {
        toast('您没有编辑权限，无法使用AI提取功能', 'error');
        closeAiExtractModal(); // 关闭模态框
        return;
    }
    
    const wordFileInput = document.getElementById('wordFileInput');
    const imageFileInput = document.getElementById('imageFileInput');
    const extractResult = document.getElementById('extractResult');
    const extractLoading = document.getElementById('extractLoading');
    const applyButton = document.getElementById('applyButton');
    
    // 隐藏上一次的结果
    if (extractResult) extractResult.classList.add('hidden');
    if (applyButton) applyButton.classList.add('hidden');
    
    // 显示加载状态
    if (extractLoading) extractLoading.classList.remove('hidden');
    
    // 准备上传的数据
    const formData = new FormData();
    
    console.log("当前激活的标签页:", currentTab);
    console.log("Word标签页状态:", document.getElementById('wordUploadTab').classList.contains('active'));
    console.log("图片标签页状态:", document.getElementById('imageUploadTab').classList.contains('active'));
    
    // 根据当前选择的标签页获取文件
    if (currentTab === 'word') {
        console.log("当前是Word标签页");
        const wordFileInput = document.getElementById('wordFileInput');
        if (!wordFileInput.files || wordFileInput.files.length === 0) {
            alert('请选择Word文档');
            document.getElementById('extractLoading').classList.add('hidden');
            return;
        }
        formData.append('word_file', wordFileInput.files[0]);
        console.log("已选择Word文件:", wordFileInput.files[0].name);
    } else {
        // 直接使用else而不是检查图片标签页是否激活
        console.log("当前是图片标签页");
        const imageFile = imageFileInput.files[0] || pastedImage;
        console.log("提取图片信息，图片文件：", imageFile ? imageFile.name : "无");
        
        if (!imageFile) {
            alert('请选择或粘贴图片');
            document.getElementById('extractLoading').classList.add('hidden');
            return;
        }
        formData.append('file', imageFile);
        console.log("图片文件信息:", imageFile.name, imageFile.size, imageFile.type);
    }
    
    // 发送请求
    console.log("正在发送API请求到：", '/api/extract_project_info');
    fetch('/api/extract_project_info', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏加载状态
        document.getElementById('extractLoading').classList.add('hidden');
        
        if (data.success) {
            // 显示提取结果
            const extractedInfo = document.getElementById('extractedInfo');
            let infoHTML = '';
            
            // 兼容旧版和新版接口返回格式
            const projectInfo = data.project_info || data.info;
            console.log("API返回的原始数据:", JSON.stringify(data));
            console.log("提取到的项目信息:", JSON.stringify(projectInfo));
            
            // 遍历提取的信息并格式化显示
            for (const key in projectInfo) {
                // 跳过原始文本字段
                if (key === 'raw_text') continue;
                infoHTML += `<div class="mb-1">
                    <span class="text-purple-300 font-medium">${key}:</span> 
                    <span class="text-gray-200">${projectInfo[key] || '-'}</span>
                </div>`;
            }
            
            extractedInfo.innerHTML = infoHTML;
            document.getElementById('extractResult').classList.remove('hidden');
            document.getElementById('applyButton').classList.remove('hidden');
            
            // 存储提取的信息以便后续应用
            window.extractedProjectInfo = projectInfo;
            console.log("已保存提取信息到window.extractedProjectInfo");
            
            // 验证保存是否成功
            setTimeout(() => {
                console.log("验证提取信息:", window.extractedProjectInfo ? "已保存" : "未保存");
                if (window.extractedProjectInfo) {
                    console.log("保存的字段:", Object.keys(window.extractedProjectInfo).join(", "));
                }
            }, 100);
        } else {
            alert('提取失败: ' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        document.getElementById('extractLoading').classList.add('hidden');
        console.error('提取项目信息出错:', error);
        alert('提取失败: ' + error.message);
    });
}

// 将extractProjectInfo函数暴露到全局作用域
window.extractProjectInfo = function() {
    extractProjectInfo();  // 调用内部函数
};

// 应用提取的信息到表单
function applyExtractedInfo() {
    if (!lastExtractedData) {
        toast('没有可应用的数据', 'error');
        closeAiExtractModal(); // 关闭模态框
        return;
    }
    
    try {
        // 检查是否有编辑权限
        if (isFormReadOnly) {
            toast('您没有编辑权限，无法应用提取的信息', 'error');
            closeAiExtractModal(); // 关闭模态框
            return;
        }
        
        console.log("开始应用提取的信息到表单...");
        const info = window.extractedProjectInfo;
        if (!info) {
            console.error("没有可用的提取信息");
            alert("没有可用的提取信息，请先提取数据");
            return;
        }
        
        // 显示提取到的信息（调试用）
        console.log("提取到的所有字段:", Object.keys(info).join(", "));
        console.log("提取到的完整信息:", JSON.stringify(info));
        
        // 尝试把提取的信息复制到剪贴板（调试用）
        try {
            navigator.clipboard.writeText(JSON.stringify(info, null, 2)).then(() => {
                console.log('提取的信息已复制到剪贴板');
            });
        } catch (e) {
            console.error('无法复制到剪贴板:', e);
        }
        
        // 确保提取的信息是对象类型（防止纯文本字符串）
        if (typeof info === 'string') {
            try {
                info = JSON.parse(info);
                console.log("解析提取的JSON字符串成功");
            } catch (e) {
                console.error("提取的信息不是有效的JSON:", e);
            }
        }
        
        // 字段映射表
        const fieldMappings = {
            // 基本信息字段 - 添加更多别名匹配
            '项目名称': 'project_name',
            'name': 'project_name',
            '名称': 'project_name',
            
            '项目编号': 'project_code',
            'code': 'project_code',
            '编号': 'project_code',
            
            '建设单位': 'construction_unit',
            'construction_unit': 'construction_unit',
            '建设方': 'construction_unit',
            '甲方': 'construction_unit',
            '甲方单位': 'construction_unit',
            
            '设计单位': 'design_unit',
            'design_unit': 'design_unit',
            '设计方': 'design_unit',
            '设计公司': 'design_unit',
            
            '项目地点': 'project_location',
            'location': 'project_location',
            '地点': 'project_location',
            '项目位置': 'project_location',
            '位置': 'project_location',
            
            '建筑类型': 'building_type',
            'building_type': 'building_type',
            '类型': 'building_type',
            '项目类型': 'building_type',
            
            '气候区划': 'climate_zone',
            'climate_zone': 'climate_zone',
            '气候分区': 'climate_zone',
            '区划': 'climate_zone',
            
            '星级目标': 'star_rating_target',
            'star_rating_target': 'star_rating_target',
            '星级': 'star_rating_target',
            '绿建星级': 'star_rating_target',
            
            // 详细信息字段
            '总用地面积': 'total_land_area',
            'total_land_area': 'total_land_area',
            '用地面积': 'total_land_area',
            
            '总建筑面积': 'total_building_area',
            'total_building_area': 'total_building_area',
            '建筑面积': 'total_building_area',
            
            '地上建筑面积': 'above_ground_area',
            'above_ground_area': 'above_ground_area',
            
            '地下建筑面积': 'underground_area',
            'underground_area': 'underground_area',
            
            '地下一层建筑面积': 'first_floor_underground_area',
            'underground_floor_area': 'first_floor_underground_area',
            
            '地面停车位数量': 'ground_parking_spaces',
            'ground_parking_spaces': 'ground_parking_spaces',
            '地面停车位': 'ground_parking_spaces',
            '地上停车位': 'ground_parking_spaces',
            
            '容积率': 'plot_ratio',
            'plot_ratio': 'plot_ratio',
            
            '建筑基底面积': 'building_base_area',
            'building_base_area': 'building_base_area',
            '基底面积': 'building_base_area',
            
            '建筑密度': 'building_density',
            'building_density': 'building_density',
            '密度': 'building_density',
            '建密': 'building_density',
            '建筑密度系数': 'building_density',
            
            '绿地面积': 'green_area',
            'green_area': 'green_area',
            
            '绿地率': 'green_ratio',
            'green_ratio': 'green_ratio',
            '绿化率': 'green_ratio',
            
            '住宅户数': 'residential_units',
            'residential_units': 'residential_units',
            '户数': 'residential_units',
            
            '建筑高度': 'building_height',
            'building_height': 'building_height',
            '高度': 'building_height',
            
            '建筑层数': 'building_floors',
            'building_floors': 'building_floors',
            '层数': 'building_floors',
            
            '地下层数': 'underground_floors',
            'underground_floors': 'underground_floors',
            
            '地下停车位数量': 'underground_parking_spaces',
            'underground_parking_spaces': 'underground_parking_spaces',
            '地下停车位': 'underground_parking_spaces',
            
            '绿地向公众开放': 'public_green_space',
            'public_green_space': 'public_green_space',
            
            '项目所在地区': 'project_area',
            'project_area': 'project_area'
        };
        
        // 保存需要设置的字段，用于延迟检查
        const fieldsToSet = [];
        
        // 记录所有表单字段的可用性
        console.log("检查表单字段可用性:");
        for (const fieldId of Object.values(fieldMappings)) {
            const fieldElement = document.getElementById(fieldId);
            console.log(`字段 ${fieldId} ${fieldElement ? '存在' : '不存在'}`);
        }
        
        let successCount = 0;
        let failedCount = 0;
        let skippedCount = 0;
        
        // 应用提取的信息到表单
        for (const [key, value] of Object.entries(info)) {
            // 尝试标准化字段名
            const normalizedKey = key.trim();
            console.log(`处理字段: ${normalizedKey} = ${value}`);
            
            if (fieldMappings[normalizedKey] && value) {
                const fieldId = fieldMappings[normalizedKey];
                const fieldElement = document.getElementById(fieldId);
                
                if (fieldElement) {
                    // 处理数值类型
                    let processedValue = value;
                    
                    // 尝试去除数值中的单位和非数字字符
                    if (fieldId.includes('area') || fieldId.includes('height') || fieldId.includes('ratio')) {
                        const numericValue = value.toString().replace(/[^0-9.-]/g, '');
                        if (numericValue && !isNaN(parseFloat(numericValue))) {
                            processedValue = numericValue;
                        }
                    }
                    
                    // 设置字段值
                    fieldElement.value = processedValue;
                    console.log(`成功设置 ${normalizedKey} -> ${fieldId}: ${processedValue}`);
                    successCount++;
                    
                    // 添加到待检查列表
                    fieldsToSet.push({fieldId, value: processedValue});
                    
                    // 对于项目地点，尝试解析省市
                    if (fieldId === 'project_location') {
                        parseLocationForProvinceCity(processedValue);
                    }
                    
                    // 对于select字段，触发change事件
                    if (fieldElement.tagName === 'SELECT') {
                        // 触发change事件以便更新相关联的字段
                        const event = new Event('change', { bubbles: true });
                        fieldElement.dispatchEvent(event);
                    }
                } else {
                    console.error(`字段 ${fieldId} 不存在，无法设置值 ${value}`);
                    failedCount++;
                }
            } else {
                if (!fieldMappings[normalizedKey]) {
                    console.warn(`没有字段映射: ${normalizedKey}`);
                } else if (!value) {
                    console.warn(`值为空: ${normalizedKey}`);
                }
                skippedCount++;
            }
        }
        
        // 特殊处理：直接尝试以固定项填入关键字段
        const directMapping = {
            '项目名称': 'project_name',
            '建设单位': 'construction_unit',
            '设计单位': 'design_unit',
            '项目地点': 'project_location',
            '建筑类型': 'building_type',
            '建筑密度': 'building_density',
            '容积率': 'plot_ratio',
            '绿地率': 'green_ratio'
        };
        
        for (const [key, fieldId] of Object.entries(directMapping)) {
            if (info[key] && document.getElementById(fieldId)) {
                // 对于数值字段进行特殊处理
                let valueToSet = info[key];
                
                // 处理数值和百分比
                if (fieldId === 'building_density' || fieldId === 'plot_ratio' || fieldId === 'green_ratio') {
                    // 提取数字部分
                    const numMatch = String(valueToSet).match(/[0-9.]+/);
                    if (numMatch) {
                        valueToSet = numMatch[0];
                        console.log(`为${fieldId}提取数值: ${valueToSet}`);
                    }
                }
                
                document.getElementById(fieldId).value = valueToSet;
                console.log(`直接映射设置: ${key} -> ${fieldId}: ${valueToSet}`);
                
                // 对于项目地点，尝试解析省市
                if (fieldId === 'project_location') {
                    parseLocationForProvinceCity(valueToSet);
                }
            }
        }
        
        // 特殊处理建筑密度字段 - 直接从info中查找所有可能的建筑密度键
        const densityKeys = ['建筑密度', 'building_density', '密度', '建密', '建筑密度系数'];
        const densityField = document.getElementById('building_density');
        
        if (densityField) {
            // 遍历所有可能的建筑密度键
            for (const key of densityKeys) {
                if (info[key]) {
                    let densityValue = info[key];
                    // 提取数字部分
                    const numMatch = String(densityValue).match(/[0-9.]+/);
                    if (numMatch) {
                        densityValue = numMatch[0];
                    }
                    
                    densityField.value = densityValue;
                    console.log(`直接设置建筑密度: ${key} -> ${densityValue}`);
                    break; // 找到一个有效值后退出循环
                }
            }
            
            // 如果建筑密度还是空的，尝试从其他字段计算
            if (!densityField.value) {
                const buildingBaseArea = parseFloat(document.getElementById('building_base_area').value) || 0;
                const totalLandArea = parseFloat(document.getElementById('total_land_area').value) || 0;
                
                if (buildingBaseArea > 0 && totalLandArea > 0) {
                    const calculated = ((buildingBaseArea / totalLandArea) * 100).toFixed(2);
                    densityField.value = calculated;
                    console.log(`已计算并设置建筑密度: ${calculated}%`);
                }
            }
        }
        
        console.log(`应用结果: 成功=${successCount}, 失败=${failedCount}, 跳过=${skippedCount}`);
        
        // 计算可计算的字段
        calculateDerivedFields();
        
        // 延迟检查字段是否正确设置
        setTimeout(() => {
            console.log("检查字段值是否正确设置:");
            for (const {fieldId, value} of fieldsToSet) {
                const fieldElement = document.getElementById(fieldId);
                if (fieldElement) {
                    const currentValue = fieldElement.value;
                    if (currentValue !== value) {
                        console.warn(`字段 ${fieldId} 的值不匹配，期望: ${value}, 实际: ${currentValue}`);
                        // 再次尝试设置
                        fieldElement.value = value;
                        console.log(`重新设置 ${fieldId}: ${value}`);
                    } else {
                        console.log(`字段 ${fieldId} 值正确: ${currentValue}`);
                    }
                }
            }
            
            // 显示当前建筑密度字段值
            const buildingDensityField = document.getElementById('building_density');
            if (buildingDensityField) {
                console.log(`当前建筑密度字段值: ${buildingDensityField.value || '空'}`);
            }
            
            // 再次特殊处理建筑密度和其他关键字段
            console.log("再次检查建筑密度和关键字段...");
            // 检查映射结果
            if (window.extractedProjectInfo) {
                console.log("最终映射结果:", JSON.stringify(window.extractedProjectInfo));
                
                // 直接处理 building_density 字段
                if (window.extractedProjectInfo.building_density) {
                    const densityField = document.getElementById('building_density');
                    if (densityField) {
                        let densityValue = window.extractedProjectInfo.building_density;
                        // 提取数字部分
                        const numMatch = String(densityValue).match(/[0-9.]+/);
                        if (numMatch) {
                            densityValue = numMatch[0];
                        }
                        densityField.value = densityValue;
                        console.log(`直接从mapping设置建筑密度: ${densityValue}`);
                    }
                }
                
                // 直接处理 建筑密度 字段
                if (window.extractedProjectInfo['建筑密度']) {
                    const densityField = document.getElementById('building_density');
                    if (densityField) {
                        let densityValue = window.extractedProjectInfo['建筑密度'];
                        // 提取数字部分
                        const numMatch = String(densityValue).match(/[0-9.]+/);
                        if (numMatch) {
                            densityValue = numMatch[0];
                        }
                        densityField.value = densityValue;
                        console.log(`直接从中文key设置建筑密度: ${densityValue}`);
                    }
                }
            }
            
            // 尝试再次处理省市选择
            const locationField = document.getElementById('project_location');
            if (locationField && locationField.value) {
                console.log(`再次处理地址: ${locationField.value}`);
                parseLocationForProvinceCity(locationField.value);
            }
            
            // 如果建筑密度仍然为空，尝试计算
            const densityField = document.getElementById('building_density');
            if (densityField && (!densityField.value || parseFloat(densityField.value) === 0)) {
                try {
                    // 建筑密度 = 建筑基底面积 / 总用地面积 * 100%
                    const buildingBaseArea = parseFloat(document.getElementById('building_base_area').value) || 0;
                    const totalLandArea = parseFloat(document.getElementById('total_land_area').value) || 0;
                    if (buildingBaseArea > 0 && totalLandArea > 0) {
                        const buildingDensity = ((buildingBaseArea / totalLandArea) * 100).toFixed(2);
                        densityField.value = buildingDensity;
                        console.log(`已重新计算并设置建筑密度: ${buildingDensity}%`);
                    } else {
                        console.log("缺少建筑基底面积或总用地面积，无法计算建筑密度");
                    }
                } catch (e) {
                    console.error("重新计算建筑密度时出错:", e);
                }
            }
            
            // 尝试强制设置建筑密度为15.14（用于调试）
            if (window.extractedProjectInfo && window.extractedProjectInfo['建筑密度'] === '15.14%') {
                console.log("检测到建筑密度为15.14%，强制设置");
                const densityField = document.getElementById('building_density');
                if (densityField) {
                    densityField.value = '15.14';
                    console.log("已强制设置建筑密度为15.14");
                }
            }
            
            // 计算衍生字段
            calculateDerivedFields();
            
            // 延迟关闭模态窗口
            setTimeout(() => closeAiExtractModal(), 200);
        }, 500);
    } catch (error) {
        console.error("应用提取信息到表单时出错:", error);
        alert("应用信息时出错: " + error.message);
        
        // 确保发生错误时也关闭模态窗口
        try {
            closeAiExtractModal();
        } catch (e) {
            console.error("关闭模态窗口时出错:", e);
        }
    }
}
    
// 将applyExtractedInfo函数暴露到全局作用域
window.applyExtractedInfo = function() {
    applyExtractedInfo();  // 调用内部函数
};

// 计算可计算的衍生字段
function calculateDerivedFields() {
    try {
        console.log("开始计算衍生字段...");
        
        // 获取所有相关字段
        const aboveGroundArea = parseFloat(document.getElementById('above_ground_area').value) || 0;
        const totalLandArea = parseFloat(document.getElementById('total_land_area').value) || 0;
        const buildingBaseArea = parseFloat(document.getElementById('building_base_area').value) || 0;
        const greenArea = parseFloat(document.getElementById('green_area').value) || 0;
        
        // 显示获取到的值
        console.log(`计算用字段值: 地上建筑面积=${aboveGroundArea}, 总用地面积=${totalLandArea}, ` +
                    `建筑基底面积=${buildingBaseArea}, 绿地面积=${greenArea}`);
        
        // 1. 计算容积率：地上建筑面积/总用地面积
        if (aboveGroundArea > 0 && totalLandArea > 0) {
            const plotRatio = (aboveGroundArea / totalLandArea).toFixed(2);
            const plotRatioField = document.getElementById('plot_ratio');
            
            if (!plotRatioField.value || parseFloat(plotRatioField.value) === 0) {
                plotRatioField.value = plotRatio;
                console.log(`已计算并设置容积率: ${plotRatio}`);
            } else {
                console.log(`容积率已有值: ${plotRatioField.value}，不进行计算替换`);
            }
        } else {
            console.log("缺少地上建筑面积或总用地面积，无法计算容积率");
        }
        
        // 2. 计算建筑密度：建筑基底面积/总用地面积 * 100%
        if (buildingBaseArea > 0 && totalLandArea > 0) {
            const buildingDensity = ((buildingBaseArea / totalLandArea) * 100).toFixed(2);
            const buildingDensityField = document.getElementById('building_density');
            
            if (!buildingDensityField.value || parseFloat(buildingDensityField.value) === 0) {
                buildingDensityField.value = buildingDensity;
                console.log(`已计算并设置建筑密度: ${buildingDensity}%`);
            } else {
                console.log(`建筑密度已有值: ${buildingDensityField.value}，不进行计算替换`);
            }
        } else {
            console.log("缺少建筑基底面积或总用地面积，无法计算建筑密度");
        }
        
        // 3. 计算绿地率：绿地面积/总用地面积 * 100%
        if (greenArea > 0 && totalLandArea > 0) {
            const greenRatio = ((greenArea / totalLandArea) * 100).toFixed(2);
            const greenRatioField = document.getElementById('green_ratio');
            
            if (!greenRatioField.value || parseFloat(greenRatioField.value) === 0) {
                greenRatioField.value = greenRatio;
                console.log(`已计算并设置绿地率: ${greenRatio}%`);
            } else {
                console.log(`绿地率已有值: ${greenRatioField.value}，不进行计算替换`);
            }
        } else {
            console.log("缺少绿地面积或总用地面积，无法计算绿地率");
        }
        
        // 触发所有计算字段的change事件，确保其他依赖计算更新
        ['plot_ratio', 'building_density', 'green_ratio'].forEach(fieldId => {
            try {
                const field = document.getElementById(fieldId);
                if (field) {
                    const event = new Event('change', { bubbles: true });
                    field.dispatchEvent(event);
                    console.log(`已触发${fieldId}的change事件`);
                }
            } catch (e) {
                console.error(`触发${fieldId}的change事件失败:`, e);
            }
        });
        
        console.log("衍生字段计算完成");
    } catch (e) {
        console.error("计算衍生字段时出错:", e);
    }
}

// 初始化省市选择器
function initProvinceCity() {
    // 获取省市数据
    fetch('/static/json/province_city.json')
        .then(response => response.json())
        .then(data => {
            const provinceSelect = document.getElementById('province');
            const citySelect = document.getElementById('city');
            
            // 清空现有选项
            provinceSelect.innerHTML = '<option value="">请选择省份</option>';
            
            // 添加省份选项（86键包含所有省份）
            if (data['86']) {
                for (const provinceCode in data['86']) {
                    const provinceName = data['86'][provinceCode];
                    const option = document.createElement('option');
                    option.value = provinceCode;
                    option.textContent = provinceName;
                    provinceSelect.appendChild(option);
                }
            } else {
                console.error('省份数据格式不正确');
            }
            
            // 设置初始值
            const locationValue = document.getElementById('project_location').value;
            if (locationValue) {
                parseLocationForProvinceCity(locationValue);
            }
            
            // 省份变化时更新城市
            provinceSelect.addEventListener('change', function() {
                const provinceCode = this.value;
                updateCityOptions(provinceCode, data);
                updateProvinceCity();
            });
            
            // 城市变化时更新隐藏字段
            citySelect.addEventListener('change', function() {
                updateProvinceCity();
            });
        })
        .catch(error => {
            console.error('加载省市数据出错:', error);
        });
}
    
// 更新城市选择器选项
function updateCityOptions(provinceCode, data) {
    const citySelect = document.getElementById('city');
    citySelect.innerHTML = '<option value="">请选择城市</option>';
    
    if (provinceCode && data[provinceCode]) {
        for (const cityCode in data[provinceCode]) {
            const cityName = data[provinceCode][cityCode];
            const option = document.createElement('option');
            option.value = cityCode;
            option.textContent = cityName;
            citySelect.appendChild(option);
        }
    }
}
    
// 更新省市隐藏字段
function updateProvinceCity() {
    const provinceSelect = document.getElementById('province');
    const citySelect = document.getElementById('city');
    const locationField = document.getElementById('project_location');
    
    const provinceCode = provinceSelect.value;
    const cityCode = citySelect.value;
    
    // 获取省市名称而非代码
    const provinceName = provinceSelect.options[provinceSelect.selectedIndex]?.text || '';
    const cityName = citySelect.options[citySelect.selectedIndex]?.text || '';
    
    if (provinceName && cityName) {
        locationField.value = provinceName + cityName;
    } else if (provinceName) {
        locationField.value = provinceName;
    } else {
        locationField.value = '';
    }
    
    // 尝试自动判断气候区划
    if (provinceName || cityName) {
        autoDetectClimateZone(provinceName, cityName);
    }
}
    
// 从位置字符串解析省市
function parseLocationForProvinceCity(location) {
    if (!location) {
        console.log("地址为空，无法解析省市");
        return;
    }
    
    console.log(`开始解析地址: "${location}"`);
    
    fetch('/static/json/province_city.json')
        .then(response => response.json())
        .then(data => {
            // 先获取省份列表
            const provinces = data['86'] || {};
            console.log(`加载了${Object.keys(provinces).length}个省份数据`);
            
            let foundProvinceCode = '';
            let foundCityCode = '';
            
            // 尝试匹配省份
            for (const provinceCode in provinces) {
                const provinceName = provinces[provinceCode];
                if (location.includes(provinceName)) {
                    foundProvinceCode = provinceCode;
                    console.log(`找到匹配的省份: ${provinceName} (${provinceCode})`);
                    
                    // 如果找到省份，尝试匹配该省的城市
                    const cities = data[provinceCode] || {};
                    console.log(`${provinceName}有${Object.keys(cities).length}个城市数据`);
                    
                    for (const cityCode in cities) {
                        const cityName = cities[cityCode];
                        if (location.includes(cityName)) {
                            foundCityCode = cityCode;
                            console.log(`找到匹配的城市: ${cityName} (${cityCode})`);
                            break;
                        }
                    }
                    break;
                }
            }
            
            // 设置省份和城市
            if (foundProvinceCode) {
                const provinceSelect = document.getElementById('province');
                
                // 检查省份选择器是否已加载选项
                if (provinceSelect.options.length <= 1) {
                    console.log('省份选择器尚未加载选项，先添加省份选项');
                    // 手动添加省份选项
                    provinceSelect.innerHTML = '<option value="">请选择省份</option>';
                    for (const code in provinces) {
                        const option = document.createElement('option');
                        option.value = code;
                        option.textContent = provinces[code];
                        provinceSelect.appendChild(option);
                    }
                }
                
                // 设置省份值
                provinceSelect.value = foundProvinceCode;
                console.log(`已设置省份选择器值: ${foundProvinceCode}`);
                
                // 更新城市选项
                updateCityOptions(foundProvinceCode, data);
                console.log(`已更新城市选择器选项`);
                
                // 等待城市选项加载完成
                setTimeout(() => {
                    // 设置城市
                    if (foundCityCode) {
                        const citySelect = document.getElementById('city');
                        citySelect.value = foundCityCode;
                        console.log(`已设置城市选择器值: ${foundCityCode}`);
                    }
                    
                    // 触发更新事件
                    updateProvinceCity();
                    console.log('触发了省市更新事件');
                    
                    // 检查最终结果
                    const locationField = document.getElementById('project_location');
                    console.log(`最终地址字段值: ${locationField.value}`);
                }, 200);
            } else {
                console.log(`未找到匹配的省份，使用原始地址: ${location}`);
                // 直接设置地址字段
                document.getElementById('project_location').value = location;
            }
        })
        .catch(error => {
            console.error('解析省市数据出错:', error);
            // 出错时直接使用原始地址
            document.getElementById('project_location').value = location;
        });
}
    
// 自动判断气候区划
function autoDetectClimateZone(province, city) {
    const location = (province || '') + (city || '');
    if (!location) return;
    
    // 先尝试使用气候区划脚本提供的功能
    if (window.climateZoneUtils && window.climateZoneUtils.getClimateZone) {
        try {
            const zoneInfo = window.climateZoneUtils.getClimateZone(province, city);
            if (zoneInfo && zoneInfo.气候区划) {
                const climateZoneSelect = document.getElementById('climate_zone');
                climateZoneSelect.value = zoneInfo.气候区划;
                console.log('已自动判断气候区划:', zoneInfo.气候区划);
                return;
            }
        } catch (e) {
            console.error('使用气候区划脚本判断出错:', e);
        }
    }
    
    // 如果脚本功能不可用，提示用户手动选择
    console.log('请手动选择气候区划');
}
    
    // 添加调试脚本检查提取按钮
    document.addEventListener('DOMContentLoaded', function() {
        // 检查提取按钮是否存在
        const extractButton = document.getElementById('extractButton');
        if (extractButton) {
            console.log('已找到提取按钮元素:', extractButton);
            
            // 重新绑定事件处理函数
            extractButton.addEventListener('click', function(e) {
                console.log('提取按钮被点击(通过事件监听器)');
                e.preventDefault(); // 阻止可能的默认行为
                
                // 直接调用提取函数
                extractProjectInfo();
            });
        } else {
            console.error('未找到提取按钮!');
        }
        
        // 检查模态框元素是否存在
        const modal = document.getElementById('aiExtractModal');
        if (modal) {
            console.log('已找到模态框元素');
        } else {
            console.error('未找到模态框元素!');
        }
    });


// Toast通知系统

// 全局Toast函数实现
function toast(message, type = 'info') {
// 显示Toast
const container = document.getElementById('custom-toast-container');
if (container) {
    // 确保container有足够高的z-index
    container.style.zIndex = '9999';
    
    const toastElement = document.createElement('div');
    toastElement.className = `custom-toast ${type}`;
    
    // 根据类型设置图标
    let icon = '';
    switch(type) {
        case 'success':
            icon = '<i class="fas fa-check-circle custom-toast-icon"></i>';
            break;
        case 'error':
            icon = '<i class="fas fa-exclamation-circle custom-toast-icon"></i>';
            break;
        case 'warning':
            icon = '<i class="fas fa-exclamation-triangle custom-toast-icon"></i>';
            break;
        case 'info':
        default:
            icon = '<i class="fas fa-info-circle custom-toast-icon"></i>';
            break;
    }
    
    toastElement.innerHTML = `
        ${icon}
        <div class="custom-toast-message">${message}</div>
    `;
    
    container.appendChild(toastElement);
    
    // 3秒后自动移除
    setTimeout(() => {
        toastElement.style.animation = 'toast-out 0.3s ease-in forwards';
        setTimeout(() => {
            if (container.contains(toastElement)) {
                container.removeChild(toastElement);
            }
        }, 300);
    }, 3000);
}
}

})();
