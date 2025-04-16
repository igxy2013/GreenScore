/**
 * 导出加载提示窗口组件
 * 提供在文档导出过程中显示加载状态的标准化组件
 * 可在多个页面复用，支持计时器、超时保护和自定义标题
 */

// 使用立即执行函数避免全局命名空间污染
(function() {
    // 如果已经存在ExportLoadingModal，就不再重复定义
    if (typeof window.ExportLoadingModal !== 'undefined') {
        console.log('ExportLoadingModal已存在，跳过重复定义');
        return;
    }
    
    // 私有变量
    let currentTimerId = null;
    let currentSafetyTimeoutId = null;
    
    // 默认配置
    const defaultConfig = {
        title: '正在生成文档',
        description: '请耐心等待，文档生成需要一点时间...',
        showTimer: true,
        showBackdrop: false,
        autoTimeout: 30000, // 自动关闭时间，默认30秒
        footerText: '您的文件即将准备就绪'
    };
    
    // 组件的CSS样式
    const styleRules = `
        #exportLoading {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 9999;
            pointer-events: all;
        }
        #exportLoading .backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(5px);
            z-index: 9999;
            display: none;
        }
        #exportLoading .content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(to right, #e6f1ff, #d1e5ff);
            border: 3px solid #3b82f6;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            width: 90%;
            max-width: 400px;
            text-align: center;
            z-index: 10000;
        }
        #exportLoading .spinner {
            display: inline-block;
            width: 50px;
            height: 50px;
            border: 4px solid rgba(59, 130, 246, 0.3);
            border-radius: 50%;
            border-top-color: #3b82f6;
            animation: spinner 1s linear infinite;
            margin-bottom: 16px;
        }
        #exportLoading .title {
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        #exportLoading .desc {
            font-size: 14px;
            color: #555;
            margin-bottom: 16px;
        }
        #exportLoading .progress-bar {
            width: 100%;
            height: 6px;
            background-color: #e5e7eb;
            border-radius: 9999px;
            overflow: hidden;
            margin-bottom: 12px;
        }
        #exportLoading .progress-value {
            height: 100%;
            width: 0%;
            background-color: #3b82f6;
            border-radius: 9999px;
            animation: progress 1.5s ease-in-out infinite;
        }
        @keyframes spinner {
            to {transform: rotate(360deg);}
        }
        @keyframes progress {
            0% { width: 0%; margin-left: 0%; }
            50% { width: 70%; margin-left: 15%; }
            100% { width: 0%; margin-left: 100%; }
        }
    `;
    
    /**
     * 显示导出加载窗口
     * @param {Object} options - 配置选项
     * @param {string} options.title - 窗口标题
     * @param {string} options.description - 描述文本
     * @param {boolean} options.showTimer - 是否显示计时器
     * @param {boolean} options.showBackdrop - 是否显示背景遮罩
     * @param {number} options.autoTimeout - 超时自动关闭时间(毫秒)
     * @param {string} options.footerText - 底部文本
     * @returns {HTMLElement} - 创建的加载窗口元素
     */
    function show(options = {}) {
        // 合并默认配置和用户配置
        const config = { ...defaultConfig, ...options };
        
        // 先清理可能存在的旧加载框
        hide();
        
        // 创建加载窗口
        const loadingElem = document.createElement('div');
        loadingElem.id = 'exportLoading';
        
        // 构建HTML内容
        let html = `<style>${styleRules}</style>`;
        
        // 根据配置决定是否显示背景遮罩
        html += `<div class="backdrop" style="${config.showBackdrop ? 'display:block;' : ''}"></div>`;
        
        // 主要内容区域
        html += `
            <div class="content">
                <div class="spinner"></div>
                <div class="title">${config.title}</div>
                <div class="desc">${config.description}</div>
                <div class="progress-bar">
                    <div class="progress-value"></div>
                </div>
        `;
        
        // 添加计时器或底部文本
        if (config.showTimer) {
            html += `<div id="export-timer" style="font-size: 12px; color: #666;">已等待: 0秒</div>`;
        } else if (config.footerText) {
            html += `<div style="font-size: 12px; color: #666;">${config.footerText}</div>`;
        }
        
        html += `</div>`;
        loadingElem.innerHTML = html;
        
        document.body.appendChild(loadingElem);
        
        // 如果需要计时器，启动计时
        if (config.showTimer) {
            let seconds = 0;
            const timerElem = document.getElementById('export-timer');
            currentTimerId = setInterval(() => {
                seconds++;
                if (timerElem) {
                    timerElem.textContent = `已等待: ${seconds}秒`;
                }
            }, 1000);
            
            // 存储计时器ID以便后续清除
            loadingElem.dataset.timerId = currentTimerId;
        }
        
        // 如果设置了自动超时，添加超时保护
        if (config.autoTimeout > 0) {
            currentSafetyTimeoutId = setTimeout(() => {
                console.warn('导出操作超时保护触发，强制关闭加载提示');
                hide();
            }, config.autoTimeout);
        }
        
        return loadingElem;
    }
    
    /**
     * 隐藏并移除导出加载窗口
     */
    function hide() {
        const loading = document.getElementById('exportLoading');
        if (loading) {
            // 清除计时器
            const timerId = loading.dataset.timerId;
            if (timerId) {
                clearInterval(parseInt(timerId));
            }
            
            // 清除全局存储的计时器ID
            if (currentTimerId) {
                clearInterval(currentTimerId);
                currentTimerId = null;
            }
            
            // 清除安全超时
            if (currentSafetyTimeoutId) {
                clearTimeout(currentSafetyTimeoutId);
                currentSafetyTimeoutId = null;
            }
            
            // 使用动画淡出效果
            loading.style.opacity = '1';
            loading.style.transition = 'opacity 0.3s ease';
            loading.style.opacity = '0';
            
            // 等待动画完成后移除元素
            setTimeout(() => {
                if (loading && loading.parentNode) {
                    loading.parentNode.removeChild(loading);
                }
            }, 300);
        }
    }
    
    // 公开API - 将ExportLoadingModal暴露为全局对象
    window.ExportLoadingModal = {
        show,
        hide
    };
    
    // 输出调试信息
    console.log('ExportLoadingModal组件已成功初始化');
})();

// 如果在Node.js环境中，导出模块
if (typeof module !== 'undefined' && module.exports && typeof window !== 'undefined') {
    module.exports = window.ExportLoadingModal;
} 