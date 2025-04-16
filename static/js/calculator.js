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
    
    // 不再将reportData添加到window对象
    // window.reportData = reportData;
    
    // 优化后的用户信息加载
    document.addEventListener('DOMContentLoaded', function() {
        // 延迟加载表单数据
        setTimeout(loadForm, 300);
        
        // 初始化折叠功能
        initializeCollapsibleSections();
        
        // 初始化复选框事件
        initializeCheckboxes();
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
    
    function calculate() {
        try {
            // 重置数据
            reportData.buildingNo = document.getElementById('buildingNo').value || '';
            reportData.standard = document.getElementById('standardSelection').value || '成都市标';
            
            // 根据选择的标准设置显示文本
            switch(reportData.standard) {
                case 'municipal':
                    reportData.standardText = '成都市标';
                    break;
                case 'provincial':
                    reportData.standardText = '四川省标';
                    break;
                case 'national':
                    reportData.standardText = '通用国标';
                    break;
                default:
                    reportData.standardText = '成都市标';
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
            if (reportData.totalScore > 10 && reportData.result == 0)
            {
              reportData.Original = "本项目绿色建材应用比例为" + reportData.totalScore.toFixed(1) + "%，满足《绿色建筑评价标准》GB/T 50378-2019（2024版）第3.2.8条要求。"
            }
            else if(reportData.result>0)
            {
              reportData.Original = "本项目绿色建材应用比例为" + reportData.totalScore.toFixed(1) + "%，满足《绿色建筑评价标准》GB/T 50378-2019（2024版）第3.2.8条要求，且满足第7.2.18条要求，可得" + reportData.result + "分。"
            }
            // 显示结果
            showResult(reportData);
            // 添加200ms延时，确保滚动到底部
            setTimeout(() => {
                window.scrollTo(0, document.body.scrollHeight);
            }, 200);
        } catch (error) {
            alert('计算错误：' + error.message);
            console.error('计算错误详情:', error);
        }
    }

    function calculateGreenScore(total) {
        if (total >= 70) return 12;
        if (total >= 60) return 8;
        if (total >= 40) return 4;
        return 0;
    }
    function calculateGreenStar(total) {
        if (total >= 30) return '三星级绿色建筑';
        if (total >= 20) return '二星级绿色建筑';
        if (total >= 10) return '一星级绿色建筑';
        return '未达到绿建星级'; // 默认返回值
    }
    // 更新后的结果显示函数
    function showResult(data) {
        const resultDiv = document.getElementById('result');
        resultDiv.classList.remove('hidden');
        const GreenStar = calculateGreenStar(data.totalScore);
        
        resultDiv.innerHTML = `
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

    // 添加保存表单数据的函数
    async function saveForm() {
        try {
            // 显示保存中的提示
            const saveBtn = document.querySelector('button[onclick="saveForm()"]');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '保存中...';
            saveBtn.disabled = true;
            
            // 收集所有表单数据
            const formData = {
                buildingNo: document.getElementById('buildingNo').value || '',
                standardSelection: document.getElementById('standardSelection').value || 'municipal',
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
            console.error('保存数据失败:', error);
            alert('保存失败: ' + error.message);
            
            // 确保按钮恢复正常状态
            const saveBtn = document.querySelector('button[onclick="saveForm()"]');
            if (saveBtn.disabled) {
                saveBtn.textContent = '保存数据';
                saveBtn.disabled = false;
            }
        }
    }

    // 添加加载表单数据的函数
    async function loadForm() {
        // 添加检查，如果不存在buildingNo元素，说明不是目标计算器页面，直接返回
        if (!document.getElementById('buildingNo')) {
            console.log('当前页面不是绿色建材计算器页面，跳过loadForm执行');
            return;
        }
        
        try {
            const response = await fetch('/api/load_form');
            if (response.ok) {
                const data = await response.json();
                
                // 填充基本信息
                document.getElementById('buildingNo').value = data.buildingNo || '';
                if (document.getElementById('standardSelection')) {
                    document.getElementById('standardSelection').value = data.standardSelection || 'municipal';
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
            console.error('加载数据失败:', error);
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
    
    // 将需要在外部调用的函数挂载到 window 对象
    window.calculate = calculate;
    window.saveForm = saveForm;
    window.loadForm = loadForm;
    // 将reportData的引用也挂载到window，供导出函数使用（如果导出函数无法作为参数传递）
    window.getCurrentReportData = function() { return reportData; }; 
})(); // 立即执行函数结束
    
    
    

