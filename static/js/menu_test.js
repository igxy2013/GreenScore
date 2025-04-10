/**
 * 菜单功能测试脚本
 * 用于验证菜单展开/折叠功能是否正常
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("菜单测试脚本加载...");
    
    // 等待主菜单脚本加载完成后再执行测试
    setTimeout(function() {
        // 获取菜单元素
        const basicMenuToggle = document.getElementById('basicMenuToggle');
        const basicMenuContent = document.getElementById('basicMenuContent');
        const advancedMenuToggle = document.getElementById('advancedMenuToggle');
        const advancedMenuContent = document.getElementById('advancedMenuContent');
        const reportMenuToggle = document.getElementById('reportMenuToggle');
        const reportMenuContent = document.getElementById('reportMenuContent');
        const specialCalcMenuToggle = document.getElementById('specialCalcMenuToggle');
        const specialCalcMenuContent = document.getElementById('specialCalcMenuContent');
        
        if (!basicMenuToggle || !basicMenuContent) {
            console.error("基本级菜单元素缺失");
            return;
        }
        
        // 记录菜单初始状态
        console.log("菜单初始状态:");
        console.log("- 基本级菜单: " + (basicMenuContent.classList.contains('expanded') ? "展开" : "折叠"));
        if (advancedMenuContent) {
            console.log("- 提高级菜单: " + (advancedMenuContent.classList.contains('expanded') ? "展开" : "折叠"));
        }
        if (reportMenuContent) {
            console.log("- 报告菜单: " + (reportMenuContent.classList.contains('expanded') ? "展开" : "折叠"));
        }
        if (specialCalcMenuContent) {
            console.log("- 专项计算菜单: " + (specialCalcMenuContent.classList.contains('expanded') ? "展开" : "折叠"));
        }
        
        // 测试菜单样式是否与状态一致
        function checkMenuStyle(menuContent, menuName) {
            const isExpanded = menuContent.classList.contains('expanded');
            const displayStyle = window.getComputedStyle(menuContent).display;
            const isVisuallyExpanded = displayStyle !== 'none';
            
            if (isExpanded !== isVisuallyExpanded) {
                console.error(`${menuName}菜单样式与状态不一致: expanded=${isExpanded}, display=${displayStyle}`);
            } else {
                console.log(`${menuName}菜单样式与状态一致`);
            }
        }
        
        // 检查所有菜单的样式
        checkMenuStyle(basicMenuContent, '基本级');
        if (advancedMenuContent) checkMenuStyle(advancedMenuContent, '提高级');
        if (reportMenuContent) checkMenuStyle(reportMenuContent, '报告');
        if (specialCalcMenuContent) checkMenuStyle(specialCalcMenuContent, '专项计算');
        
        // 模拟点击测试
        console.log("\n开始菜单点击测试...");
        
        // 为子菜单项添加点击测试
        const submenuItems = document.querySelectorAll('.submenu-item');
        if (submenuItems.length > 0) {
            console.log(`找到 ${submenuItems.length} 个子菜单项`);
            
            // 针对前5个子菜单项添加点击测试标记
            for (let i = 0; i < Math.min(5, submenuItems.length); i++) {
                const item = submenuItems[i];
                item.addEventListener('click', function(e) {
                    if (!e.isTrusted) return; // 忽略模拟点击
                    
                    console.log(`子菜单项 "${this.textContent.trim()}" 被点击`);
                    // 确认父菜单保持展开状态
                    const parentMenu = this.closest('.menu-content');
                    if (parentMenu) {
                        console.log(`父菜单 ${parentMenu.id} 状态: ${parentMenu.classList.contains('expanded') ? '展开' : '折叠'}`);
                        console.log(`父菜单 ${parentMenu.id} 显示样式: ${window.getComputedStyle(parentMenu).display}`);
                    }
                });
            }
        }
        
        // 检查报告菜单项的进度条效果
        function testProgressBar() {
            // 获取报告菜单项
            const wordMenuItem = document.querySelector('a[onclick="generateWord()"]');
            const dwgMenuItem = document.querySelector('a[onclick="generateDWG()"]');
            const reportMenuItem = document.querySelector('a[onclick="generateSelfAssessmentReport(); return false;"]');
            
            if (wordMenuItem) {
                console.log("检测到报审表菜单项，验证进度条动画样式...");
                console.log("- background-image支持: " + (CSS.supports('background-image', 'linear-gradient(to right, rgba(0,0,0,0.1), transparent)') ? "是" : "否"));
                
                // 测试添加loading类和背景
                wordMenuItem.classList.add('loading');
                wordMenuItem.style.backgroundImage = 'linear-gradient(to right, rgba(79, 209, 197, 0.3) 50%, transparent 50%)';
                
                console.log("- 报审表菜单项测试背景样式已添加");
                
                // 5秒后移除测试样式
                setTimeout(() => {
                    wordMenuItem.classList.remove('loading');
                    wordMenuItem.style.backgroundImage = '';
                    console.log("- 报审表菜单项测试背景样式已移除");
                }, 5000);
            }
            
            if (dwgMenuItem) {
                console.log("检测到绿色建筑设计专篇菜单项");
            }
            
            if (reportMenuItem) {
                console.log("检测到绿建自评估报告菜单项");
            }
        }
        
        // 执行进度条测试
        setTimeout(testProgressBar, 2000);
        
        console.log("菜单测试初始化完成");
    }, 500); // 延迟500ms执行，确保主菜单脚本已加载完成
}); 