/**
 * GreenScore系统全局错误处理模块
 * 用于捕获、记录和处理前端JavaScript错误
 */

// 全局错误处理器
window.onerror = function(message, source, lineno, colno, error) {
    const errorInfo = {
        type: 'runtime',
        message: message,
        source: source,
        line: lineno,
        column: colno,
        stack: error && error.stack ? error.stack : '未获取到堆栈信息',
        userAgent: navigator.userAgent,
        time: new Date().toISOString()
    };
    
    console.error('捕获到错误:', errorInfo);
    logErrorToServer(errorInfo);
    
    // 显示用户友好的错误信息
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: '系统错误',
            text: '操作过程中发生错误，请刷新页面重试或联系管理员',
            confirmButtonText: '确定'
        });
    }
    
    return true; // 阻止默认错误处理
};

// 未处理的Promise错误
window.addEventListener('unhandledrejection', function(event) {
    const errorInfo = {
        type: 'promise',
        message: event.reason ? (event.reason.message || '未知Promise错误') : '未知Promise错误',
        stack: event.reason && event.reason.stack ? event.reason.stack : '未获取到堆栈信息',
        userAgent: navigator.userAgent,
        time: new Date().toISOString()
    };
    
    console.error('未处理的Promise错误:', errorInfo);
    logErrorToServer(errorInfo);
    
    // 不需要每次都显示给用户，除非是关键操作
    if (event.reason && event.reason.critical && typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: '操作失败',
            text: '请求处理失败，请稍后再试',
            confirmButtonText: '确定'
        });
    }
});

// CDN资源加载失败处理
function handleResourceError() {
    const cdnResources = document.querySelectorAll('script[data-cdn]');
    cdnResources.forEach(resource => {
        resource.onerror = function() {
            const localFallback = resource.getAttribute('data-local-fallback');
            if (localFallback) {
                console.warn(`CDN资源加载失败: ${resource.src}, 正在尝试本地资源: ${localFallback}`);
                resource.src = localFallback;
                
                // 记录资源加载失败
                logErrorToServer({
                    type: 'resource',
                    message: 'CDN资源加载失败',
                    resource: resource.src,
                    fallback: localFallback,
                    userAgent: navigator.userAgent,
                    time: new Date().toISOString()
                });
            }
        };
    });
}

// 初始化资源错误处理
document.addEventListener('DOMContentLoaded', handleResourceError);

// 表单验证错误处理
function handleFormValidationErrors(form, errors) {
    // 清除之前的错误提示
    const previousErrors = form.querySelectorAll('.validation-error');
    previousErrors.forEach(el => el.remove());
    
    // 显示新的错误提示
    for (const field in errors) {
        const inputElement = form.querySelector(`[name="${field}"]`);
        if (inputElement) {
            inputElement.classList.add('is-invalid');
            
            const errorMessage = document.createElement('div');
            errorMessage.className = 'validation-error text-danger';
            errorMessage.textContent = errors[field];
            
            inputElement.parentNode.appendChild(errorMessage);
        }
    }
    
    // 滚动到第一个错误字段
    const firstError = form.querySelector('.is-invalid');
    if (firstError) {
        firstError.focus();
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// 错误日志上报服务器
function logErrorToServer(errorInfo) {
    // 过滤掉不需要上报的错误
    if (shouldIgnoreError(errorInfo)) {
        return;
    }
    
    // 使用Beacon API在页面关闭时也能发送数据
    if (navigator.sendBeacon) {
        const blob = new Blob([JSON.stringify(errorInfo)], { type: 'application/json' });
        navigator.sendBeacon('/api/log-error', blob);
    } else {
        // 降级处理
        fetch('/api/log-error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(errorInfo),
            // 不需要等待响应
            keepalive: true
        }).catch(err => console.error('错误日志上报失败:', err));
    }
}

// 判断是否应该忽略某些错误
function shouldIgnoreError(errorInfo) {
    // 忽略第三方脚本错误
    if (errorInfo.source && (
        errorInfo.source.includes('chrome-extension://') || 
        errorInfo.source.includes('extension://') ||
        errorInfo.source.includes('//localhost:') && location.hostname !== 'localhost'
    )) {
        return true;
    }
    
    // 忽略特定类型的错误消息
    const ignoredMessages = [
        'Script error.',
        'ResizeObserver loop limit exceeded',
        'ResizeObserver loop completed with undelivered notifications'
    ];
    
    if (ignoredMessages.some(msg => errorInfo.message && errorInfo.message.includes(msg))) {
        return true;
    }
    
    return false;
}

// 导出工具函数，供其他模块使用
window.GreenScoreErrorHandler = {
    handleFormValidationErrors: handleFormValidationErrors,
    logCustomError: function(message, data) {
        logErrorToServer({
            type: 'custom',
            message: message,
            data: data,
            userAgent: navigator.userAgent,
            time: new Date().toISOString()
        });
    }
}; 