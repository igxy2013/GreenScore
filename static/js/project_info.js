var provinceData = {};
var cityData = {};
// 用户权限控制状态
var userPermissions = null;
var isFormReadOnly = false;
// 当前激活的标签页
var currentTab = 'word';
// 粘贴的图片数据
var pastedImage = null;
// 上次提取的数据
var lastExtractedData = null;
// 评价标准初始值
let initialStandardValue = '';
// 项目地点初始值
let initialProjectLocation = '';

// 初始化省市数据
document.addEventListener('DOMContentLoaded', function() {
    initializeProvinceCitySelectors();
    loadUserPermissions();

    // --- 新增：存储评价标准初始值 ---
    const standardSelect = document.getElementById('standard_selection');
    if (standardSelect) {
        initialStandardValue = standardSelect.value;
        console.log('Initial standard value stored:', initialStandardValue);
    }
    // --- 新增结束 ---

    // --- 新增：存储项目地点初始值 ---
    const locationInput = document.getElementById('project_location');
    if (locationInput) {
        initialProjectLocation = locationInput.value;
        console.log('Initial project location stored:', initialProjectLocation);
    }
    // --- 新增结束 ---

    // --- 修改：整合 Switchery 初始化和状态更新 --- 
    const scoreToggle = document.getElementById('scoreToggle');
    let switcheryInstance = null; // 将实例变量提升作用域，初始为 null

    // 1. 初始化 Switchery (如果元素存在)
    if (scoreToggle) {
        try {
            switcheryInstance = new Switchery(scoreToggle, { 
                color: '#34C759', 
                secondaryColor: '#e9e9ea',
                jackColor: '#ffffff', 
                jackSecondaryColor: '#ffffff',
                size: 'small'
            });
            console.log("Switchery 已成功初始化");

            // 监听开关的人工交互变化 (用于保存到 localStorage)
            scoreToggle.addEventListener('change', function() {
                console.log("用户手动切换开关状态:", this.checked ? "开启" : "关闭");
                localStorage.setItem('scoreToggleState', this.checked);
            });
        } catch (e) {
            console.error("Switchery 初始化失败:", e);
            // 即使初始化失败，也尝试继续执行后续逻辑
        }
    } else {
        console.error('未能找到 ID 为 scoreToggle 的开关元素进行初始化');
    }

    // 2. 页面加载后获取项目信息并更新开关状态
    const projectIdInput = document.getElementById('project_id');
    const currentProjectId = projectIdInput ? projectIdInput.value : null;
    
    if (currentProjectId && scoreToggle) { // 确保项目ID和开关元素都存在
        console.log("页面加载，获取项目信息以更新开关状态...");
        fetch('/api/project_info?project_id=' + currentProjectId)
            .then(response => {
                if (!response.ok) {
                    throw new Error('获取项目信息失败: ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log("API /api/project_info 返回数据:", data);
                if (data && typeof data.auto_calculate_score !== 'undefined') {
                    const newState = data.auto_calculate_score; // 从API获取的布尔值
                    const currentState = scoreToggle.checked;
                    
                    console.log(`开关更新: API值=${newState}, 当前DOM状态=${currentState}`);
                    
                    // 只有当API状态与当前DOM状态不同时才更新
                    if (newState !== currentState) {
                        scoreToggle.checked = newState;
                        console.log(`已设置 scoreToggle.checked = ${newState}`);
                        
                        // 更新 Switchery 的视觉状态 (使用上面初始化的实例)
                        if (switcheryInstance) {
                            // 先销毁旧的Switchery实例（如果存在并且需要重建）
                            // 但通常setPosition足够了
                            switcheryInstance.setPosition(true); // true表示立即更新，无动画
                            console.log("已调用 switchery.setPosition() 更新视觉状态");
                        } else {
                            // 如果 Switchery 初始化失败，我们无法更新视觉效果
                            console.error("无法更新视觉状态：Switchery实例未初始化或初始化失败!"); 
                        }
                    } else {
                        console.log("API状态与DOM状态一致，无需更新");
                    }
                } else {
                    console.warn('API /api/project_info 未返回有效的 auto_calculate_score 字段');
                }
            })
            .catch(error => {
                console.error('页面加载时获取项目信息失败:', error);
            });
    }
    // --- 修改结束 ---
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
                cityData = data; // <--- 存储完整数据，包含所有省份及其城市
                
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
                const response = await fetch(`/api/star_case_scores?project_id=${projectId}`);
                const data = await response.json();

                // 恢复按钮状态
                this.textContent = originalText;
                this.disabled = false;

                if (data.success) {
                    alert(`成功导入 ${data.imported_count} 条星级案例数据！\n标准: ${data.standard}\n星级目标: ${data.star_rating_target}`);
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

// 页面加载完成后执行计算和更新
document.addEventListener('DOMContentLoaded', function() {
    // 初始化省市选择器
    initProvinceCity();
    const scoreToggle = document.getElementById('scoreToggle');
    // 直接从 localStorage 读取状态，而不是从 checkbox 的 .checked 属性
    const isChecked = localStorage.getItem('scoreToggleState') === 'true';
    console.log("isChecked (from localStorage)", isChecked);
    if (isChecked) { 
        console.log("自动计算功能开启，将异步执行");
        // 将耗时操作放入setTimeout异步执行
        setTimeout(calculateAndUpdateScores, 0);
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
    let jscs="";//人均用地指标技术措施
    if (!projectId) {
        console.log('未找到项目ID，无法更新得分');
        return;
    }
    
    try {
        if (standard === '成都市标'){
            if (buildingType === '居住建筑'){
                if(perCapitaLandScore>0){
                    jscs="满足要求,详见建筑施工图及总图经济技术指标";
                }
                else{
                    jscs="";
                }
                updateDatabaseScore('3.1.2.14', perCapitaLandScore,null,jscs);

            } else if (buildingType === '公共建筑'){
                updateDatabaseScore('3.1.2.14', plotRatioScore,null,null);

            }
            updateDatabaseScore('3.1.2.15', undergroundScore,null,null);
            updateDatabaseScore('3.1.2.21', greenSpaceScore,null,null);
            updateDatabaseScore('3.1.2.16', parkingScore,null,null);

        }
        else if (standard === '四川省标'){
            if (buildingType === '居住建筑'){
                if(perCapitaLandScore>0){
                    jscs="满足要求,详见建筑施工图及总图经济技术指标";
                }
                else{
                    jscs="";
                }
                updateDatabaseScore('3.1.16', perCapitaLandScore,null,jscs);


            }
            else if (buildingType === '公共建筑'){
                updateDatabaseScore('3.1.16', plotRatioScore,null,null);

            }
            updateDatabaseScore('3.1.17', undergroundScore,null,null);
            updateDatabaseScore('3.1.25', greenSpaceScore,null,null);
            updateDatabaseScore('3.1.18', parkingScore,null,null);

        }
        else if (standard === '国标'){
            if (buildingType === '居住建筑'){
                if(perCapitaLandScore>0){
                    jscs="满足要求,详见建筑施工图及总图经济技术指标";
                }
                else{
                    jscs="";
                }
                updateDatabaseScore('7.2.1', perCapitaLandScore,null,jscs);

            }
            else if (buildingType === '公共建筑'){
                updateDatabaseScore('7.2.1', plotRatioScore,null,null);
            }
            updateDatabaseScore('7.2.2', undergroundScore,null,null);
            updateDatabaseScore('8.2.3', greenSpaceScore,null,null);
            updateDatabaseScore('7.2.3', parkingScore,null,null);
        }
        console.log('得分更新完成');
    } catch (error) {
        console.error('更新得分时出错:', error);
    }
}
//自动更新技术措施
function auto_update_jscs(){
        const buildingType = document.getElementById('building_type').value;   
        let standard = document.getElementById('current-project-standard')?.value || '成都市标';
        let has_underground_garage = document.getElementById('has_underground_garage')?.value || '无';
        let has_elevator = document.getElementById('has_elevator')?.value || '无';
        let ac_type = document.getElementById('ac_type')?.value || '无';

        try {
            if (standard === '成都市标'){
                if (buildingType === '居住建筑'){
                    updateDatabaseScore('3.1.1.26', 0,null, '满足要求，详见室外热环境分析报告');
                    updateDatabaseScore('3.6.1.2', 0,null, '满足要求，详见室外热环境分析报告');
                } else if (buildingType === '公共建筑'){
                    updateDatabaseScore('3.1.1.26', 0,null, '本项目为非居住区，满足要求');
                    updateDatabaseScore('3.6.1.2', 0,null, '本项目为非居住区，满足要求');
                }
                if (has_underground_garage === '有'){
                    updateDatabaseScore('3.4.1.5', 0,null, '满足要求，详见暖通设计图纸');
                    updateDatabaseScore('3.5.1.2', 0,null, '满足要求，详见电气设计图纸');
                }
                else{
                    updateDatabaseScore('3.4.1.5', 0,"不参评", '本项目无地下车库，本条不参评');
                    updateDatabaseScore('3.5.1.2', 0,"不参评", '本项目无地下车库，本条不参评');
                }   
                if (has_elevator === '有'){
                    updateDatabaseScore('3.5.1.8', 0,null, '满足要求，详见电气设计图纸');
                }
                else{
                    updateDatabaseScore('3.5.1.8', 0,"不参评", '本项目无电梯或扶梯，本条不参评');
                }
                if (ac_type === '无'){
                    updateDatabaseScore('3.4.1.3', 0,"不参评", '本项目无空调，本条不参评');
                    updateDatabaseScore('3.4.1.4', 0,"不参评", '本项目无空调，本条不参评');
                }
                else if (ac_type === '分体式空调'){
                    updateDatabaseScore('3.4.1.3', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('3.4.1.4', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('3.4.2.4', 5,null, '本项目设置分体空调，设计能效等级为二级');
                    updateDatabaseScore('3.4.2.5', 5,null, '本项目设置分体空调，满足要求');
                }
                else if (ac_type === '多联式空调'){
                    updateDatabaseScore('3.4.1.3', 0,null, '本项目设置多联式空调，直接满足要求');
                    updateDatabaseScore('3.4.1.4', 0,null, '本项目设置多联式空调，直接满足要求');
                }   
                else if (ac_type === '集中空调'){
                    updateDatabaseScore('3.4.1.3', 0,null, '满足要求，详见暖通设计图纸');
                }
                else if (ac_type === '组合形式'){
                    updateDatabaseScore('3.4.1.3', 0,null, '满足要求，详见暖通设计图纸');
                }
    
            }
            else if (standard === '四川省标'){
                if (buildingType === '居住建筑'){
                    updateDatabaseScore('2.6.2', 0,null, '满足要求，详见室外热环境分析报告');
                    updateDatabaseScore('2.7.7', 0,null, '满足要求，详见室外热环境分析报告');
                }
                else if (buildingType === '公共建筑'){
                    updateDatabaseScore('2.6.2', 0,null, '本项目为非居住区，满足要求');
                    updateDatabaseScore('2.7.7', 0,null, '本项目为非居住区，满足要求');
                }
                if (has_underground_garage === '有'){
                    updateDatabaseScore('2.4.5', 0,null, '满足要求，详见暖通设计图纸');
                    updateDatabaseScore('2.5.2', 0,null, '满足要求，详见电气设计图纸');
                }
                else{
                    updateDatabaseScore('3.4.1.5', 0,"不参评", '本项目无地下车库，本条不参评');
                    updateDatabaseScore('3.5.1.2', 0,"不参评", '本项目无地下车库，本条不参评');
                }   
                if (has_elevator === '有'){
                    updateDatabaseScore('2.5.8', 0,null, '满足要求，详见电气设计图纸');
                }
                else{
                    updateDatabaseScore('2.5.8', 0,"不参评", '本项目无电梯或扶梯，本条不参评');
                }
                if (ac_type === '无'){
                    updateDatabaseScore('2.4.3', 0,"不参评", '本项目无空调，本条不参评');
                    updateDatabaseScore('2.4.4', 0,"不参评", '本项目无空调，本条不参评');
                }
                else if (ac_type === '分体式空调'){
                    updateDatabaseScore('2.4.3', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('2.4.4', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('2.4.6', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('3.4.4', 5,null, '本项目采用分体式空调系统，且设计能效等级为二级。');
                    updateDatabaseScore('3.4.5', 5,null, '本项目采用分体式空调系统，且设计能效等级为二级。');
                }
                else if (ac_type === '多联式空调'){
                    updateDatabaseScore('2.4.3', 0,null, '本项目设置多联式空调，满足要求');
                    updateDatabaseScore('3.4.5', 0,null, '本项目设置多联式空调，满足要求');
                }   
                else if (ac_type === '集中空调'){
                    updateDatabaseScore('2.4.3', 0,null, '满足要求，详见暖通设计图纸');
                }
                else if (ac_type === '组合形式'){
                    updateDatabaseScore('2.4.3', 0,null, '满足要求，详见暖通设计图纸');
                }
    
            }
            else if (standard === '国标'){
                if (buildingType === '居住建筑'){
                    updateDatabaseScore('8.1.2', 0,null, '满足要求，详见室外热环境分析报告');
    
                }
                else if (buildingType === '公共建筑'){
                    updateDatabaseScore('8.1.2', 0,null, '本项目为非居住区，满足要求');
                }

                if (has_underground_garage === '有'){
                    updateDatabaseScore('5.1.9', 0,null, '满足要求，详见暖通设计图纸');
                }
                else{
                    updateDatabaseScore('5.1.9', 0,"不参评", '本项目无地下车库，本条不参评');
                } 
                if (has_elevator === '有'){
                    updateDatabaseScore('7.1.6', 0,null, '满足要求，详见电气设计图纸');
                }
                else{
                    updateDatabaseScore('7.1.6', 0,"不参评", '本项目无电梯或扶梯，本条不参评');
                }
                if (ac_type === '无'){
                    updateDatabaseScore('5.1.6', 0,"不参评", '本项目无空调，本条不参评');
                    updateDatabaseScore('5.1.8', 0,"不参评", '本项目无空调，本条不参评');
                    updateDatabaseScore('7.1.2', 0,"不参评", '本项目无空调，本条不参评');
                }
                else if (ac_type === '分体式空调'){
                    updateDatabaseScore('5.1.6', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('5.1.8', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('7.1.2', 0,null, '本项目设置分体空调，直接满足要求');
                    updateDatabaseScore('7.2.5', 5,null, '本项目采用分体式空调系统，且设计能效等级为二级。');
                    updateDatabaseScore('7.2.6', 5,null, '本项目采用分体式空调系统，且设计能效等级为二级。');
                }
                else if (ac_type === '多联式空调'){
                    updateDatabaseScore('5.1.6', 0,null, '本项目设置多联式空调，满足要求');
                    updateDatabaseScore('7.1.2', 0,null, '本项目设置多联式空调，满足要求');
                    updateDatabaseScore('7.2.6', 5,null, '本项目采用分体式空调系统，且设计能效等级为二级。');
                }   
                else if (ac_type === '集中空调'){
                    updateDatabaseScore('5.1.6', 0,null, '满足要求，详见暖通设计图纸');
                    updateDatabaseScore('7.1.2', 0,null, '满足要求，详见暖通设计图纸');
                }
                else if (ac_type === '组合形式'){
                    updateDatabaseScore('5.1.6', 0,null, '满足要求，详见暖通设计图纸');
                    updateDatabaseScore('7.1.2', 0,null, '满足要求，详见暖通设计图纸');
                }
            }
            console.log('技术措施更新完成');
        } catch (error) {
            console.error('更新技术措施时出错:', error);
        }
}
document.addEventListener('DOMContentLoaded', function() {
    // 查找保存按钮并添加事件监听器
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

            // --- 新增：检查评价标准是否更改 ---
            const standardSelect = document.getElementById('standard_selection');
            let currentStandardValue = '';
            let standardHasChanged = false;
            if (standardSelect) {
                currentStandardValue = standardSelect.value;
                standardHasChanged = currentStandardValue !== initialStandardValue;
                console.log('Checking standard change:', { initial: initialStandardValue, current: currentStandardValue, changed: standardHasChanged });
            }
            // --- 新增结束 ---

            // --- 新增：检查项目地点是否更改 ---
            const locationInput = document.getElementById('project_location');
            let currentLocationValue = '';
            let locationHasChanged = false;
            if (locationInput) {
                currentLocationValue = locationInput.value;
                locationHasChanged = currentLocationValue !== initialProjectLocation;
                console.log('Checking location change:', { initial: initialProjectLocation, current: currentLocationValue, changed: locationHasChanged });
            }
            // --- 新增结束 ---
            
            // 获取得分计算开关的当前状态并添加到表单数据
            const scoreToggleInput = document.getElementById('scoreToggle');
            const autoCalcEnabled = scoreToggleInput ? scoreToggleInput.checked : false;
            formData.append('auto_calculate_score', autoCalcEnabled);
            console.log('Sending auto_calculate_score:', autoCalcEnabled);
            
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
                    // --- 修改：根据评价标准或项目地点是否更改决定刷新或继续 ---
                    if (standardHasChanged || locationHasChanged) {
                        toast('项目信息保存成功', 'success');
                        // 更新初始值，防止重复刷新
                        initialStandardValue = currentStandardValue;
                        initialProjectLocation = currentLocationValue; // 更新地点初始值
                        // 短暂延迟后刷新页面
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000); // 延迟1秒以便用户看到提示
                    } else {
                        toast('项目信息保存成功', 'success');
                        // 更新页面显示的项目ID
                        if (data.project_id) {
                            document.getElementById('project_id').value = data.project_id;
                        }
                        
                        const scoreToggle = document.getElementById('scoreToggle');
                        // 读取 input 的当前 checked 状态来决定是否计算
                        const isChecked = scoreToggle ? scoreToggle.checked : false; 
                        console.log("isChecked (from input element)", isChecked);
                        if (isChecked) { 
                            console.log("自动计算功能开启，将异步执行");
                            // calculateAndUpdateScores(); // 移除或保持注释之前的直接调用
                            // 将耗时操作放入setTimeout异步执行
                            setTimeout(calculateAndUpdateScores, 0);
                        }
                        auto_update_jscs();
                    }
                    // --- 修改结束 ---
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
    } else {
        console.error('未能找到保存项目信息按钮 (saveProjectInfoBtn)!'); // 如果找不到按钮，输出错误
    }
});
        
// AI提取项目信息相关函数
    
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
        
        // 如果有拖放的Word文件，显示文件名
        if (window.droppedWordFile) {
            showWordFileName(window.droppedWordFile);
        } else if (document.getElementById('wordFileInput').files.length > 0) {
            showWordFileName(document.getElementById('wordFileInput').files[0]);
        }
        
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
    
// 清除图片预览
function clearImagePreview(event) {
    // 阻止事件冒泡，防止触发文件选择
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const previewContainer = document.getElementById('previewContainer');
    const dropAreaText = document.getElementById('dropAreaText');
    const imageFileInput = document.getElementById('imageFileInput');
    const clearImageBtn = document.getElementById('clearImageBtn');
    const imagePreview = document.getElementById('imagePreview');

    if (previewContainer) previewContainer.classList.add('hidden');
    if (dropAreaText) dropAreaText.classList.remove('hidden');
    if (clearImageBtn) clearImageBtn.classList.add('hidden');
    if (imageFileInput) imageFileInput.value = ''; // 清空文件输入
    if (imagePreview) imagePreview.src = ''; // 清空预览图片

    pastedImage = null; // 清除粘贴的图片数据
    console.log('图片预览已清除');
}

// 处理图片预览
function handleImagePreview(file) {
    if (!file || !file.type || !file.type.startsWith('image/')) {
        console.warn('无效的图片文件:', file);
        toast('请选择有效的图片文件 (JPG, PNG, BMP等)', 'warning');
        clearImagePreview(); // 清除可能存在的无效状态
        return;
    }

    console.log('处理图片预览:', file.name);
    const reader = new FileReader();

    reader.onload = function(e) {
        console.log('FileReader 加载完成');
        const img = document.getElementById('imagePreview');
        const previewContainer = document.getElementById('previewContainer');
        const dropAreaText = document.getElementById('dropAreaText');
        const clearImageBtn = document.getElementById('clearImageBtn');

        if (img && previewContainer && dropAreaText && clearImageBtn) {
            // --- 开始强制样式修改 ---
            img.onload = () => {
                // console.log(`图片已加载: ${img.naturalWidth}x${img.naturalHeight}`);
                // 确保图片加载后容器可见
                previewContainer.style.display = 'block'; 
                img.style.display = 'block'; // 确保img本身也显示
                // 可以临时设置固定大小以调试
                // img.style.height = '160px';
                // img.style.width = 'auto'; 
            };
            
            img.src = e.target.result;
            // console.log('设置 img.src');

            // 强制设置容器和文本的显示/隐藏
            // previewContainer.classList.remove('hidden'); // 尝试移除类
            // previewContainer.style.display = 'block';    // 直接设置style
            // console.log('设置 previewContainer display: block');

            // dropAreaText.classList.add('hidden');      // 尝试添加类
            // dropAreaText.style.display = 'none';       // 直接设置style
            // console.log('设置 dropAreaText display: none');  

            // clearImageBtn.classList.remove('hidden'); // 尝试移除类
            // clearImageBtn.style.display = 'inline-block'; // 直接设置style (或 block)
            // console.log('设置 clearImageBtn display: inline-block');
            // --- 结束强制样式修改 ---

            // console.log('图片预览尝试显示');
        } else {
            console.error('缺少用于预览的DOM元素');
            toast('无法显示图片预览，页面元素缺失', 'error');
        }
    };

    reader.onerror = function(e) {
        console.error('FileReader 读取错误:', e);
        toast('读取图片文件时出错', 'error');
        clearImagePreview();
    };

    reader.readAsDataURL(file);
}
    
// 显示Word文件名
function showWordFileName(file) {
    console.log("显示Word文件名函数被调用:", file ? file.name : "无文件");
    const fileNameDiv = document.getElementById('wordFileName');
    if (!fileNameDiv) {
        console.error("未找到wordFileName元素");
        return;
    }
    
    if (file) {
        fileNameDiv.textContent = `已选择: ${file.name}`;
        fileNameDiv.style.display = 'block'; // 使用style.display确保显示
        fileNameDiv.classList.remove('hidden');
        console.log("文件名显示已设置为:", file.name);
    } else {
        fileNameDiv.classList.add('hidden');
        fileNameDiv.style.display = 'none';
        console.log("文件名显示已隐藏");
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
    if (wordFileName) {
        wordFileName.classList.add('hidden');
        wordFileName.style.display = 'none';
    }
    
    clearImagePreview(); // 重置图片预览区域
    
    // 添加ESC键监听
    document.addEventListener('keydown', handleEscKeyForModal);
    // 添加粘贴监听 (只在模态框打开时监听)
    document.addEventListener('paste', handlePasteImage);
    
    // 确保DOM已经完全加载再初始化文件上传监听
    // 使用 requestAnimationFrame 确保在下一次绘制前执行
    requestAnimationFrame(() => {
        console.log("延迟初始化文件上传监听器 (requestAnimationFrame)");
        initFileUploadListeners(); // 初始化所有监听器
        
        // 检查各元素是否已加载
        console.log("检查关键元素:");
        console.log("- wordFileInput:", !!document.getElementById('wordFileInput'));
        console.log("- wordFileName:", !!document.getElementById('wordFileName'));
        console.log("- wordDropArea:", !!document.getElementById('wordDropArea'));
        console.log("- imageFileInput:", !!document.getElementById('imageFileInput'));
        console.log("- imageDropArea:", !!document.getElementById('imageDropArea'));
        console.log("- imagePreview:", !!document.getElementById('imagePreview'));
    });
    
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
        'wordFileName': el => { el.classList.add('hidden'); el.textContent = '尚未选择文件'; },
        'extractResult': el => el.classList.add('hidden'),
        'extractedInfo': el => el.innerHTML = '',
        'applyButton': el => el.classList.add('hidden')
        // 图片相关的重置由 clearImagePreview 处理
    };
    clearImagePreview(); // 调用清除函数来重置图片区域
    
    for (const [id, resetFn] of Object.entries(resetElements)) {
        const element = document.getElementById(id);
        if (element) resetFn(element);
    }
    
    // 清除粘贴的图片数据
    pastedImage = null;
    // 清除拖放的Word文件
    window.droppedWordFile = null;
    
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
    console.log("[initFileUploadListeners] Function called."); // 新增日志

    // Word文件选择
    const wordFileInput = document.getElementById('wordFileInput');
    if (wordFileInput) {
        console.log("为wordFileInput添加change事件监听器");
        wordFileInput.addEventListener('change', function(event) {
            console.log("wordFileInput change事件触发");
            console.log("选择的文件:", this.files);
            if (this.files && this.files.length > 0) {
                console.log("选择了文件:", this.files[0].name);
                // 保存到全局变量，以便后续使用
                window.droppedWordFile = this.files[0];
                showWordFileName(this.files[0]);
            } else {
                console.log("未选择文件");
                window.droppedWordFile = null;
                showWordFileName(null);
            }
        });
    } else {
        console.error("未找到wordFileInput元素");
    }
    
    // 添加Word拖放区域的拖放事件监听
    const wordDropArea = document.getElementById('wordDropArea');
    if (wordDropArea) {
        console.log("为wordDropArea添加拖放事件监听器");
        
        // 拖拽文件进入区域
        wordDropArea.addEventListener('dragenter', function(e) {
            console.log("dragenter事件触发");
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('border-purple-300');
            this.classList.add('bg-gray-700');
        });
        
        // 拖拽文件在区域上方
        wordDropArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            // 添加视觉反馈但不记录日志，避免控制台刷屏
            this.classList.add('border-purple-300');
            this.classList.add('bg-gray-700');
        });
        
        // 拖拽文件离开区域
        wordDropArea.addEventListener('dragleave', function(e) {
            console.log("dragleave事件触发");
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('border-purple-300');
            this.classList.remove('bg-gray-700');
        });
        
        // 拖拽文件放置到区域
        wordDropArea.addEventListener('drop', function(e) {
            console.log("drop事件触发");
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('border-purple-300');
            this.classList.remove('bg-gray-700');
            
            try {
                const dt = e.dataTransfer;
                console.log("拖放的文件数量:", dt.files ? dt.files.length : 0);
                
                if (dt.files && dt.files.length > 0) {
                    const file = dt.files[0];
                    console.log("拖放的文件:", file.name, file.size, file.type);
                    
                    // 检查文件类型
                    if (!file.name.endsWith('.doc') && !file.name.endsWith('.docx')) {
                        console.error("文件类型不是Word文档:", file.type);
                        alert('请上传Word文档（.doc或.docx格式）');
                        return;
                    }
                    
                    // 由于无法直接设置fileInput.files，我们保存文件到全局变量
                    window.droppedWordFile = file;
                    // 显示文件名
                    showWordFileName(file);
                    
                    console.log('成功拖放Word文件:', file.name);
                }
            } catch (error) {
                console.error("处理拖放文件时出错:", error);
                alert('处理文件时出错: ' + error.message);
            }
        });
    } else {
        console.error("未找到wordDropArea元素");
    }
    
    // 图片文件选择
    const imageFileInput = document.getElementById('imageFileInput');
    if (imageFileInput) {
        console.log("[initFileUploadListeners] Found imageFileInput element."); // 新增日志
        imageFileInput.addEventListener('change', function() {
            console.log("[imageFileInput change event] Triggered."); // 新增日志
            // Check if files were selected
            if (this.files && this.files.length > 0) {
                console.log("[imageFileInput change event] File selected:", this.files[0].name); // 新增日志
                handleImagePreview(this.files[0]);
            } else {
                console.log("[imageFileInput change event] No files selected."); // 新增日志
            }
        });
        console.log("[initFileUploadListeners] Added 'change' listener to imageFileInput."); // 新增日志
    } else {
        console.error("[initFileUploadListeners] Could not find imageFileInput element!"); // 新增日志
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
    console.log("========== 开始执行extractProjectInfo函数 ==========");
    
    // 检查是否有编辑权限
    if (isFormReadOnly) {
        console.log("表单为只读状态，无法提取");
        toast('您没有编辑权限，无法使用AI提取功能', 'error');
        closeAiExtractModal(); // 关闭模态框
        return;
    }
    
    // 获取相关DOM元素
    const wordFileInput = document.getElementById('wordFileInput');
    const imageFileInput = document.getElementById('imageFileInput');
    const extractResult = document.getElementById('extractResult');
    const extractLoading = document.getElementById('extractLoading');
    const applyButton = document.getElementById('applyButton');
    
    console.log("DOM元素检查:");
    console.log("- wordFileInput存在:", !!wordFileInput);
    console.log("- imageFileInput存在:", !!imageFileInput);
    console.log("- extractResult存在:", !!extractResult);
    console.log("- extractLoading存在:", !!extractLoading);
    console.log("- applyButton存在:", !!applyButton);
    
    // 隐藏上一次的结果
    if (extractResult) extractResult.classList.add('hidden');
    if (applyButton) applyButton.classList.add('hidden');
    
    // 显示加载状态
    if (extractLoading) extractLoading.classList.remove('hidden');
    
    // 准备上传的数据
    const formData = new FormData();
    
    console.log("当前激活的标签页:", currentTab);
    
    // 根据当前选择的标签页获取文件
    if (currentTab === 'word') {
        console.log("当前是Word标签页");
        // 优先使用拖放的文件
        const wordFile = window.droppedWordFile || (wordFileInput.files && wordFileInput.files.length > 0 ? wordFileInput.files[0] : null);
        
        console.log("检查是否有Word文件:");
        console.log("- 全局拖放文件:", window.droppedWordFile ? window.droppedWordFile.name : "无");
        console.log("- 文件输入框:", wordFileInput.files && wordFileInput.files.length > 0 ? wordFileInput.files[0].name : "无");
        console.log("- 最终使用:", wordFile ? wordFile.name : "无");
        
        if (!wordFile) {
            console.log("未选择Word文档，显示提示并终止操作");
            alert('请选择Word文档');
            if (extractLoading) extractLoading.classList.add('hidden');
            return;
        }
        
        try {
            formData.append('word_file', wordFile);
            console.log("已选择Word文件:", wordFile.name, "大小:", wordFile.size, "类型:", wordFile.type);
        } catch (error) {
            console.error("添加文件到FormData时出错:", error);
            alert('处理文件时出错: ' + error.message);
            if (extractLoading) extractLoading.classList.add('hidden');
            return;
        }
    } else {
        // 图片标签页处理...
        console.log("当前是图片标签页");
        const imageFile = imageFileInput.files[0] || pastedImage;
        console.log("图片文件状态:", 
            imageFileInput.files && imageFileInput.files.length > 0 ? "已选择文件" : "未选择文件", 
            pastedImage ? "有粘贴图片" : "无粘贴图片");
        
        if (!imageFile) {
            console.log("未选择或粘贴图片，显示提示并终止操作");
            alert('请选择或粘贴图片');
            if (extractLoading) extractLoading.classList.add('hidden');
            return;
        }
        
        try {
            formData.append('file', imageFile);
            console.log("已添加图片文件到表单:", imageFile.name, "大小:", imageFile.size, "类型:", imageFile.type);
        } catch (error) {
            console.error("添加图片到FormData时出错:", error);
            alert('处理图片时出错: ' + error.message);
            if (extractLoading) extractLoading.classList.add('hidden');
            return;
        }
    }
    
    // 发送请求
    console.log("准备发送API请求到: /api/extract_project_info");
    console.log("FormData包含的键:", Array.from(formData.keys()));
    
    fetch('/api/extract_project_info', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        console.log("API响应状态:", response.status);
        return response.json();
    })
    .then(data => {
        // 隐藏加载状态
        if (extractLoading) extractLoading.classList.add('hidden');
        
        console.log("API响应数据:", data);
        
        if (data.success) {
            // 显示提取结果
            const extractedInfo = document.getElementById('extractedInfo');
            let infoHTML = '';
            
            // 兼容旧版和新版接口返回格式
            const projectInfo = data.project_info || data.info;
            console.log("API返回的原始数据:", JSON.stringify(data));
            console.log("提取到的项目信息:", JSON.stringify(projectInfo));
            
            // 清理拖放的Word文件
            window.droppedWordFile = null;
            
            // 遍历提取的信息并格式化显示
            for (const key in projectInfo) {
                // 跳过原始文本字段
                if (key === 'raw_text') continue;
                infoHTML += `<div class="mb-1">
                    <span class="text-purple-300 font-medium">${key}:</span> 
                    <span class="text-gray-200">${projectInfo[key] || '-'}</span>
                </div>`;
            }
            
            if (extractedInfo) {
                extractedInfo.innerHTML = infoHTML;
                document.getElementById('extractResult').classList.remove('hidden');
                document.getElementById('applyButton').classList.remove('hidden');
                
                console.log("提取结果已显示");
            } else {
                console.error("未找到extractedInfo元素，无法显示结果");
            }
            
            // 存储提取的信息以便后续应用
            window.extractedProjectInfo = projectInfo;
            lastExtractedData = projectInfo; // 同时保存到lastExtractedData
            console.log("已保存提取信息到window.extractedProjectInfo");
            
            // 验证保存是否成功
            setTimeout(() => {
                console.log("验证提取信息:", window.extractedProjectInfo ? "已保存" : "未保存");
                if (window.extractedProjectInfo) {
                    console.log("保存的字段:", Object.keys(window.extractedProjectInfo).join(", "));
                }
            }, 100);
        } else {
            console.error("API返回失败:", data.message || '未知错误');
            alert('提取失败: ' + (data.message || '未知错误'));
        }
    })
    .catch(error => {
        if (extractLoading) extractLoading.classList.add('hidden');
        console.error('提取项目信息出错:', error);
        alert('提取失败: ' + error.message);
        
        // 清理拖放的Word文件
        window.droppedWordFile = null;
    });
    
    console.log("========== extractProjectInfo函数执行完毕 ==========");
}

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
                const provinceName = this.options[this.selectedIndex]?.text || '';
                updateCityOptions(provinceCode, data);
                updateProvinceCity(); // 更新隐藏字段
                // 在用户更改省份后尝试自动检测气候区划
                const citySelect = document.getElementById('city');
                const cityName = citySelect.options[citySelect.selectedIndex]?.text || '';
                if (provinceName && cityName && provinceName !== '请选择省份' && cityName !== '请选择城市') {
                    autoDetectClimateZone(provinceName, cityName);
                }
            });
            
            // 城市变化时更新隐藏字段
            citySelect.addEventListener('change', function() {
                updateProvinceCity(); // 更新隐藏字段
                // 在用户更改城市后尝试自动检测气候区划
                const provinceSelect = document.getElementById('province');
                const provinceName = provinceSelect.options[provinceSelect.selectedIndex]?.text || '';
                const cityName = this.options[this.selectedIndex]?.text || '';
                 if (provinceName && cityName && provinceName !== '请选择省份' && cityName !== '请选择城市') {
                    autoDetectClimateZone(provinceName, cityName);
                }
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
    
    console.log(`开始解析地址: "${location}" (使用缓存数据)`);
    
    // 使用已加载的全局数据，不再 fetch
    const provinces = provinceData || {}; 
    const allCityData = cityData || {}; // 使用包含所有层级的数据
    
    console.log(`缓存中有${Object.keys(provinces).length}个省份数据`);
    
    let foundProvinceCode = '';
    let foundCityCode = '';
    
    // 尝试匹配省份
    for (const provinceCode in provinces) {
        const provinceName = provinces[provinceCode];
        if (location.includes(provinceName)) {
            foundProvinceCode = provinceCode;
            console.log(`找到匹配的省份: ${provinceName} (${provinceCode})`);
            
            // 如果找到省份，尝试匹配该省的城市
            const cities = allCityData[provinceCode] || {}; // 从完整数据中获取该省的城市
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
        const citySelect = document.getElementById('city');
        
        // 检查省份选择器是否已加载选项
        if (provinceSelect.options.length <= 1 && Object.keys(provinces).length > 0) {
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
        
        // 更新城市选项 (使用完整数据)
        updateCityOptions(foundProvinceCode, allCityData); 
        console.log(`已更新城市选择器选项`);
        
        // 移除 setTimeout，直接设置城市并更新
        if (foundCityCode) {
            citySelect.value = foundCityCode;
            console.log(`已设置城市选择器值: ${foundCityCode}`);
        }
        
        // 触发更新事件 (这会根据下拉框更新 project_location 输入框)
        updateProvinceCity(); 
        console.log('触发了省市更新事件');
        
        // 检查最终结果
        const locationField = document.getElementById('project_location');
        console.log(`解析后地址字段值: ${locationField.value}`);

    } else {
        console.log(`未找到匹配的省份，使用原始地址: ${location}`);
        // 直接设置地址字段 (或者保持不变，因为之前可能已经设置过了)
        // document.getElementById('project_location').value = location; 
    }

    // 移除 fetch 和 catch
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
    console.log('Toast function called with message:', message, 'and type:', type); // 添加日志：记录 toast 函数调用
    // 显示Toast
    const container = document.getElementById('custom-toast-container');
    if (container) {
        console.log('Appending toast element to container:', container); // 添加日志：记录元素添加
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


