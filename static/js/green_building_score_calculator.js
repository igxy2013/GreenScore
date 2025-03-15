/**
 * 绿色建筑评分计算工具
 * 包含各种计算绿建得分的函数
 */

/**
 * 计算人均居住用地指标得分
 * @param {number} totalLandArea - 总用地面积(平方米)
 * @param {number} residentialUnits - 住宅户数
 * @param {number} averagePersonPerUnit - 每户平均人数，默认为3.2人/户
 * @param {string} climateZone - 建筑气候区划 (I、II、III、IV、V、VI)
 * @param {number} averageFloors - 住宅平均层数
 * @returns {Object} 包含得分和评级的对象
 */
function calculatePerCapitaLandScore(totalLandArea, residentialUnits, averagePersonPerUnit = 3.2, climateZone = 'III', averageFloors = 10) {
    // 如果在其他页面调用此方法，可以通过以下方式：
    // 1. 在HTML中引入此JS文件：<script src="/static/js/green_building_score_calculator.js"></script>
    // 2. 然后直接调用：const result = calculatePerCapitaLandScore(1000, 30, 3.2, 'III', 10);
    // 3. 或者通过window对象调用：window.calculatePerCapitaLandScore(1000, 30);

    // 计算总人数
    const totalPopulation = residentialUnits * averagePersonPerUnit;
    
    // 计算人均居住用地面积(平方米/人)
    const perCapitaLand = totalLandArea / totalPopulation;
    
    // 标准化气候区划
    const normalizedClimateZone = climateZone.toUpperCase().replace('Ⅰ', 'I').replace('Ⅱ', 'II').replace('Ⅲ', 'III').replace('Ⅳ', 'IV').replace('Ⅴ', 'V').replace('Ⅵ', 'VI');
    
    // 根据评分规则计算得分
    let score = 0;
    
    // 根据气候区划和平均层数确定评分标准
    if (['I', 'VII'].includes(normalizedClimateZone)) {
        // I、VI气候区
        if (averageFloors <= 3) {
            if (perCapitaLand <= 33) {
                score = 20;
            } else if (perCapitaLand <= 36) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 4 && averageFloors <= 6) {
            if (perCapitaLand <= 29) {
                score = 20;
            } else if (perCapitaLand <= 32) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 7 && averageFloors <= 9) {
            if (perCapitaLand <= 21) {
                score = 20;
            } else if (perCapitaLand <= 22) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 10 && averageFloors <= 18) {
            if (perCapitaLand <= 17) {
                score = 20;
            } else if (perCapitaLand <= 19) {
                score = 15;
            } else {
                score = 0;
            }
        } else { // 19层及以上
            if (perCapitaLand <= 12) {
                score = 20;
            } else if (perCapitaLand <= 13) {
                score = 15;
            } else {
                score = 0;
            }
        }
    } else if (['II', 'VI'].includes(normalizedClimateZone)) {
        // II、V气候区
        if (averageFloors <= 3) {
            if (perCapitaLand <= 33) {
                score = 20;
            } else if (perCapitaLand <= 36) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 4 && averageFloors <= 6) {
            if (perCapitaLand <= 27) {
                score = 20;
            } else if (perCapitaLand <= 30) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 7 && averageFloors <= 9) {
            if (perCapitaLand <= 20) {
                score = 20;
            } else if (perCapitaLand <= 21) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 10 && averageFloors <= 18) {
            if (perCapitaLand <= 16) {
                score = 20;
            } else if (perCapitaLand <= 17) {
                score = 15;
            } else {
                score = 0;
            }
        } else { // 19层及以上
            if (perCapitaLand <= 12) {
                score = 20;
            } else if (perCapitaLand <= 13) {
                score = 15;
            } else {
                score = 0;
            }
        }
    } else {
        // III、IV、气候区（默认）
        if (averageFloors <= 3) {
            if (perCapitaLand <= 33) {
                score = 20;
            } else if (perCapitaLand <= 36) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 4 && averageFloors <= 6) {
            if (perCapitaLand <= 24) {
                score = 20;
            } else if (perCapitaLand <= 27) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 7 && averageFloors <= 9) {
            if (perCapitaLand <= 19) {
                score = 20;
            } else if (perCapitaLand <= 20) {
                score = 15;
            } else {
                score = 0;
            }
        } else if (averageFloors >= 10 && averageFloors <= 18) {
            if (perCapitaLand <= 15) {
                score = 20;
            } else if (perCapitaLand <= 16) {
                score = 15;
            } else {
                score = 0;
            }
        } else { // 19层及以上
            if (perCapitaLand <= 11) {
                score = 20;
            } else if (perCapitaLand <= 12) {
                score = 15;
            } else {
                score = 0;
            }
        }
    }

    return score;
}


