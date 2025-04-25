/**
 * 根据条文号查询得分
 * @param {string} clauseNumber - 条文号
 * @param {number} [projectId] - 可选：项目ID，默认从页面获取或使用1
 * @returns {Promise} - 返回Promise对象，包含查询结果
 */
function getScoreByClauseNumber(clauseNumber, projectId) {
    // 验证参数
    if (!clauseNumber) {
        return Promise.reject(new Error('缺少必要参数：条文号'));
    }
    
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备请求数据
    const requestData = {
        project_id: projectId,
        standard: standard,
        clause_number: clauseNumber
    };
    
    // 发送AJAX请求到后端API
    return fetch('/api/get_score_by_clause', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP错误，状态码: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.message || '查询分值失败');
        }
        
        return {
            success: true,
            clauseNumber: clauseNumber,
            score: data.score,
            category: data.category,
            specialty: data.specialty,
            is_achieved: data.is_achieved
        };
    })
    .catch(error => {
        throw error;
    });
}

/**
 * 简单查询条文得分 - 在控制台显示结果
 * @param {string} clauseNumber - 条文号
 * @param {number} [projectId] - 可选：项目ID
 */
function queryScore(clauseNumber, projectId) {
    getScoreByClauseNumber(clauseNumber, projectId)
        .then(result => {
            // 如果在页面上有显示结果的元素，也可以更新页面
            const resultElement = document.getElementById('query-result');
            if (resultElement) {
                resultElement.innerHTML = `
                    <div class="p-4 bg-green-100 rounded-lg">
                        <h3 class="text-lg font-bold">条文 ${clauseNumber} 的得分信息</h3>
                        <p>得分: <span class="font-bold">${result.score}</span></p>
                        <p>分类: ${result.category}</p>
                        <p>专业: ${result.specialty}</p>
                        <p>是否达标: ${result.is_achieved}</p>
                    </div>
                `;
            }
            
            return result;
        })
        .catch(error => {
            // 如果在页面上有显示结果的元素，也可以更新页面显示错误信息
            const resultElement = document.getElementById('query-result');
            if (resultElement) {
                resultElement.innerHTML = `
                    <div class="p-4 bg-red-100 rounded-lg">
                        <h3 class="text-lg font-bold">查询失败</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        });
}

/**
 * 直接更新数据库中的条文得分 - 增强版，添加更详细的错误处理
 * @param {string} clauseNumber - 条文号
 * @param {number} score - 分值
 * @param {number} [projectId] - 可选：项目ID，默认从页面获取或使用1
 * @param {string} [isAchieved] - 可选：是否达标，默认为'是'
 * @param {string} [technicalMeasures] - 可选：技术措施内容
 * @returns {Promise} - 返回Promise对象，包含更新结果
 */
function updateDatabaseScore(clauseNumber, score, isAchieved = '是', technicalMeasures = '') {
    // 验证参数
    if (!clauseNumber) {
        alert('缺少必要参数：条文号');
        return Promise.reject(new Error('缺少必要参数：条文号'));
    }
    
    if (score === undefined || score === null) {
        alert('缺少必要参数：分值');
        return Promise.reject(new Error('缺少必要参数：分值'));
    }
    
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    console.log("项目ID：",projectId);
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备请求数据 - 只包含必要的字段
    const requestData = {
        project_id: projectId,
        standard: standard,
        clause_number: clauseNumber,
        score: parseFloat(score),
        is_achieved: isAchieved,
        technical_measures: technicalMeasures
    };
    
    // 如果提供了技术措施，则添加到请求数据中
    if (technicalMeasures) {
        requestData.technical_measures = technicalMeasures;
    }
    
    // 发送AJAX请求到后端API
    return fetch('/api/update_score_direct', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                alert(`HTTP错误，状态码: ${response.status}, 内容: ${text}`);
                throw new Error(`HTTP错误，状态码: ${response.status}, 内容: ${text}`);
            });
        }
        
        return response.text().then(text => {
            try {
                return JSON.parse(text);
            } catch (e) {
                if (text.includes('success') || text.includes('成功')) {
                    return { success: true, message: '更新成功' };
                }
                alert(`响应格式错误: ${text}`);
                throw new Error(`响应格式错误: ${text}`);
            }
        });
    })
    .then(data => {
        if (!data.success) {
            const errorMsg = data.message || '修改分值失败';
            alert(errorMsg);
            throw new Error(errorMsg);
        }
        
        // 清除缓存
        try {
            localStorage.removeItem(`scores_提高级_建筑专业_${projectId}_${standard}`);
            localStorage.removeItem(`score_summary_${projectId}_${standard}`);
        } catch (e) {
            // 处理缓存清除失败
        }
        
        return {
            success: true,
            message: '分值修改成功',
            clauseNumber: clauseNumber,
            score: score,
            technicalMeasures: technicalMeasures
        };
    })
    .catch(error => {
        alert(`修改分值出错: ${error.message}`);
        throw error;
    });
}

/**
 * 根据条文号查询得分 - 简化版，直接在控制台输出结果
 * @param {string} clauseNumber - 条文号
 * @param {number} [projectId] - 可选：项目ID
 */
function getScore(clauseNumber, projectId) {
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备请求数据
    const requestData = {
        project_id: projectId,
        standard: standard,
        clause_number: clauseNumber
    };
    
    // 发送AJAX请求到后端API
    fetch('/api/get_score_by_clause', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP错误，状态码: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            return;
        }
        
        return data;
    })
    .catch(error => {
        // 处理查询出错
    });
}

/**
 * 修改条文得分 - 简化版，直接在控制台输出结果
 * @param {string} clauseNumber - 条文号
 * @param {number} score - 分值
 * @param {number} [projectId] - 可选：项目ID
 * @param {string} [isAchieved] - 可选：是否达标，默认为'是'
 * @param {string} [technicalMeasures] - 可选：技术措施内容
 */
function setScore(clauseNumber, score, projectId, isAchieved = '是', technicalMeasures = '') {
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备请求数据 - 只包含必要的字段
    const requestData = {
        project_id: projectId,
        standard: standard,
        clause_number: clauseNumber,
        score: parseFloat(score),
        is_achieved: isAchieved
    };
    
    // 如果提供了技术措施，则添加到请求数据中
    if (technicalMeasures) {
        requestData.technical_measures = technicalMeasures;
    }
    
    // 发送AJAX请求到后端API
    fetch('/api/update_score_direct', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP错误，状态码: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            return;
        }
        
        // 清除缓存
        try {
            localStorage.removeItem(`scores_提高级_建筑专业_${projectId}_${standard}`);
            localStorage.removeItem(`score_summary_${projectId}_${standard}`);
        } catch (e) {
            // 处理缓存清除失败
        }
        
        return data;
    })
    .catch(error => {
        // 处理修改出错
    });
}

/**
 * 批量修改多个条文的得分
 * @param {Object} scoresData - 条文号和得分的键值对，例如：{'3.1.2.14': 12, '4.2.1.5': 8}
 * @param {number} [projectId] - 可选：项目ID
 * @param {string} [isAchieved] - 可选：是否达标，默认为'是'
 * @param {Object} [technicalMeasuresData] - 可选：条文号和技术措施的键值对，例如：{'3.1.2.14': '采用节能设计', '4.2.1.5': '使用环保材料'}
 */
function setMultipleScores(scoresData, projectId, isAchieved = '是', technicalMeasuresData = {}) {
    if (!scoresData || typeof scoresData !== 'object') {
        return;
    }
    
    // 遍历所有条文号和得分
    for (const clauseNumber in scoresData) {
        if (Object.prototype.hasOwnProperty.call(scoresData, clauseNumber)) {
            const score = scoresData[clauseNumber];
            
            // 获取对应的技术措施（如果有）
            const technicalMeasures = technicalMeasuresData[clauseNumber] || '';
            
            // 修改得分
            setScore(clauseNumber, score, projectId, isAchieved, technicalMeasures);
        }
    }
}

/**
 * 使用XMLHttpRequest直接更新条文得分 - 最简单的方法
 * @param {string} clauseNumber - 条文号
 * @param {number} score - 分值
 * @param {number} [projectId] - 可选：项目ID
 */
function updateScoreXHR(clauseNumber, score, projectId) {
    // 验证参数
    if (!clauseNumber) {
        alert('缺少必要参数：条文号');
        return;
    }
    
    if (score === undefined || score === null) {
        alert('缺少必要参数：分值');
        return;
    }
    
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 如果仍然没有项目ID，使用默认值1
    if (!projectId) {
        projectId = 1;
    }
    
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备请求数据 - 只包含必要的字段
    const requestData = {
        project_id: projectId,
        standard: standard,
        clause_number: clauseNumber,
        score: parseFloat(score)
    };
    
    // 创建XMLHttpRequest对象
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/update_score_direct', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    // 设置回调函数
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        alert(`条文 ${clauseNumber} 的得分已成功更新为 ${score}`);
                        
                        // 清除缓存
                        try {
                            localStorage.removeItem(`scores_提高级_建筑专业_${projectId}_${standard}`);
                            localStorage.removeItem(`score_summary_${projectId}_${standard}`);
                        } catch (e) {
                            // 处理缓存清除失败
                        }
                    } else {
                        alert(`更新失败: ${response.message || '未知错误'}`);
                    }
                } catch (e) {
                    if (xhr.responseText.includes('success') || xhr.responseText.includes('成功')) {
                        alert(`条文 ${clauseNumber} 的得分已成功更新为 ${score}`);
                    } else {
                        alert(`解析响应失败: ${e.message}`);
                    }
                }
            } else {
                alert(`HTTP错误，状态码: ${xhr.status}, 响应: ${xhr.responseText}`);
            }
        }
    };
    
    // 发送请求
    xhr.send(JSON.stringify(requestData));
}

/**
 * 使用直接SQL语句更新条文得分 - 最后的解决方案
 * @param {string} clauseNumber - 条文号
 * @param {number} score - 分值
 * @param {number} [projectId] - 可选：项目ID
 */
function updateScoreSQL(clauseNumber, score, projectId) {
    // 验证参数
    if (!clauseNumber) {
        alert('缺少必要参数：条文号');
        return;
    }
    
    if (score === undefined || score === null) {
        alert('缺少必要参数：分值');
        return;
    }
    
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 如果仍然没有项目ID，使用默认值1
    if (!projectId) {
        projectId = 1;
    }
    
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备SQL语句
    const sql = `
        INSERT INTO 得分表 (
            项目ID, 项目名称, 专业, 评价等级, 条文号, 
            分类, 是否达标, 得分, 技术措施, 评价标准
        )
        VALUES (
            ${projectId}, '项目${projectId}', '建筑专业', '提高级', '${clauseNumber}',
            '资源节约', '是', ${parseFloat(score)}, '', '${standard}'
        )
        ON DUPLICATE KEY UPDATE
            得分 = ${parseFloat(score)}
    `;
    
    // 准备请求数据
    const requestData = {
        sql: sql
    };
    
    // 创建XMLHttpRequest对象
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/execute_sql', true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    // 设置回调函数
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status >= 200 && xhr.status < 300) {
                alert(`条文 ${clauseNumber} 的得分已成功更新为 ${score}`);
                
                // 清除缓存
                try {
                    localStorage.removeItem(`scores_提高级_建筑专业_${projectId}_${standard}`);
                    localStorage.removeItem(`score_summary_${projectId}_${standard}`);
                } catch (e) {
                    // 处理缓存清除失败
                }
            } else {
                alert(`SQL执行错误，状态码: ${xhr.status}, 响应: ${xhr.responseText}`);
            }
        }
    };
    
    // 发送请求
    xhr.send(JSON.stringify(requestData));
}

/**
 * 执行SQL语句
 * @param {string} sql - 要执行的SQL语句
 * @param {Array} params - 参数数组（可选）
 * @param {function} callback - 回调函数，参数为(error, results)
 */
function executeSQL(sql, params, callback) {
    // 处理可选参数
    if (typeof params === 'function') {
        callback = params;
        params = [];
    }
    
    if (!sql) {
        alert('缺少必要参数: sql');
        if (callback) callback(new Error('缺少必要参数: sql'), null);
        return;
    }

    // 准备请求数据
    const requestData = {
        sql: sql,
        params: params
    };

    // 发送请求
    fetch('/api/execute_sql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            if (callback) callback(null, data.results);
        } else {
            if (callback) callback(new Error(data.message), null);
        }
    })
    .catch(error => {
        if (callback) callback(error, null);
    });
}

/**
 * 执行SQL语句（Promise版本）
 * @param {string} sql - 要执行的SQL语句
 * @returns {Promise} - 返回Promise对象
 */
function executeSQLPromise(sql) {
    return new Promise((resolve, reject) => {
        executeSQL(sql, [], (error, results) => {
            if (error) {
                reject(error);
            } else {
                resolve(results);
            }
        });
    });
}

/**
 * 使用SQL语句更新条文得分
 * @param {string} clauseNumber - 条文编号
 * @param {number} score - 得分
 * @param {number} projectId - 项目ID，默认为当前项目
 * @param {boolean} isAchieved - 是否达标，默认为达标
 */
function updateScoreWithSQL(clauseNumber, score, projectId, isAchieved = '达标') {
    if (!clauseNumber || score === undefined) {
        alert('缺少必要参数: clauseNumber 或 score');
        return;
    }

    // 获取当前项目ID
    if (!projectId) {
        const projectIdElement = document.getElementById('current-project-id');
        if (projectIdElement) {
            projectId = projectIdElement.value || 1;
        } else {
            projectId = 1;
        }
    }

    // 获取当前标准
    let standard = '成都市标';
    const standardElement = document.getElementById('current-project-standard');
    if (standardElement) {
        standard = standardElement.value || '成都市标';
    }

    // 构建SQL语句和参数
    const checkSql = `SELECT * FROM 得分表 WHERE 项目ID = ? AND 条文号 = ?`;
    const checkParams = [projectId, clauseNumber];
    
    // 先检查记录是否存在
    executeSQL(checkSql, checkParams, (error, results) => {
        if (error) {
            alert(`检查记录失败: ${error.message}`);
            return;
        }

        let sql;
        let params;
        if (results && results.length > 0) {
            // 更新现有记录，只修改得分字段
            sql = `UPDATE 得分表 SET 得分 = ? WHERE 项目ID = ? AND 条文号 = ?`;
            params = [score, projectId, clauseNumber];
        } else {
            // 如果记录不存在，则插入新记录
            sql = `INSERT INTO 得分表 (项目ID, 项目名称, 条文号, 分类, 是否达标, 得分, 技术措施, 评价等级, 专业, 评价标准) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
            params = [
                projectId, 
                '项目' + projectId, 
                clauseNumber, 
                '资源节约', 
                '是', 
                score, 
                '', 
                '提高级', 
                '建筑专业', 
                standard
            ];
        }

        // 执行更新或插入
        executeSQL(sql, params, (error) => {
            if (error) {
                alert(`更新得分失败: ${error.message}`);
                return;
            }

            alert(`条文 ${clauseNumber} 的得分已更新为 ${score}`);

            // 清除缓存
            const cacheKey = `score_${clauseNumber}_${projectId}`;
            if (localStorage.getItem(cacheKey)) {
                localStorage.removeItem(cacheKey);
            }
        });
    });
}

