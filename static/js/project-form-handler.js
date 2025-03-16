/**
 * 项目表单处理脚本
 * 用于处理项目信息表单的提交和数据保存
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取保存信息按钮
    const saveProjectInfoBtn = document.getElementById('saveProjectInfoBtn');
    
    // 如果按钮存在，添加点击事件处理
    if (saveProjectInfoBtn) {
        saveProjectInfoBtn.addEventListener('click', function(e) {
            // 不再需要阻止表单默认提交行为，因为所有字段都在同一个表单中
            // e.preventDefault();
            
            // 不再需要单独保存详细信息，因为所有字段都在同一个表单中
            // 直接提交表单即可
            console.log('提交项目信息表单');
        });
    }
    
    // 不再需要恢复详细信息数据，因为所有字段都在同一个表单中
    // 清除可能存在的旧数据
    localStorage.removeItem('projectDetailTempData');
}); 