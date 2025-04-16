/**
 * GreenScore系统前端错误处理
 * 用于捕获和处理资源加载错误，尝试本地加载并提交错误日志
 */

(function() {
    // 全局错误处理
    window.addEventListener('error', function(event) {
        console.error('JS错误被捕获:', event.error);
        
        // 记录错误到控制台
        const errorDetails = {
            message: event.message || '未知错误',
            file: event.filename,
            line: event.lineno,
            column: event.colno,
            stack: event.error ? event.error.stack : null,
            timestamp: new Date().toISOString(),
            page: window.location.href
        };
        
        console.error('错误详情:', errorDetails);
        
        // 可选：向后端报告错误
        // reportErrorToBackend(errorDetails);
        
        // 防止错误冒泡
        event.preventDefault();
    });
    
    // 未捕获的Promise错误
    window.addEventListener('unhandledrejection', function(event) {
        console.error('未处理的Promise拒绝:', event.reason);
        
        // 防止错误冒泡
        event.preventDefault();
    });
    
    // 向后端报告错误的函数
    function reportErrorToBackend(errorDetails) {
        try {
            fetch('/api/log_js_error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(errorDetails)
            }).catch(err => {
                console.error('无法发送错误报告:', err);
            });
        } catch (e) {
            console.error('发送错误报告时出错:', e);
        }
    }
    
    // 显示错误消息的辅助函数
    window.showErrorMessage = function(container, message) {
        if (!container) {
            // 尝试找到一个合适的容器
            container = document.querySelector('.main-content') || 
                      document.querySelector('main') || 
                      document.body;
        }
        
        const errorMsg = document.createElement('div');
        errorMsg.className = 'alert alert-danger js-error-message';
        errorMsg.style.padding = '10px';
        errorMsg.style.margin = '10px 0';
        errorMsg.style.backgroundColor = '#f8d7da';
        errorMsg.style.color = '#721c24';
        errorMsg.style.borderRadius = '4px';
        errorMsg.style.border = '1px solid #f5c6cb';
        errorMsg.textContent = message || '页面加载时发生错误，请刷新页面或联系管理员。';
        
        // 添加到容器顶部
        if (container.firstChild) {
            container.insertBefore(errorMsg, container.firstChild);
        } else {
            container.appendChild(errorMsg);
        }
        
        return errorMsg;
    };
})(); 