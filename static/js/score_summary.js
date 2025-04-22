// 项目ID缓存
let cachedProjectId = null;

/**
 * 评分辅助功能
 * 以下函数从score_helper.js整合而来，处理评分级别和专业类型的自动检测
 */

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
    // 从DOM元素获取当前级别和专业
    let level = document.querySelector('.current_level')?.value || '';
    let specialty = document.querySelector('.current_specialty')?.value || '';
    const standard = document.getElementById('current-project-standard')?.value || '成都市标';
    
    // 如果无法从DOM中获取level或specialty，使用辅助函数获取
    if (!level) {
        level = getLevelFromPage();
    }
    
    if (!specialty) {
        specialty = getSpecialtyFromPage();
    }
    
    // 获取项目ID（如果有的话）
    let projectId = getSelectedProjectId();
    
    // 构建API URL
    let apiUrl = `/api/project_scores?level=${encodeURIComponent(level)}&specialty=${encodeURIComponent(specialty)}&standard=${encodeURIComponent(standard)}`;
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
        if (data.success && data.sample_scores && data.sample_scores.length > 0) {
            // 填充表格数据
            fillScoreTable(data.sample_scores);
            console.log('成功加载评分数据，共', data.sample_scores.length, '条记录');
            
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
                clauseNumber = cellText.trim();
                break;
            } 
        }
        
        if (!clauseNumber) return;
        
        // 查找匹配的评分数据
        const scoreData = scores.find(s => s.clause_number.trim() === clauseNumber.trim());
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

// 保存评分数据函数
function saveScoreData() {
    console.log('saveScoreData函数被调用');
    
    // 获取按钮元素，可能是当前点击的按钮或指定的保存按钮
    const saveBtn = this instanceof HTMLElement ? this : document.querySelector('.save-score-btn') || document.getElementById('saveScoreBtn');
    const originalText = saveBtn.textContent || '';
    const originalHTML = saveBtn.innerHTML;
    
    // 将按钮显示为保存中状态
    if (saveBtn.tagName === 'BUTTON') {
        saveBtn.textContent = '保存中...';
    } else if (saveBtn.id === 'floatingSaveBtn') {
        // 特殊处理悬浮保存按钮
        saveBtn.classList.add('saving');
        saveBtn.innerHTML = '<i class="ri-loader-2-line"></i>';
        saveBtn.style.animation = 'pulse 1.5s infinite';
    } else {
        saveBtn.innerHTML = '<i class="ri-loader-2-line"></i> 保存中...';
        saveBtn.style.animation = 'pulse 1.5s infinite';
    }
    saveBtn.disabled = true;
    
    // 获取项目信息
    let projectId = getSelectedProjectId();
    
    // 检查项目ID
    if (!projectId) {
        console.error('未找到项目ID');
        alert('未找到项目ID，请先选择一个项目');
        restoreButton(saveBtn, originalText, originalHTML);
        return;
    }
    
    // 从DOM元素获取当前级别和专业
    let level = document.querySelector('.current_level')?.value || document.getElementById('current_level')?.value || document.querySelector('input[name="level"]')?.value || '';
    let specialty = document.querySelector('.current_specialty')?.value || document.getElementById('current_specialty')?.value || document.querySelector('input[name="specialty"]')?.value || '';
    let standard = document.getElementById('current-project-standard')?.value || '成都市标';
    
    // 收集评分数据
    let scoreData = [];
    try {
        scoreData = collectScoreData();
        console.log(`收集到${scoreData.length}条评分数据`);
        
        if (scoreData.length === 0) {
            console.warn('没有找到有效的评分数据');
            alert('没有找到有效的评分数据，请确认表格已正确加载');
            restoreButton(saveBtn, originalText, originalHTML);
            return;
        }
    } catch (e) {
        console.error('收集评分数据失败:', e);
        alert('收集评分数据失败: ' + e.message);
        restoreButton(saveBtn, originalText, originalHTML);
        return;
    }
    
    // 如果无法从DOM中获取level或specialty，使用辅助函数获取
    if (!level) {
        level = getLevelFromPage();
    }
    
    if (!specialty) {
        specialty = getSpecialtyFromPage();
    }
    
    const requestData = {
        level: level,
        specialty: specialty,
        project_id: projectId,
        scores: scoreData,
        standard: standard
    };
    
    console.log('准备发送请求数据:', requestData);

    // 发送数据到服务器
    console.log('开始发送数据到服务器...');
    fetch('/api/save_score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('收到服务器响应，状态码:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('解析响应JSON数据:', data);
        if (!data.success) {
            throw new Error(data.error || '保存失败');
        }
        
        // 触发保存成功的自定义事件
        document.dispatchEvent(new CustomEvent('save-score-completed', { 
            detail: { success: true, message: '评分信息保存成功！' } 
        }));
        
        // 更新徽章状态
        if (level === '提高级') {
            // 延迟一小段时间后更新徽章，确保数据已保存到数据库
            setTimeout(() => {
                console.log('更新徽章状态');
                updateCategoryBadges();
            }, 500);
        }
    })
    .catch(error => {
        console.error('保存失败:', error);
        alert('保存失败: ' + error.message);
    })
    .finally(() => {
        console.log('请求完成，恢复按钮状态');
        restoreButton(saveBtn, originalText, originalHTML);
    });
}

