(function() {
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
            resultDiv: document.getElementById('result')
        };
        
        // 初始化折叠功能
        initializeCollapsibleSections();
        // 初始化复选框
        initializeCheckboxes();
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

                    category.items.push({
                        name: itemDiv.textContent.split('≥')[0].trim(),
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
            
            // 收集所有表单数据
            const formData = {
                buildingNo: DOM.buildingNo ? DOM.buildingNo.value || '' : '',
                standardSelection: DOM.standardSelection ? DOM.standardSelection.value || 'municipal' : 'municipal',
                project_id: DOM.projectId ? DOM.projectId.value || '' : '', // 获取当前项目ID
                formData: {}
            };

            // 收集所有分类的数据
            document.querySelectorAll('.category').forEach(category => {
                const categoryKey = category.getAttribute('data-category');
                formData.formData[categoryKey] = [];
                
                // 跳过第一个子项（标题行）
                let isFirstItem = true;
                category.querySelectorAll('.sub-item').forEach(item => {
                    if (isFirstItem) {
                        isFirstItem = false;
                        return;
                    }
                    
                    const checkbox = item.querySelector('input[type="checkbox"]');
                    const input = item.querySelector('input[type="number"]');
                    
                    if (checkbox && input) {
                        formData.formData[categoryKey].push({
                            checked: checkbox.checked,
                            value: input.value || "0"
                        });
                    }
                });
            });

            // 确保 JSON 数据不超过数据库字段长度限制
            const jsonString = JSON.stringify(formData.formData);
            if (jsonString.length > 4000) {
                throw new Error('表单数据过大，请减少输入数据量');
            }

            const response = await fetch('/api/save_form', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            // 恢复按钮状态
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;

            if (response.ok) {
                // 显示成功消息
                alert('数据保存成功！');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || '保存失败');
            }
        } catch (error) {
            handleError('保存数据失败', error);
            
            // 确保按钮恢复正常状态
            const saveBtn = document.querySelector('button[onclick="saveForm()"]');
            if (saveBtn && saveBtn.disabled) {
                saveBtn.textContent = '保存数据';
                saveBtn.disabled = false;
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
            // 构建请求URL，加入项目ID参数
            let url = '/api/load_form';
            if (projectId) {
                url += `?project_id=${projectId}`;
            }
            
            const response = await fetch(url);
            if (response.ok) {
                const data = await response.json();
                
                // 填充基本信息
                DOM.buildingNo.value = data.buildingNo || '';
                if (DOM.standardSelection) {
                    DOM.standardSelection.value = data.standardSelection || 'municipal';
                }
                
                // 填充表单数据
                if (data.formData) {
                    Object.entries(data.formData).forEach(([categoryKey, items]) => {
                        const category = document.querySelector(`.category[data-category="${categoryKey}"]`);
                        if (!category) return;
                        
                        // 跳过第一个子项（标题行）
                        let subItems = Array.from(category.querySelectorAll('.sub-item'));
                        subItems = subItems.slice(1); // 跳过标题行
                        
                        items.forEach((item, index) => {
                            if (index >= subItems.length) return;
                            
                            const subItem = subItems[index];
                            const checkbox = subItem.querySelector('input[type="checkbox"]');
                            const input = subItem.querySelector('input[type="number"]');
                            
                            if (checkbox && input) {
                                checkbox.checked = item.checked;
                                input.value = item.value || "0";
                                
                                // 触发checkbox的change事件以更新样式
                                const event = new Event('change');
                                checkbox.dispatchEvent(event);
                            }
                        });
                    });
                }
                console.log('表单数据加载成功');
            } else if (response.status !== 404) {
                // 404 表示没有保存的数据，这是正常的
                console.warn('加载表单数据失败:', response.statusText);
            }
        } catch (error) {
            handleError('加载数据失败', error);
        }
    }

    // 导出到Word功能
    function exportToWordSimple() {
        var exportContent = document.querySelector('#export-content');
        if (!exportContent) return;
        
        var html = exportContent.innerHTML;
        var blob = new Blob(['<html><head><meta charset="utf-8"><title>绿色建材应用比例计算</title><style>body{font-family:SimSun, serif;font-size:12pt;line-height:1.5;}table{border-collapse:collapse;width:100%;}th,td{border:1px solid black;padding:8px;text-align:left;}th{background-color:#f2f2f2;}h1,h2,h3{text-align:center;}</style></head><body>' + html + '</body></html>'], {type: 'application/msword'});
        saveAs(blob, '绿色建材应用比例计算.doc');
    }
    
    // 统一的错误处理函数
    function handleError(message, error) {
        console.error(`${message}:`, error);
        const debugInfo = document.getElementById('debug-info');
        if (debugInfo) {
            debugInfo.textContent = `错误: ${error.message}`;
        }
        alert(`${message}: ${error.message}`);
    }
    
    // 将需要在外部调用的函数挂载到 window 对象
    window.calculate = calculate;
    window.saveForm = saveForm;
    window.loadForm = loadForm;
    window.exportToWordSimple = exportToWordSimple;
    // 将reportData的引用也挂载到window，供导出函数使用
    window.getCurrentReportData = function() { return reportData; }; 
})();
    
    
    

