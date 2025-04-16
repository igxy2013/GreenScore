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
                alert('数据已保存！');
            });
            
            // 导出数据（导出计算书）
            exportBtn.addEventListener('click', function() {
                exportReport();
            });
            
            // 导出计算书函数
            async function exportReport() {
                const data = collectData();
                
                if (data.rows.length === 0) {
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
                const projectIdFromElement = document.getElementById('current-project-id')?.value;

                // 优先使用路径中的ID，然后是URL参数，最后是隐藏字段中的ID
                const projectId = projectIdFromPath || projectIdFromUrl || projectIdFromElement || null;
                
                if (!projectId) {
                    alert("未能获取到项目ID，无法导出计算书！请确保URL中包含project_id参数。");
                    return;
                }
                
                let projectInfo = {};
                
                try {
                    if (projectId) {
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
                        }
                    } else {
                        alert("未提供项目ID，无法获取项目信息!");
                        return;
                    }
                } catch (error) {
                    console.error("获取项目信息时发生错误:", error);
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
                ExportLoadingModal.show({
                    title: '正在生成计算书',
                    description: '请耐心等待，文档生成需要一点时间...',
                    showTimer: false,
                    showBackdrop: false,
                    footerText: '您的文件即将准备就绪',
                    autoTimeout: 30000
                });
                
                // 发送请求到后端API
                fetch('/api/generate_decorative_cost_report', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(exportData)
                })
                .then(response => {
                    // 隐藏加载提示窗口
                    ExportLoadingModal.hide();
                    
                    if (!response.ok) {
                        // 如果响应不成功，解析错误消息
                        return response.json().then(data => {
                            throw new Error(data.error || '导出失败');
                        });
                    }
                    
                    // 创建下载链接
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = data.projectName ? 
                        `${data.projectName}-装饰性构件造价比例计算书.docx` : 
                        '装饰性构件造价比例计算书.docx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                })
                .catch(error => {
                    alert('导出失败: ' + error.message);
                    console.error('导出错误:', error);
                });
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
                const rows = tbody.querySelectorAll('tr');
                const rowData = [];
                
                rows.forEach(row => {
                    const subItem = row.querySelector('td:nth-child(1) input').value;
                    const buildingType = row.querySelector('td:nth-child(2) select').value;
                    const unitPrice = row.querySelector('td:nth-child(3) input').value;
                    const buildingArea = row.querySelector('td:nth-child(4) input').value;
                    const totalCost = row.querySelector('td:nth-child(5) input').value;
                    const designRatio = row.querySelector('td:nth-child(6) input').value;
                    const decorativeCost = row.querySelector('td:nth-child(7) input').value;
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
                });
                
                return {
                    rows: rowData
                };
            }
            
            // 加载保存的数据
            function loadSavedData() {
                const savedData = localStorage.getItem('decorativeCostData');
                
                if (savedData) {
                    const data = JSON.parse(savedData);
                    
                    // 如果没有行数据，直接返回
                    if (!data.rows || data.rows.length === 0) {
                        return;
                    }
                    
                    // 清空现有行，只保留一行
                    while (tbody.children.length > 1) {
                        tbody.removeChild(tbody.lastChild);
                    }
                    
                    // 清空第一行数据
                    const firstRow = tbody.querySelector('tr');
                    const firstRowInputs = firstRow.querySelectorAll('input');
                    firstRowInputs.forEach(input => {
                        input.value = '';
                    });
                    const firstRowSelect = firstRow.querySelector('select');
                    firstRowSelect.selectedIndex = 0;
                    
                    // 填充第一行数据
                    if (data.rows.length > 0) {
                        const item = data.rows[0];
                        firstRow.querySelector('td:nth-child(1) input').value = item.subItem || '';
                        firstRow.querySelector('td:nth-child(2) select').value = item.buildingType || '';
                        // 触发buildingType的change事件以更新unitPrice
                        const event = new Event('change');
                        firstRow.querySelector('td:nth-child(2) select').dispatchEvent(event);
                        firstRow.querySelector('td:nth-child(4) input').value = item.buildingArea || '';
                        firstRow.querySelector('td:nth-child(6) input').value = item.designRatio || '';
                        // 触发计算
                        const buildingAreaInput = firstRow.querySelector('td:nth-child(4) input');
                        const designRatioInput = firstRow.querySelector('td:nth-child(6) input');
                        buildingAreaInput.dispatchEvent(new Event('input'));
                        designRatioInput.dispatchEvent(new Event('input'));
                        
                        // 处理图片数据
                        const imagePreview = firstRow.querySelector('.image-preview');
                        const removeImageBtn = firstRow.querySelector('.remove-image-btn');
                        if (item.imageData) {
                            imagePreview.src = item.imageData;
                            imagePreview.style.display = 'block';
                            imagePreview.dataset.imageData = item.imageData;
                            // 显示删除按钮
                            removeImageBtn.style.display = 'block';
                        } else {
                            imagePreview.src = '';
                            imagePreview.style.display = 'none';
                            delete imagePreview.dataset.imageData;
                            // 隐藏删除按钮
                            removeImageBtn.style.display = 'none';
                        }
                    }
                    
                    // 添加其他行数据
                    for (let i = 1; i < data.rows.length; i++) {
                        addRowBtn.click();
                        const row = tbody.lastChild;
                        const item = data.rows[i];
                        
                        row.querySelector('td:nth-child(1) input').value = item.subItem || '';
                        row.querySelector('td:nth-child(2) select').value = item.buildingType || '';
                        // 触发buildingType的change事件以更新unitPrice
                        const event = new Event('change');
                        row.querySelector('td:nth-child(2) select').dispatchEvent(event);
                        row.querySelector('td:nth-child(4) input').value = item.buildingArea || '';
                        row.querySelector('td:nth-child(6) input').value = item.designRatio || '';
                        // 触发计算
                        const buildingAreaInput = row.querySelector('td:nth-child(4) input');
                        const designRatioInput = row.querySelector('td:nth-child(6) input');
                        buildingAreaInput.dispatchEvent(new Event('input'));
                        designRatioInput.dispatchEvent(new Event('input'));
                        
                        // 处理图片数据
                        const imagePreview = row.querySelector('.image-preview');
                        const removeImageBtn = row.querySelector('.remove-image-btn');
                        if (item.imageData) {
                            imagePreview.src = item.imageData;
                            imagePreview.style.display = 'block';
                            imagePreview.dataset.imageData = item.imageData;
                            // 显示删除按钮
                            removeImageBtn.style.display = 'block';
                        } else {
                            imagePreview.src = '';
                            imagePreview.style.display = 'none';
                            delete imagePreview.dataset.imageData;
                            // 隐藏删除按钮
                            removeImageBtn.style.display = 'none';
                        }
                    }
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

        // 设置当前行的全局粘贴事件 (备用方案)
        function setupGlobalPasteForTarget(targetRow) {
            const pasteHandler = function(e) {
                if (e.clipboardData && e.clipboardData.items) {
                    const items = e.clipboardData.items;
                    
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].type.indexOf("image") !== -1) {
                            const blob = items[i].getAsFile();
                            const reader = new FileReader();
                            const imagePreview = targetRow.querySelector('.image-preview');
                            const removeImageBtn = targetRow.querySelector('.remove-image-btn');
                            
                            reader.onload = function(event) {
                                imagePreview.src = event.target.result;
                                imagePreview.style.display = 'block';
                                // 保存图片数据以便后续导出
                                imagePreview.dataset.imageData = event.target.result;
                                // 显示删除按钮
                                removeImageBtn.style.display = 'block';
                            };
                            
                            reader.readAsDataURL(blob);
                            // 一旦处理完毕，移除事件监听器
                            document.removeEventListener('paste', pasteHandler);
                            break;
                        }
                    }
                }
            };
            
            // 添加一次性粘贴事件
            document.addEventListener('paste', pasteHandler);
            
            // 通知用户
            alert('请按下 Ctrl+V 粘贴图片');
        }

        // 全局粘贴事件监听
        document.addEventListener('paste', function(e) {
            // 只有在特定焦点元素上才处理粘贴事件
            const activeElement = document.activeElement;
            if (activeElement && activeElement.classList.contains('paste-image-btn')) {
                if (e.clipboardData && e.clipboardData.items) {
                    const items = e.clipboardData.items;
                    
                    for (let i = 0; i < items.length; i++) {
                        if (items[i].type.indexOf("image") !== -1) {
                            e.preventDefault(); // 阻止默认粘贴行为
                            
                            const blob = items[i].getAsFile();
                            const reader = new FileReader();
                            //
                            const currentRow = activeElement.closest('tr');
                            const imagePreview = currentRow.querySelector('.image-preview');
                            
                            reader.onload = function(event) {
                                imagePreview.src = event.target.result;
                                imagePreview.style.display = 'block';
                                // 保存图片数据以便后续导出
                                imagePreview.dataset.imageData = event.target.result;
                            };
                            
                            reader.readAsDataURL(blob);
                            break;
                        }
                    }
                }
            }
        });