// 辅助函数：收集评分数据
function collectScoreData() {
    const scoreData = [];
    const table = document.querySelector('table');
    if (!table) {
        console.error('未找到表格元素');
        return [];
    }
    
    // 获取当前级别
    let currentLevel = document.querySelector('.current_level')?.value || '';
    if (!currentLevel) {
        if (document.querySelector('select.is-achieved-select') || document.querySelector('select[name="is_achieved"]')) {
            currentLevel = '基本级';
        } else if (document.querySelector('input[name="score"]') || document.querySelector('input[type="number"]')) {
            currentLevel = '提高级';
        }
    }
    
    // 获取表头并建立列索引映射
    const headerCells = Array.from(table.querySelectorAll('thead th'));
    const headerMap = {};
    
    headerCells.forEach((cell, index) => {
        const headerText = cell.textContent.trim().toLowerCase();
        headerMap[headerText] = index;
        
        // 处理同义词以增强匹配能力
        if (headerText.includes('条文号')) headerMap['条文号'] = index;
        if (headerText.includes('分类')) headerMap['分类'] = index;
        if (headerText.includes('内容')) headerMap['条文内容'] = index;
        if (headerText.includes('分值')) headerMap['分值'] = index;
        if (headerText.includes('得分')) headerMap['得分'] = index;
        if (headerText.includes('技术措施')) headerMap['技术措施'] = index;
        if (headerText.includes('达标')) headerMap['是否达标'] = index;
    });
    
    console.log('表头映射:', headerMap);
    console.log(`开始收集评分数据, 级别: ${currentLevel}`);
    
    // 获取表格行
    const rows = table.querySelectorAll('tbody tr');
    console.log(`表格共有 ${rows.length} 行数据`);
    
    // 遍历每一行
    rows.forEach((row, rowIndex) => {
        try {
            const cells = row.querySelectorAll('td');
            if (cells.length === 0) return; // 跳过空行
            
            // 使用表头映射获取各列数据
            const clauseCell = cells[headerMap['条文号'] || 0];
            if (!clauseCell) {
                console.warn(`第 ${rowIndex + 1} 行没有条文号单元格`);
                return;
            }
            
            // 获取条文号
            let clauseNumber = clauseCell.textContent.trim();
            if (!clauseNumber) {
                // 如果无法获取条文号，使用行号作为备用
                clauseNumber = `Row_${rowIndex + 1}`;
                console.log(`使用行号作为条文号: ${clauseNumber}`);
            }
            
            // 获取分类
            let category = '';
                const categoryCell = cells[headerMap['分类']];
                const categoryTag = categoryCell.querySelector('.category-tag');
                if (categoryTag) {
                    category = categoryTag.textContent.trim();
                } else {
                    category = categoryCell.textContent.trim();
                }

            
            // 基本级和提高级通用数据
            const dataItem = {
                project_name: document.getElementById('current_project_name')?.value || '',
                clause_number: clauseNumber,
                category: category,
                technical_measures: '',
                is_achieved: '是',
                score: '0'
            };
            
            // 根据级别获取特定数据
            if (currentLevel === '基本级') {
                // 获取是否达标
                const isAchievedSelect = row.querySelector('select.is-achieved-select') || row.querySelector('select[name="is_achieved"]');
                if (isAchievedSelect) {
                    dataItem.is_achieved = isAchievedSelect.value.trim();
                }
                
                // 获取技术措施
                const technicalMeasuresTextarea = row.querySelector('textarea.technical-measures') || 
                                                row.querySelector('textarea[name="technical_measures"]');
                if (technicalMeasuresTextarea) {
                    dataItem.technical_measures = technicalMeasuresTextarea.value.trim();
                }
            } else if (currentLevel === '提高级') {
                // 获取得分
                let score = '0';
                const scoreInput = row.querySelector('input[name="score"]') || 
                                 row.querySelector('input.score-input') || 
                                 row.querySelector('input[type="number"]');
                
                if (scoreInput) {
                    // 从输入框获取
                    score = scoreInput.value.trim();
                    if (score === '-' || score === '—' || score === '') {
                        score = '0';
                    } else if (!isNaN(parseFloat(score))) {
                        score = score;
                    } else {
                        score = '0';
                    }
                } else {
                    // 尝试从单元格内容获取
                    const scoreIndex = headerMap['得分'] || 4;
                    if (cells[scoreIndex]) {
                        const scoreText = cells[scoreIndex].textContent.trim();
                        if (scoreText === '-' || scoreText === '—') {
                            score = '0';
                        } else if (!isNaN(parseFloat(scoreText))) {
                            score = parseFloat(scoreText).toString();
                        }
                    }
                }
                
                // 保存得分
                dataItem.score = score;
                
                // 获取技术措施
                const technicalMeasuresTextarea = row.querySelector('textarea.technical-measures') || 
                                               row.querySelector('textarea[name="technical_measures"]');
                if (technicalMeasuresTextarea) {
                    dataItem.technical_measures = technicalMeasuresTextarea.value.trim();
                }
            }
            
            // 添加到收集的数据中
            scoreData.push(dataItem);
            
        } catch (rowError) {
            console.error(`处理第 ${rowIndex + 1} 行时出错:`, rowError);
            // 保存基本数据作为备用
            scoreData.push({
                project_name: document.getElementById('current_project_name')?.value || '',
                clause_number: `Row_${rowIndex + 1}`,
                category: '未知分类',
                is_achieved: currentLevel === '基本级' ? '否' : '是',
                score: '0',
                technical_measures: ''
            });
        }
    });
    
    console.log(`收集到的评分数据: ${scoreData.length}条`);
    return scoreData;
}


// 辅助函数：恢复按钮状态
function restoreButton(button, originalText, originalHTML) {
    if (button.tagName === 'BUTTON') {
        button.textContent = originalText;
    } else if (button.id === 'floatingSaveBtn') {
        // 特殊处理悬浮保存按钮
        button.classList.remove('saving');
        button.innerHTML = originalHTML;
        button.style.animation = '';
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
    debounce,
    showToast,
    initializeScoreSummary,
    ensureHiddenFields,
    getLevelFromPage,
    getSpecialtyFromPage
}; 