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
    // 填充表格数据
    function fillScoreTable(scores) {
        const rows = document.querySelectorAll('table tbody tr');
        const level = '{{ current_level }}';
        
        rows.forEach(row => {
            const clauseNumber = row.querySelector('td:nth-child(1)')?.textContent.trim();
            if (!clauseNumber) return;
            
            // 查找匹配的评分数据
            const scoreData = scores.find(s => s.clause_number === clauseNumber);
            if (!scoreData) return;
            
            console.log(`填充数据: 条文号=${clauseNumber}, 是否达标=${scoreData.is_achieved}, 技术措施长度=${scoreData.technical_measures ? scoreData.technical_measures.length : 0}`);
            
            // 根据不同级别填充数据
            if (level === '基本级') {
                // 选择"是否达标"下拉框
                const selectElement = row.querySelector('select.is-achieved-select');
                if (selectElement) {
                    selectElement.value = scoreData.is_achieved;
                    console.log(`设置是否达标: ${scoreData.is_achieved}`);
                } else {
                    console.log(`未找到是否达标下拉框: 条文号=${clauseNumber}`);
                }
                
                // 填充技术措施
                const textareaElement = row.querySelector('textarea.technical-measures');
                if (textareaElement) {
                    textareaElement.value = scoreData.technical_measures || '';
                    console.log(`设置技术措施: 长度=${scoreData.technical_measures ? scoreData.technical_measures.length : 0}`);
                } else {
                    console.log(`未找到技术措施文本框: 条文号=${clauseNumber}`);
                }
            } else if (level === '提高级') {
                // 填充得分
                const inputElement = row.querySelector('input[name="score"]');
                if (inputElement) {
                    inputElement.value = scoreData.score || '0';
                    console.log(`设置得分: ${scoreData.score}`);
                } else {
                    console.log(`未找到得分输入框: 条文号=${clauseNumber}`);
                }
                
                // 填充技术措施
                const textareaElement = row.querySelector('textarea.technical-measures');
                if (textareaElement) {
                    textareaElement.value = scoreData.technical_measures || '';
                    console.log(`设置技术措施: 长度=${scoreData.technical_measures ? scoreData.technical_measures.length : 0}`);
                } else {
                    console.log(`未找到技术措施文本框: 条文号=${clauseNumber}`);
                }
            }
        });
    }
    // 加载已保存的评分数据
    function loadSavedScores() {
        const level = '{{ current_level }}';
        const specialty = '{{ current_specialty }}';
        const standard = '{{ project.standard if project and project.standard else "成都市标" }}';
        
        // 获取项目ID（如果有的话）
        let projectId = null;
        const projectIdField = document.getElementById('project_id');
        if (projectIdField) {
            projectId = projectIdField.value;
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
            const projectId = document.getElementById('project_id')?.value;
            
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

            const requestData = {
                level: '{{ current_level }}',
                specialty: '{{ current_specialty }}',
                project_id: projectId,
                scores: scoreData,
                standard: '{{ project.standard if project and project.standard else "成都市标" }}'
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
                if ('{{ current_level }}' === '提高级') {
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
            const currentLevel = '{{ current_level }}';
            
            rows.forEach((row, index) => {
                try {
                    // 基本级
                    if (currentLevel === '基本级') {
                        const clauseNumber = row.querySelector('td:nth-child(1)')?.textContent.trim();
                        if (!clauseNumber) return;
                        
                        const isAchievedSelect = row.querySelector('select.is-achieved-select');
                        if (!isAchievedSelect) return;
                        
                        const technicalMeasuresTextarea = row.querySelector('textarea.technical-measures');
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
                        const clauseNumber = row.querySelector('td:nth-child(1)')?.textContent.trim();
                        if (!clauseNumber) return;
                        
                        const categoryElement = row.querySelector('td:nth-child(2) span');
                        if (!categoryElement) return;
                        
                        const category = categoryElement.textContent.trim();
                        const scoreInput = row.querySelector('input[name="score"]');
                        const technicalMeasuresTextarea = row.querySelector('textarea.technical-measures');
                        
                        let score = '0';
                        if (scoreInput) {
                            score = scoreInput.value || '0';
                            const maxScore = parseFloat(row.querySelector('td:nth-child(4)')?.textContent.trim());
                            if (!isNaN(maxScore) && parseFloat(score) > maxScore) {
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
            
            return scoreData;
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