// 项目ID缓存
let cachedProjectId = null;

// 页面加载时检查并添加必要的隐藏字段
document.addEventListener('DOMContentLoaded', function() {
    // 检查并添加级别和专业隐藏字段
    ensureHiddenFields();
});

// 确保页面包含必要的隐藏字段
function ensureHiddenFields() {
    // 检查level字段
    if (!document.querySelector('.current_level')) {
        addHiddenField('current_level', getLevelFromPage());
    }
    
    // 检查specialty字段
    if (!document.querySelector('.current_specialty')) {
        addHiddenField('current_specialty', getSpecialtyFromPage());
    }
    
    // 记录已添加字段
    console.log('已确保页面包含必要的隐藏字段:', {
        level: document.querySelector('.current_level')?.value,
        specialty: document.querySelector('.current_specialty')?.value
    });
}

// 添加隐藏字段到页面
function addHiddenField(className, value) {
    const hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.className = className;
    hiddenField.value = value || '';
    document.body.appendChild(hiddenField);
    console.log(`添加隐藏字段: ${className} = ${value}`);
}

// 从页面各种线索获取level值
function getLevelFromPage() {
    // 1. 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    let level = urlParams.get('level') || '';
    
    // 2. 从URL路径获取
    if (!level) {
        const pathParts = window.location.pathname.split('/');
        for (let i = 0; i < pathParts.length; i++) {
            if (['基本级', '提高级'].includes(pathParts[i])) {
                level = pathParts[i];
                break;
            }
        }
    }
    
    // 3. 从页面标题或内容推断
    if (!level) {
        // 检查是否有选择或评分输入框来判断级别
        if (document.querySelector('select.is-achieved-select') || document.querySelector('select[name="is_achieved"]')) {
            level = '基本级';
        } else if (document.querySelector('input[name="score"]') || document.querySelector('input[type="number"]')) {
            level = '提高级';
        }
    }
    
    // 4. 设置默认值
    return level || '基本级';
}

// 从页面各种线索获取specialty值
function getSpecialtyFromPage() {
    // 1. 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    let specialty = urlParams.get('specialty') || '';
    
    // 2. 从URL路径获取
    if (!specialty) {
        const pathParts = window.location.pathname.split('/');
        for (let i = 0; i < pathParts.length; i++) {
            if (['建筑', '结构', '给排水', '电气', '暖通', '景观', '环境健康与节能'].includes(pathParts[i])) {
                specialty = pathParts[i];
                break;
            }
        }
    }
    
    // 3. 从页面标题或内容推断
    if (!specialty) {
        const pageTitle = document.querySelector('h1, h2, h3')?.textContent || '';
        if (pageTitle.includes('建筑')) specialty = '建筑';
        else if (pageTitle.includes('结构')) specialty = '结构';
        else if (pageTitle.includes('给排水')) specialty = '给排水';
        else if (pageTitle.includes('电气')) specialty = '电气';
        else if (pageTitle.includes('暖通')) specialty = '暖通';
        else if (pageTitle.includes('景观')) specialty = '景观';
        else if (pageTitle.includes('环境健康与节能')) specialty = '环境健康与节能';
    }
    
    // 4. 设置默认值
    return specialty || '建筑';
}

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

        return data;
    } catch (error) {
        console.error('获取评分汇总数据失败:', error);
        
        // 显示错误提示
        alert('获取评分汇总数据失败: ' + error.message);
        throw error;
    }
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
        loadScores();
        
        // 绑定保存按钮事件
        const saveButtons = document.querySelectorAll('.save-score-btn, #saveScoresBtn, button[onclick*="save"]');
        if (saveButtons.length > 0) {
            saveButtons.forEach(btn => {
                // 移除可能已存在的事件处理程序
                btn.removeEventListener('click', saveScores);
                // 添加新的事件处理程序
                btn.addEventListener('click', saveScores);
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
                saveBtn.addEventListener('click', saveScores);
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

// 初始化评分相关功能
document.addEventListener('DOMContentLoaded', initializeScoreSummary);

// 导出到全局空间，便于HTML文件直接引用
window.scoreUtils = {
    getSelectedProjectId,
    fetchScoreSummary,
    debounce,
    showToast,
    initializeScoreSummary,
    ensureHiddenFields,
    getLevelFromPage,
    getSpecialtyFromPage
}; 