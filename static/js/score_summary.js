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