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

/**
 * iFrameResize - iframe-resizer的主函数
 * @param {Object} options - 配置选项
 * @param {String|Element} target - 目标iframe元素或选择器
 * @returns {Array} iframe元素数组
 */
function iFrameResize(options, target) {
    // 默认配置
    const defaultOptions = {
        log: false,
        heightCalculationMethod: 'bodyOffset',
        checkOrigin: false,
        autoResize: true,
        minHeight: 500,
        scrolling: false,
        resizeFrom: 'parent'
    };
    
    // 合并选项
    const settings = {...defaultOptions, ...options};
    
    // 目标元素
    let targetElements = [];
    
    // 根据选择器或元素获取目标
    if (typeof target === 'string') {
        targetElements = [...document.querySelectorAll(target)];
    } else if (target instanceof HTMLElement) {
        targetElements = [target];
    } else if (target instanceof Array) {
        targetElements = target;
    }
    
    console.log('iFrameResize: 找到', targetElements.length, '个iframe元素');
    
    // 对每个iframe应用设置
    targetElements.forEach(iframe => {
        if (!(iframe instanceof HTMLIFrameElement)) {
            console.error('iFrameResize: 目标不是iframe元素');
            return;
        }
        
        // 设置基础样式
        iframe.style.width = '100%';
        iframe.style.border = 'none';
        
        // 设置滚动属性
        if (settings.scrolling === false) {
            iframe.scrolling = 'no';
            iframe.style.overflow = 'hidden';
        } else {
            iframe.scrolling = 'auto';
            iframe.style.overflow = 'auto';
        }
        
        // 设置最小高度
        if (settings.minHeight) {
            iframe.style.minHeight = settings.minHeight + 'px';
        }

        // 监听iframe加载完成
        iframe.addEventListener('load', function() {
            // 延时确保iframe内容完全加载
            setTimeout(() => {
                try {
                    // 获取iframe内容高度
                    let height = 800; // 默认高度
                    
                    if (iframe.contentWindow && iframe.contentWindow.document && iframe.contentWindow.document.body) {
                        if (settings.heightCalculationMethod === 'max') {
                            // 使用最大值计算高度
                            const body = iframe.contentWindow.document.body;
                            const html = iframe.contentWindow.document.documentElement;
                            
                            height = Math.max(
                                body.scrollHeight, html.scrollHeight,
                                body.offsetHeight, html.offsetHeight,
                                body.clientHeight, html.clientHeight
                            );
                        } else {
                            // 默认使用body的offsetHeight
                            height = iframe.contentWindow.document.body.offsetHeight;
                        }
                    }
                    
                    // 应用最小高度
                    height = Math.max(settings.minHeight, height);
                    
                    // 设置iframe高度
                    iframe.style.height = height + 'px';
                    
                    if (settings.log) {
                        console.log('iFrameResize: 设置iframe高度为', height, 'px');
                    }
                    
                    // 如果启用了自动调整大小，添加MutationObserver监控内容变化
                    if (settings.autoResize && iframe.contentWindow) {
                        try {
                            // 创建MutationObserver监控内容变化
                            const observer = new MutationObserver(debounce(() => {
                                // 重新计算并设置高度
                                if (iframe.contentWindow && iframe.contentWindow.document && iframe.contentWindow.document.body) {
                                    let newHeight = iframe.contentWindow.document.body.offsetHeight;
                                    
                                    if (settings.heightCalculationMethod === 'max') {
                                        const body = iframe.contentWindow.document.body;
                                        const html = iframe.contentWindow.document.documentElement;
                                        
                                        newHeight = Math.max(
                                            body.scrollHeight, html.scrollHeight,
                                            body.offsetHeight, html.offsetHeight,
                                            body.clientHeight, html.clientHeight
                                        );
                                    }
                                    
                                    // 应用最小高度
                                    newHeight = Math.max(settings.minHeight, newHeight);
                                    
                                    // 设置iframe高度
                                    iframe.style.height = newHeight + 'px';
                                    
                                    if (settings.log) {
                                        console.log('iFrameResize: 更新iframe高度为', newHeight, 'px');
                                    }
                                }
                            }, 100));
                            
                            // 监控iframe内容变化
                            observer.observe(iframe.contentWindow.document.body, {
                                childList: true,
                                subtree: true,
                                attributes: true,
                                characterData: true
                            });
                        } catch (error) {
                            console.error('iFrameResize: 无法设置内容监控', error);
                        }
                    }
                } catch (error) {
                    console.error('iFrameResize: 设置iframe高度时出错', error);
                }
            }, 100);
        });
    });
    
    return targetElements;
}

// 将iFrameResize添加到全局作用域
window.iFrameResize = iFrameResize; 