/**
 * 使用SQL语句查询条文得分
 * @param {string} clauseNumber - 条文编号
 * @param {number} projectId - 项目ID，默认为当前项目
 */
function queryScoreWithSQL(clauseNumber, projectId) {
    if (!clauseNumber) {
        alert('缺少必要参数: clauseNumber');
        return;
    }

    // 获取当前项目ID
    if (!projectId) {
        const projectIdElement = document.getElementById('current-project-id');
        if (projectIdElement) {
            projectId = projectIdElement.value || 1;
        } else {
            projectId = 1;
        }
    }

    // 构建SQL语句和参数
    const sql = `SELECT * FROM 得分表 WHERE 项目ID = ? AND 条文号 = ?`;
    const params = [projectId, clauseNumber];
    
    // 执行查询
    executeSQL(sql, params, (error, results) => {
        if (error) {
            alert(`查询得分失败: ${error.message}`);
            return;
        }

        if (results && results.length > 0) {
            const scoreData = results[0];
            alert(`条文 ${clauseNumber} 的得分信息:\n得分: ${scoreData.得分}\n是否达标: ${scoreData.是否达标}\n标准: ${scoreData.评价标准}`);
        } else {
            alert(`未找到条文 ${clauseNumber} 的得分记录`);
        }
    });
}

