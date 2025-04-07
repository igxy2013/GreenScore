// 菜单初始化和事件处理
document.addEventListener('DOMContentLoaded', function() {
    // 获取菜单元素
    const basicMenuToggle = document.getElementById('basicMenuToggle');
    const basicMenuContent = document.getElementById('basicMenuContent');
    const advancedMenuToggle = document.getElementById('advancedMenuToggle');
    const advancedMenuContent = advancedMenuToggle ? document.getElementById('advancedMenuContent') : null;
    const reportMenuToggle = document.getElementById('reportMenuToggle');
    const reportMenuContent = document.getElementById('reportMenuContent');
    const specialCalcMenuToggle = document.getElementById('specialCalcMenuToggle');
    const specialCalcMenuContent = document.getElementById('specialCalcMenuContent');

    // 添加菜单切换事件
    if (basicMenuToggle && basicMenuContent) {
        basicMenuToggle.addEventListener('click', function() {
            basicMenuContent.classList.toggle('expanded');
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = basicMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        });
    }
    
    if (advancedMenuToggle && advancedMenuContent) {
        advancedMenuToggle.addEventListener('click', function() {
            advancedMenuContent.classList.toggle('expanded');
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = advancedMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        });
    }
    
    if (reportMenuToggle && reportMenuContent) {
        reportMenuToggle.addEventListener('click', function() {
            reportMenuContent.classList.toggle('expanded');
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = reportMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        });
    }
    
    // 专项计算菜单处理 - 确保这个菜单能正确展开折叠
    if (specialCalcMenuToggle && specialCalcMenuContent) {
        console.log('初始化专项计算菜单事件');
        
        specialCalcMenuToggle.addEventListener('click', function(e) {
            // 阻止事件冒泡
            e.stopPropagation();
            
            console.log('专项计算菜单被点击');
            console.log('点击前状态:', specialCalcMenuContent.classList.contains('expanded') ? '已展开' : '已折叠');
            
            // 切换expanded类，控制菜单的显示/隐藏
            specialCalcMenuContent.classList.toggle('expanded');
            
            console.log('点击后状态:', specialCalcMenuContent.classList.contains('expanded') ? '已展开' : '已折叠');
            
            // 旋转箭头图标
            const arrow = this.querySelector('.ri-arrow-down-s-line');
            if (arrow) {
                arrow.style.transform = specialCalcMenuContent.classList.contains('expanded') ? 'rotate(180deg)' : 'rotate(0deg)';
            }
            
            // 强制检查display样式
            setTimeout(function() {
                const computedStyle = window.getComputedStyle(specialCalcMenuContent);
                console.log('菜单实际display状态:', computedStyle.display);
                
                // 确保display属性正确设置
                if (specialCalcMenuContent.classList.contains('expanded') && computedStyle.display === 'none') {
                    console.log('强制设置display为block');
                    specialCalcMenuContent.style.display = 'block';
                } else if (!specialCalcMenuContent.classList.contains('expanded') && computedStyle.display !== 'none') {
                    console.log('强制设置display为none');
                    specialCalcMenuContent.style.display = 'none';
                }
            }, 10);
        });
    }
    
    // 根据当前页面设置初始菜单状态
    function setInitialMenuState() {
        // 获取当前页面信息
        const currentLevel = document.body.getAttribute('data-level') || '';
        const currentPage = document.body.getAttribute('data-page') || '';
        
        // 根据当前页面展开相应菜单
        if (currentLevel === '基本级' && basicMenuContent) {
            basicMenuContent.classList.add('expanded');
            if (basicMenuToggle) {
                const arrow = basicMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        } else if (currentLevel === '提高级' && advancedMenuContent) {
            advancedMenuContent.classList.add('expanded');
            if (advancedMenuToggle) {
                const arrow = advancedMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        }
        
        // 如果当前页面是报告导出相关页面，展开报告导出菜单
        if (currentPage === 'report_table' && reportMenuContent) {
            reportMenuContent.classList.add('expanded');
            if (reportMenuToggle) {
                const arrow = reportMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        }
        
        // 如果当前页面是专项计算相关页面，展开专项计算菜单
        if ((currentPage === 'solar_calculator' || currentPage === 'green_materials') && specialCalcMenuContent) {
            specialCalcMenuContent.classList.add('expanded');
            if (specialCalcMenuToggle) {
                const arrow = specialCalcMenuToggle.querySelector('.ri-arrow-down-s-line');
                if (arrow) arrow.style.transform = 'rotate(180deg)';
            }
        }
    }
    
    // 设置初始菜单状态
    setInitialMenuState();
    
    // 防止页面跳动的函数
    function preventPageJump() {
        // 记录当前滚动位置
        const scrollPosition = window.scrollY;
        
        // 在下一个事件循环中恢复滚动位置
        setTimeout(() => {
            window.scrollTo(0, scrollPosition);
        }, 0);
    }
    
    // 为所有子菜单链接添加点击事件处理
    const allSubmenuItems = document.querySelectorAll('.submenu-item');
    const allMenuItems = document.querySelectorAll('.menu-item');
    
    allSubmenuItems.forEach(item => {
        // 阻止事件冒泡，防止触发父菜单的折叠
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // 在导航前调用防止页面跳动的函数
            preventPageJump();
        });
    });
    
    // 添加测试代码，显示专项计算菜单状态
    console.log('菜单初始化完成');
    console.log('专项计算菜单元素:', specialCalcMenuToggle);
    
    if (specialCalcMenuToggle && specialCalcMenuContent) {
        console.log('专项计算菜单已找到，当前状态:', specialCalcMenuContent.classList.contains('expanded') ? '已展开' : '已折叠');
        console.log('专项计算菜单样式:', window.getComputedStyle(specialCalcMenuContent));
    } else {
        console.error('专项计算菜单元素未找到，请检查HTML结构');
    }
}); 