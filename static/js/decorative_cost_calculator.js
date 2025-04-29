// 删除自定义的ExportLoadingModal定义，使用导入的组件

document.addEventListener('DOMContentLoaded', function() {
    // 获取表格和按钮元素
    const table = document.getElementById('decorative-cost-table');
    const tbody = table.querySelector('tbody');
    const addRowBtn = document.getElementById('add-row');
    const saveBtn = document.getElementById('save-btn');
    const exportBtn = document.getElementById('export-btn');
    const clearBtn = document.getElementById('clear-btn');
    
    // 初始化项目ID - 改为直接从页面元素获取
    let projectId = null;
    
    // 1. 直接从当前页面的隐藏字段获取项目ID
    const projectIdElement = document.getElementById('current-project-id');
    if (projectIdElement && projectIdElement.value) {
        projectId = projectIdElement.value;
        console.log("从页面元素获取项目ID:", projectId);
    }
    
    // 2. 从URL参数获取
    if (!projectId) {
        const urlParams = new URLSearchParams(window.location.search);
        const projectIdFromUrl = urlParams.get('project_id');
        if (projectIdFromUrl) {
            projectId = projectIdFromUrl;
            console.log("从URL参数获取项目ID:", projectId);
        }
    }
    
    // 3. 从URL路径中提取项目ID - 格式通常是 /project/{project_id}
    if (!projectId) {
        const pathMatch = window.location.pathname.match(/\/project\/(\d+)/);
        if (pathMatch && pathMatch[1]) {
            projectId = pathMatch[1];
            console.log("从URL路径获取项目ID:", projectId);
        }
    }
    
    if (projectId) {
        document.getElementById('current-project-id').value = projectId;
        console.log("最终使用的项目ID:", projectId);
    } else {
        console.log("警告：未能获取到项目ID");
    }
    
    // 添加新行
    addRowBtn.addEventListener('click', function() {
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>
                <input type="text" class="input-field" placeholder="请输入子项名称">
            </td>
            <td>
                <select class="building-type-select" aria-label="建筑类型">
                    <option value="">请选择建筑类型</option>
                    <option value="住宅" data-price="3200">住宅</option>
                    <option value="商业" data-price="3500">商业</option>
                    <option value="办公" data-price="3800">办公</option>
                    <option value="工业" data-price="2800">工业</option>
                    <option value="医疗" data-price="4500">医疗</option>
                    <option value="教育" data-price="3600">教育</option>
                    <option value="文化" data-price="4200">文化</option>
                    <option value="体育" data-price="5000">体育</option>
                    <option value="其他" data-price="3000">其他</option>
                </select>
            </td>
            <td>
                <input type="number" min="0" class="input-field unit-price" placeholder="综合单价" readonly>
            </td>
            <td>
                <input type="number" min="0" class="input-field building-area" placeholder="建筑面积">
            </td>
            <td>
                <input type="number" min="0" class="calculated-field total-cost" placeholder="单体总造价" readonly>
            </td>
            <td>
                <input type="number" min="0" max="100" class="input-field design-ratio" placeholder="设计比例">
            </td>
            <td>
                <input type="number" class="calculated-field decorative-cost" placeholder="装饰性构件造价" readonly>
            </td>
            <td class="image-cell">
                <div class="image-preview-container">
                    <img class="image-preview" src="" alt="示意图" style="display: none; max-width: 100px; max-height: 80px;">
                    <div class="image-actions">
                        <input type="file" class="image-input" accept="image/*" style="display: none;">
                        <button class="btn btn-sm btn-primary upload-image-btn icon-btn" title="上传图片"><i class="ri-upload-line"></i></button>
                        <button class="btn btn-sm btn-primary paste-image-btn icon-btn ml-1" title="粘贴"><i class="ri-clipboard-line"></i></button>
                        <button class="btn btn-sm btn-danger remove-image-btn icon-btn ml-1" style="display: none;" title="删除"><i class="ri-delete-bin-line"></i></button>
                    </div>
                </div>
            </td>
            <td>
                <div class="row-actions">
                    <button class="btn btn-danger btn-sm delete-row icon-btn" title="删除"><i class="ri-delete-bin-line"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(newRow);
        
        // 为新行中的输入字段添加事件监听器
        addInputEventListeners(newRow);
        addImageEventListeners(newRow);
        
        // 为新行中的删除按钮添加事件监听器
        const deleteBtn = newRow.querySelector('.delete-row');
        deleteBtn.addEventListener('click', function() {
            if (tbody.children.length > 1) {
                tbody.removeChild(newRow);
            } else {
                alert('至少保留一行数据');
            }
        });
    });
    
    // 为所有现有行添加事件监听器
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
        addInputEventListeners(row);
        addImageEventListeners(row);
        
        // 为删除按钮添加事件监听器
        const deleteBtn = row.querySelector('.delete-row');
        deleteBtn.addEventListener('click', function() {
            if (tbody.children.length > 1) {
                tbody.removeChild(row);
            } else {
                alert('至少保留一行数据');
            }
        });
    });
    
    // 为输入字段添加事件监听器的函数
    function addInputEventListeners(row) {
        const buildingTypeSelect = row.querySelector('.building-type-select');
        const unitPriceInput = row.querySelector('.unit-price');
        const buildingAreaInput = row.querySelector('.building-area');
        const totalCostOutput = row.querySelector('.total-cost');
        const designRatioInput = row.querySelector('.design-ratio');
        const decorativeCostOutput = row.querySelector('.decorative-cost');
        
        // 更新综合单价
        function updateUnitPrice() {
            const selectedOption = buildingTypeSelect.options[buildingTypeSelect.selectedIndex];
            const unitPrice = selectedOption ? selectedOption.getAttribute('data-price') : '';
            unitPriceInput.value = unitPrice;
            
            // 触发单体总造价和装饰性构件造价计算
            calculateTotalCost();
        }
        
        // 计算单体总造价
        function calculateTotalCost() {
            const unitPrice = parseFloat(unitPriceInput.value) || 0;
            const buildingArea = parseFloat(buildingAreaInput.value) || 0;
            
            if (unitPrice && buildingArea) {
                const totalCost = unitPrice * buildingArea/10000;
                totalCostOutput.value = totalCost.toFixed(2);
            } else {
                totalCostOutput.value = '';
            }
            
            // 触发装饰性构件造价计算
            calculateDecorativeCost();
        }
        
        // 计算装饰性构件造价
        function calculateDecorativeCost() {
            const totalCost = parseFloat(totalCostOutput.value) || 0;
            const designRatio = parseFloat(designRatioInput.value) || 0;
            
            if (totalCost && designRatio) {
                const decorativeCost = totalCost * (designRatio / 100);
                decorativeCostOutput.value = decorativeCost.toFixed(2);
            } else {
                decorativeCostOutput.value = '';
            }
        }
        
        // 为输入字段添加事件监听器
        buildingTypeSelect.addEventListener('change', updateUnitPrice);
        buildingAreaInput.addEventListener('input', calculateTotalCost);
        designRatioInput.addEventListener('input', calculateDecorativeCost);
        
        // 初始化数据
        updateUnitPrice();
    }
    
    // 保存数据
    saveBtn.addEventListener('click', function() {
        const data = collectData();
        localStorage.setItem('decorativeCostData', JSON.stringify(data));
        Toastify({
            text: '数据已保存！',
            duration: 3000,
            gravity: 'top',
            position: 'right',
            style: {
                background: 'linear-gradient(to right, #00b09b, #96c93d)'
            }
        }).showToast();
    });
    
    // 导出数据（导出计算书）
    exportBtn.addEventListener('click', function() {
        exportReport();
    });
    
    // 导出计算书函数
    async function exportReport() {
        try {
            const data = collectData();
            
            if (!data || !data.rows || data.rows.length === 0) {
                alert('请先添加数据再导出计算书！');
                return;
            }
            
            // 获取项目信息
            const urlParams = new URLSearchParams(window.location.search);
            
            // 从URL路径中提取项目ID - 格式通常是 /project/{project_id}
            let projectIdFromPath = null;
            const pathMatch = window.location.pathname.match(/\/project\/(\d+)/);
            if (pathMatch && pathMatch[1]) {
                projectIdFromPath = pathMatch[1];
            }
            
            // 从URL参数中获取项目ID
            const projectIdFromUrl = urlParams.get('project_id');
            
            // 从隐藏字段获取项目ID
            const projectIdElement = document.getElementById('current-project-id');
            const projectIdFromElement = projectIdElement ? projectIdElement.value : null;

            // 优先使用路径中的ID，然后是URL参数，最后是隐藏字段中的ID
            const projectId = projectIdFromPath || projectIdFromUrl || projectIdFromElement || null;
            
            if (!projectId) {
                alert("未能获取到项目ID，无法导出计算书！请确保URL中包含project_id参数。");
                console.error("未能获取到项目ID，导出失败");
                return;
            }
            
            let projectInfo = {};
            
            try {
                console.log("正在通过API获取项目信息...");
                const projectInfoResponse = await fetch(`/api/project_info?project_id=${projectId}`);
                
                if (projectInfoResponse.ok) {
                    projectInfo = await projectInfoResponse.json();
                    console.log("成功获取项目信息:", projectInfo);
                } else {
                    console.error("获取项目信息失败:", projectInfoResponse.status, projectInfoResponse.statusText);
                    try {
                        const errorText = await projectInfoResponse.text();
                        console.error("错误详情:", errorText);
                    } catch (e) {
                        console.error("无法获取错误详情:", e);
                    }
                    // 继续执行，使用空项目信息
                    alert("获取项目信息失败，将使用默认信息继续导出。");
                }
            } catch (error) {
                console.error("获取项目信息时发生错误:", error);
                alert("获取项目信息时发生错误，将使用默认信息继续导出。");
                // 继续执行，使用空项目信息
            }

            // 准备表格数据格式
            const tableRows = [];
            
            // 处理每一行数据，转换成Word表格需要的格式
            data.rows.forEach(row => {
                // 计算装饰性构件造价占单栋建筑总造价的比例（%）
                const totalCost = parseFloat(row.totalCost) || 0;
                const decorativeCost = parseFloat(row.decorativeCost) || 0;
                const percentage = totalCost > 0 ? ((decorativeCost / totalCost) * 100).toFixed(2) + '%' : '0.00%';
                
                tableRows.push({
                    subItem: row.subItem || '',                            // 子项名称
                    decorativeCost: decorativeCost.toFixed(2) || '0.00',   // 装饰性构件造价（万元）
                    totalCost: totalCost.toFixed(2) || '0.00',             // 单栋建筑总造价（万元）
                    percentage: percentage                                 // 装饰性构件造价占单栋建筑总造价的比例（%）
                });
            });

            // 准备要发送到服务器的数据
            const exportData = {
                projectId: projectId,
                projectInfo: projectInfo,
                rows: data.rows,
                tableRows: tableRows,  // 新增的表格格式数据
                templateFile: '装饰性构件造价比例计算书.docx'
            };
            
            // 收集所有行的图片数据
            const allImages = [];
            for (const row of data.rows) {
                if (row.imageData) {
                    allImages.push(row.imageData);
                }
            }
            
            // 将图片数据添加到项目信息中
            if (allImages.length > 0) {
                if (!exportData.projectInfo) {
                    exportData.projectInfo = {};
                }
                
                // 第一张图片使用常规键（向后兼容）
                exportData.projectInfo.示意图 = allImages[0];
                
                // 所有图片添加到数组中
                exportData.projectInfo.示意图数组 = allImages;
                
                console.log(`已添加${allImages.length}张示意图数据到导出信息`);
            }
            
            // 显示加载提示窗口
            try {
                ExportLoadingModal.show({
                    title: '正在生成计算书',
                    description: '请耐心等待，文档生成需要一点时间...',
                    showTimer: true,
                    showBackdrop: false,
                    autoTimeout: 30000
                });
            } catch (modalError) {
                console.error("显示导出加载模态框失败:", modalError);
                // 继续执行，不阻断导出流程
            }
            
            // 发送请求到后端API
            try {
                const response = await fetch('/api/generate_decorative_cost_report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(exportData)
                });
                
                // 隐藏加载提示窗口
                try {
                    ExportLoadingModal.hide();
                } catch (modalError) {
                    console.error("隐藏导出加载模态框失败:", modalError);
                }
                
                if (!response.ok) {
                    // 尝试读取错误信息
                    let errorMessage = '导出失败';
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.error || errorMessage;
                    } catch (e) {
                        console.error("无法解析错误响应:", e);
                    }
                    alert('导出失败: ' + errorMessage);
                    return;
                }
                
                // 获取blob数据
                const blob = await response.blob();
                
                // 创建下载链接
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download =  '装饰性构件造价比例计算书.docx';
                document.body.appendChild(a);
                a.click();
                
                // 清理
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);
                
            } catch (error) {
                // 隐藏加载提示窗口
                try {
                    ExportLoadingModal.hide();
                } catch (modalError) {
                    console.error("隐藏导出加载模态框失败:", modalError);
                }
                
                alert('导出失败: ' + (error.message || '未知错误'));
                console.error('导出错误:', error);
            }
        } catch (error) {
            alert('导出过程中发生错误: ' + (error.message || '未知错误'));
            console.error('导出主函数错误:', error);
        }
    }
    
    // 清空数据
    clearBtn.addEventListener('click', function() {
        if (confirm('确定要清空所有数据吗？')) {
            document.getElementById('projectName').value = '';
            const rows = tbody.querySelectorAll('tr');
            rows.forEach(row => {
                const inputs = row.querySelectorAll('input');
                inputs.forEach(input => {
                    input.value = '';
                });
                const selects = row.querySelectorAll('select');
                selects.forEach(select => {
                    select.selectedIndex = 0;
                    // 触发change事件，更新相关计算
                    const event = new Event('change');
                    select.dispatchEvent(event);
                });
            });
            
            // 清空图片
            const imageElements = document.querySelectorAll('.image-preview');
            imageElements.forEach(img => {
                img.src = '';
                img.style.display = 'none';
                delete img.dataset.imageData;
            });
            
            localStorage.removeItem('decorativeCostData');
        }
    });
    
    // 收集表格和项目数据
    function collectData() {
        try {
            if (!tbody) {
                console.error("找不到tbody元素");
                return { rows: [] };
            }
            
            const rows = tbody.querySelectorAll('tr');
            const rowData = [];
            
            rows.forEach(row => {
                try {
                    const subItem = row.querySelector('td:nth-child(1) input')?.value || '';
                    const buildingTypeElem = row.querySelector('td:nth-child(2) select');
                    const buildingType = buildingTypeElem ? buildingTypeElem.value : '';
                    const unitPrice = row.querySelector('td:nth-child(3) input')?.value || '';
                    const buildingArea = row.querySelector('td:nth-child(4) input')?.value || '';
                    const totalCost = row.querySelector('td:nth-child(5) input')?.value || '';
                    const designRatio = row.querySelector('td:nth-child(6) input')?.value || '';
                    const decorativeCost = row.querySelector('td:nth-child(7) input')?.value || '';
                    const imagePreview = row.querySelector('.image-preview');
                    const imageData = imagePreview && imagePreview.style.display !== 'none' ? 
                                        imagePreview.dataset.imageData : null;
                    
                    if (subItem || buildingType || buildingArea || totalCost || designRatio) {
                        rowData.push({
                            subItem,
                            buildingType,
                            unitPrice,
                            buildingArea,
                            totalCost,
                            designRatio,
                            decorativeCost,
                            imageData
                        });
                    }
                } catch (rowError) {
                    console.error("处理数据行时出错:", rowError);
                    // 继续处理下一行，不中断整个过程
                }
            });
            
            return {
                rows: rowData
            };
        } catch (error) {
            console.error("收集数据时出错:", error);
            return { rows: [] };
        }
    }
    
    // 从本地存储加载数据并填充表格
    function loadSavedData() {
        try {
            // 获取保存的数据
            const savedData = localStorage.getItem('decorativeCostData');
            if (!savedData) {
                console.log('没有找到保存的数据');
                return;
            }
            
            const parsedData = JSON.parse(savedData);
            if (!parsedData || !parsedData.rows || !Array.isArray(parsedData.rows) || parsedData.rows.length === 0) {
                console.log('保存的数据格式无效或为空');
                return;
            }
            
            // 清除现有行
            if (!tbody) {
                console.error("找不到tbody元素");
                return;
            }
            
            // 保留第一行并清除其它行
            const rows = tbody.querySelectorAll('tr');
            for (let i = rows.length - 1; i > 0; i--) {
                tbody.removeChild(rows[i]);
            }
            
            // 恢复第一行数据
            let firstRowRestored = false;
            
            // 填充数据到表格
            parsedData.rows.forEach((rowData, index) => {
                try {
                    let row;
                    if (index === 0 && rows.length > 0) {
                        // 使用现有的第一行
                        row = rows[0];
                        firstRowRestored = true;
                    } else {
                        // 为其他数据添加新行
                        addRowBtn.click(); // 使用已有的addRowBtn按钮触发添加行
                        row = tbody.querySelectorAll('tr')[index];
                    }
                    
                    if (!row) {
                        console.error(`找不到索引为 ${index} 的行`);
                        return;
                    }
                    
                    // 填充输入框
                    const subItemInput = row.querySelector('td:nth-child(1) input');
                    if (subItemInput) subItemInput.value = rowData.subItem || '';
                    
                    const buildingTypeSelect = row.querySelector('td:nth-child(2) select');
                    if (buildingTypeSelect) buildingTypeSelect.value = rowData.buildingType || '';
                    
                    const unitPriceInput = row.querySelector('td:nth-child(3) input');
                    if (unitPriceInput) unitPriceInput.value = rowData.unitPrice || '';
                    
                    const buildingAreaInput = row.querySelector('td:nth-child(4) input');
                    if (buildingAreaInput) buildingAreaInput.value = rowData.buildingArea || '';
                    
                    const totalCostInput = row.querySelector('td:nth-child(5) input');
                    if (totalCostInput) totalCostInput.value = rowData.totalCost || '';
                    
                    const designRatioInput = row.querySelector('td:nth-child(6) input');
                    if (designRatioInput) designRatioInput.value = rowData.designRatio || '';
                    
                    const decorativeCostInput = row.querySelector('td:nth-child(7) input');
                    if (decorativeCostInput) decorativeCostInput.value = rowData.decorativeCost || '';
                    
                    // 恢复图片（如果有）
                    if (rowData.imageData) {
                        const imagePreview = row.querySelector('.image-preview');
                        if (imagePreview) {
                            imagePreview.style.display = 'block';
                            imagePreview.src = rowData.imageData;  // 使用src属性而不是backgroundImage
                            imagePreview.dataset.imageData = rowData.imageData;
                            
                            // 显示删除按钮
                            const removeButton = row.querySelector('.remove-image-btn');
                            if (removeButton) {
                                removeButton.style.display = 'block';
                            }
                        }
                    }
                    
                    // 触发计算事件
                    const calculateEvent = new Event('input', { bubbles: true });
                    const buildingAreaInputForEvent = row.querySelector('td:nth-child(4) input');
                    if (buildingAreaInputForEvent) {
                        buildingAreaInputForEvent.dispatchEvent(calculateEvent);
                    }
                    
                } catch (rowError) {
                    console.error(`恢复第 ${index} 行数据时出错:`, rowError);
                }
            });
            
            console.log('成功加载保存的数据');
            
        } catch (error) {
            console.error('加载保存的数据时出错:', error);
        }
    }
    
    // 加载保存的数据
    loadSavedData();
});