/**
 * 批量更新条文得分
 * @param {Object} scoresData - 条文得分数据，格式为 {条文编号: 得分, ...}
 * @param {number} projectId - 项目ID，默认为当前项目
 * @param {boolean} isAchieved - 是否达标，默认为true
 * @param {function} callback - 回调函数，参数为(error, results)
 */
function batchUpdateScores(scoresData, projectId, isAchieved = true, callback) {
    if (!scoresData || typeof scoresData !== 'object') {
        alert('缺少必要参数: scoresData 或格式不正确');
        if (callback) callback(new Error('缺少必要参数: scoresData 或格式不正确'), null);
        return;
    }

    // 获取当前项目ID
    if (!projectId) {
        const projectIdElement = document.getElementById('current-project-id');
        if (projectIdElement) {
            projectId = projectIdElement.value || 1;
        } else {
            projectId = 1;
        }
    }

    // 获取当前标准
    let standard = '成都市标';
    const standardElement = document.getElementById('current-project-standard');
    if (standardElement) {
        standard = standardElement.value || '成都市标';
    }

    // 构建批量更新SQL
    const clauseNumbers = Object.keys(scoresData);
    if (clauseNumbers.length === 0) {
        alert('没有要更新的条文得分数据');
        if (callback) callback(new Error('没有要更新的条文得分数据'), null);
        return;
    }

    // 使用事务进行批量更新
    const beginTransactionSQL = 'BEGIN TRANSACTION';
    
    executeSQL(beginTransactionSQL, [], (error) => {
        if (error) {
            alert(`开始事务失败: ${error.message}`);
            if (callback) callback(error, null);
            return;
        }

        // 创建一个Promise数组，用于跟踪所有更新操作
        const updatePromises = clauseNumbers.map(clauseNumber => {
            return new Promise((resolve, reject) => {
                const score = scoresData[clauseNumber];
                
                // 检查记录是否存在
                const checkSql = `SELECT * FROM 得分表 WHERE 项目ID = ? AND 条文号 = ?`;
                const checkParams = [projectId, clauseNumber];
                
                executeSQL(checkSql, checkParams, (error, results) => {
                    if (error) {
                        reject(error);
                        return;
                    }
                    
                    let sql;
                    let params;
                    if (results && results.length > 0) {
                        // 更新现有记录，只修改得分字段
                        sql = `UPDATE 得分表 SET 得分 = ? WHERE 项目ID = ? AND 条文号 = ?`;
                        params = [score, projectId, clauseNumber];
                    } else {
                        // 插入新记录
                        sql = `INSERT INTO 得分表 (项目ID, 项目名称, 条文号, 分类, 是否达标, 得分, 技术措施, 评价等级, 专业, 评价标准) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
                        params = [
                            projectId, 
                            '项目' + projectId, 
                            clauseNumber, 
                            '资源节约', 
                            '是', 
                            score, 
                            '', 
                            '提高级', 
                            '建筑专业', 
                            standard
                        ];
                    }
                    
                    executeSQL(sql, params, (error) => {
                        if (error) {
                            reject(error);
                            return;
                        }
                        
                        // 清除缓存
                        const cacheKey = `score_${clauseNumber}_${projectId}`;
                        if (localStorage.getItem(cacheKey)) {
                            localStorage.removeItem(cacheKey);
                        }
                        
                        resolve();
                    });
                });
            });
        });
        
        // 等待所有更新完成
        Promise.all(updatePromises)
            .then(() => {
                // 提交事务
                const commitTransactionSQL = 'COMMIT TRANSACTION';
                executeSQL(commitTransactionSQL, [], (error) => {
                    if (error) {
                        alert(`提交事务失败: ${error.message}`);
                        
                        // 回滚事务
                        const rollbackTransactionSQL = 'ROLLBACK TRANSACTION';
                        executeSQL(rollbackTransactionSQL, [], () => {
                            if (callback) callback(error, null);
                        });
                        return;
                    }
                    
                    alert(`批量更新完成，共更新 ${clauseNumbers.length} 条记录`);
                    if (callback) callback(null, { updatedCount: clauseNumbers.length });
                });
            })
            .catch(error => {
                alert(`批量更新过程中出错: ${error.message}`);
                
                // 回滚事务
                const rollbackTransactionSQL = 'ROLLBACK TRANSACTION';
                executeSQL(rollbackTransactionSQL, [], () => {
                    if (callback) callback(error, null);
                });
            });
    });
}

/**
 * 批量更新条文得分（Promise版本）
 * @param {Object} scoresData - 条文得分数据，格式为 {条文编号: 得分, ...}
 * @param {number} projectId - 项目ID，默认为当前项目
 * @param {boolean} isAchieved - 是否达标，默认为true
 * @returns {Promise} - 返回Promise对象
 */
function batchUpdateScoresPromise(scoresData, projectId, isAchieved = true) {
    return new Promise((resolve, reject) => {
        batchUpdateScores(scoresData, projectId, isAchieved, (error, results) => {
            if (error) {
                reject(error);
            } else {
                resolve(results);
            }
        });
    });
}

/**
 * 获取当前项目ID
 * @returns {number} 当前项目ID
 */
function getCurrentProjectId() {
    // 尝试从多个可能的位置获取项目ID
    
    // 1. 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    const projectIdFromUrl = urlParams.get('project_id');
    if (projectIdFromUrl) {
        return parseInt(projectIdFromUrl, 10);
    }
    
    // 2. 从隐藏输入字段获取
    const projectIdInput = document.getElementById('project_id');
    if (projectIdInput && projectIdInput.value) {
        return parseInt(projectIdInput.value, 10);
    }
    
    // 3. 从data属性获取
    const projectIdData = document.body.getAttribute('data-project-id');
    if (projectIdData) {
        return parseInt(projectIdData, 10);
    }
    
    // 4. 从localStorage获取
    const projectIdFromStorage = localStorage.getItem('currentProjectId');
    if (projectIdFromStorage) {
        return parseInt(projectIdFromStorage, 10);
    }
    
    // 如果都没有找到，返回null
    console.warn('无法确定当前项目ID');
    return null;
}

/**
 * 获取当前项目评价标准
 * @returns {string} 当前项目评价标准
 */
function getCurrentProjectStandard() {
    // 尝试从多个可能的位置获取项目标准
    
    // 1. 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    const standardFromUrl = urlParams.get('standard');
    if (standardFromUrl) {
        return standardFromUrl;
    }
    
    // 2. 从隐藏输入字段获取
    const standardInput = document.getElementById('current-project-standard');
    if (standardInput && standardInput.value) {
        return standardInput.value;
    }
    
    // 3. 从data属性获取
    const standardData = document.body.getAttribute('data-standard');
    if (standardData) {
        return standardData;
    }
    
    // 4. 从localStorage获取
    const standardFromStorage = localStorage.getItem('currentProjectStandard');
    if (standardFromStorage) {
        return standardFromStorage;
    }
    
    // 默认返回成都市标
    return '成都市标';
}

/**
 * 获取当前专业
 * @returns {string} 当前专业
 */
function getCurrentSpecialty() {
    // 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    const specialty = urlParams.get('specialty');
    if (specialty) {
        return specialty;
    }
    
    // 尝试从页面元素获取
    const specialtyElement = document.getElementById('current-specialty');
    if (specialtyElement) {
        return specialtyElement.value || '建筑';
    }
    
    return '建筑';
}

/**
 * 获取当前评价等级
 * @returns {string} 当前评价等级
 */
function getCurrentLevel() {
    // 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    const level = urlParams.get('level');
    if (level) {
        return level;
    }
    
    // 尝试从页面元素获取
    const levelElement = document.getElementById('current-level');
    if (levelElement) {
        return levelElement.value || '提高级';
    }
    
    return '提高级';
}

/**
 * 处理条文之间的依赖关系
 * @param {string} sourceClauseNumber - 源条文号（触发条件的条文）
 * @param {string} targetClauseNumber - 目标条文号（被影响的条文）
 * @param {string} condition - 条件（如 'score > 0'）
 * @param {string} action - 要执行的操作（如 'set_achieved'）
 * @param {number} projectId - 项目ID，默认为当前项目
 * @returns {Promise} - 返回Promise对象
 */
function handleClauseDependency(sourceClauseNumber, targetClauseNumber, condition, projectId) {
    if (!sourceClauseNumber || !targetClauseNumber || !condition) {
        console.error('处理条文依赖关系时缺少必要参数');
        return Promise.reject(new Error('缺少必要参数'));
    }
    
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 如果仍然没有项目ID，使用默认值
    if (!projectId) {
        const projectIdElement = document.getElementById('project_id');
        if (projectIdElement) {
            projectId = projectIdElement.value;
        } else {
            projectId = 1;
        }
    }
    
    // 日志记录
    console.log(`检查条文依赖: 源条文=${sourceClauseNumber}, 目标条文=${targetClauseNumber}, 条件=${condition}, 项目ID=${projectId}`);
    
    // 获取当前项目标准、专业和评价等级
    const standard = getCurrentProjectStandard() || '成都市标';
    const specialty = getCurrentSpecialty() || '建筑专业';
    const level = getCurrentLevel() || '提高级';
    
    console.log(`当前项目标准: ${standard}, 专业: ${specialty}, 评价等级: ${level}`);
    
    // 首先查询源条文的得分 
    return getScoreByClauseNumber(sourceClauseNumber, projectId)
        .then(sourceResult => {
            console.log(`源条文 ${sourceClauseNumber} 查询结果:`, sourceResult);
            
            // 获取源条文得分
            const sourceScore = parseFloat(sourceResult.score) || 0;
            console.log(`源条文 ${sourceClauseNumber} 得分: ${sourceScore}`);
            
            // 解析条件
            let conditionMet = false;
            if (condition === 'score > 0' && sourceScore > 0) {
                conditionMet = true;
            } else if (condition === 'score = 0' && sourceScore === 0) {
                conditionMet = true;
            } else if (condition.startsWith('score >= ')) {
                const threshold = parseFloat(condition.replace('score >= ', ''));
                conditionMet = sourceScore >= threshold;
            }
            
            console.log(`条件 "${condition}" 是否满足: ${conditionMet}`);
            
            // 如果条件不满足，直接返回
            if (!conditionMet) 
            {
                // 准备请求参数
                const requestData = {
                    project_id: projectId,
                    standard: standard,
                    clause_number: targetClauseNumber,
                    specialty: specialty,
                    level: level,
                    is_achieved: '是',
                    score: '—',
                    technical_measures: `由条文 ${sourceClauseNumber} 自动设置为达标 [${new Date().toLocaleString()}]`
                };
                // 直接发起请求更新
                return fetch('/api/update_score_direct', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                })

            }
            else 
            {
                // 准备请求参数
                const requestData = {
                    project_id: projectId,
                    standard: standard,
                    clause_number: targetClauseNumber,
                    specialty: specialty,
                    level: level,
                    is_achieved: '是',
                    score: '达标',
                };
                // 直接发起请求更新
                return fetch('/api/update_score_direct', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                })
            }
                
        })
        .catch(error => {
            // 如果源条文不存在，这是正常的，不需要抛出错误
            if (error.message && error.message.includes('未找到')) {
                console.log(`源条文 ${sourceClauseNumber} 不存在，跳过处理`);
                return false;
            }
            
            console.error('处理条文依赖关系时出错:', error);
            throw error;
        });
}

/**
 * 处理所有已知的条文依赖关系
 * @param {number} projectId - 项目ID，默认为当前项目
 * @returns {Promise} - 返回Promise对象
 */
function handleAllClauseDependencies(projectId) {
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 声明一个包含所有依赖关系的数组
    const dependencies = [
        {
            source: '3.5.1',
            target: '3.1.4',
            condition: 'score > 0',
        },
        {
            source: '3.3.11',
            target: '3.1.20',
            condition: 'score > 0',
        },
        {
            source: '3.3.14',
            target: '3.1.26',
            condition: 'score > 0',
        },
        {
            source: '3.5.14',
            target: '3.1.30',
            condition: 'score > 0',
        },
        {
            source: '3.1.5',
            target: '3.2.2',
            condition: 'score > 0',
        },
        {
            source: '3.5.8',
            target: '3.3.7',
            condition: 'score > 0',
        },
        {
            source: '3.5.10',
            target: '3.3.8',
            condition: 'score > 0',
        },
        {
            source: '3.5.14',
            target: '3.3.19',
            condition: 'score > 0',
        },
        {
            source: '3.3.6',
            target: '3.5.6',
            condition: 'score > 0',
        },    
        {
            source: '3.7.9',
            target: '3.5.9',
            condition: 'score > 0',
        },    
        {
            source: '3.3.16',
            target: '3.5.11',
            condition: 'score > 0',
        },    
        {
            source: '3.3.17',
            target: '3.5.12',
            condition: 'score > 0',
        },    
        {
            source: '3.7.1',
            target: '3.4.1',
            condition: 'score > 0',
        },    
        {
            source: '3.7.5',
            target: '3.4.2',
            condition: 'score > 0',
        },    
        {
            source: '3.7.8',
            target: '3.4.3',
            condition: 'score > 0',
        },    
        {
            source: '3.5.8',
            target: '3.4.6',
            condition: 'score > 0',
        },    
        {
            source: '3.7.9',
            target: '3.4.7',
            condition: 'score > 0',
        },    
        {
            source: '3.5.10',
            target: '3.4.8',
            condition: 'score > 0',
        },    
        {
            source: '3.3.10',
            target: '3.4.9',
            condition: 'score > 0',
        },    
        {
            source: '3.7.14',
            target: '3.4.10',
            condition: 'score > 0',
        },    
        {
            source: '3.5.14',
            target: '3.4.11',
            condition: 'score > 0',
        },    
        {
            source: '3.5.16',
            target: '3.4.12',
            condition: 'score > 0',
        },    
        {
            source: '3.3.10',
            target: '3.6.2',
            condition: 'score > 0',
        },    
        {
            source: '3.3.11',
            target: '3.6.3',
            condition: 'score > 0',
        },    
        {
            source: '3.3.14',
            target: '3.6.6',
            condition: 'score > 0',
        },    
        {
            source: '3.1.9',
            target: '3.7.6',
            condition: 'score > 0',
        },    
        {
            source: '3.1.10',
            target: '3.7.7',
            condition: 'score > 0',
        },    
        {
            source: '3.6.7',
            target: '3.7.11',
            condition: 'score > 0',
        },    
        {
            source: '3.6.8',
            target: '3.7.13',
            condition: 'score > 0',
        }
        // 可以在这里添加更多的依赖关系
    ];
    
    // 处理所有依赖关系
    const promises = dependencies.map(dep => {
        return handleClauseDependency(
            dep.source, 
            dep.target, 
            dep.condition, 
            projectId
        );
    });
    
    return Promise.all(promises);
}

/**
 * 更新条文的技术措施
 * @param {string} clauseNumber - 条文号
 * @param {string} technicalMeasures - 技术措施内容
 * @param {number} [projectId] - 可选：项目ID
 * @returns {Promise} - 返回Promise对象，包含更新结果
 */
function setTechnicalMeasure(clauseNumber, technicalMeasures, projectId) {
    // 验证参数
    if (!clauseNumber) {
        console.error('缺少必要参数：条文号');
        return Promise.reject(new Error('缺少必要参数：条文号'));
    }
    
    if (!technicalMeasures) {
        console.error('缺少必要参数：技术措施');
        return Promise.reject(new Error('缺少必要参数：技术措施'));
    }
    
    // 获取当前项目ID
    if (!projectId) {
        projectId = getCurrentProjectId();
    }
    
    // 获取当前项目标准
    const standard = getCurrentProjectStandard() || '成都市标';
    
    // 准备请求数据
    const requestData = {
        project_id: projectId,
        standard: standard,
        clause_number: clauseNumber,
        technical_measures: technicalMeasures
    };
    
    // 发送AJAX请求到后端API
    return fetch('/api/update_technical_measure', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`HTTP错误，状态码: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.message || '更新技术措施失败');
        }
        
        return {
            success: true,
            message: '技术措施更新成功',
            clauseNumber: clauseNumber
        };
    })
    .catch(error => {
        console.error(`更新技术措施出错: ${error.message}`);
        throw error;
    });
}