/**
 * 计算绿地率得分
 * @param {number} greenArea - 绿地面积(平方米)
 * @param {number} totalLandArea - 总用地面积(平方米)
 * @returns {Object} 包含得分和评级的对象
 */
function calculateGreenRatioScore(greenArea, totalLandArea) {
    // 参数验证
    if (!greenArea || greenArea <= 0) {
        console.error('绿地面积必须大于0');
        return { score: 0, rating: '无效数据', greenRatio: 0 };
    }
    
    if (!totalLandArea || totalLandArea <= 0) {
        console.error('总用地面积必须大于0');
        return { score: 0, rating: '无效数据', greenRatio: 0 };
    }
    
    // 计算绿地率(%)
    const greenRatio = (greenArea / totalLandArea) * 100;
    
    // 根据评分规则计算得分
    let score = 0;
    let rating = '';
    
    // 评分规则 (这里需要根据实际表格调整)
    if (greenRatio < 30) {
        score = 0;
        rating = '不达标';
    } else if (greenRatio >= 30 && greenRatio < 35) {
        score = 8;
        rating = '一般';
    } else if (greenRatio >= 35 && greenRatio < 40) {
        score = 12;
        rating = '良好';
    } else if (greenRatio >= 40 && greenRatio < 45) {
        score = 16;
        rating = '优秀';
    } else {
        score = 20;
        rating = '卓越';
    }
    
    return {
        score: score,
        rating: rating,
        greenRatio: greenRatio.toFixed(2)
    };
}

/**
 * 计算容积率得分
 * @param {number} r - 容积率
 * @param {string} type - 公共建筑类型 
 */
function calculatePlotRatioScore(r, type) {
    // 处理第一类建筑（行政办公、商务办公等）
    if (['办公', '商业', '金融', '旅馆饭店', '交通枢纽'].includes(type)) {
        if (r >= 1.0 && r < 1.5) return 8;
        if (r >= 1.5 && r < 2.5) return 12;
        if (r >= 2.5 && r < 3.5) return 16;
        if (r >= 3.5) return 20;
    }
    
    // 处理第二类建筑（教育、医疗等） 
    if (['教育', '文化', '体育', '医疗', '卫生', '社会福利'].includes(type)) {
        if (r >= 0.5 && r < 0.8) return 8;
        if (r >= 0.8 && r < 1.5) return 16;
        if (r >= 1.5 && r < 2.0) return 20;
        if (r >= 2.0) return 12;  // 注意这个特殊规则：R≥2.0得12分
    }

    return 0; //    
}


/**
 * 计算地下空间开发利用得分
 * @param {string} buildingType        - 建筑类型 ('住宅建筑'/'公共建筑')
 * @param {number} undergroundArea    - 地下建筑面积
 * @param {number} undergroundFirstFloor - 地下一层建筑面积
 * @param {number} aboveGroundArea     - 地上建筑面积（住宅建筑用）
 * @param {number} totalLandArea       - 总用地面积
 * @returns {number}                   - 得分 0/5/7/12
 */
