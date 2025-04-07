// 获取当前选中的项目ID
function getSelectedProjectId() {
    // 先尝试从隐藏字段获取
    let projectId = document.getElementById('current-project-id')?.value;
    if (!projectId) {
        // 尝试从project_id字段获取
        projectId = document.getElementById('project_id')?.value;
    }
    if (!projectId) {
        // 尝试从URL参数获取
        const urlParams = new URLSearchParams(window.location.search);
        projectId = urlParams.get('project_id');
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
        console.log('更新项目表中的评分数据:', projectId, scoreData);
        
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
            console.log('成功更新项目评分:', result);
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
    // 获取项目ID
    let projectId = null;
    const projectIdField = document.getElementById('project_id');
    if (projectIdField) {
        projectId = projectIdField.value;
        console.log('从project_id字段获取项目ID:', projectId);
    } else {
        // 尝试从URL中获取项目ID
        const urlParams = new URLSearchParams(window.location.search);
        projectId = urlParams.get('project_id');
        console.log('从URL参数获取项目ID:', projectId);
    }
    
    // 如果依然没有项目ID，尝试从current-project-id获取
    if (!projectId) {
        const currentProjectIdField = document.getElementById('current-project-id');
        if (currentProjectIdField) {
            projectId = currentProjectIdField.value;
            console.log('从current-project-id字段获取项目ID:', projectId);
        }
    }
    
    // 如果没有项目ID，则无法获取评分汇总
    if (!projectId) {
        console.warn('未找到项目ID，无法获取评分汇总');
        return;
    }
    
    // 获取项目评价标准
    let projectStandard = document.getElementById('current-project-standard')?.value || '成都市标';
    
    console.log(`获取评分汇总数据: 项目ID=${projectId}, 评价标准=${projectStandard}, 强制刷新=${forceRefresh}`);
 
    // 显示加载指示器
    const pageLoader = document.getElementById('page-loader');
    if (pageLoader) {
        pageLoader.style.display = 'flex';
    }

    // 使用get_score_summary接口获取评分数据
    fetch(`/api/get_score_summary?project_id=${projectId}&force_refresh=${forceRefresh}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`服务器错误 (${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            console.log('获取评分汇总数据成功:', data);
            
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
            if (window.location.href.includes('page=score_summary')) {
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
        })
        .catch(error => {
            console.error('获取评分汇总数据失败:', error);
            // 隐藏加载指示器
            if (pageLoader) {
                pageLoader.style.display = 'none';
            }
            // 显示错误提示
            alert('获取评分汇总数据失败: ' + error.message);
        });
}

// 显示评分汇总数据
function displayScoreSummary(data) {
    const summaryContainer = document.getElementById('score-summary-container');
    
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

// 在页面加载完成后，添加评分菜单点击事件
document.addEventListener('DOMContentLoaded', function() {
    // 如果当前是评分汇总页面，不再自动加载评分数据
    if (window.location.href.includes('page=score_summary')) {
        console.log('当前是评分汇总页面');
    }
    
    // 获取评分汇总菜单项
    const scoreSummaryMenuItem = document.querySelector('a[data-content="score-summary"]');
    if (scoreSummaryMenuItem) {
        console.log('找到评分汇总菜单项，添加点击事件');
        
        // 添加点击事件，确保点击时先计算评分
        scoreSummaryMenuItem.addEventListener('click', function(e) {
            // 不阻止默认行为，让导航正常工作
        });
    }
});

// 更新分类徽章
function updateCategoryBadges() {
    if (typeof window.updateCategoryBadges === 'function') {
        window.updateCategoryBadges();
    }
}

function initializeBadgeFilters() {
    if (typeof window.initializeBadgeFilters === 'function') {
        window.initializeBadgeFilters();
    }
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

// 使用防抖处理的获取评分汇总函数
const debouncedFetchScoreSummary = debounce(fetchScoreSummary, 300);

// 在页面加载完成后获取评分汇总数据
document.addEventListener('DOMContentLoaded', function() {
    // 恢复之前保存的滚动位置
    const savedScrollPosition = sessionStorage.getItem('scrollPosition');
    if (savedScrollPosition) {
        window.scrollTo(0, parseInt(savedScrollPosition));
        // 清除保存的滚动位置，避免影响后续页面加载
        sessionStorage.removeItem('scrollPosition');
    }
    
    // 获取项目星级目标
    const starRatingTarget = document.getElementById('star_rating_target')?.value || '';
    
    // 如果不是基本级且当前是评分汇总页面，才获取评分汇总数据
    if (starRatingTarget !== '基本级' && window.location.href.includes('page=score_summary')) {
        console.log('当前在评分汇总页面，获取最新评分汇总数据');
        
        // 获取最新评分汇总数据（自动计算评分）
        fetchScoreSummary(true);
    }
}); 