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

    // 函数：折叠除指定菜单外的所有菜单
    function collapseOtherMenus(exceptMenuId) {
        const allMenuContents = document.querySelectorAll('.menu-content');
        allMenuContents.forEach(menuContent => {
            if (menuContent.id !== exceptMenuId) {
                // 折叠其他菜单
                menuContent.classList.remove('expanded');
                menuContent.style.display = 'none';
                
                // 更新对应的箭头图标
                const otherToggle = document.querySelector(`#${menuContent.id.replace('Content', 'Toggle')}`);
                if (otherToggle) {
                    const arrow = otherToggle.querySelector('.ri-arrow-down-s-line');
                    if (arrow) arrow.style.transform = 'rotate(0deg)';
                }
            }
        });
    }

    // 添加菜单切换事件
    if (basicMenuToggle && basicMenuContent) {
        basicMenuToggle.addEventListener('click', function(e) {
            console.log("基本级菜单被点击");
            e.preventDefault();
            e.stopPropagation();
            
            // 在展开基本级菜单前，先折叠其他菜单
            if (!basicMenuContent.classList.contains('expanded')) {
                collapseOtherMenus('basicMenuContent');
            }
            
            // 切换展开/折叠状态
            basicMenuContent.classList.toggle('expanded');
            
            // 更新箭头图标
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = basicMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 更新菜单样式
            basicMenuContent.style.display = basicMenuContent.classList.contains('expanded') ? 'block' : 'none';
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    if (advancedMenuToggle && advancedMenuContent) {
        advancedMenuToggle.addEventListener('click', function(e) {
            console.log("提高级菜单被点击");
            e.preventDefault();
            e.stopPropagation();
            
            // 在展开提高级菜单前，先折叠其他菜单
            if (!advancedMenuContent.classList.contains('expanded')) {
                collapseOtherMenus('advancedMenuContent');
            }
            
            // 切换展开/折叠状态
            advancedMenuContent.classList.toggle('expanded');
            
            // 更新箭头图标
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = advancedMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 更新菜单样式
            advancedMenuContent.style.display = advancedMenuContent.classList.contains('expanded') ? 'block' : 'none';
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    if (reportMenuToggle && reportMenuContent) {
        reportMenuToggle.addEventListener('click', function(e) {
            console.log("报告菜单被点击");
            e.preventDefault();
            e.stopPropagation();
            
            // 在展开报告菜单前，先折叠其他菜单
            if (!reportMenuContent.classList.contains('expanded')) {
                collapseOtherMenus('reportMenuContent');
            }
            
            // 切换展开/折叠状态
            reportMenuContent.classList.toggle('expanded');
            
            // 更新箭头图标
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = reportMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 更新菜单样式
            reportMenuContent.style.display = reportMenuContent.classList.contains('expanded') ? 'block' : 'none';
            
            // 保存菜单状态
            saveMenuState();
        });
    }
    
    // 专项计算菜单处理
    if (specialCalcMenuToggle && specialCalcMenuContent) {
        console.log('初始化专项计算菜单事件');
        
        specialCalcMenuToggle.addEventListener('click', function(e) {
            // 阻止事件冒泡和默认行为
            e.preventDefault();
            e.stopPropagation();
            
            console.log('专项计算菜单被点击');
            
            // 在展开专项计算菜单前，先折叠其他菜单
            if (!specialCalcMenuContent.classList.contains('expanded')) {
                collapseOtherMenus('specialCalcMenuContent');
            }
            
            // 切换展开/折叠状态
            specialCalcMenuContent.classList.toggle('expanded');
            
            // 更新箭头图标
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = specialCalcMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 更新菜单样式
            specialCalcMenuContent.style.display = specialCalcMenuContent.classList.contains('expanded') ? 'block' : 'none';
            
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
        
        // 确保所有菜单初始都是折叠状态
        collapseOtherMenus("");
        
        // 如果没有保存的状态或恢复失败，根据当前页面设置菜单
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
        } else if (currentPage === 'report_table' && reportMenuContent) {
            // 如果当前页面是报告导出相关页面，展开报告导出菜单
            console.log("展开报告菜单");
            reportMenuContent.classList.add('expanded');
            reportMenuContent.style.display = 'block';
            if (reportMenuToggle) {
                const arrow = reportMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        } else if ((currentPage === 'solar_calculator' || currentPage === 'green_materials' || currentPage === 'public_transport_analysis') && specialCalcMenuContent) {
            // 如果当前页面是专项计算相关页面，展开专项计算菜单
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
            
            // 检查是否有href属性且不是javascript:开头
            const href = this.getAttribute('href');
            if (href && !href.startsWith('javascript:')) {
                // 这是一个导航链接，让它正常工作
                console.log("这是一个导航链接，正常跳转");
                
                // 在导航前调用防止页面跳动的函数
                preventPageJump();
                
                // 保存当前菜单状态
                saveMenuState();
                return;
            }
            
            // 检查是否为报告导出子菜单下的项 - 这些按钮有onclick事件
            if (this.getAttribute('onclick')) {
                console.log("检测到点击有onclick事件的子菜单项");
                
                // 阻止默认行为，让onclick正常执行
                e.preventDefault();
                
                // 保存当前菜单状态
                saveMenuState();
                return;
            }
            
            // 对于其他子菜单项的处理...
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
        
        if (reportMenuContent) {
            // 检查当前是否有报告相关页面（兼容report_table、dwg_export等不同页面）
            if (currentPage === 'report_table' || currentPage === 'dwg_export') {
                console.log("强制展开报告菜单");
                reportMenuContent.classList.add('expanded');
                reportMenuContent.classList.add('keep-open');
                reportMenuContent.style.display = 'block';
                const arrow = reportMenuToggle?.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
            
            // 为报告菜单下的子菜单项保持一致的样式，确保它们不会被隐藏
            const reportSubMenuItems = reportMenuContent.querySelectorAll('.submenu-item');
            reportSubMenuItems.forEach(item => {
                // 保持原有的布局和样式
                item.style.display = 'flex';
                item.style.alignItems = 'center';
                item.style.paddingLeft = '1rem';
                item.style.paddingRight = '1rem';
                item.style.paddingTop = '0.75rem';
                item.style.paddingBottom = '0.75rem';
                console.log("为报告子菜单项添加一致样式:", item.textContent.trim());
            });
        }
        
        if (specialCalcMenuContent && (currentPage === 'solar_calculator' || currentPage === 'green_materials' || currentPage === 'public_transport_analysis')) {
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