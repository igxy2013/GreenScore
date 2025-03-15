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
 * @returns {Promise} - 返回Promise对象，包含更新结果
 */
function updateDatabaseScore(clauseNumber, score, projectId, isAchieved = '是') {
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
            score: score
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
 * @param {string} [isAchieved] - 可选：是否达标，默认为'true'
 */
function setScore(clauseNumber, score, projectId, isAchieved = 'true') {
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
        score: parseFloat(score)
    };
    
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
 * @param {string} [isAchieved] - 可选：是否达标，默认为'true'
 */
function setMultipleScores(scoresData, projectId, isAchieved = 'true') {
    if (!scoresData || typeof scoresData !== 'object') {
        return;
    }
    
    // 遍历所有条文号和得分
    for (const clauseNumber in scoresData) {
        if (Object.prototype.hasOwnProperty.call(scoresData, clauseNumber)) {
            const score = scoresData[clauseNumber];
            
            // 修改得分
            setScore(clauseNumber, score, projectId, isAchieved);
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
        IF EXISTS (
            SELECT 1 FROM 得分表 
            WHERE 项目ID = ${projectId} 
            AND 条文号 = '${clauseNumber}'
            AND 评价标准 = '${standard}'
        )
        BEGIN
            UPDATE 得分表
            SET 得分 = ${parseFloat(score)}
            WHERE 项目ID = ${projectId}
            AND 条文号 = '${clauseNumber}'
            AND 评价标准 = '${standard}';
        END
        ELSE
        BEGIN
            INSERT INTO 得分表 (
                项目ID, 项目名称, 专业, 评价等级, 条文号, 
                分类, 是否达标, 得分, 技术措施, 评价标准
            )
            VALUES (
                ${projectId}, '项目${projectId}', '建筑专业', '提高级', '${clauseNumber}',
                '资源节约', '是', ${parseFloat(score)}, '', '${standard}'
            );
        END
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
 * @param {boolean} isAchieved - 是否达标，默认为true
 */
function updateScoreWithSQL(clauseNumber, score, projectId, isAchieved = true) {
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
 * @returns {number} 当前项目ID，如果未找到则返回1
 */
function getCurrentProjectId() {
    const projectIdElement = document.getElementById('current-project-id');
    if (projectIdElement) {
        return projectIdElement.value || 1;
    }
    
    // 尝试从URL中获取项目ID
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project_id');
    if (projectId) {
        return projectId;
    }
    
    // 默认返回1
    return 1;
}

/**
 * 获取当前项目标准
 * @returns {string} 当前项目标准，如果未找到则返回'成都市标'
 */
function getCurrentProjectStandard() {
    const standardElement = document.getElementById('current-project-standard');
    if (standardElement) {
        return standardElement.value || '成都市标';
    }
    
    // 尝试从URL中获取标准
    const urlParams = new URLSearchParams(window.location.search);
    const standard = urlParams.get('standard');
    if (standard) {
        return standard;
    }
    
    // 默认返回成都市标
    return '成都市标';
} 