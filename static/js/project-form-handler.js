/**
 * 项目表单处理脚本
 * 用于处理项目基本信息和详细信息表单的提交和数据保存
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取保存信息按钮
    const saveProjectInfoBtn = document.getElementById('saveProjectInfoBtn');
    
    // 如果按钮存在，添加点击事件处理
    if (saveProjectInfoBtn) {
        saveProjectInfoBtn.addEventListener('click', function(e) {
            // 阻止表单默认提交行为
            e.preventDefault();
            
            // 保存详细信息表格中的数据到临时存储
            const detailInputs = document.querySelectorAll('input[form="projectDetailForm"]');
            const detailSelects = document.querySelectorAll('select[form="projectDetailForm"]');
            const tempData = {};
            
            // 保存输入框的值
            detailInputs.forEach(input => {
                tempData[input.id] = input.value;
            });
            
            // 保存下拉框的值
            detailSelects.forEach(select => {
                tempData[select.id] = select.value;
            });
            
            // 将临时数据存储到localStorage
            localStorage.setItem('projectDetailTempData', JSON.stringify(tempData));
            
            // 提交基本信息表单 - 使用更通用的选择器
            saveProjectInfoBtn.closest('form').submit();
        });
    }
    
    // 页面加载时，恢复之前保存的详细信息数据
    const restoreDetailData = function() {
        const tempDataStr = localStorage.getItem('projectDetailTempData');
        if (tempDataStr) {
            try {
                const tempData = JSON.parse(tempDataStr);
                
                // 恢复输入框的值
                const detailInputs = document.querySelectorAll('input[form="projectDetailForm"]');
                detailInputs.forEach(input => {
                    if (tempData[input.id]) {
                        input.value = tempData[input.id];
                    }
                });
                
                // 恢复下拉框的值
                const detailSelects = document.querySelectorAll('select[form="projectDetailForm"]');
                detailSelects.forEach(select => {
                    if (tempData[select.id]) {
                        select.value = tempData[select.id];
                    }
                });
                
                // 清除临时数据
                localStorage.removeItem('projectDetailTempData');
            } catch (e) {
                console.error('恢复详细信息数据失败:', e);
            }
        }
    };
    
    // 页面加载完成后恢复数据
    setTimeout(restoreDetailData, 500);
}); 