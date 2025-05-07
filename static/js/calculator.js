
    // 全局存储计算结果 - 仅在此作用域内
    let reportData = {
        projectName: '',
        buildingNo: '',
        categories: {
            Q1: { score: 0, label: '主体及围护结构工程用材', total: 45 },
            Q2: { score: 0, label: '装饰装修工程用材', total: 35 },
            Q3: { score: 0, label: '机电安装工程用材', total: 15 },
            Q4: { score: 0, label: '室外工程用材', total: 5 }
        },
        totalScore: 0,
        result: 0,
        Original: '',
        standard: '',
        standardText: ''
    };
    
    // 使用常量存储固定值
    const STANDARDS = {
        CHENGDU: '成都市标',
        SICHUAN: '四川省标',
        NATIONAL: '通用国标'
    };

    const MIN_SCORES = {
        '安全耐久': 30.0,
        '健康舒适': 30.0,
        '生活便利': 21.0,
        '资源节约': 60.0,
        '环境宜居': 30.0,
        '提高与创新': 0.0
    };

    const STAR_LEVELS = {
        THREE_STAR: { score: 450, text: '三星级', color: 'text-green-600' },
        TWO_STAR: { score: 300, text: '二星级', color: 'text-blue-600' },
        ONE_STAR: { score: 200, text: '一星级', color: 'text-yellow-600' },
        NO_STAR: { text: '未达标', color: 'text-red-600' }
    };
    
    // DOM元素缓存
    let DOM = {};
    
    // 主要初始化函数
    document.addEventListener('DOMContentLoaded', function() {
        console.log('计算器页面加载完成');
        
        // 缓存常用DOM元素
        DOM = {
            specialtyScoresRow: document.getElementById('specialty-scores-row'),
            categoryScoresRow: document.getElementById('category-scores-row'),
            judgmentRow: document.querySelector('tbody tr:nth-child(3)'),
            starRatingScore: document.getElementById('star-rating-score'),
            starRatingStars: document.getElementById('star-rating-stars'),
            starRatingTotal: document.getElementById('star-rating-total'),
            buildingNo: document.getElementById('buildingNo'),
            standardSelection: document.getElementById('standardSelection'),
            projectId: document.getElementById('project_id'),
            resultDiv: document.getElementById('result'),
            indicatorsDiv: document.getElementById('indicators'),
            aiExtractButton: document.getElementById('aiExtractButton'),
            excelFileInput: document.getElementById('excelFileInput'),
            messageArea: document.getElementById('message-area')
        };
            
        // 初始化折叠功能
        initializeCollapsibleSections();
        // 初始化复选框
        initializeCheckboxes();
        // 初始化比例输入框事件
        initializeRatioInputs();
        // 初始化用量自动计算
        initializeQuantityCalculation();

        // --- 重新添加: 绑定 AI 提取按钮点击事件 ---
        if (DOM.aiExtractButton) {
            DOM.aiExtractButton.addEventListener('click', triggerFileInput);
        } else {
            console.error('未能找到 AI 提取按钮 (aiExtractButton)');
        }

        // 尝试加载表单数据
        loadForm();
    });

    // 折叠功能
    function initializeCollapsibleSections() {
        document.querySelectorAll('.toggle, .category h3').forEach((toggle, index) => {
            toggle.style.cursor = 'pointer';
            const content = toggle.parentElement.querySelector('.sub-items');
            
            // 默认折叠除了第一个类别
            if (index !== 0 && content) {
                content.style.display = 'none';
            }

            toggle.addEventListener('click', () => {
                if (content) {
                    content.style.display = content.style.display === 'none' ? 'block' : 'none';
                    const toggleIcon = toggle.parentElement.querySelector('.toggle');
                    if (toggleIcon) {
                        toggleIcon.innerHTML = content.style.display === 'none' ? 
                            '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M6 0L16 8L6 16V0Z"/></svg>' : 
                            '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6L16 6L8 16L0 6Z"/></svg>';
                    }
                }
            });
        });
    }
    
    // 初始化复选框事件
    function initializeCheckboxes() {
        document.querySelectorAll('.checkbox-wrapper input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const customCheckbox = this.nextElementSibling;
                if (this.checked) {
                    customCheckbox.classList.add('checked');
                } else {
                    customCheckbox.classList.remove('checked');
                }
            });
        });

        document.querySelectorAll('.checkbox-wrapper .custom-checkbox').forEach(customCheckbox => {
            customCheckbox.addEventListener('click', function() {
                const checkbox = this.previousElementSibling;
                checkbox.click();
            });
        });
    }
    
    // --- 新增: 初始化比例输入框事件 (空实现) ---
    function initializeRatioInputs() {
        // 目前不需要实际操作，保留为空以避免错误
        console.log('initializeRatioInputs called, but no action needed currently.');
    }
    
    // --- 新增: 初始化用量自动计算 ---
    function initializeQuantityCalculation() {
        console.log('Initializing quantity calculation listeners...');
        DOM.indicatorsDiv.querySelectorAll('.sub-item.checkbox-wrapper').forEach(itemRow => {
            const ratioInput = itemRow.querySelector('input[type="number"]'); // 绿材应用比例
            const totalQuantityInput = itemRow.querySelector('input[placeholder="材料总量"]'); // 材料总量
            const greenQuantityInput = itemRow.querySelector('input[placeholder="绿材用量"]'); // 绿材应用量
            const checkbox = itemRow.querySelector('input[type="checkbox"]'); // 获取同一行的复选框

            if (ratioInput && totalQuantityInput && greenQuantityInput && checkbox) {
                const calculateAndUpdate = () => {
                    const ratio = parseFloat(ratioInput.value) || 0;
                    const totalQuantity = parseFloat(totalQuantityInput.value) || 0;

                    // 计算绿材用量
                    if (!isNaN(ratio) && !isNaN(totalQuantity) && ratio >= 0 && totalQuantity >= 0) {
                        const greenQuantity = (totalQuantity * (ratio / 100)).toFixed(2); // 保留两位小数
                        greenQuantityInput.value = greenQuantity;
                    } else {
                        // 如果输入无效或为空，清空绿材用量
                        greenQuantityInput.value = ''; 
                    }

                    // --- 新增逻辑: 如果材料总量 > 0，则勾选复选框 ---
                    if (totalQuantity > 0 && !checkbox.checked) {
                        checkbox.checked = true;
                        // 触发 change 事件以更新自定义复选框的样式
                        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    // ----------------------------------------------
                };

                // 为比例和总量输入框添加事件监听器
                ratioInput.addEventListener('input', calculateAndUpdate);
                totalQuantityInput.addEventListener('input', calculateAndUpdate);

                // // 可选：页面加载时也计算一次初始值 (如果需要)
                // calculateAndUpdate(); 
            } else {
                // console.warn('Could not find all required inputs or checkbox in a sub-item row for calculation.', itemRow);
            }
        });
        console.log('Quantity calculation listeners initialized.');
    }
    
    // 计算得分
    function calculate() {
        try {
            // 重置数据
            reportData.buildingNo = DOM.buildingNo ? DOM.buildingNo.value || '' : '';
            reportData.standard = DOM.standardSelection ? DOM.standardSelection.value || 'municipal' : 'municipal';
            
            // 根据选择的标准设置显示文本
            switch(reportData.standard) {
                case 'municipal':
                    reportData.standardText = STANDARDS.CHENGDU;
                    break;
                case 'provincial':
                    reportData.standardText = STANDARDS.SICHUAN;
                    break;
                case 'national':
                    reportData.standardText = STANDARDS.NATIONAL;
                    break;
                default:
                    reportData.standardText = STANDARDS.CHENGDU;
            }
            
            Object.values(reportData.categories).forEach(cat => {
                cat.score = 0;
                cat.items = []; // 确保 items 数组被重置
            });
            reportData.totalScore = 0;
            reportData.result = 0;
            reportData.Original = '';

            // 遍历每个分类区块
            document.querySelectorAll('.category').forEach(categoryDiv => {
                const categoryKey = categoryDiv.getAttribute('data-category');
                const category = reportData.categories[categoryKey];

                if (!category) {
                    console.error(`未找到分类: ${categoryKey}`);
                    return;
                }
                // 遍历子项，跳过第一项（标题行）
                let checkedCount = 0;
                let qualifiedCount = 0;
                let isFirstItem = true;
                categoryDiv.querySelectorAll('.sub-item').forEach(itemDiv => {
                    // 跳过第一项（标题行）
                    if (isFirstItem) {
                        isFirstItem = false;
                        return;
                    }

                    const checkbox = itemDiv.querySelector('input[type="checkbox"]');
                    const input = itemDiv.querySelector('input[type="number"]');
                    const actualValue = parseFloat(input.value) || 0;

                    // 查找指标名称
                    const indicatorSpan = itemDiv.querySelector('.col-indicator');
                    const itemName = indicatorSpan ? indicatorSpan.textContent.trim() : '未知指标';

                    category.items.push({
                        name: itemName,
                        checked: checkbox.checked,
                        actual: actualValue
                    });

                    if (checkbox.checked) {
                        checkedCount++;
                        if (actualValue >= 80) qualifiedCount++;
                    }
                });

                // 计算分类得分（核心公式）
                const categoryTotal = category.total;
                const categoryScore = checkedCount > 0 
                    ? (qualifiedCount / checkedCount) * categoryTotal
                    : 0;
                category.score = categoryScore;
                reportData.totalScore += categoryScore; // 累加总得分
            });

            // 计算绿建得分
            reportData.result = calculateGreenScore(reportData.totalScore);
            //结论
            if (reportData.totalScore > 10 && reportData.result == 0) {
                reportData.Original = "本项目绿色建材应用比例为" + reportData.totalScore.toFixed(1) + "%，满足《绿色建筑评价标准》GB/T 50378-2019（2024版）第3.2.8条要求。";
            } else if(reportData.result > 0) {
                reportData.Original = "本项目绿色建材应用比例为" + reportData.totalScore.toFixed(1) + "%，满足《绿色建筑评价标准》GB/T 50378-2019（2024版）第3.2.8条要求，且满足第7.2.18条要求，可得" + reportData.result + "分。";
            }
            
            // 显示结果
            showResult(reportData);
            
            // 添加200ms延时，确保滚动到底部
            setTimeout(() => {
                window.scrollTo(0, document.body.scrollHeight);
            }, 200);
        } catch (error) {
            handleError('计算错误', error);
        }
    }

    // 计算绿建得分
    function calculateGreenScore(total) {
        if (total >= 70) return 12;
        if (total >= 60) return 8;
        if (total >= 40) return 4;
        return 0;
    }
    
    // 计算绿建星级
    function calculateGreenStar(total) {
        if (total >= 30) return '三星级绿色建筑';
        if (total >= 20) return '二星级绿色建筑';
        if (total >= 10) return '一星级绿色建筑';
        return '未达到绿建星级'; // 默认返回值
    }
    
    // 结果显示函数
    function showResult(data) {
        if (!DOM.resultDiv) return;
        
        DOM.resultDiv.classList.remove('hidden');
        const GreenStar = calculateGreenStar(data.totalScore);
        
        DOM.resultDiv.innerHTML = `
            <h3 class="text-2xl font-semibold text-primary mb-6">绿色建材得分统计</h3>
            <div class="space-y-4 mb-6">
                <p class="text-gray-700">子项名称：${data.buildingNo || '未填写'}</p>
                <p class="text-gray-700">评价标准：${data.standardText || '成都市标'}</p>
            </div>
            <hr class="my-6">
            <div class="space-y-4">
                ${Object.entries(data.categories).map(([key, category]) => `
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <div class="font-medium text-gray-900">${category.label}</div>
                        <div class="mt-2 text-gray-600">
                            得分 ${category.score.toFixed(1)} / 总分 ${category.total}
                            <span class="text-primary">(达标率 ${(category.score / category.total * 100).toFixed(1)}%)</span>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="mt-6 p-4 bg-blue-50 rounded-lg">
                <h4 class="text-xl font-medium text-primary">
                    总得分：${data.totalScore.toFixed(1)} 分（满分100分）
                </h4>
            </div>
            <div class="mt-6 p-4 bg-green-50 rounded-lg">
                <h3 class="text-lg font-medium text-green-800">
                    绿色建材应用比例：${(data.totalScore / 100 * 100).toFixed(1)}%
                    <br>
                    ${GreenStar}，绿建评分项可得分：${data.result}分
                </h3>
            </div>
        `;
    }

    // 保存表单数据
    async function saveForm() {
        try {
            // 显示保存中的提示
            const saveBtn = document.querySelector('button[onclick="saveForm()"]');
            if (!saveBtn) return;
            
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '保存中...';
            saveBtn.disabled = true;
            
            // 获取项目ID
            const projectId = DOM.projectId ? DOM.projectId.value : '';
            if (!projectId) {
                // 恢复按钮状态以防万一
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
                alert('未找到项目ID，请确保在项目环境中操作');
                // throw new Error('未找到项目ID，请确保在项目环境中操作'); // 改为 alert 并提前返回
                return;
            }
            
            // 收集所有表单数据
            const formData = {
                buildingNo: DOM.buildingNo ? DOM.buildingNo.value || '' : '',
                standardSelection: DOM.standardSelection ? DOM.standardSelection.value || 'municipal' : 'municipal',
                project_id: projectId,
                formData: {} // This will store category data like Q1, Q2 etc.
            };

            // 收集所有分类的数据
            document.querySelectorAll('.category').forEach(category => {
                const categoryKey = category.getAttribute('data-category');
                formData.formData[categoryKey] = [];
                
                let isFirstItem = true; // Skip header row
                category.querySelectorAll('.sub-item').forEach(item => {
                    if (isFirstItem) {
                        isFirstItem = false;
                        return;
                    }
                    
                    const indicatorSpan = item.querySelector('.col-indicator');
                    const checkbox = item.querySelector('input[type="checkbox"]');
                    const ratioInput = item.querySelector('input[type="number"]'); // For "绿材应用比例"
                    const totalQuantityInput = item.querySelector('input[placeholder="材料总量"]');
                    const greenQuantityInput = item.querySelector('input[placeholder="绿材用量"]');
                    
                    if (indicatorSpan && checkbox) { // Basic elements to identify a row
                        const itemName = indicatorSpan.textContent.trim();
                        const itemData = {
                            name: itemName,
                            checked: checkbox.checked,
                            ratio: ratioInput ? (ratioInput.value || "0") : "0",
                            totalQuantity: totalQuantityInput ? (totalQuantityInput.value || "") : "",
                            greenQuantity: greenQuantityInput ? (greenQuantityInput.value || "") : ""
                        };
                        formData.formData[categoryKey].push(itemData);
                    }
                });
            });

            // 确保 JSON 数据不超过数据库字段长度限制 (针对 formData.formData 部分)
            const itemsJsonString = JSON.stringify(formData.formData);
            if (itemsJsonString.length > 40000) { // Increased limit, adjust as necessary for your DB
                // 恢复按钮状态
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
                alert('表单数据过大，请减少输入数据量');
                // throw new Error('表单数据过大，请减少输入数据量'); // 改为 alert 并提前返回
                return;
            }

            // 发送保存请求
            console.log(`正在保存项目ID ${projectId} 的表单数据...`, formData);
            const response = await fetch('/api/save_form', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData) // Send the whole formData object
            });

            // 恢复按钮状态 (无论成功或失败，除非特定错误提前返回)
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;

            if (response.ok) {
                const data = await response.json();
                Toastify({
                    text: '数据保存成功！',
                    duration: 3000,
                    gravity: 'top',
                    position: 'right',
                    style: {
                            background: 'linear-gradient(to right, #00b09b, #96c93d)'
                        }
                    }).showToast();

            } else {
                const errorData = await response.json().catch(() => ({ error: '保存失败，无法解析响应内容' }));
                // throw new Error(errorData.error || '保存失败，服务器返回错误'); 
                // 让下面的 catch 处理UI和日志记录
                // Forcing error to be an Error object for the catch block
                const err = new Error(errorData.error || `保存失败，服务器状态: ${response.status}`);
                err.response = errorData; // Attach more details if needed
                throw err;
            }
        } catch (error) {
            console.error('保存数据时发生错误:', error); // Log the full error
            // 确保按钮恢复正常状态
            const saveBtn = document.querySelector('button[onclick="saveForm()"]');
            if (saveBtn && saveBtn.disabled) { // Check if it's still disabled (might have been enabled before error)
                saveBtn.textContent = '保存数据'; // Or originalText if accessible here
                saveBtn.disabled = false;
            }
            
            // 调用 handleError (如果已定义) 或显示通用错误消息
            if (typeof handleError === 'function') {
                handleError('保存数据失败', error);
            } else {
                alert('保存数据失败: ' + (error.message || '未知错误，请查看控制台。'));
            }
        }
    }

    // 加载表单数据
    async function loadForm() {
        // 添加检查，如果不存在buildingNo元素，说明不是目标计算器页面，直接返回
        if (!DOM.buildingNo) {
            console.log('当前页面不是绿色建材计算器页面，跳过loadForm执行');
            return;
        }
        
        try {
            // 获取当前项目ID
            const projectId = DOM.projectId ? DOM.projectId.value : '';
            if (!projectId) {
                console.warn('未找到项目ID，无法加载表单数据');
                return;
            }
            
            console.log(`尝试加载项目ID ${projectId} 的表单数据`);
            
            // 构建请求URL，加入项目ID参数
            let url = `/api/load_form?project_id=${projectId}`;
            
            const response = await fetch(url);
            
            if (response.status === 404) {
                console.log(`项目ID ${projectId} 没有保存的表单数据`);
                return; // 没有数据是正常的，直接返回
            }
            
            if (!response.ok) {
                console.error(`加载数据失败: 状态码 ${response.status}, 状态文本 ${response.statusText}`);
                try {
                    const errorText = await response.text();
                    console.error(`错误详情: ${errorText}`);
                } catch (e) {
                    console.error(`无法获取错误详情: ${e.message}`);
                }
                throw new Error(`加载数据失败: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('成功加载表单数据:', data);
            
            // 填充基本信息
            if (data.buildingNo) {
                DOM.buildingNo.value = data.buildingNo;
                console.log(`设置子项名称: ${data.buildingNo}`);
            }
            
            if (data.standardSelection && DOM.standardSelection) {
                DOM.standardSelection.value = data.standardSelection;
                console.log(`设置评价依据: ${data.standardSelection}`);
            }
            
            // 检查数据结构，新的后端接口直接返回表单数据
            const formDataToLoad = data.formData || data; // 'formData' is the key where item data is stored by saveForm
            
            if (formDataToLoad && Object.keys(formDataToLoad).length > 0) {
                console.log('开始填充表单数据');
                
                // 遍历所有类别
                Object.entries(formDataToLoad).forEach(([categoryKey, items]) => {
                    if (!Array.isArray(items)) {
                        console.warn(`类别 ${categoryKey} 的数据不是数组:`, items);
                        return;
                    }
                    
                    const categoryElement = document.querySelector(`.category[data-category="${categoryKey}"]`);
                    if (!categoryElement) {
                        console.warn(`未找到类别元素: ${categoryKey}`);
                        return;
                    }
                    
                    console.log(`处理类别 ${categoryKey}, 包含 ${items.length} 项数据`);
                    
                    // 获取所有子项（不包括标题行）
                    const allSubItems = Array.from(categoryElement.querySelectorAll('.sub-item')).slice(1);
                    
                    // 填充数据
                    items.forEach((itemData, index) => { // Renamed 'item' to 'itemData' to avoid conflict
                        if (index >= allSubItems.length) {
                            console.warn(`项索引超出范围: ${index}, 类别: ${categoryKey}`);
                            return;
                        }
                        
                        const subItem = allSubItems[index];
                        const checkbox = subItem.querySelector('input[type="checkbox"]');
                        const ratioInput = subItem.querySelector('input[type="number"]'); // "绿材应用比例"
                        const totalQuantityInput = subItem.querySelector('input[placeholder="材料总量"]');
                        const greenQuantityInput = subItem.querySelector('input[placeholder="绿材用量"]');
                        
                        if (itemData) { // Ensure itemData exists
                            if (checkbox && 'checked' in itemData) {
                                checkbox.checked = itemData.checked === true || String(itemData.checked).toLowerCase() === 'true';
                                // 触发change事件更新自定义复选框的样式
                                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                            
                            if (ratioInput && 'ratio' in itemData) {
                                ratioInput.value = itemData.ratio || '0';
                            }
                            
                            if (totalQuantityInput && 'totalQuantity' in itemData) {
                                totalQuantityInput.value = itemData.totalQuantity || '';
                            }
                            
                            if (greenQuantityInput && 'greenQuantity' in itemData) {
                                // Directly set green quantity from saved data.
                                // The automatic calculation will verify/override this if totalQuantity or ratio changes.
                                greenQuantityInput.value = itemData.greenQuantity || '';
                            }

                            // After setting values, trigger input events to ensure
                            // dependent calculations and UI updates (like checkbox state from totalQuantity) occur.
                            if (ratioInput) {
                                ratioInput.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                            if (totalQuantityInput) {
                                totalQuantityInput.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }
                    });
                });
                
                console.log('表单数据填充完成');
            } else {
                console.warn('没有可用的表单数据或表单数据为空');
            }
        } catch (error) {
            console.error('加载表单数据时出错:', error);
            // Ensure handleError is defined or provide a fallback
            if (typeof handleError === 'function') {
                handleError('加载数据失败', error);
            } else {
                alert('加载数据失败: ' + error.message);
            }
        }
    }

    // 统一的错误处理函数
    function handleError(message, error) {
        console.error(`${message}:`, error);
        if (DOM.messageArea) {
            setMessage(`${message}: ${error.message}`, 'text-red-600');
        } else {
            alert(`${message}: ${error.message}`);
        }
        const debugInfo = document.getElementById('debug-info');
        if (debugInfo) {
            debugInfo.textContent = `错误: ${error.message}`;
        }
        alert(`${message}: ${error.message}`);
    }
    // 应用得分到项目
    async function applyScore() {
        //获取评价标准
        const standardSelection = document.getElementById('standardSelection').value || 'municipal';
        // 获取计算结果数据
        if (reportData.result && reportData.result > 0) {
            if(standardSelection == 'municipal'){
                updateDatabaseScore('3.1.2.20', reportData.result,"是", '满足要求，详见绿色建材应用比例计算书');
            }else if(standardSelection == 'provincial'){
                updateDatabaseScore('3.1.24', reportData.result,"是", '满足要求，详见绿色建材应用比例计算书');
            }else if(standardSelection == 'national'){
                updateDatabaseScore('7.2.18', reportData.result,"是", '满足要求，详见绿色建材应用比例计算书');
            }
            Toastify({
                text: '得分已成功应用到项目！',
                duration: 3000,
                gravity: 'top',
                position: 'right',
                style: {
                    background: 'linear-gradient(to right, #00b09b, #96c93d)'
                }
            }).showToast();
        }
    }
    // 导出Word功能 - 异步函数
    async function exportWord() {
        try {
            // 数据校验
            if (!reportData || typeof reportData.totalScore === 'undefined') throw new Error('请先计算数据！');
            
            // 从页面获取子项名称和评价依据
            const buildingNo = document.getElementById('buildingNo').value || '';
            const selectedValue = document.getElementById('standardSelection').value || 'municipal';

            // 获取项目ID - 多种方式尝试获取
            let projectId = null;
            
            // 1. 从模板直接获取（服务器端渲染）
            const projectIdFromTemplate = document.getElementById('current-project-id')?.value;
            if (projectIdFromTemplate && projectIdFromTemplate !== "") {
                projectId = projectIdFromTemplate;
                console.log("从current-project-id元素获取项目ID:", projectId);
            }
            
            // 2. 从URL参数获取
            if (!projectId) {
                const urlParams = new URLSearchParams(window.location.search);
                const projectIdFromUrl = urlParams.get('project_id');
                if (projectIdFromUrl) {
                    projectId = projectIdFromUrl;
                    console.log("从URL参数获取项目ID:", projectId);
                }
            }
            
            // 3. 从project_id元素获取
            if (!projectId) {
                const projectIdFromElement = document.getElementById('project_id')?.value;
                if (projectIdFromElement) {
                    projectId = projectIdFromElement;
                    console.log("从project_id元素获取项目ID:", projectId);
                }
            }
            
            // 4. 从URL路径获取
            if (!projectId) {
                const pathMatch = window.location.pathname.match(/\/project\/(\d+)/);
                if (pathMatch && pathMatch[1]) {
                    projectId = pathMatch[1];
                    console.log("从URL路径获取项目ID:", projectId);
                }
            }
            
            // 检查是否获取到项目ID
            if (!projectId) {
                alert("未能获取到项目ID，无法导出计算书！请确保在项目详情页中操作，或者页面正确传递了项目参数。");
                console.error("无法获取项目ID，导出失败");
                return;
            }
            
            console.log("最终使用的项目ID:", projectId);
            
            // 显示加载提示窗口
            try {
                if (typeof ExportLoadingModal !== 'undefined') {
                    ExportLoadingModal.show({
                        title: '正在生成计算书',
                        description: '请耐心等待，文档生成需要一点时间...',
                        showTimer: true,
                        showBackdrop: false,
                        autoTimeout: 30000
                    });
                } else {
                    console.warn("ExportLoadingModal组件未定义，使用基本加载提示");
                }
            } catch (modalError) {
                console.error("显示导出加载模态框失败:", modalError);
                // 继续执行，不阻断导出流程
            }
            
            // 获取项目信息
            let projectInfo = {};
            
            try {
                console.log("正在通过API获取项目信息...");
                const projectInfoResponse = await fetch(`/api/project_info?project_id=${projectId}`);
                
                if (projectInfoResponse.ok) {
                    const responseData = await projectInfoResponse.json();
                    console.log("成功获取项目信息:", responseData);
                    
                    // 处理可能的中英文字段名
                    projectInfo = {
                        projectName: responseData.projectName || responseData['项目名称'] || '',
                        projectLocation: responseData.projectLocation || responseData['项目地点'] || '',
                        projectCode: responseData.projectCode || responseData['项目编号'] || '',
                        constructionUnit: responseData.constructionUnit || responseData['建设单位'] || '',
                        designUnit: responseData.designUnit || responseData['设计单位'] || ''
                    };
                } else {
                    console.error("获取项目信息失败:", projectInfoResponse.status, projectInfoResponse.statusText);
                }
            } catch (error) {
                console.error("获取项目信息时发生错误:", error);
            }
            
            // 直接从静态目录获取模板文件
            const response = await fetch('/static/templates/绿色建材应用比例计算书.docx');
            if (!response.ok) throw new Error('无法获取模板文件，请确认模板文件存在');
            
            const blob = await response.blob();
            const zip = await JSZip.loadAsync(blob);
            let xml = await zip.file('word/document.xml').async('text');
            
            let standardtext = '';
            // 评价依据处理
            switch(selectedValue) {
                case 'national':
                    standardtext = `1、《绿色建筑评价标准》GB/T50378-2019（2024版）\n2、《绿色建筑评价技术细则》`;
                    break;
                case 'provincial':
                    standardtext = `1、《绿色建筑评价标准》GB/T50378-2019（2024版）\n2、四川省建筑工程绿色建材应用比例核算技术细则（试行）\n3、四川省民用绿色建筑设计施工图阶段审查技术要点（2024版）\n4、《绿色建筑评价技术细则》`;
                    break;
                case 'municipal':
                    standardtext = `1、《绿色建筑评价标准》GB/T50378-2019（2024版）\n2、四川省建筑工程绿色建材应用比例核算技术细则（试行）\n3、成都市绿色建筑施工图设计与审查技术要点（2024版）\n4、《绿色建筑评价技术细则》`;
                    break;
                default:
                    console.warn("未选择有效的评价依据");
                    break;
            }

            // 替换模板中的占位符
            const replacements = {
                '{{项目名称}}': projectInfo.projectName || '',
                '{{子项名称}}': buildingNo, // 从页面获取
                '{{工程地点}}': projectInfo.projectLocation || '',
                '{{设计编号}}': projectInfo.projectCode || '', // 使用项目编号作为设计编号
                '{{建设单位}}': projectInfo.constructionUnit || '',
                '{{设计单位}}': projectInfo.designUnit || '',
                '{{总得分}}': (reportData.totalScore ?? 0).toFixed(1),
                '{{评价依据}}': standardtext,
                '{{Q1_分值}}': (reportData.categories.Q1?.score ?? 0).toFixed(1),
                '{{Q2_分值}}': (reportData.categories.Q2?.score ?? 0).toFixed(1),
                '{{Q3_分值}}': (reportData.categories.Q3?.score ?? 0).toFixed(1),
                '{{Q4_分值}}': (reportData.categories.Q4?.score ?? 0).toFixed(1),
                '{{绿建评分}}': (reportData.result ?? 0).toString(),
                '{{计算日期}}': new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }),
                '{{结论}}': reportData.Original || ''
            };

            // 动态添加子项占位符
            if (reportData.categories) {
                Object.keys(reportData.categories).forEach(categoryKey => {
                    const category = reportData.categories[categoryKey];
                    if (category.items) {
                        category.items.forEach((item, index) => {
                            replacements[`{{${categoryKey}_item${index + 1}}}`] = item.checked ? item.actual.toFixed(1) + '%' : '——';
                        });
                    }
                });
            }

            // 替换所有占位符
            xml = xml.replace(/{{(.*?)}}/g, (match, p1) => replacements[match] || '');

            // 保存文件
            zip.file('word/document.xml', xml);
            const resultBlob = await zip.generateAsync({ type: 'blob' });
            saveAs(resultBlob, buildingNo+`-绿色建材应用比例计算书.docx`);
        } catch (error) {
            alert(`导出失败: ${error.message}`);
            console.error('导出Word错误详情:', error);
        } finally {
            // 隐藏加载提示窗口
            try {
                if (typeof ExportLoadingModal !== 'undefined') {
                    ExportLoadingModal.hide();
                } else {
                    console.warn("ExportLoadingModal组件未定义，无法隐藏加载提示");
                }
            } catch (modalError) {
                console.error("隐藏导出加载模态框失败:", modalError);
            }
        }
    }
    
    // --- 重新添加: 设置消息 ---
    function setMessage(text, cssClass = 'text-gray-600') {
        if (DOM.messageArea) {
            DOM.messageArea.textContent = text;
            DOM.messageArea.className = `mt-4 text-sm ${cssClass}`; // 重置样式并添加新类
        } else {
            // 如果找不到消息区域，打印到控制台作为备用
            console.log("Message:", text, `(CSS Class: ${cssClass})`);
            // 可以考虑在这里添加一个 alert 作为更强的提示
            // alert(text);
        }
    }

    // --- 重新添加: 清除文件输入框的值 ---
    function clearFileInput() {
        if (DOM.excelFileInput) {
            DOM.excelFileInput.value = ''; // 清除文件选择
        }
    }

    // --- 重新添加: 触发文件选择 ---
    function triggerFileInput() {
        if (DOM.excelFileInput) {
            DOM.excelFileInput.click(); // 模拟点击隐藏的文件输入框
        } else {
            // 如果找不到元素，使用 handleError
            handleError('无法找到文件输入元素', new Error('DOM.excelFileInput is null or undefined. Make sure the element with id="excelFileInput" exists.'));
        }
    }

    // --- 修改: 处理文件选择和上传 (不更新输入框) ---
    async function handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) {
            setMessage('未选择文件。', 'text-yellow-600');
            return;
        }

        // 文件类型检查 (可选)
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
             setMessage('请选择 Excel 文件 (.xlsx 或 .xls)。', 'text-red-600');
             clearFileInput(); // 清除选择
             return;
        }

        setMessage('正在处理文件...', 'text-blue-600');

        const formData = new FormData();
        formData.append('excel_file', file);

        try {
            const response = await fetch('/api/extract_quantities', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                 throw new Error(data.error);
            }

            console.log('后端返回的工程量:', data.quantities); // 在控制台打印结果

            // --- 开始: 更新前端输入框 ---
            let updatedCount = 0;
            const notFoundIndicators = [];
            const successfullyUpdated = []; // 跟踪成功更新的指标

            if (data.quantities && typeof data.quantities === 'object') {
                Object.entries(data.quantities).forEach(([backendIndicatorName, quantity]) => {
                    let foundMatch = false;
                    // 尝试精确匹配指标名称
                    document.querySelectorAll('.sub-item.checkbox-wrapper').forEach(itemRow => {
                        const indicatorSpan = itemRow.querySelector('.col-indicator');
                        const rowIndicatorName = indicatorSpan ? indicatorSpan.textContent.trim() : null;

                        if (rowIndicatorName && rowIndicatorName === backendIndicatorName) {
                            const totalQuantityInput = itemRow.querySelector('input[placeholder="材料总量"]');
                            if (totalQuantityInput) {
                                console.log(`匹配成功: ${rowIndicatorName} -> 填入值: ${quantity}`);
                                totalQuantityInput.value = quantity;
                                // 触发 input 事件以更新"绿材用量"
                                totalQuantityInput.dispatchEvent(new Event('input', { bubbles: true })); 
                                updatedCount++;
                                successfullyUpdated.push(rowIndicatorName);
                                foundMatch = true;
                                // 如果假设指标名称唯一，可以在这里停止内部循环，但为安全起见，继续检查所有行
                            } else {
                                console.warn(`在指标 "${rowIndicatorName}" 的行中未找到 "材料总量" 输入框。`);
                            }
                        }
                    });

                    if (!foundMatch) {
                        notFoundIndicators.push(backendIndicatorName);
                    }
                });

                 // 更新消息反馈
                let message = `成功更新了 ${updatedCount} 个指标的工程量。`;
                if (successfullyUpdated.length > 0) {
                    // 可以选择性地列出部分更新的指标
                    // message += ` 更新的指标包括: ${successfullyUpdated.slice(0, 5).join(', ')}${successfullyUpdated.length > 5 ? ' 等' : ''}.`;
                }
                 if (notFoundIndicators.length > 0) {
                    message += ` ${notFoundIndicators.length} 个指标未在页面上找到匹配项: ${notFoundIndicators.join(', ')}。请检查Excel表头或页面指标名称。`;
                    setMessage(message, 'text-yellow-600');
                } else {
                    setMessage(message, 'text-green-600');
                }

            } else {
                 setMessage('未从文件中提取到有效数据或数据格式不正确。', 'text-yellow-600');
            }
            // --- 结束: 更新前端输入框 ---

        } catch (error) {
            handleError('提取工程量失败', error);
            setMessage(`提取失败: ${error.message}`, 'text-red-600');
        } finally {
            clearFileInput(); // 清除文件输入，以便下次可以选择同名文件
        }
    }







