// 菜单初始化和事件处理
document.addEventListener('DOMContentLoaded', function() {
    console.log("menu.js 开始加载...");
    
    // 添加专门用于处理菜单抖动的CSS
    const style = document.createElement('style');
    style.textContent = `
        /* 防止页面加载过程中的菜单抖动 */
        body {
            scroll-behavior: smooth;
        }
        
        /* 固定菜单图标尺寸 */
        .submenu-item i, .menu-item i {
            width: 1.5rem !important;
            height: 1.5rem !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            position: relative !important;
            transform: translateZ(0) !important;
            will-change: transform;
        }
        
        /* 确保菜单项宽度固定 */
        .submenu-item, .menu-item {
            position: relative;
            transform: translateZ(0);
            backface-visibility: hidden;
            -webkit-font-smoothing: antialiased;
        }
        
        /* 在页面跳转前保持菜单可见 */
        .menu-content.expanded {
            display: block !important;
            height: auto !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        /* 为加载新页面添加预加载遮罩，可以平滑过渡 */
        body::after {
            content: "";
            position: fixed;
            pointer-events: none;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: transparent;
            z-index: -1;
            transition: background 0.2s ease;
        }
        
        body.navigating::after {
            background: rgba(255, 255, 255, 0.3);
            z-index: 9998;
        }
    `;
    document.head.appendChild(style);
    
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
    
    // 防止页面跳动的函数 - 修改此函数，仅保存当前点击的子菜单所属父菜单状态
    function preventPageJump(currentMenuId) {
        // 记录当前滚动位置
        const scrollPosition = window.scrollY;
        
        // 设置导航状态，添加遮罩
        document.body.classList.add('navigating');
        
        // 清除所有菜单的保存状态
        clearAllMenuStates();
        
        // 只保存当前菜单的状态
        if (currentMenuId) {
            localStorage.setItem(`menu_expanded_${currentMenuId}`, 'true');
            console.log(`仅保存菜单状态: ${currentMenuId}`);
        }
        
        // 在下一个事件循环中恢复滚动位置
        setTimeout(() => {
            window.scrollTo(0, scrollPosition);
        }, 10);
    }

    // 清除所有菜单状态的函数
    function clearAllMenuStates() {
        console.log("清除所有菜单展开状态");
        // 清除所有菜单状态
        localStorage.removeItem(`menu_expanded_basicMenuContent`);
        localStorage.removeItem(`menu_expanded_advancedMenuContent`);
        localStorage.removeItem(`menu_expanded_reportMenuContent`);
        localStorage.removeItem(`menu_expanded_specialCalcMenuContent`);
    }

    // 获取当前页面信息
    const currentLevel = document.body.getAttribute('data-level') || '';
    const currentPage = document.body.getAttribute('data-page') || '';
    const currentSpecialty = document.body.getAttribute('data-specialty') || '';
    
    console.log("当前页面信息:", "级别:", currentLevel, "页面:", currentPage, "专业:", currentSpecialty);

    // 保存菜单状态到 localStorage (不用sessionStorage，确保跨页面保持)
    function saveMenuState(specificMenuId = null) {
        if (specificMenuId) {
            // 如果指定了特定菜单ID，则只保存该菜单的状态
            clearAllMenuStates();
            localStorage.setItem(`menu_expanded_${specificMenuId}`, 'true');
            console.log(`仅保存指定菜单状态: ${specificMenuId}`);
        } else {
            // 否则保存全局菜单状态对象（用于手动点击菜单时）
        const menuState = {
            basicMenuExpanded: basicMenuContent?.classList.contains('expanded') || false,
            advancedMenuExpanded: advancedMenuContent?.classList.contains('expanded') || false,
            reportMenuExpanded: reportMenuContent?.classList.contains('expanded') || false,
            specialCalcMenuExpanded: specialCalcMenuContent?.classList.contains('expanded') || false,
            currentLevel: currentLevel,
            currentPage: currentPage,
            currentSpecialty: currentSpecialty
        };
            localStorage.setItem('menuState', JSON.stringify(menuState));
            console.log("全局菜单状态已保存:", menuState);
        }
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
            
            // 保存菜单状态 - 用户手动点击切换
            saveMenuState();
            
            // 如果展开了此菜单，则在localStorage中保存其展开状态
            if (basicMenuContent.classList.contains('expanded')) {
                clearAllMenuStates();
                localStorage.setItem(`menu_expanded_basicMenuContent`, 'true');
            } else {
                localStorage.removeItem(`menu_expanded_basicMenuContent`);
            }
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
            
            // 保存菜单状态 - 用户手动点击切换
            saveMenuState();
            
            // 如果展开了此菜单，则在localStorage中保存其展开状态
            if (advancedMenuContent.classList.contains('expanded')) {
                clearAllMenuStates();
                localStorage.setItem(`menu_expanded_advancedMenuContent`, 'true');
            } else {
                localStorage.removeItem(`menu_expanded_advancedMenuContent`);
            }
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
            
            // 保存菜单状态 - 用户手动点击切换
            saveMenuState();
            
            // 如果展开了此菜单，则在localStorage中保存其展开状态
            if (reportMenuContent.classList.contains('expanded')) {
                clearAllMenuStates();
                localStorage.setItem(`menu_expanded_reportMenuContent`, 'true');
            } else {
                localStorage.removeItem(`menu_expanded_reportMenuContent`);
            }
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
            
            // 保存菜单状态 - 用户手动点击切换
            saveMenuState();
            
            // 如果展开了此菜单，则在localStorage中保存其展开状态
            if (specialCalcMenuContent.classList.contains('expanded')) {
                clearAllMenuStates();
                localStorage.setItem(`menu_expanded_specialCalcMenuContent`, 'true');
                } else {
                localStorage.removeItem(`menu_expanded_specialCalcMenuContent`);
            }
        });
    }
    
    // 为所有子菜单链接添加点击事件处理
    const allSubmenuItems = document.querySelectorAll('.submenu-item');
    
    allSubmenuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            console.log("子菜单项被点击:", this.textContent.trim());
            
            // 阻止事件冒泡，防止触发父菜单的折叠
            e.stopPropagation();
            
            // 获取父菜单内容元素
            const parentMenu = this.closest('.menu-content');
            if (!parentMenu) {
                console.log("未找到父级菜单");
                return true;
            }
            
            // 检查是否有href属性且不是javascript:开头
            const href = this.getAttribute('href');
            if (href && !href.startsWith('javascript:')) {
                // 这是一个导航链接，让它正常工作
                console.log("这是一个导航链接，正常跳转");
                
                // 获取菜单项的层级和专业信息
                const menuLevel = this.getAttribute('data-level') || 
                                  (parentMenu.id.includes('basic') ? '基本级' : 
                                   parentMenu.id.includes('advanced') ? '提高级' : '');
                
                const menuSpecialty = this.getAttribute('data-specialty') || '';
                
                // 保存当前选中的菜单信息，用于页面加载后自动加载数据
                if (menuLevel && menuSpecialty) {
                    console.log(`保存菜单信息: 级别=${menuLevel}, 专业=${menuSpecialty}`);
                    localStorage.setItem('selectedMenuLevel', menuLevel);
                    localStorage.setItem('selectedMenuSpecialty', menuSpecialty);
                }
                
                // 清除所有菜单状态，仅保存当前父菜单
                clearAllMenuStates();
                localStorage.setItem(`menu_expanded_${parentMenu.id}`, 'true');
                console.log(`仅保存父菜单状态: ${parentMenu.id}`);
                
                // 在导航前调用防止页面跳动的函数，传入当前父菜单ID
                preventPageJump(parentMenu.id);
                
                // 不阻止默认跳转
                return true;
            }
            
            // 检查是否为报告导出子菜单下的项 - 这些按钮有onclick事件
            if (this.getAttribute('onclick')) {
                console.log("检测到点击有onclick事件的子菜单项");
                
                // 阻止默认行为，让onclick正常执行
                e.preventDefault();
                
                // 保存当前菜单状态，仅保存当前父菜单
                if (parentMenu) {
                    clearAllMenuStates();
                    localStorage.setItem(`menu_expanded_${parentMenu.id}`, 'true');
                }
                return;
            }
            
            // 对于其他子菜单项的处理...
        });
    });
    
    // 页面加载时，根据之前保存的状态恢复菜单
    function restoreMenusOnPageLoad() {
        console.log("恢复菜单状态...");
        
        // 检查是否有菜单展开状态
        let hasExpandedMenu = false;
        
        // 首先折叠所有菜单
        const allMenus = document.querySelectorAll('.menu-content');
        allMenus.forEach(menu => {
            menu.classList.remove('expanded');
            menu.style.display = 'none';
            
            // 重置所有箭头
            const toggleId = menu.id.replace('Content', 'Toggle');
            const toggle = document.getElementById(toggleId);
            if (toggle) {
                const arrow = toggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(0deg)';
            }
        });
        
        // 恢复各个菜单内容区域
        const menuContents = document.querySelectorAll('.menu-content');
        menuContents.forEach(menu => {
            const isExpanded = localStorage.getItem(`menu_expanded_${menu.id}`) === 'true';
            if (isExpanded) {
                hasExpandedMenu = true;
                menu.classList.add('expanded');
                menu.style.display = 'block';
                
                // 更新对应菜单按钮的箭头
                const toggleId = menu.id.replace('Content', 'Toggle');
                const toggle = document.getElementById(toggleId);
                if (toggle) {
                    const arrow = toggle.querySelector('.ri-arrow-down-s-line');
                    if (arrow) arrow.style.transform = 'rotate(180deg)';
                }
            }
        });
        
        // 如果没有展开的菜单，检查URL参数是否有指定菜单
        if (!hasExpandedMenu) {
            const urlParams = new URLSearchParams(window.location.search);
            const menuParam = urlParams.get('menu');
            
            if (menuParam) {
                const targetMenu = document.getElementById(menuParam + 'Content');
                if (targetMenu) {
                    targetMenu.classList.add('expanded');
                    targetMenu.style.display = 'block';
                    
                    // 更新箭头
                    const toggleId = targetMenu.id.replace('Content', 'Toggle');
                    const toggle = document.getElementById(toggleId);
                    if (toggle) {
                        const arrow = toggle.querySelector('.ri-arrow-down-s-line');
                        if (arrow) arrow.style.transform = 'rotate(180deg)';
                    }
                }
            }
        }
        
        // 移除导航状态
        document.body.classList.remove('navigating');
    }
    
    // 页面加载完成后，恢复菜单状态
    window.addEventListener('DOMContentLoaded', function() {
        restoreMenusOnPageLoad();
    });
    
    // 在页面完全加载后，再次检查和修复菜单状态
    window.addEventListener('load', function() {
        setTimeout(restoreMenusOnPageLoad, 50);
    });
    
    // 在页面卸载前保存当前菜单状态
    window.addEventListener('beforeunload', function() {
        // 页面卸载前不需要做额外操作，仅使用当前保存的状态
    });
    
    // 初始调用一次恢复菜单
    restoreMenusOnPageLoad();
    
    console.log("menu.js加载完成");
}); 