// 添加图片相关事件监听器的函数
function addImageEventListeners(row) {
    const imagePreviewContainer = row.querySelector('.image-preview-container');
    const imageInput = row.querySelector('.image-input');
    const imagePreview = row.querySelector('.image-preview');
    const uploadImageBtn = row.querySelector('.upload-image-btn');
    const pasteImageBtn = row.querySelector('.paste-image-btn');
    const removeImageBtn = row.querySelector('.remove-image-btn');
    
    // 上传图片按钮点击事件
    uploadImageBtn.addEventListener('click', function() {
        imageInput.click();
    });
    
    // 文件输入变化事件
    imageInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(event) {
                imagePreview.src = event.target.result;
                imagePreview.style.display = 'block';
                // 保存图片数据以便后续导出
                imagePreview.dataset.imageData = event.target.result;
                // 显示删除按钮
                removeImageBtn.style.display = 'block';
            };
            
            reader.readAsDataURL(e.target.files[0]);
        }
    });
    
    // 粘贴图片按钮点击事件
    pasteImageBtn.addEventListener('click', function() {
        // 焦点需要在文档上才能捕获粘贴事件
        document.body.focus();
        navigator.clipboard.read().then(clipboardItems => {
            for (const clipboardItem of clipboardItems) {
                for (const type of clipboardItem.types) {
                    if (type.startsWith('image/')) {
                        clipboardItem.getType(type).then(blob => {
                            const reader = new FileReader();
                            reader.onload = function(event) {
                                imagePreview.src = event.target.result;
                                imagePreview.style.display = 'block';
                                // 保存图片数据以便后续导出
                                imagePreview.dataset.imageData = event.target.result;
                                // 显示删除按钮
                                removeImageBtn.style.display = 'block';
                            };
                            reader.readAsDataURL(blob);
                        });
                        break;
                    }
                }
            }
        }).catch(err => {
            // 捕获 navigator.clipboard.read() 的可能权限错误
            if (err.name === 'NotAllowedError' || err.name === 'SecurityError') {
                alert('无法读取剪贴板。请确保您的浏览器设置允许访问剪贴板。\n\n尝试使用快捷键 Ctrl+V 直接粘贴。');
                // 设置当前行的全局粘贴事件
                setupGlobalPasteForTarget(row);
            } else {
                console.error('粘贴图片失败:', err);
                alert('粘贴图片失败: ' + err.message);
            }
        });
    });
    
    // 删除图片按钮点击事件
    removeImageBtn.addEventListener('click', function() {
        imagePreview.src = '';
        imagePreview.style.display = 'none';
        delete imagePreview.dataset.imageData;
        // 隐藏删除按钮
        removeImageBtn.style.display = 'none';
    });
    
    // 图片预览点击事件（放大查看）
    imagePreview.addEventListener('click', function() {
        if (this.src) {
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            modal.style.zIndex = '1000';
            modal.style.cursor = 'pointer';
            
            const img = document.createElement('img');
            img.src = this.src;
            img.style.maxWidth = '90%';
            img.style.maxHeight = '90%';
            img.style.objectFit = 'contain';
            
            modal.appendChild(img);
            document.body.appendChild(modal);
            
            modal.onclick = function() {
                document.body.removeChild(modal);
            };
        }
    });
}

