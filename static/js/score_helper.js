/**
 * score_helper.js - 评分辅助功能
 * 此文件包含处理评分相关的辅助函数，特别是修复可能缺失隐藏字段的问题
 */

// 页面加载时检查并添加必要的隐藏字段
document.addEventListener('DOMContentLoaded', function() {
    // 检查并添加级别和专业隐藏字段
    ensureHiddenFields();
});

// 确保页面包含必要的隐藏字段
function ensureHiddenFields() {
    // 检查level字段
    if (!document.querySelector('.current_level')) {
        addHiddenField('current_level', getLevelFromPage());
    }
    
    // 检查specialty字段
    if (!document.querySelector('.current_specialty')) {
        addHiddenField('current_specialty', getSpecialtyFromPage());
    }
    
    // 记录已添加字段
    console.log('已确保页面包含必要的隐藏字段:', {
        level: document.querySelector('.current_level')?.value,
        specialty: document.querySelector('.current_specialty')?.value
    });
}

// 添加隐藏字段到页面
function addHiddenField(className, value) {
    const hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.className = className;
    hiddenField.value = value || '';
    document.body.appendChild(hiddenField);
    console.log(`添加隐藏字段: ${className} = ${value}`);
}

// 从页面各种线索获取level值
function getLevelFromPage() {
    // 1. 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    let level = urlParams.get('level') || '';
    
    // 2. 从URL路径获取
    if (!level) {
        const pathParts = window.location.pathname.split('/');
        for (let i = 0; i < pathParts.length; i++) {
            if (['基本级', '提高级'].includes(pathParts[i])) {
                level = pathParts[i];
                break;
            }
        }
    }
    
    // 3. 从页面标题或内容推断
    if (!level) {
        // 检查是否有选择或评分输入框来判断级别
        if (document.querySelector('select.is-achieved-select') || document.querySelector('select[name="is_achieved"]')) {
            level = '基本级';
        } else if (document.querySelector('input[name="score"]') || document.querySelector('input[type="number"]')) {
            level = '提高级';
        }
    }
    
    // 4. 设置默认值
    return level || '基本级';
}

// 从页面各种线索获取specialty值
function getSpecialtyFromPage() {
    // 1. 从URL参数获取
    const urlParams = new URLSearchParams(window.location.search);
    let specialty = urlParams.get('specialty') || '';
    
    // 2. 从URL路径获取
    if (!specialty) {
        const pathParts = window.location.pathname.split('/');
        for (let i = 0; i < pathParts.length; i++) {
            if (['建筑', '结构', '给排水', '电气', '暖通', '景观', '环境健康与节能'].includes(pathParts[i])) {
                specialty = pathParts[i];
                break;
            }
        }
    }
    
    // 3. 从页面标题或内容推断
    if (!specialty) {
        const pageTitle = document.querySelector('h1, h2, h3')?.textContent || '';
        if (pageTitle.includes('建筑')) specialty = '建筑';
        else if (pageTitle.includes('结构')) specialty = '结构';
        else if (pageTitle.includes('给排水')) specialty = '给排水';
        else if (pageTitle.includes('电气')) specialty = '电气';
        else if (pageTitle.includes('暖通')) specialty = '暖通';
        else if (pageTitle.includes('景观')) specialty = '景观';
        else if (pageTitle.includes('环境健康与节能')) specialty = '环境健康与节能';
    }
    
    // 4. 设置默认值
    return specialty || '建筑';
} 