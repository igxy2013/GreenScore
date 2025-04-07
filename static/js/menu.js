// 菜单初始化和事件处理
document.addEventListener('DOMContentLoaded', function() {
    console.log("menu.js 开始加载...");
    
    // 获取菜单元素 - 使用let而不是const允许后面重新赋值
    let basicMenuToggle = document.getElementById('basicMenuToggle');
    let basicMenuContent = document.getElementById('basicMenuContent');
    let advancedMenuToggle = document.getElementById('advancedMenuToggle');
    let advancedMenuContent = advancedMenuToggle ? document.getElementById('advancedMenuContent') : null;
    let reportMenuToggle = document.getElementById('reportMenuToggle');
    let reportMenuContent = document.getElementById('reportMenuContent');
    let specialCalcMenuToggle = document.getElementById('specialCalcMenuToggle');
    let specialCalcMenuContent = document.getElementById('specialCalcMenuContent');

    console.log("菜单元素获取状态:", 
                "基本级:", basicMenuToggle ? "找到" : "未找到", 
                "提高级:", advancedMenuToggle ? "找到" : "未找到",
                "报告:", reportMenuToggle ? "找到" : "未找到",
                "专项计算:", specialCalcMenuToggle ? "找到" : "未找到");
    
    // 防止页面跳动的函数
    function preventPageJump() {
        // 记录当前滚动位置
        const scrollPosition = window.scrollY;
        
        // 在下一个事件循环中恢复滚动位置
        setTimeout(() => {
            window.scrollTo(0, scrollPosition);
        }, 0);
    }

    // 获取当前页面信息
    const currentLevel = document.body.getAttribute('data-level') || '';
    const currentPage = document.body.getAttribute('data-page') || '';
    const currentSpecialty = document.body.getAttribute('data-specialty') || '';
    
    console.log("当前页面信息:", "级别:", currentLevel, "页面:", currentPage, "专业:", currentSpecialty);

    // 保存菜单状态到 sessionStorage 的函数
    function saveMenuState() {
        const menuState = {
            basicMenuExpanded: basicMenuContent?.classList.contains('expanded') || false,
            advancedMenuExpanded: advancedMenuContent?.classList.contains('expanded') || false,
            reportMenuExpanded: reportMenuContent?.classList.contains('expanded') || false,
            specialCalcMenuExpanded: specialCalcMenuContent?.classList.contains('expanded') || false,
            currentLevel: currentLevel,
            currentPage: currentPage,
            currentSpecialty: currentSpecialty
        };
        sessionStorage.setItem('menuState', JSON.stringify(menuState));
        console.log("菜单状态已保存:", menuState);
    }

    // 首先移除可能存在的旧事件监听器（通过克隆节点的方式）
    if (basicMenuToggle) {
        const newBasicMenuToggle = basicMenuToggle.cloneNode(true);
        if (basicMenuToggle.parentNode) {
            basicMenuToggle.parentNode.replaceChild(newBasicMenuToggle, basicMenuToggle);
        }
        basicMenuToggle = newBasicMenuToggle;
    }
    
    if (advancedMenuToggle) {
        const newAdvancedMenuToggle = advancedMenuToggle.cloneNode(true);
        if (advancedMenuToggle.parentNode) {
            advancedMenuToggle.parentNode.replaceChild(newAdvancedMenuToggle, advancedMenuToggle);
        }
        advancedMenuToggle = newAdvancedMenuToggle;
    }
    
    if (reportMenuToggle) {
        const newReportMenuToggle = reportMenuToggle.cloneNode(true);
        if (reportMenuToggle.parentNode) {
            reportMenuToggle.parentNode.replaceChild(newReportMenuToggle, reportMenuToggle);
        }
        reportMenuToggle = newReportMenuToggle;
    }
    
    if (specialCalcMenuToggle) {
        const newSpecialCalcMenuToggle = specialCalcMenuToggle.cloneNode(true);
        if (specialCalcMenuToggle.parentNode) {
            specialCalcMenuToggle.parentNode.replaceChild(newSpecialCalcMenuToggle, specialCalcMenuToggle);
        }
        specialCalcMenuToggle = newSpecialCalcMenuToggle;
    }
    
    console.log("已清除旧事件监听器");

    // 添加菜单切换事件
    if (basicMenuToggle && basicMenuContent) {
        basicMenuToggle.addEventListener('click', function(e) {
            console.log("基本级菜单被点击");
            e.stopPropagation();
            basicMenuContent.classList.toggle('expanded');
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = basicMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 确保菜单样式正确
            if (basicMenuContent.classList.contains('expanded')) {
                basicMenuContent.style.display = 'block';
            } else {
                basicMenuContent.style.display = 'none';
            }
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    if (advancedMenuToggle && advancedMenuContent) {
        advancedMenuToggle.addEventListener('click', function(e) {
            console.log("提高级菜单被点击");
            e.stopPropagation();
            advancedMenuContent.classList.toggle('expanded');
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = advancedMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 确保菜单样式正确
            if (advancedMenuContent.classList.contains('expanded')) {
                advancedMenuContent.style.display = 'block';
            } else {
                advancedMenuContent.style.display = 'none';
            }
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    if (reportMenuToggle && reportMenuContent) {
        reportMenuToggle.addEventListener('click', function(e) {
            console.log("报告菜单被点击");
            e.stopPropagation();
            reportMenuContent.classList.toggle('expanded');
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = reportMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 确保菜单样式正确
            if (reportMenuContent.classList.contains('expanded')) {
                reportMenuContent.style.display = 'block';
            } else {
                reportMenuContent.style.display = 'none';
            }
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    // 专项计算菜单处理
    if (specialCalcMenuToggle && specialCalcMenuContent) {
        console.log('初始化专项计算菜单事件');
        
        specialCalcMenuToggle.addEventListener('click', function(e) {
            // 阻止事件冒泡
            e.stopPropagation();
            
            console.log('专项计算菜单被点击');
            
            // 切换expanded类，控制菜单的显示/隐藏
            specialCalcMenuContent.classList.toggle('expanded');
            
            // 旋转箭头图标
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = specialCalcMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 确保菜单样式正确
            if (specialCalcMenuContent.classList.contains('expanded')) {
                specialCalcMenuContent.style.display = 'block';
            } else {
                specialCalcMenuContent.style.display = 'none';
            }
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    // 尝试从 sessionStorage 恢复菜单状态
    function restoreMenuState() {
        try {
            const savedState = sessionStorage.getItem('menuState');
            if (savedState) {
                const menuState = JSON.parse(savedState);
                console.log("尝试恢复菜单状态:", menuState);
                
                // 如果当前页面与保存时的页面类似，则恢复菜单状态
                const isSamePage = (
                    currentLevel === menuState.currentLevel || 
                    currentPage === menuState.currentPage ||
                    (currentLevel && currentLevel === menuState.currentLevel && currentSpecialty === menuState.currentSpecialty)
                );
                
                if (isSamePage) {
                    console.log("当前页面与保存的页面相似，恢复菜单状态");
                    
                    // 恢复基本级菜单状态
                    if (basicMenuContent && menuState.basicMenuExpanded) {
                        basicMenuContent.classList.add('expanded');
                        basicMenuContent.style.display = 'block';
                        const arrow = basicMenuToggle?.querySelector('.ri-arrow-down-s-line');
                        if (arrow) arrow.style.transform = 'rotate(180deg)';
                    }
                    
                    // 恢复提高级菜单状态
                    if (advancedMenuContent && menuState.advancedMenuExpanded) {
                        advancedMenuContent.classList.add('expanded');
                        advancedMenuContent.style.display = 'block';
                        const arrow = advancedMenuToggle?.querySelector('.ri-arrow-down-s-line');
                        if (arrow) arrow.style.transform = 'rotate(180deg)';
                    }
                    
                    // 恢复报告菜单状态
                    if (reportMenuContent && menuState.reportMenuExpanded) {
                        reportMenuContent.classList.add('expanded');
                        reportMenuContent.style.display = 'block';
                        const arrow = reportMenuToggle?.querySelector('.ri-arrow-down-s-line');
                        if (arrow) arrow.style.transform = 'rotate(180deg)';
                    }
                    
                    // 恢复专项计算菜单状态
                    if (specialCalcMenuContent && menuState.specialCalcMenuExpanded) {
                        specialCalcMenuContent.classList.add('expanded');
                        specialCalcMenuContent.style.display = 'block';
                        const arrow = specialCalcMenuToggle?.querySelector('.ri-arrow-down-s-line');
                        if (arrow) arrow.style.transform = 'rotate(180deg)';
                    }
                    
                    return true;
                } else {
                    console.log("当前页面与保存的页面不同，不恢复菜单状态");
                }
            }
        } catch (error) {
            console.error("恢复菜单状态时出错:", error);
        }
        return false;
    }
    
    // 根据当前页面设置初始菜单状态
    function setInitialMenuState() {
        console.log("设置初始菜单状态:", "级别:", currentLevel, "页面:", currentPage);
        
        // 首先尝试恢复保存的菜单状态
        if (restoreMenuState()) {
            console.log("已从保存的状态恢复菜单");
            return;
        }
        
        // 如果没有保存的状态或恢复失败，根据当前页面设置菜单
        // 根据当前页面展开相应菜单
        if (currentLevel === '基本级' && basicMenuContent) {
            console.log("展开基本级菜单");
            basicMenuContent.classList.add('expanded');
            basicMenuContent.style.display = 'block';
            if (basicMenuToggle) {
                const arrow = basicMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        } else if (currentLevel === '提高级' && advancedMenuContent) {
            console.log("展开提高级菜单");
            advancedMenuContent.classList.add('expanded');
            advancedMenuContent.style.display = 'block';
            if (advancedMenuToggle) {
                const arrow = advancedMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        }
        
        // 如果当前页面是报告导出相关页面，展开报告导出菜单
        if (currentPage === 'report_table' && reportMenuContent) {
            console.log("展开报告菜单");
            reportMenuContent.classList.add('expanded');
            reportMenuContent.style.display = 'block';
            if (reportMenuToggle) {
                const arrow = reportMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        }
        
        // 如果当前页面是专项计算相关页面，展开专项计算菜单
        if ((currentPage === 'solar_calculator' || currentPage === 'green_materials') && specialCalcMenuContent) {
            console.log("展开专项计算菜单");
            specialCalcMenuContent.classList.add('expanded');
            specialCalcMenuContent.style.display = 'block';
            if (specialCalcMenuToggle) {
                const arrow = specialCalcMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        }
        
        // 保存设置的菜单状态
        saveMenuState();
    }
    
    // 设置初始菜单状态
    setInitialMenuState();
    
    // 为所有子菜单链接添加点击事件处理
    const allSubmenuItems = document.querySelectorAll('.submenu-item');
    
    allSubmenuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            console.log("子菜单项被点击:", this.textContent.trim());
            
            // 阻止事件冒泡，防止触发父菜单的折叠
            e.stopPropagation();
            
            // 在导航前调用防止页面跳动的函数
            preventPageJump();
            
            // 保存菜单状态到 sessionStorage
            // 获取当前父菜单
            let parentMenuContent = this.closest('.menu-content');
            if (parentMenuContent) {
                console.log("找到父菜单:", parentMenuContent.id);
                
                // 临时强制父菜单保持展开状态
                parentMenuContent.classList.add('expanded');
                parentMenuContent.style.display = 'block';
                
                // 更新箭头图标
                const parentToggle = document.querySelector(`[id$="Toggle"][aria-controls="${parentMenuContent.id}"], #${parentMenuContent.id.replace('Content', 'Toggle')}`);
                if (parentToggle) {
                    const arrow = parentToggle.querySelector('.ri-arrow-down-s-line');
                    if (arrow) arrow.style.transform = 'rotate(180deg)';
                }
            }
            
            // 保存当前菜单状态
            saveMenuState();
            
            // 如果有 href 属性，让链接正常工作
            const href = this.getAttribute('href');
            if (href && !href.startsWith('javascript:') && !e.defaultPrevented) {
                console.log("正在导航到:", href);
            }
        });
    });
    
    // 强制修复菜单展开状态（延迟执行以确保页面完全加载）
    setTimeout(function() {
        console.log("开始检查并修复菜单状态");
        
        // 检查样式并强制修复
        if (basicMenuContent && currentLevel === '基本级') {
            console.log("强制展开基本级菜单");
            basicMenuContent.classList.add('expanded');
            basicMenuContent.style.display = 'block';
            const arrow = basicMenuToggle?.querySelector('.ri-arrow-down-s-line');
            if (arrow) arrow.style.transform = 'rotate(180deg)';
        }
        
        if (advancedMenuContent && currentLevel === '提高级') {
            console.log("强制展开提高级菜单");
            advancedMenuContent.classList.add('expanded');
            advancedMenuContent.style.display = 'block';
            const arrow = advancedMenuToggle?.querySelector('.ri-arrow-down-s-line');
            if (arrow) arrow.style.transform = 'rotate(180deg)';
        }
        
        if (reportMenuContent && currentPage === 'report_table') {
            console.log("强制展开报告菜单");
            reportMenuContent.classList.add('expanded');
            reportMenuContent.style.display = 'block';
            const arrow = reportMenuToggle?.querySelector('.ri-arrow-down-s-line');
            if (arrow) arrow.style.transform = 'rotate(180deg)';
        }
        
        if (specialCalcMenuContent && (currentPage === 'solar_calculator' || currentPage === 'green_materials')) {
            console.log("强制展开专项计算菜单");
            specialCalcMenuContent.classList.add('expanded');
            specialCalcMenuContent.style.display = 'block';
            const arrow = specialCalcMenuToggle?.querySelector('.ri-arrow-down-s-line');
            if (arrow) arrow.style.transform = 'rotate(180deg)';
        }
        
        // 保存强制修复后的菜单状态
        saveMenuState();
        
        console.log("菜单状态修复完成");
    }, 300); // 延迟300ms执行
    
    // 在页面卸载前保存当前菜单状态
    window.addEventListener('beforeunload', function() {
        saveMenuState();
    });
    
    console.log("menu.js加载完成");
}); 