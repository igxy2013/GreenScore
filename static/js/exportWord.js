async function exportWord() {
    try {
        // 数据校验
        if (!reportData.totalScore) throw new Error('请先计算数据！');
        
        // 从页面获取子项名称和评价依据
        const buildingNo = document.getElementById('buildingNo').value || '';
        const selectedValue = document.getElementById('standardSelection').value || 'municipal';
        
        // 从数据库获取项目信息
        const projectInfoResponse = await fetch('/api/project_info');
        if (!projectInfoResponse.ok) {
            console.warn('获取项目信息失败，将使用默认值');
        }
        const projectInfo = projectInfoResponse.ok ? await projectInfoResponse.json() : {};
        
        // 直接从静态目录获取模板文件
        const response = await fetch('/static/绿色建材应用比例计算书.docx');
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
            '{{项目名称}}': projectInfo.projectName || '绿色建材应用比例计算',
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
