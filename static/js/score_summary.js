// 项目ID缓存
let cachedProjectId = null;

// 获取当前选中的项目ID
function getSelectedProjectId() {
    // 如果有缓存直接返回
    if (cachedProjectId) {
        return cachedProjectId;
    }

    // 尝试从各种来源获取项目ID
    let projectId = document.getElementById('current-project-id')?.value
        || document.getElementById('project_id')?.value
        || new URLSearchParams(window.location.search).get('project_id');
    
    // 缓存获取到的项目ID
    if (projectId) {
        cachedProjectId = projectId;
    }
    
    return projectId;
}

/**
 * 更新项目评分表的函数
 * 注意：此函数不再自动调用，因为后端get_score_summary已集成更新项目表的功能
 * 保留此函数以便需要时手动触发项目评分更新
 */
async function updateProjectScores(projectId, scoreData) {
    try {
        // 调用更新项目评分的API
        const response = await fetch('/api/update_project_scores', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: projectId,
                scores: scoreData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            return true;
        } else {
            console.error('更新项目评分失败:', result.message);
            return false;
        }
    } catch (error) {
        console.error('更新项目评分时出错:', error);
        return false;
    }
}

// 获取评分汇总信息的函数
async function fetchScoreSummary(forceRefresh = false) {
    try {
        // 获取项目ID
        let projectId = getSelectedProjectId();
        
        // 如果没有项目ID，则无法获取评分汇总
        if (!projectId) {
            console.warn('未找到项目ID，无法获取评分汇总');
            return;
        }
        
        // 获取项目评价标准
        let projectStandard = document.getElementById('current-project-standard')?.value || '成都市标';
        
        // 显示加载指示器
        const pageLoader = document.getElementById('page-loader');
        if (pageLoader) {
            pageLoader.style.display = 'flex';
        }

        // 使用async/await简化异步处理
        const response = await fetch(`/api/get_score_summary?project_id=${projectId}&force_refresh=${forceRefresh}`);
        if (!response.ok) {
            throw new Error(`服务器错误 (${response.status})`);
        }
        
        const data = await response.json();
        
        // 显示评价标准信息 - 如果元素存在才执行
        const standardInfoEl = document.getElementById('standard-info');
        if (standardInfoEl && data.project_standard) {
            standardInfoEl.innerHTML = `
                <span class="font-semibold">当前评价标准:</span> 
                <span class="text-primary">${data.project_standard}</span>
            `;
        }
        
        // 更新评分汇总表格
        if (typeof updateScoreSummaryTables === 'function') {
            updateScoreSummaryTables(data);
        }
        
        // 确保在数据加载后更新星级评定
        const isScoreSummaryPage = window.location.href.includes('page=score_summary') || 
                                 document.querySelector('.current_page')?.value === 'score_summary';
        if (isScoreSummaryPage) {
            setTimeout(() => {
                if (typeof updateStarRating === 'function') {
                    updateStarRating();
                }
            }, 100);
        }

        // 隐藏加载指示器
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        
        return data;
    } catch (error) {
        console.error('获取评分汇总数据失败:', error);
        
        // 隐藏加载指示器
        const pageLoader = document.getElementById('page-loader');
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        
        // 显示错误提示
        alert('获取评分汇总数据失败: ' + error.message);
        throw error;
    }
}

