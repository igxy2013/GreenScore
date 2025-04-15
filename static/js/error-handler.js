/**
 * GreenScore系统前端错误处理
 * 用于捕获和处理资源加载错误，尝试本地加载并提交错误日志
 */

(function() {
    // 全局错误处理
    window.addEventListener('error', function(event) {
        // 检查是否是资源加载错误
        if (event.target && (event.target.tagName === 'SCRIPT' || event.target.tagName === 'LINK')) {
            handleResourceError(event);
            return;
        }
        
        // 常规JS错误处理
        logError({
            type: 'javascript',
            message: event.message,
            url: event.filename,
            line: event.lineno,
            column: event.colno,
            stack: event.error ? event.error.stack : null
        });
    }, true); // 捕获阶段处理，确保能捕获资源加载错误
    
    // Promise未处理的拒绝
    window.addEventListener('unhandledrejection', function(event) {
        logError({
            type: 'promise',
            message: event.reason ? (event.reason.message || String(event.reason)) : 'Promise rejected',
            stack: event.reason && event.reason.stack
        });
    });
    
    // 资源加载错误处理
    function handleResourceError(event) {
        const target = event.target;
        const url = target.src || target.href;
        
        // 检查CDN资源
        if (url && url.includes('cdn.jsdelivr.net')) {
            console.warn(`CDN资源加载失败: ${url}，尝试使用本地资源`);
            
            // 替换为本地资源
            if (url.includes('alpine')) {
                replaceResource(target, '/static/js/libs/alpine.min.js');
            } else if (url.includes('chart.js')) {
                replaceResource(target, '/static/js/libs/chart.min.js');
            } else if (url.includes('iframe-resizer.js')) {
                replaceResource(target, '/static/js/libs/iframe-resizer.js');
            }
            
            // 记录错误
            logError({
                type: 'resource',
                message: `资源加载失败: ${target.tagName}`,
                url: url,
                element: target.outerHTML
            });
            
            // 阻止事件冒泡
            event.preventDefault();
            return false;
        }
    }
    
    // 替换资源
    function replaceResource(element, newUrl) {
        if (element.tagName === 'SCRIPT') {
            const newScript = document.createElement('script');
            newScript.src = newUrl;
            
            // 复制原始属性
            Array.from(element.attributes).forEach(attr => {
                if (attr.name !== 'src') {
                    newScript.setAttribute(attr.name, attr.value);
                }
            });
            
            // 替换原始脚本
            element.parentNode.replaceChild(newScript, element);
        } else if (element.tagName === 'LINK' && element.rel === 'stylesheet') {
            const newLink = document.createElement('link');
            newLink.href = newUrl;
            newLink.rel = 'stylesheet';
            
            // 复制原始属性
            Array.from(element.attributes).forEach(attr => {
                if (attr.name !== 'href') {
                    newLink.setAttribute(attr.name, attr.value);
                }
            });
            
            // 替换原始链接
            element.parentNode.replaceChild(newLink, element);
        }
    }
    
    // 记录错误到服务器
    function logError(errorData) {
        // 添加页面信息
        errorData.page = window.location.href;
        errorData.timestamp = new Date().toISOString();
        
        // 发送错误数据
        fetch('/log-js-error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(errorData),
            // 使用keepalive确保页面卸载时也能发送请求
            keepalive: true
        }).catch(err => {
            console.error('Error logging failed:', err);
        });
        
        // 打印到控制台以便调试
        console.error('GreenScore错误:', errorData);
    }
    
    // 初始化消息
    console.log('GreenScore错误处理已初始化');
})(); 