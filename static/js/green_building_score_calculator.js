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
    // 参数验证
    if (!totalLandArea || totalLandArea <= 0) {
        console.error('总用地面积必须大于0');
        return { score: 0, rating: '无效数据', perCapitaLand: 0 };
    }
    
    if (!residentialUnits || residentialUnits <= 0) {
        console.error('住宅户数必须大于0');
        return { score: 0, rating: '无效数据', perCapitaLand: 0 };
    }
    
    // 计算总人数
    const totalPopulation = residentialUnits * averagePersonPerUnit;
    
    // 计算人均居住用地面积(平方米/人)
    const perCapitaLand = totalLandArea / totalPopulation;
    
    // 标准化气候区划
    const normalizedClimateZone = climateZone.toUpperCase().replace('Ⅰ', 'I').replace('Ⅱ', 'II').replace('Ⅲ', 'III').replace('Ⅳ', 'IV').replace('Ⅴ', 'V').replace('Ⅵ', 'VI');
    
    // 根据评分规则计算得分
    let score = 0;
    let rating = '';
    
    // 根据气候区划和平均层数确定评分标准
    if (['I', 'VI'].includes(normalizedClimateZone)) {
        // I、VI气候区
        if (averageFloors <= 3) {
            if (perCapitaLand <= 33) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 36) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 4 && averageFloors <= 6) {
            if (perCapitaLand <= 29) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 32) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 7 && averageFloors <= 9) {
            if (perCapitaLand <= 21) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 22) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 10 && averageFloors <= 18) {
            if (perCapitaLand <= 17) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 19) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else { // 19层及以上
            if (perCapitaLand <= 12) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 13) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        }
    } else if (['II', 'V'].includes(normalizedClimateZone)) {
        // II、V气候区
        if (averageFloors <= 3) {
            if (perCapitaLand <= 33) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 36) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 4 && averageFloors <= 6) {
            if (perCapitaLand <= 27) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 30) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 7 && averageFloors <= 9) {
            if (perCapitaLand <= 20) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 21) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 10 && averageFloors <= 18) {
            if (perCapitaLand <= 16) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 17) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else { // 19层及以上
            if (perCapitaLand <= 12) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 13) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        }
    } else {
        // III、IV气候区（默认）
        if (averageFloors <= 3) {
            if (perCapitaLand <= 33) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 36) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 4 && averageFloors <= 6) {
            if (perCapitaLand <= 24) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 27) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 7 && averageFloors <= 9) {
            if (perCapitaLand <= 19) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 20) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else if (averageFloors >= 10 && averageFloors <= 18) {
            if (perCapitaLand <= 15) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 16) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        } else { // 19层及以上
            if (perCapitaLand <= 11) {
                score = 20;
                rating = '卓越';
            } else if (perCapitaLand <= 12) {
                score = 15;
                rating = '优秀';
            } else {
                score = 0;
                rating = '不达标';
            }
        }
    }
    
    return {
        score: score,
        rating: rating,
        perCapitaLand: perCapitaLand.toFixed(2)
    };
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
    if (type === '行政办公、商务办公、商业金融、旅馆饭店、交通枢纽等') {
        if (r >= 1.0 && r < 1.5) return 8;
        if (r >= 1.5 && r < 2.5) return 12;
        if (r >= 2.5 && r < 3.5) return 16;
        if (r >= 3.5) return 20;
    }
    
    // 处理第二类建筑（教育、医疗等） 
    if (type === '教育、文化、体育、医疗、卫生、社会福利等') {
        if (r >= 0.5 && r < 0.8) return 8;
        if (r >= 0.8 && r < 1.5) return 16;
        if (r >= 1.5 && r < 2.0) return 20;
        if (r >= 2.0) return 12;  // 注意这个特殊规则：R≥2.0得12分
    }

    return null; // 无效输入时返回null
}



/**
 * 计算建筑密度得分
 * @param {number} buildingDensity - 建筑密度(%)
 * @param {string} buildingType - 建筑类型 (住宅/公共建筑)
 * @returns {Object} 包含得分和评级的对象
 */
function calculateBuildingDensityScore(buildingDensity, buildingType) {
    // 参数验证
    if (buildingDensity === undefined || buildingDensity < 0 || buildingDensity > 100) {
        console.error('建筑密度必须在0-100%之间');
        return { score: 0, rating: '无效数据' };
    }
    
    // 根据建筑类型和评分规则计算得分
    let score = 0;
    let rating = '';
    
    if (buildingType === '住宅') {
        // 住宅建筑密度评分规则
        if (buildingDensity > 30) {
            score = 0;
            rating = '不达标';
        } else if (buildingDensity > 25 && buildingDensity <= 30) {
            score = 8;
            rating = '一般';
        } else if (buildingDensity > 20 && buildingDensity <= 25) {
            score = 12;
            rating = '良好';
        } else if (buildingDensity > 15 && buildingDensity <= 20) {
            score = 16;
            rating = '优秀';
        } else {
            score = 20;
            rating = '卓越';
        }
    } else {
        // 公共建筑密度评分规则
        if (buildingDensity > 40) {
            score = 0;
            rating = '不达标';
        } else if (buildingDensity > 35 && buildingDensity <= 40) {
            score = 8;
            rating = '一般';
        } else if (buildingDensity > 30 && buildingDensity <= 35) {
            score = 12;
            rating = '良好';
        } else if (buildingDensity > 25 && buildingDensity <= 30) {
            score = 16;
            rating = '优秀';
        } else {
            score = 20;
            rating = '卓越';
        }
    }
    
    return {
        score: score,
        rating: rating,
        buildingDensity: buildingDensity.toFixed(2)
    };
}

/**
 * 从项目数据中计算总绿建得分
 * @param {Object} projectData - 项目数据对象
 * @returns {Object} 包含各项得分和总分的对象
 */
function calculateTotalGreenBuildingScore(projectData) {
    // 验证项目数据
    if (!projectData) {
        console.error('项目数据不能为空');
        return { totalScore: 0, details: {} };
    }
    
    // 提取项目数据
    const {
        total_land_area,
        residential_units,
        green_area,
        plot_ratio,
        building_density,
        building_type,
        climate_zone,
        average_floors
    } = projectData;
    
    // 计算各项得分
    const perCapitaLandResult = calculatePerCapitaLandScore(
        total_land_area, 
        residential_units, 
        3.2, // 默认每户平均3.2人
        climate_zone, 
        average_floors
    );
    const greenRatioResult = calculateGreenRatioScore(green_area, total_land_area);
    const plotRatioResult = calculatePlotRatioScore(plot_ratio, building_type);
    const buildingDensityResult = calculateBuildingDensityScore(building_density, building_type);
    
    // 计算总分
    const totalScore = perCapitaLandResult.score + greenRatioResult.score + 
                       plotRatioResult.score + buildingDensityResult.score;
    
    // 返回详细结果
    return {
        totalScore: totalScore,
        details: {
            perCapitaLand: perCapitaLandResult,
            greenRatio: greenRatioResult,
            plotRatio: plotRatioResult,
            buildingDensity: buildingDensityResult
        }
    };
}

// 导出函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        calculatePerCapitaLandScore,
        calculateGreenRatioScore,
        calculatePlotRatioScore,
        calculateBuildingDensityScore,
        calculateTotalGreenBuildingScore
    };
} 