// 显示评分汇总数据
function displayScoreSummary(data) {
    const summaryContainer = document.getElementById('score-summary-container');
    if (!summaryContainer) return;
    
    // 从响应中获取专业分数和分类分数
    const { total_score, evaluation_result, specialty_scores, scores_detail } = data;
    const specialtyScores = specialty_scores || {};
    const scoresDetail = scores_detail || {};
    
    // 创建总分和评定结果卡片
    let html = `
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">总体评分</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h2 class="mb-0">${total_score || 0} <small>分</small></h2>
                        <p class="text-muted">总分</p>
                    </div>
                    <div class="col-md-6">
                        <h2 class="mb-0">${evaluation_result || '未评定'}</h2>
                        <p class="text-muted">评定结果</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 创建专业得分卡片
    html += `
        <div class="card mb-4">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0">专业得分</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>专业</th>
                                <th>得分</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    // 使用评分详情中的专业分数
    const 专业分数 = scoresDetail['专业分数'] || {};
    
    // 专业显示顺序
    const specialties = [
        {key: '建筑', label: '建筑专业'},
        {key: '结构', label: '结构专业'},
        {key: '给排水', label: '给排水专业'},
        {key: '电气', label: '电气专业'},
        {key: '暖通', label: '暖通专业'},
        {key: '景观', label: '景观专业'},
        {key: '环境健康与节能', label: '环境健康与节能专业'}
    ];
    
    // 添加专业得分行
    specialties.forEach(specialty => {
        const score = 专业分数[specialty.key] || 0;
        html += `
            <tr>
                <td>${specialty.label}</td>
                <td>${score}</td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // 创建章节得分卡片
    html += `
        <div class="card">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0">章节得分</h5>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>章节</th>
                                <th>得分</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    // 使用评分详情中的章节分数
    const 章节分数 = scoresDetail['章节分数'] || {};
    
    // 章节显示顺序
    const categories = [
        {key: '安全耐久', label: '安全耐久'},
        {key: '健康舒适', label: '健康舒适'},
        {key: '生活便利', label: '生活便利'},
        {key: '资源节约', label: '资源节约'},
        {key: '环境宜居', label: '环境宜居'},
        {key: '提高与创新', label: '提高与创新'}
    ];
    
    // 添加章节得分行
    categories.forEach(category => {
        const score = 章节分数[category.key] || 0;
        html += `
            <tr>
                <td>${category.label}</td>
                <td>${score}</td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // 更新容器内容
    summaryContainer.innerHTML = html;
}

// 简单的提示函数
function showToast(message, type = 'info') {
    // 如果有现成的Toast系统可以使用
    if (typeof toast !== 'undefined') {
        toast(message, type);
        return;
    }
    
    // 否则使用简单的alert
    alert(message);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

// 初始化页面上的各种评分相关元素和事件
function initializeScoreSummary() {
    // 恢复之前保存的滚动位置
    const savedScrollPosition = sessionStorage.getItem('scrollPosition');
    if (savedScrollPosition) {
        window.scrollTo(0, parseInt(savedScrollPosition));
        // 清除保存的滚动位置，避免影响后续页面加载
        sessionStorage.removeItem('scrollPosition');
    }
    
    // 检查当前页面是否是标准列表页面（基本级或提高级），需要加载已保存的评分数据
    // 增强检测逻辑，通过URL和表格结构判断
    const hasTable = document.querySelector('table tbody tr');
    const hasScoreInput = document.querySelector('input[name="score"]') || document.querySelector('select.is-achieved-select');
    const hasTechnicalTextarea = document.querySelector('textarea.technical-measures') || document.querySelector('textarea[placeholder*="技术措施"]');
    const isStandardsPage = hasTable && (hasScoreInput || hasTechnicalTextarea || window.location.href.includes('filter_standards'));
    
    console.log('页面检测状态:', {
        hasTable,
        hasScoreInput,
        hasTechnicalTextarea,
        urlIncludesStandards: window.location.href.includes('filter_standards')
    });
    
    if (isStandardsPage) {
        console.log('当前是标准列表页面，加载已保存的评分数据');
        loadSavedScores();
        
        // 绑定保存按钮事件
        const saveButtons = document.querySelectorAll('.save-score-btn, #saveScoreBtn, button[onclick*="save"]');
        if (saveButtons.length > 0) {
            saveButtons.forEach(btn => {
                // 移除可能已存在的事件处理程序
                btn.removeEventListener('click', saveScoreData);
                // 添加新的事件处理程序
                btn.addEventListener('click', saveScoreData);
                console.log('已为保存按钮绑定事件:', btn);
            });
        } else {
            // 如果没有找到专用的保存按钮，尝试创建一个
            const containerElement = document.querySelector('.container') || document.querySelector('main');
            if (containerElement && !document.getElementById('autoAddedSaveBtn')) {
                const saveBtn = document.createElement('button');
                saveBtn.id = 'autoAddedSaveBtn';
                saveBtn.className = 'px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 fixed bottom-4 right-4 shadow-lg';
                saveBtn.innerHTML = '<i class="ri-save-line mr-1"></i> 保存评分';
                saveBtn.addEventListener('click', saveScoreData);
                containerElement.appendChild(saveBtn);
                console.log('已创建并添加保存按钮');
            }
        }
    }
    
    // 获取项目星级目标
    const starRatingTarget = document.getElementById('star_rating_target')?.value || '';
    const isScoreSummaryPage = window.location.href.includes('page=score_summary') || 
                             document.querySelector('.current_page')?.value === 'score_summary';
    
    // 如果不是基本级且当前是评分汇总页面，才获取评分汇总数据
    if (starRatingTarget !== '基本级' && isScoreSummaryPage) {
        // 获取最新评分汇总数据（自动计算评分）
        fetchScoreSummary(true).catch(error => {
            console.error('初始加载评分汇总数据失败:', error);
        });
    }
    
    // 为刷新按钮添加点击事件
    const refreshScoreBtn = document.getElementById('refreshScoreBtn');
    if (refreshScoreBtn) {
        const debouncedFetch = debounce(function() {
            fetchScoreSummary().catch(error => {
                console.error('手动刷新评分数据失败:', error);
            });
        }, 300);
        
        refreshScoreBtn.addEventListener('click', debouncedFetch);
    }
    
    // 在页面加载时检查是否有预加载的数据
    if (isScoreSummaryPage) {
        const preloadedData = sessionStorage.getItem('score_summary_data');
        if (preloadedData) {
            // 使用预加载的数据更新页面
            try {
                const data = JSON.parse(preloadedData);
                if (typeof updateScoreSummaryTables === 'function') {
                    updateScoreSummaryTables(data);
                }
                // 清除预加载数据
                sessionStorage.removeItem('score_summary_data');
            } catch (error) {
                console.error('解析预加载数据失败:', error);
                // 如果解析失败，主动获取数据
                fetchScoreSummary(true).catch(error => {
                    console.error('获取评分汇总数据失败:', error);
                });
            }
        }
    }
    
    // 监听技术措施输入框的自动增高
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            // 自动调整高度
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        // 初始调整
        textarea.dispatchEvent(new Event('input'));
    });
}

// 更新评分汇总表格
function updateScoreSummaryTables(data) {
    console.log('更新评分汇总表格:', data);
    
    // 显示最后更新时间
    const lastUpdateTimeElement = document.getElementById('lastUpdateTime');
    if (lastUpdateTimeElement && data.timestamp) {
        lastUpdateTimeElement.textContent = `最后更新时间: ${data.timestamp}`;
    }
    
    // 更新专业得分行
    const specialtyScoresRow = document.getElementById('specialty-scores-row');
    if (specialtyScoresRow && data.specialty_scores) {
        const specialtyScores = data.specialty_scores;
        
        // 获取项目评价标准
        const projectStandard = document.getElementById('current-project-standard')?.value || '';
        
        // 显示或隐藏环境健康与节能专业列
        const envHealthEnergyHeader = document.getElementById('env_health_energy_header');
        const envHealthEnergyColumn = document.getElementById('env_health_energy_column');
        if (envHealthEnergyHeader) {
            envHealthEnergyHeader.style.display = projectStandard === '四川省标' ? '' : 'none';
            if (envHealthEnergyColumn) {
                envHealthEnergyColumn.style.display = projectStandard === '四川省标' ? '' : 'none';
            }
        }
        
        // 更新各专业得分
        updateCell(specialtyScoresRow, 1, specialtyScores['建筑专业'] || 0);
        updateCell(specialtyScoresRow, 2, specialtyScores['结构专业'] || 0);
        updateCell(specialtyScoresRow, 3, specialtyScores['给排水专业'] || 0);
        updateCell(specialtyScoresRow, 4, specialtyScores['电气专业'] || 0);
        updateCell(specialtyScoresRow, 5, specialtyScores['暖通专业'] || 0);
        updateCell(specialtyScoresRow, 6, specialtyScores['景观专业'] || 0);
        
        // 如果是四川省标，更新环境健康与节能专业得分
        if (projectStandard === '四川省标') {
            updateCell(specialtyScoresRow, 7, specialtyScores['环境健康与节能专业'] || 0);
        }
        
        // 更新总分
        const totalScore = data.total_score || 0;
        const totalScoreCell = specialtyScoresRow.querySelector('.total-score');
        if (totalScoreCell) {
            totalScoreCell.textContent = totalScore.toFixed(1);
        }
    }
    
    // 更新分类得分行
    const categoryScoresRow = document.getElementById('category-scores-row');
    if (categoryScoresRow && data.specialty_scores_by_category) {
        // 计算各分类得分
        const categoryScores = {
            '安全耐久': 0,
            '健康舒适': 0,
            '生活便利': 0,
            '资源节约': 0,
            '环境宜居': 0,
            '提高与创新': 0
        };
        
        // 遍历各专业的分类得分
        Object.values(data.specialty_scores_by_category).forEach(specialtyData => {
            Object.entries(specialtyData).forEach(([category, score]) => {
                if (category !== '总分' && categoryScores.hasOwnProperty(category)) {
                    categoryScores[category] += parseFloat(score) || 0;
                }
            });
        });
        
        // 更新各分类得分
        updateCell(categoryScoresRow, 1, categoryScores['安全耐久']);
        updateCell(categoryScoresRow, 2, categoryScores['健康舒适']);
        updateCell(categoryScoresRow, 3, categoryScores['生活便利']);
        updateCell(categoryScoresRow, 4, categoryScores['资源节约']);
        updateCell(categoryScoresRow, 5, categoryScores['环境宜居']);
        updateCell(categoryScoresRow, 6, categoryScores['提高与创新']);
        
        // 更新总分
        const totalScore = Object.values(categoryScores).reduce((sum, score) => sum + score, 0);
        updateCell(categoryScoresRow, 7, totalScore);
        
        // 更新达标判断行
        const judgmentRow = categoryScoresRow.parentNode.querySelector('tr:nth-child(3)');
        if (judgmentRow) {
            // 使用静态的最低分值数据
            const minScores = {
                '安全耐久': 30.0,
                '健康舒适': 30.0,
                '生活便利': 21.0,
                '资源节约': 60.0,
                '环境宜居': 30.0,
                '提高与创新': 0.0
            };
            const totalMinScore = 171; // 静态总分
            
            // 判断各分类是否达标
            updateJudgmentCell(judgmentRow, 1, categoryScores['安全耐久'] >= minScores['安全耐久']);
            updateJudgmentCell(judgmentRow, 2, categoryScores['健康舒适'] >= minScores['健康舒适']);
            updateJudgmentCell(judgmentRow, 3, categoryScores['生活便利'] >= minScores['生活便利']);
            updateJudgmentCell(judgmentRow, 4, categoryScores['资源节约'] >= minScores['资源节约']);
            updateJudgmentCell(judgmentRow, 5, categoryScores['环境宜居'] >= minScores['环境宜居']);
            updateJudgmentCell(judgmentRow, 6, categoryScores['提高与创新'] >= minScores['提高与创新']);
            
            // 判断总分是否达标 - 只有当所有分类都达标时，总分才达标
            const allCategoriesAchieved = 
                categoryScores['安全耐久'] >= minScores['安全耐久'] &&
                categoryScores['健康舒适'] >= minScores['健康舒适'] &&
                categoryScores['生活便利'] >= minScores['生活便利'] &&
                categoryScores['资源节约'] >= minScores['资源节约'] &&
                categoryScores['环境宜居'] >= minScores['环境宜居'] &&
                categoryScores['提高与创新'] >= minScores['提高与创新'];
            
            // 总分达标需要同时满足：1.总分达到要求 2.所有分类都达标
            updateJudgmentCell(judgmentRow, 7, totalScore >= totalMinScore && allCategoriesAchieved);
        }
        
        // 更新星级判定
        setTimeout(updateStarRating, 100);
    }
}

// 更新表格单元格
function updateCell(row, cellIndex, value) {
    const cell = row.querySelector(`td:nth-child(${cellIndex + 1})`);
    if (cell) {
        cell.textContent = typeof value === 'number' ? value.toFixed(1) : value;
    }
}

// 更新判断单元格
function updateJudgmentCell(row, cellIndex, isAchieved) {
    const cell = row.querySelector(`td:nth-child(${cellIndex + 1})`);
    if (cell) {
        if (isAchieved) {
            cell.textContent = '达标';
            cell.className = 'px-6 py-4 text-green-600 bg-green-50';
        } else {
            cell.textContent = '未达标';
            cell.className = 'px-6 py-4 text-red-600 bg-red-50';
        }
    }
}

// 添加评分统计更新功能
function updateScoreStatistics() {
    // 获取所有填写了得分的条目
    const rows = document.querySelectorAll('table tbody tr');
    
    // 准备各分类的得分统计
    const categoryScores = {
        '安全耐久': 0,
        '健康舒适': 0,
        '生活便利': 0,
        '资源节约': 0,
        '环境宜居': 0,
        '提高与创新': 0
    };
    
    // 计算各分类的得分
    rows.forEach(row => {
        const category = row.querySelector('td:nth-child(2) span')?.textContent.trim();
        // 检查是否有输入框，如果没有则查找span元素（针对分值为'-'的情况）
        const scoreInput = row.querySelector('td:nth-child(5) input');
        let score = 0;
        
        if (scoreInput) {
            // 如果有输入框，获取其值
            if (scoreInput.value && !isNaN(parseFloat(scoreInput.value))) {
                score = parseFloat(scoreInput.value);
            }
        } else {
            // 如果没有输入框，查找span元素（针对分值为'-'的情况）
            const scoreSpan = row.querySelector('td:nth-child(5) span');
            if (scoreSpan && scoreSpan.textContent === '0') {
                score = 0;
            }
        }
        
        if (category && categoryScores.hasOwnProperty(category)) {
            categoryScores[category] += score;
        }
    });
    
    // 更新统计表格
    const statTable = document.querySelector('.mt-10 table');
    if (statTable) {
        const statRow = statTable.querySelector('tbody tr');
        if (statRow) {
            // 更新各分类得分
            updateCategoryCell(statRow, 1, categoryScores['安全耐久']);
            updateCategoryCell(statRow, 2, categoryScores['健康舒适']);
            updateCategoryCell(statRow, 3, categoryScores['生活便利']);
            updateCategoryCell(statRow, 4, categoryScores['资源节约']);
            updateCategoryCell(statRow, 5, categoryScores['环境宜居']);
            updateCategoryCell(statRow, 6, categoryScores['提高与创新']);
            
            // 计算总分
            const totalScore = Object.values(categoryScores).reduce((sum, score) => sum + score, 0);
            updateCategoryCell(statRow, 7, totalScore);
        }
    }
}

// 加载已保存的评分数据
function loadSavedScores() {
    // 从DOM元素获取当前级别和专业，如果没有直接指定的元素，则从URL中提取
    let level = document.querySelector('.current_level')?.value || '';
    let specialty = document.querySelector('.current_specialty')?.value || '';
    const standard = document.getElementById('current-project-standard')?.value || '成都市标';
    
    // 如果没有找到级别和专业信息，尝试从URL中提取
    if (!level || !specialty) {
        try {
            const url = new URL(window.location.href);
            const pathParts = url.pathname.split('/');
            const queryParams = new URLSearchParams(url.search);
            
            if (url.pathname.includes('filter_standards')) {
                level = queryParams.get('level') || '';
                specialty = queryParams.get('specialty') || '';
                
                // 如果仍然无法获取，查看URL路径中是否包含这些信息
                if (!level || !specialty) {
                    for (let i = 0; i < pathParts.length; i++) {
                        if (pathParts[i] === '基本级' || pathParts[i] === '提高级') {
                            level = pathParts[i];
                        }
                        if (['建筑', '结构', '给排水', '电气', '暖通', '景观', '环境健康与节能'].includes(pathParts[i])) {
                            specialty = pathParts[i];
                        }
                    }
                }
            }
            
            console.log('从URL提取的信息:', { level, specialty });
        } catch (e) {
            console.error('从URL提取信息失败:', e);
        }
    }
    
    if (!level || !specialty) {
        console.error('未找到当前级别或专业信息');
        
        // 最后尝试从页面标题或其他元素推断
        const pageTitle = document.querySelector('h2')?.textContent || '';
        if (pageTitle.includes('建筑')) specialty = '建筑';
        else if (pageTitle.includes('结构')) specialty = '结构';
        else if (pageTitle.includes('给排水')) specialty = '给排水';
        else if (pageTitle.includes('电气')) specialty = '电气';
        else if (pageTitle.includes('暖通')) specialty = '暖通';
        else if (pageTitle.includes('景观')) specialty = '景观';
        else if (pageTitle.includes('环境健康与节能')) specialty = '环境健康与节能';
        
        // 判断基本级还是提高级
        if (document.querySelector('select.is-achieved-select')) {
            level = '基本级';
        } else if (document.querySelector('input[name="score"]')) {
            level = '提高级';
        }
        
        if (!level || !specialty) {
            console.error('无法确定级别或专业，无法加载数据');
            return;
        }
    }
    
    // 获取项目ID（如果有的话）
    let projectId = null;
    const projectIdField = document.getElementById('project_id') || document.getElementById('current-project-id');
    if (projectIdField) {
        projectId = projectIdField.value;
    } else {
        // 尝试从URL获取项目ID
        const urlParams = new URLSearchParams(window.location.search);
        projectId = urlParams.get('project_id');
    }
    
    // 构建API URL
    let apiUrl = `/api/load_scores?level=${encodeURIComponent(level)}&specialty=${encodeURIComponent(specialty)}&standard=${encodeURIComponent(standard)}`;
    if (projectId) {
        apiUrl += `&project_id=${encodeURIComponent(projectId)}`;
    }
    
    console.log('加载评分数据URL:', apiUrl);
    
    // 请求服务器数据
    fetch(apiUrl)
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应异常');
        }
        return response.json();
    })
    .then(data => {
        if (data.success && data.scores && data.scores.length > 0) {
            // 填充表格数据
            fillScoreTable(data.scores);
            console.log('成功加载评分数据，共', data.scores.length, '条记录');
            
            // 如果需要，可以更新统计数据
            if (level === '提高级') {
                updateScoreStatistics();
            }
        } else {
            console.log('未找到评分数据或数据为空');
        }
    })
    .catch(error => {
        console.error('加载评分数据失败:', error);
    });
}

// 填充表格数据
function fillScoreTable(scores) {
    const rows = document.querySelectorAll('table tbody tr');
    // 尝试各种方式确定当前级别
    let level = document.querySelector('.current_level')?.value || '';
    if (!level) {
        if (document.querySelector('select.is-achieved-select')) {
            level = '基本级';
        } else if (document.querySelector('input[name="score"]')) {
            level = '提高级';
        }
    }
    
    console.log(`开始填充表格数据, 级别: ${level}, 行数: ${rows.length}, 得分记录数: ${scores.length}`);
    
    rows.forEach(row => {
        // 尝试获取条文号，可能在不同的单元格
        let clauseNumber = null;
        for (let i = 1; i <= 3; i++) {
            const cellText = row.querySelector(`td:nth-child(${i})`)?.textContent.trim();
            if (cellText && /^\d+\.\d+(\.\d+)*$/.test(cellText)) {
                clauseNumber = cellText;
                break;
            }
        }
        
        if (!clauseNumber) return;
        
        // 查找匹配的评分数据
        const scoreData = scores.find(s => s.clause_number === clauseNumber);
        if (!scoreData) {
            console.log(`未找到条文 ${clauseNumber} 的评分数据`);
            return;
        }
        
        console.log(`填充数据: 条文号=${clauseNumber}, 是否达标=${scoreData.is_achieved}, 技术措施长度=${scoreData.technical_measures ? scoreData.technical_measures.length : 0}`);
        
        // 根据不同级别填充数据
        if (level === '基本级') {
            // 选择"是否达标"下拉框
            const selectElement = row.querySelector('select.is-achieved-select') || row.querySelector('select[name="is_achieved"]');
            if (selectElement) {
                selectElement.value = scoreData.is_achieved;
                console.log(`设置是否达标: ${scoreData.is_achieved}`);
            } else {
                console.log(`未找到是否达标下拉框: 条文号=${clauseNumber}`);
            }
            
            // 填充技术措施
            const textareaElement = row.querySelector('textarea.technical-measures') || 
                                   row.querySelector('textarea[placeholder*="技术措施"]') ||
                                   row.querySelector('textarea');
            if (textareaElement) {
                textareaElement.value = scoreData.technical_measures || '';
                console.log(`设置技术措施: 长度=${scoreData.technical_measures ? scoreData.technical_measures.length : 0}`);
            } else {
                console.log(`未找到技术措施文本框: 条文号=${clauseNumber}`);
            }
        } else if (level === '提高级') {
            // 填充得分
            const inputElement = row.querySelector('input[name="score"]') || row.querySelector('input.score-input') || row.querySelector('input[type="number"]');
            if (inputElement) {
                inputElement.value = scoreData.score || '0';
                console.log(`设置得分: ${scoreData.score}`);
            } else {
                console.log(`未找到得分输入框: 条文号=${clauseNumber}`);
            }
            
            // 填充技术措施
            const textareaElement = row.querySelector('textarea.technical-measures') || 
                                   row.querySelector('textarea[placeholder*="技术措施"]') ||
                                   row.querySelector('textarea');
            if (textareaElement) {
                textareaElement.value = scoreData.technical_measures || '';
                console.log(`设置技术措施: 长度=${scoreData.technical_measures ? scoreData.technical_measures.length : 0}`);
            } else {
                console.log(`未找到技术措施文本框: 条文号=${clauseNumber}`);
            }
        }
    });
}

// 定义保存评分的函数
function saveScoreData() {
    // 显示保存中状态
    const saveBtn = this;
    const originalText = saveBtn.textContent || '';
    const originalHTML = saveBtn.innerHTML;
    
    if (saveBtn.tagName === 'BUTTON') {
        saveBtn.textContent = '保存中...';
    } else {
        saveBtn.innerHTML = '<i class="ri-loader-2-line"></i>';
        saveBtn.style.animation = 'rotate 1s linear infinite';
    }
    saveBtn.disabled = true;
    
    // 获取项目名称和ID
    const projectName = document.getElementById('current_project_name')?.value || '';
    const projectId = document.getElementById('project_id')?.value || document.getElementById('current-project-id')?.value;
    
    if (!projectId) {
        alert('未找到项目ID');
        restoreButton(saveBtn, originalText, originalHTML);
        return;
    }

    // 收集表格数据
    const scoreData = collectScoreData();
    if (scoreData.length === 0) {
        alert('未找到可保存的评分数据，请确保页面包含评分表格。');
        restoreButton(saveBtn, originalText, originalHTML);
        return;
    }

    // 从DOM元素获取当前级别和专业
    const level = document.querySelector('.current_level')?.value || '';
    const specialty = document.querySelector('.current_specialty')?.value || '';
    const standard = document.getElementById('current-project-standard')?.value || '成都市标';
    
    const requestData = {
        level: level,
        specialty: specialty,
        project_id: projectId,
        scores: scoreData,
        standard: standard
    };

    // 发送数据到服务器
    fetch('/api/save_score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || '保存失败');
        }
        
        // 显示成功消息
        // alert('评分信息保存成功！');
        
        // 更新徽章状态
        if (level === '提高级') {
            // 延迟一小段时间后更新徽章，确保数据已保存到数据库
            setTimeout(() => {
                updateCategoryBadges();
            }, 500);
        }
    })
    .catch(error => {
        console.error('保存失败:', error);
        alert('保存失败: ' + error.message);
    })
    .finally(() => {
        restoreButton(saveBtn, originalText, originalHTML);
    });
}

// 辅助函数：收集评分数据
function collectScoreData() {
    const scoreData = [];
    const rows = document.querySelectorAll('table tbody tr');
    let currentLevel = document.querySelector('.current_level')?.value || '';
    
    // 如果没有明确的当前级别标记，则通过表单元素判断
    if (!currentLevel) {
        if (document.querySelector('select.is-achieved-select') || document.querySelector('select[name="is_achieved"]')) {
            currentLevel = '基本级';
        } else if (document.querySelector('input[name="score"]') || document.querySelector('input[type="number"]')) {
            currentLevel = '提高级';
        }
    }
    
    console.log(`开始收集评分数据, 级别: ${currentLevel}, 行数: ${rows.length}`);
    
    rows.forEach((row, index) => {
        try {
            // 基本级
            if (currentLevel === '基本级') {
                // 尝试获取条文号，可能在不同的单元格
                let clauseNumber = null;
                for (let i = 1; i <= 3; i++) {
                    const cellText = row.querySelector(`td:nth-child(${i})`)?.textContent.trim();
                    if (cellText && /^\d+\.\d+(\.\d+)*$/.test(cellText)) {
                        clauseNumber = cellText;
                        break;
                    }
                }
                if (!clauseNumber) return;
                
                const isAchievedSelect = row.querySelector('select.is-achieved-select') || row.querySelector('select[name="is_achieved"]');
                if (!isAchievedSelect) return;
                
                const technicalMeasuresTextarea = row.querySelector('textarea.technical-measures') || 
                                                row.querySelector('textarea[placeholder*="技术措施"]') || 
                                                row.querySelector('textarea');
                if (!technicalMeasuresTextarea) return;
                
                const contentText = row.querySelector('td:nth-child(3)')?.textContent.trim() || '';
                let category = getCategory(contentText);
                
                scoreData.push({
                    project_name: document.getElementById('current_project_name')?.value || '',
                    clause_number: clauseNumber,
                    category: category,
                    is_achieved: isAchievedSelect.value,
                    score: '0',
                    technical_measures: technicalMeasuresTextarea.value || ''
                });
            } 
            // 提高级
            else if (currentLevel === '提高级') {
                // 尝试获取条文号，可能在不同的单元格
                let clauseNumber = null;
                for (let i = 1; i <= 3; i++) {
                    const cellText = row.querySelector(`td:nth-child(${i})`)?.textContent.trim();
                    if (cellText && /^\d+\.\d+(\.\d+)*$/.test(cellText)) {
                        clauseNumber = cellText;
                        break;
                    }
                }
                if (!clauseNumber) return;
                
                // 尝试找到分类标签
                let category = '';
                const categoryElement = row.querySelector('td:nth-child(2) span') || row.querySelector('.category-tag');
                
                // 如果找不到直接的分类标签，尝试从行内文本推断
                if (categoryElement) {
                    category = categoryElement.textContent.trim();
                } else {
                    // 从整行文本判断分类
                    const rowText = row.textContent.trim();
                    category = getCategory(rowText);
                }
                
                // 查找得分输入框
                const scoreInput = row.querySelector('input[name="score"]') || 
                                  row.querySelector('input.score-input') || 
                                  row.querySelector('input[type="number"]');
                
                // 查找技术措施文本框
                const technicalMeasuresTextarea = row.querySelector('textarea.technical-measures') || 
                                               row.querySelector('textarea[placeholder*="技术措施"]') || 
                                               row.querySelector('textarea');
                
                let score = '0';
                if (scoreInput) {
                    score = scoreInput.value || '0';
                    // 查找可能在不同单元格的最大分值
                    let maxScore = null;
                    for (let i = 3; i <= 5; i++) {
                        const cellText = row.querySelector(`td:nth-child(${i})`)?.textContent.trim();
                        if (cellText && !isNaN(parseFloat(cellText))) {
                            maxScore = parseFloat(cellText);
                            break;
                        }
                    }
                    
                    if (maxScore !== null && parseFloat(score) > maxScore) {
                        score = maxScore.toString();
                        scoreInput.value = score;
                    }
                }
                
                scoreData.push({
                    project_name: document.getElementById('current_project_name')?.value || '',
                    clause_number: clauseNumber,
                    category: category,
                    is_achieved: '是',
                    score: score,
                    technical_measures: technicalMeasuresTextarea?.value || ''
                });
            }
        } catch (rowError) {
            console.error(`处理第 ${index+1} 行时出错:`, rowError);
        }
    });
    
    console.log(`收集到的评分数据: ${scoreData.length}条`);
    return scoreData;
}

// 辅助函数：从条文内容提取分类
function getCategory(content) {
    // 定义分类关键词
    const categoryKeywords = {
        '安全耐久': ['安全', '耐久', '结构', '抗震', '防火', '防灾', '使用年限', '耐腐蚀', '安全隐患'],
        '健康舒适': ['健康', '舒适', '空气', '噪声', '光环境', '温度', '湿度', '通风', '采光', '隔声', '日照'],
        '生活便利': ['生活', '便利', '便捷', '交通', '无障碍', '服务设施', '信息', '智能化', '停车', '充电'],
        '资源节约': ['资源', '节约', '节能', '节水', '节地', '节材', '能耗', '光伏', '热水', '水循环', '雨水', '绿色'],
        '环境宜居': ['环境', '宜居', '绿化', '景观', '生态', '生物', '植被', '垃圾', '污染', '排放', '减排']
    };
    
    // 检查内容中是否包含各分类的关键词
    for (const [category, keywords] of Object.entries(categoryKeywords)) {
        for (const keyword of keywords) {
            if (content.includes(keyword)) {
                return category;
            }
        }
    }
    
    // 默认为"提高与创新"
    return '提高与创新';
}

// 辅助函数：恢复按钮状态
function restoreButton(button, originalText, originalHTML) {
    if (button.tagName === 'BUTTON') {
        button.textContent = originalText;
    } else {
        button.innerHTML = originalHTML;
        button.style.animation = '';
    }
    button.disabled = false;
}

// 初始化评分相关功能
document.addEventListener('DOMContentLoaded', initializeScoreSummary);

// 导出到全局空间，便于HTML文件直接引用
window.scoreUtils = {
    getSelectedProjectId,
    fetchScoreSummary,
    displayScoreSummary,
    debounce,
    showToast,
    updateProjectScores,
    initializeScoreSummary
}; 