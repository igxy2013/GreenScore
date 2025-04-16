/**
 * 项目页面专用错误处理
 * 用于处理装饰性构件计算器等项目页面特有功能的错误
 */
(function() {
    // 页面加载完成后初始化
    document.addEventListener('DOMContentLoaded', function() {
        // 检查是否存在必要的DOM元素
        const decorativeCostContainer = document.querySelector('.decorative-cost-calculator-container');
        if (decorativeCostContainer) {
            console.log('装饰性构件计算器页面已加载');
            initDecorationCostErrorHandling();
        }
    });
    
    // 初始化装饰性构件计算器错误处理
    function initDecorationCostErrorHandling() {
        try {
            // 检查必要的元素
            const mainTable = document.getElementById('decorative-cost-table');
            const addRowBtn = document.getElementById('add-row');
            
            if (!mainTable || !addRowBtn) {
                console.error('装饰性构件计算器缺少必要元素');
                if (window.showErrorMessage) {
                    window.showErrorMessage(
                        document.querySelector('.decorative-cost-calculator-container'), 
                        '页面加载不完整，可能影响功能使用。请刷新页面。'
                    );
                }
            }
            
            // 检查是否获取到项目ID
            const projectIdElement = document.getElementById('current-project-id');
            if (projectIdElement && !projectIdElement.value) {
                // 尝试从URL获取项目ID
                const urlParams = new URLSearchParams(window.location.search);
                const projectIdFromUrl = urlParams.get('project_id');
                
                // 从URL路径中提取项目ID - 格式通常是 /project/{project_id}
                let projectIdFromPath = null;
                const pathMatch = window.location.pathname.match(/\/project\/(\d+)/);
                if (pathMatch && pathMatch[1]) {
                    projectIdFromPath = pathMatch[1];
                }
                
                const projectId = projectIdFromUrl || projectIdFromPath;
                
                if (projectId) {
                    projectIdElement.value = projectId;
                    console.log('已从URL获取并设置项目ID:', projectId);
                } else {
                    console.warn('未能获取项目ID，可能影响导出功能');
                }
            }
        } catch (error) {
            console.error('初始化装饰性构件计算器错误处理时出错:', error);
        }
    }
    
    // 添加全局未捕获错误处理（专门针对当前页面）
    if (window.location.pathname.includes('/project/')) {
        window.addEventListener('error', function(event) {
            // 检查是否是decorative_cost_calculator.js的错误
            if (event.filename && event.filename.includes('decorative_cost_calculator.js')) {
                console.error('装饰性构件计算器脚本错误:', event);
                
                const container = document.querySelector('.decorative-cost-calculator-container');
                if (container && window.showErrorMessage) {
                    window.showErrorMessage(container, '计算器加载时发生错误，部分功能可能无法使用。');
                }
            }
        });
    }
})(); 