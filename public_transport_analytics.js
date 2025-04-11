            // 获取项目信息
            const projectId = new URLSearchParams(window.location.search).get('project_id');
            const projectInfoResponse = await fetch(`/api/project_info?project_id=${projectId}`);
            const projectInfo = projectInfoResponse.ok ? await projectInfoResponse.json() : {};
            
            console.log("获取到的项目信息:", projectInfo);
            
            // 合并项目信息和结论
            const templateData = {
                ...projectInfo,
                '详细地址': data.address,
                '设计日期': new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' }),
                '结论': conclusion.result6_1_2 + '\n\n' + conclusion.result6_2_1 + '\n\n总得分：' + conclusion.totalScore + '分',
                stations: data.stations.map((station, index) => ({
                    index: index + 1,
                    name: station.name || '未知站点',
                    type: station.type || '公交站',
                    distance: String(station.distance || '0'),
                    detail: station.detail || station.address || station.description || '无详细信息'
                }))
            };
            
            // 准备要发送的数据
            const reportData = {
                address: data.address,
                stations: templateData.stations,
                map_image: mapImageData.split(',')[1], // 移除base64前缀
                conclusion: {
                    result6_1_2: conclusion.result6_1_2,
                    result6_2_1: conclusion.result6_2_1,
                    totalScore: conclusion.totalScore
                },
                // 确保正确传递项目信息 - 采用数据库中的字段格式
                project_info: {
                    projectName: projectInfo.projectName || '',
                    projectCode: projectInfo.projectCode || '',
                    projectLocation: projectInfo.projectLocation || '',
                    constructionUnit: projectInfo.constructionUnit || '',
                    designUnit: projectInfo.designUnit || '',
                    buildingArea: projectInfo.buildingArea || '',
                    buildingType: projectInfo.buildingType || '',
                    buildingHeight: projectInfo.buildingHeight || '',
                    buildingFloors: projectInfo.buildingFloors || '',
                    // 添加额外字段以适配模板中可能的变体
                    项目名称: projectInfo.projectName || '',
                    项目编号: projectInfo.projectCode || '',
                    项目地点: projectInfo.projectLocation || '',
                    建设单位: projectInfo.constructionUnit || '',
                    设计单位: projectInfo.designUnit || '',
                    总建筑面积: projectInfo.buildingArea || '',
                    建筑类型: projectInfo.buildingType || '',
                    建筑高度: projectInfo.buildingHeight || '',
                    建筑层数: projectInfo.buildingFloors || ''
                }
            };
            
            // 记录发送的数据，方便调试
            console.log("发送到后端的数据:", JSON.stringify({
                address: data.address,
                stationsCount: templateData.stations.length,
                conclusion: reportData.conclusion,
                project_info_keys: Object.keys(reportData.project_info),
                project_info_sample: JSON.stringify(reportData.project_info).substring(0, 200) + "..."
            })); 