function calculateUndergroundScore(buildingType, undergroundArea, undergroundFirstFloor, aboveGroundArea, totalLandArea) {
    // 参数有效性校验（所有面积不能为负数）
    if ([undergroundArea, undergroundFirstFloor, aboveGroundArea, totalLandArea].some(v => typeof v !== 'number' || v < 0)) {
        return 0;
    }

    let R1, Rp;
    R1 = undergroundArea / aboveGroundArea;      // 地下/地上比率
    Rp = undergroundFirstFloor / totalLandArea;  // 地下一层/总用地

    if (buildingType === '住宅建筑') {
        // 住宅建筑计算规则
        if (aboveGroundArea === 0) return 0; // 避免除以零
        R1 = undergroundArea / aboveGroundArea;      // 地下/地上比率
        Rp = undergroundFirstFloor / totalLandArea;  // 地下一层/总用地
        
        // 评分逻辑（优先级从高到低）
        if (R1 >= 0.35 && Rp <= 0.6) return 12;  // 同时满足两个条件
        if (R1 >= 0.2) return 7;
        if (R1 >= 0.05) return 5;
        
    } else if (buildingType === '公共建筑') {
        // 公共建筑计算规则
        if (totalLandArea === 0) return 0; // 避免除以零
        R1 = undergroundArea / totalLandArea;       // 地下/总用地比率
        Rp = undergroundFirstFloor / totalLandArea; // 地下一层/总用地
        
        // 评分逻辑（优先级从高到低）
        if (R1 >= 1.0 && Rp <= 0.6) return 12;  // R1≥100%且Rp≤60%
        if (R1 >= 0.7 && Rp <= 0.7) return 7;   // R1≥70%且Rp≤70%
        if (R1 >= 0.5) return 5;
    }

    return 0;
}

/**
 * 计算绿化用地评分的函数
 * @param {string} buildingType - 建筑类型（'住宅' 或 '公共'）
 * @param {number} greenRate - 绿地率（实际绿地率 / 规划绿地率）
 * @param {number} greenArea - 人均集中绿地面积（平方米/人）
 * @param {string} projectType - 项目类型（'新区建设' 或 '旧区改建'）
 * @param {boolean} [isPublicGreenOpen] - 绿地向公众开放（仅适用于公共建筑）
 * @returns {number} 总评分
 */
function calculateGreenScore(buildingType, greenRate, greenArea, projectType, isPublicGreenOpen) {
    let totalScore = 0;

    // 住宅建筑评分
    if (buildingType === '住宅建筑') {
        // 绿地率评分
        if (greenRate >= 1.05) {
            totalScore += 10;
        }

        // 人均集中绿地面积评分
        if (projectType === '新区建设') {
            if (greenArea >= 0.60) {
                totalScore += 6;
            } else if (greenArea >= 0.50) {
                totalScore += 4;
            } else if (greenArea === 0.50) {
                totalScore += 2;
            }
        } else if (projectType === '旧区改建') {
            if (greenArea >= 0.45) {
                totalScore += 6;
            } else if (greenArea >= 0.35) {
                totalScore += 4;
            } else if (greenArea === 0.35) {
                totalScore += 2;
            }
        }
    }

    // 公共建筑评分
    if (buildingType === '公共建筑') {
        // 绿地率评分
        if (greenRate >= 1.05) {
            totalScore += 10;
        }

        // 绿地向公众开放评分
        if (isPublicGreenOpen) {
            totalScore += 6;
        }
    }

    return totalScore;
}


/**
 * 计算停车设施得分
 * @param {string} buildingType - 建筑类型（'住宅' 或 '公共'）
 * @param {number} groundParkingCount - 地面停车位数量（住宅建筑）或地面停车占地面积（公共建筑）
 * @param {number} totalUnits - 住宅总套数（住宅建筑）或总建设用地面积（公共建筑）
 * @returns {number} - 得分（0 或 8）
 */
function calculateParkingScore(buildingType, groundParkingCount, totalUnits) {
    // 参数有效性校验
    if (typeof groundParkingCount !== 'number' || groundParkingCount < 0) return 0;
    if (typeof totalUnits !== 'number' || totalUnits <= 0) return 0;

    // 计算比率
    const ratio = groundParkingCount / totalUnits;

    // 根据建筑类型评分
    if (buildingType === '住宅建筑') {
        if (ratio < 0.10) return 8; // 比率小于 10%，得 8 分
    } else if (buildingType === '公共建筑') {
        if (ratio < 0.08) return 8; // 比率小于 8%，得 8 分
    }

    // 默认返回 0 分
    return 0;
}
