/**
 * GreenScore系统前端错误处理 - 调试版本
 * 用于捕获和处理资源加载错误
 */

// 立即函数，避免污染全局命名空间
(function() {
    console.log('初始化错误处理模块');
    
    // 全局错误处理 - 简化版
    window.addEventListener('error', function(event) {
        console.log('捕获到全局错误:', event.message);
        
        // 防止错误冒泡
        if (event && typeof event.preventDefault === 'function') {
            event.preventDefault();
        }
        
        return true; // 允许浏览器继续处理错误
    });
    
    // 未捕获的Promise错误 - 简化版
    window.addEventListener('unhandledrejection', function(event) {
        console.log('捕获到未处理的Promise拒绝:', 
            event && event.reason ? event.reason.toString() : '未知原因');
            
        // 防止错误冒泡
        if (event && typeof event.preventDefault === 'function') {
            event.preventDefault();
        }
        
        return true; // 允许浏览器继续处理错误
    });
    
    // 简化版错误消息显示函数
    window.showErrorMessage = function(container, message) {
        console.log('显示错误消息:', message);
        
        if (!container) {
            container = document.body;
        }
        
        var errorDiv = document.createElement('div');
        errorDiv.style.color = 'red';
        errorDiv.style.padding = '10px';
        errorDiv.style.margin = '10px';
        errorDiv.style.border = '1px solid red';
        errorDiv.textContent = message || '发生错误';
        
        container.insertBefore(errorDiv, container.firstChild);
        
        return errorDiv;
    };
    
    console.log('错误处理模块初始化完成');
})(); 