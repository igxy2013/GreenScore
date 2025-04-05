/**
 * iframe高度自适应脚本
 * 用于父页面接收iframe发送的高度信息并调整iframe高度
 */

// 检查是否已经加载
if (typeof window.iframeResizerInitialized === 'undefined') {
    // 防抖函数，限制更新频率
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // 存储上次高度，避免频繁更新
    window.iframeLastHeights = {};

    // 防抖处理iframe高度调整
    const updateIframeHeight = debounce(function(iframe, height) {
        // 设置合理的最小和最大高度限制
        const minHeight = 500; // 最小高度
        const maxHeight = 10000; // 最大高度

        // 确保高度在合理范围内
        let newHeight = Math.max(minHeight, height);
        newHeight = Math.min(maxHeight, newHeight);
        
        // 只有当高度差异超过5px时才更新，减少不必要的重绘
        const iframeId = iframe.id || 'unknown';
        if (!window.iframeLastHeights[iframeId] || Math.abs(window.iframeLastHeights[iframeId] - newHeight) > 5) {
            iframe.style.height = newHeight + 'px';
            window.iframeLastHeights[iframeId] = newHeight;
            console.log('调整iframe高度为:', newHeight);
        }
    }, 50); // 50毫秒防抖时间

    // 监听来自iframe的消息
    window.addEventListener('message', function(e) {
        try {
            // 接收子页面发送的消息
            if (e.data && e.data.type === 'resize') {
                // 查找所有iframe
                const iframes = document.querySelectorAll('iframe');
                for (let i = 0; i < iframes.length; i++) {
                    // 检查是否为发送消息的iframe
                    if (iframes[i].contentWindow === e.source) {
                        // 如果是初始高度设置，直接应用而不考虑防抖和阈值
                        if (e.data.initial === true) {
                            const initialHeight = Math.max(500, Math.min(10000, e.data.height));
                            iframes[i].style.height = initialHeight + 'px';
                            console.log('设置iframe初始高度:', initialHeight);
                            
                            // 更新lastHeights对象
                            const iframeId = iframes[i].id || 'unknown';
                            window.iframeLastHeights[iframeId] = initialHeight;
                        } else {
                            // 否则使用防抖处理
                            updateIframeHeight(iframes[i], e.data.height);
                        }
                        break;
                    }
                }
            }
        } catch (err) {
            console.error('处理iframe高度调整消息时出错:', err);
        }
    });

    // 初始化函数
    function initIframeResizer() {
        console.log('iframe高度自适应脚本已加载');
        
        // 获取页面中所有iframe
        const iframes = document.querySelectorAll('iframe');
        
        // 为每个iframe设置初始样式
        for (let i = 0; i < iframes.length; i++) {
            iframes[i].style.width = '100%';
            iframes[i].style.border = 'none';
            iframes[i].style.overflow = 'hidden';
            // 设置初始高度
            if (!iframes[i].style.height) {
                iframes[i].style.height = '800px'; // 默认高度
            }
        }
    }

    // 在页面加载完成后初始化
    if (document.readyState === 'complete') {
        initIframeResizer();
    } else {
        window.addEventListener('load', initIframeResizer);
    }

    // 标记脚本已初始化
    window.iframeResizerInitialized = true;
    console.log('iframe-resizer.js 初始化完成');
} else {
    console.log('iframe-resizer.js 已经加载，跳过重复初始化');
} 