// 设置全局粘贴事件处理函数
function setupGlobalPasteForTarget(row) {
    const targetRow = row;
    const imagePreview = targetRow.querySelector('.image-preview');
    const removeImageBtn = targetRow.querySelector('.remove-image-btn');
    
    // 创建并显示提示信息
    const pasteHelp = document.createElement('div');
    pasteHelp.className = 'paste-help';
    pasteHelp.textContent = '请按下Ctrl+V粘贴图片';
    pasteHelp.style.color = '#3b82f6';
    pasteHelp.style.fontSize = '0.8rem';
    pasteHelp.style.textAlign = 'center';
    pasteHelp.style.marginTop = '4px';
    
    const imageActionsDiv = targetRow.querySelector('.image-actions');
    imageActionsDiv.appendChild(pasteHelp);
    
    // 监听全局的粘贴事件
    const handlePaste = function(e) {
        if (e.clipboardData && e.clipboardData.items) {
            const items = e.clipboardData.items;
            
            // 查找图片数据
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    const blob = items[i].getAsFile();
                    
                    // 读取图片数据
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        // 更新图片预览
                        imagePreview.src = event.target.result;
                        imagePreview.style.display = 'block';
                        imagePreview.dataset.imageData = event.target.result;
                        
                        // 显示删除按钮
                        removeImageBtn.style.display = 'block';
                        
                        // 移除提示文本
                        if (pasteHelp.parentNode) {
                            pasteHelp.parentNode.removeChild(pasteHelp);
                        }
                        
                        // 移除全局粘贴事件监听器
                        document.removeEventListener('paste', handlePaste);
                    };
                    reader.readAsDataURL(blob);
                    
                    // 阻止默认粘贴行为
                    e.preventDefault();
                    return;
                }
            }
        }
    };
    
    // 添加粘贴事件监听器
    document.addEventListener('paste', handlePaste);
    
    // 设置一个超时移除粘贴帮助提示
    setTimeout(() => {
        if (pasteHelp.parentNode) {
            pasteHelp.parentNode.removeChild(pasteHelp);
        }
    }, 5000);
}

