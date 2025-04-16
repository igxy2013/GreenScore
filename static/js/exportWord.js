async function exportWord() {
    try {
        // 数据校验
        if (!reportData.totalScore) throw new Error('请先计算数据！');
        
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
        
        // 5. 尝试从父窗口获取 (iframe情况)
        if (!projectId && window.parent && window.parent !== window) {
            try {
                // 从父窗口URL参数获取
                const parentUrl = new URL(window.parent.location.href);
                const parentProjectId = parentUrl.searchParams.get('project_id');
                if (parentProjectId) {
                    projectId = parentProjectId;
                    console.log("从父窗口URL参数获取项目ID:", projectId);
                } 
                // 从父窗口全局变量获取
                else if (window.parent.currentProjectId) {
                    projectId = window.parent.currentProjectId;
                    console.log("从父窗口全局变量获取项目ID:", projectId);
                }
                
                // 从父窗口路径获取
                if (!projectId) {
                    const parentPathMatch = window.parent.location.pathname.match(/\/project\/(\d+)/);
                    if (parentPathMatch && parentPathMatch[1]) {
                        projectId = parentPathMatch[1];
                        console.log("从父窗口URL路径获取项目ID:", projectId);
                    }
                }
                
                // 从父窗口DOM元素获取
                if (!projectId) {
                    try {
                        const parentProjectIdElement = window.parent.document.getElementById('current-project-id');
                        if (parentProjectIdElement && parentProjectIdElement.value) {
                            projectId = parentProjectIdElement.value;
                            console.log("从父窗口DOM元素获取项目ID:", projectId);
                        }
                    } catch (e) {
                        console.warn("跨域限制，无法直接访问父窗口DOM");
                    }
                }
            } catch (e) {
                console.error("尝试从父窗口获取项目ID失败:", e);
            }
        }
        
        // 6. 如果仍未找到项目ID，尝试通过消息通信获取
        if (!projectId && window.parent && window.parent !== window) {
            console.log("尝试通过消息通信从父页面获取项目ID...");
            try {
                // 创建一个Promise来处理异步消息
                const parentMessagePromise = new Promise((resolve, reject) => {
                    // 设置超时
                    const timeout = setTimeout(() => {
                        window.removeEventListener('message', messageHandler);
                        reject(new Error("从父页面获取项目ID超时"));
                    }, 3000);
                    
                    // 消息处理函数
                    function messageHandler(event) {
                        if (event.data && event.data.type === 'PROJECT_ID_RESPONSE') {
                            clearTimeout(timeout);
                            window.removeEventListener('message', messageHandler);
                            resolve(event.data.projectId);
                        }
                    }
                    
                    // 添加消息监听
                    window.addEventListener('message', messageHandler);
                    
                    // 向父页面发送请求
                    window.parent.postMessage({type: 'REQUEST_PROJECT_ID'}, '*');
                });
                
                // 等待父页面响应，最多3秒
                projectId = await parentMessagePromise.catch(err => {
                    console.warn(err.message);
                    return null;
                });
                
                if (projectId) {
                    console.log("通过消息通信获取到项目ID:", projectId);
                }
            } catch (err) {
                console.error("消息通信获取项目ID失败:", err);
            }
        }
        
        // 检查是否获取到项目ID
        if (!projectId) {
            alert("未能获取到项目ID，无法导出计算书！请确保在项目详情页中操作，或者页面正确传递了项目参数。");
            console.error("无法获取项目ID，导出失败");
            return;
        }
        
        console.log("最终使用的项目ID:", projectId);
        
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
                try {
                    const errorText = await projectInfoResponse.text();
                    console.error("错误详情:", errorText);
                } catch (e) {
                    console.error("无法获取错误详情:", e);
                }
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
        Object.keys(reportData.categories).forEach(categoryKey => {
            const category = reportData.categories[categoryKey];
            if (category.items) {
                category.items.forEach((item, index) => {
                    replacements[`{{${categoryKey}_item${index + 1}}}`] = item.checked ? item.actual.toFixed(1) + '%' : '——';
                });
            }
        });

        // 替换所有占位符
        xml = xml.replace(/{{(.*?)}}/g, (match, p1) => replacements[match] || '');

        // 保存文件
        zip.file('word/document.xml', xml);
        const resultBlob = await zip.generateAsync({ type: 'blob' });
        saveAs(resultBlob, `绿色建材应用比例计算书.docx`);
    } catch (error) {
        alert(`导出失败: ${error.message}`);
        console.error('导出Word错误详情:', error);
    }
}

// 添加父页面消息监听器 - 用于响应父页面的PROJECT_ID
window.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'PROJECT_ID_RESPONSE') {
        console.log("收到父页面发送的项目ID:", event.data.projectId);
    }
});
