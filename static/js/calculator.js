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
        // loadForm();
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
            
            // 获取项目ID
            const projectId = DOM.projectId ? DOM.projectId.value : '';
            if (!projectId) {
                throw new Error('未找到项目ID，请确保在项目环境中操作');
            }
            
            // 收集所有表单数据
            const formData = {
                buildingNo: DOM.buildingNo ? DOM.buildingNo.value || '' : '',
                standardSelection: DOM.standardSelection ? DOM.standardSelection.value || 'municipal' : 'municipal',
                project_id: projectId, // 获取当前项目ID
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

            // 发送保存请求
            console.log(`正在保存项目ID ${projectId} 的表单数据...`);
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
                const data = await response.json();
                // alert(data.message || '数据保存成功！');
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
            const formData = data.formData || data;
            
            if (formData && Object.keys(formData).length > 0) {
                console.log('开始填充表单数据');
                
                // 遍历所有类别
                Object.entries(formData).forEach(([categoryKey, items]) => {
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
                    items.forEach((item, index) => {
                        if (index >= allSubItems.length) {
                            console.warn(`项索引超出范围: ${index}, 类别: ${categoryKey}`);
                            return;
                        }
                        
                        const subItem = allSubItems[index];
                        const checkbox = subItem.querySelector('input[type="checkbox"]');
                        const input = subItem.querySelector('input[type="number"]');
                        
                        if (checkbox && item && ('checked' in item)) {
                            checkbox.checked = item.checked === true || item.checked === 'true';
                            
                            // 触发change事件更新样式
                            const event = new Event('change');
                            checkbox.dispatchEvent(event);
                        }
                        
                        if (input && item && ('value' in item || 'actual' in item)) {
                            // 兼容不同字段名
                            input.value = item.value || item.actual || '0';
                        }
                    });
                });
                
                console.log('表单数据填充完成');
            } else {
                console.warn('没有可用的表单数据');
            }
        } catch (error) {
            console.error('加载表单数据时出错:', error);
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
    
    // 导出Word功能 - 异步函数
    async function exportWord() {
        try {
            // 获取计算结果数据
            const reportData = window.getCurrentReportData ? window.getCurrentReportData() : null;
            
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
            saveAs(resultBlob, `绿色建材应用比例计算书.docx`);
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
    
    // 将需要在外部调用的函数挂载到 window 对象
    window.calculate = calculate;
    window.saveForm = saveForm;
    window.loadForm = loadForm;
    window.exportToWordSimple = exportToWordSimple;
    window.exportWord = exportWord;
    // 将reportData的引用也挂载到window，供导出函数使用
    window.getCurrentReportData = function() { return reportData; }; 
})();






