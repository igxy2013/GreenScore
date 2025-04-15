/**
 * GreenScore系统标准规范管理工具模块
 * 提供标准数据处理、表单验证和UI交互功能
 */

// 标准管理模块命名空间
const StandardsUtils = (function() {
    // 私有变量
    const CONFIG = {
        apiEndpoints: {
            list: '/api/standards',
            add: '/api/standards/add',
            edit: '/api/standards/edit',
            delete: '/api/standards/delete',
            export: '/api/standards/export'
        },
        categories: ['设计标准', '施工标准', '验收标准', '运维标准'],
        disciplines: ['建筑', '结构', '给排水', '暖通', '电气', '智能化', '景观', '室内', '其他'],
        attributes: ['强制', '推荐']
    };

    // 表单验证
    function validateStandardForm(formData) {
        const errors = {};
        
        // 检查条文号
        if (!formData.get('条文号') || formData.get('条文号').trim() === '') {
            errors['条文号'] = '条文号不能为空';
        }
        
        // 检查分类
        if (!formData.get('分类') || formData.get('分类').trim() === '') {
            errors['分类'] = '请选择分类';
        } else if (!CONFIG.categories.includes(formData.get('分类'))) {
            errors['分类'] = '无效的分类选项';
        }
        
        // 检查专业
        if (!formData.get('专业') || formData.get('专业').trim() === '') {
            errors['专业'] = '请选择专业';
        } else if (!CONFIG.disciplines.includes(formData.get('专业'))) {
            errors['专业'] = '无效的专业选项';
        }
        
        // 检查条文内容
        if (!formData.get('条文内容') || formData.get('条文内容').trim() === '') {
            errors['条文内容'] = '条文内容不能为空';
        }
        
        // 检查分值
        const score = formData.get('分值');
        if (!score || score.trim() === '') {
            errors['分值'] = '分值不能为空';
        } else if (isNaN(score) || parseFloat(score) < 0) {
            errors['分值'] = '分值必须是非负数';
        }
        
        // 检查属性
        if (!formData.get('属性') || formData.get('属性').trim() === '') {
            errors['属性'] = '请选择属性';
        } else if (!CONFIG.attributes.includes(formData.get('属性'))) {
            errors['属性'] = '无效的属性选项';
        }
        
        // 检查标准名称
        if (!formData.get('标准名称') || formData.get('标准名称').trim() === '') {
            errors['标准名称'] = '标准名称不能为空';
        }
        
        return {
            valid: Object.keys(errors).length === 0,
            errors: errors
        };
    }
    
    // 格式化标准数据用于表格显示
    function formatStandardForTable(standard) {
        return {
            id: standard.id,
            标准号: standard.条文号 || '-',
            分类: standard.分类 || '-',
            专业: standard.专业 || '-',
            内容: truncateText(standard.条文内容 || '-', 50),
            分值: standard.分值 || '0',
            属性: standard.属性 || '-',
            标准名称: truncateText(standard.标准名称 || '-', 30),
            操作: `
                <button class="btn btn-sm btn-primary edit-btn" data-id="${standard.id}">
                    <i class="fas fa-edit"></i> 编辑
                </button>
                <button class="btn btn-sm btn-danger delete-btn" data-id="${standard.id}">
                    <i class="fas fa-trash"></i> 删除
                </button>
            `
        };
    }
    
    // 截断文本并添加省略号
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    // 转换表单数据为JSON对象
    function formDataToJson(formData) {
        const json = {};
        for (const [key, value] of formData.entries()) {
            json[key] = value;
        }
        return json;
    }
    
    // 填充表单数据
    function populateForm(form, data) {
        // 遍历表单字段
        for (const key in data) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                // 根据输入类型设置值
                if (input.type === 'checkbox') {
                    input.checked = Boolean(data[key]);
                } else if (input.tagName === 'SELECT') {
                    // 先检查是否有对应的选项
                    const option = Array.from(input.options).find(opt => opt.value === data[key]);
                    if (option) {
                        input.value = data[key];
                    } else {
                        // 如果没有匹配的选项，可以创建一个
                        const newOption = new Option(data[key], data[key]);
                        input.add(newOption);
                        input.value = data[key];
                    }
                } else {
                    input.value = data[key] || '';
                }
            }
        }
        
        // 处理图片预览
        if (data.imageUrl) {
            const previewContainer = form.querySelector('.image-preview');
            if (previewContainer) {
                previewContainer.innerHTML = `
                    <div class="preview-image">
                        <img src="${data.imageUrl}" alt="标准图示" class="img-thumbnail">
                        <button type="button" class="btn btn-sm btn-danger remove-image">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
                previewContainer.style.display = 'block';
            }
        }
    }
    
    // 重置表单
    function resetForm(form) {
        form.reset();
        
        // 清除所有验证错误提示
        const errors = form.querySelectorAll('.validation-error');
        errors.forEach(el => el.remove());
        
        // 重置输入框的验证样式
        const inputs = form.querySelectorAll('.is-invalid');
        inputs.forEach(input => input.classList.remove('is-invalid'));
        
        // 清空图片预览
        const previewContainer = form.querySelector('.image-preview');
        if (previewContainer) {
            previewContainer.innerHTML = '';
            previewContainer.style.display = 'none';
        }
    }
    
    // 处理图片上传预览
    function setupImageUploadPreview(form) {
        const fileInput = form.querySelector('input[type="file"]');
        const previewContainer = form.querySelector('.image-preview');
        
        if (!fileInput || !previewContainer) return;
        
        fileInput.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files && this.files[0]) {
                const file = this.files[0];
                
                // 检查文件类型
                const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
                if (!validTypes.includes(file.type)) {
                    Swal.fire({
                        icon: 'error',
                        title: '文件类型错误',
                        text: '请上传JPG、PNG或GIF格式的图片'
                    });
                    this.value = '';
                    return;
                }
                
                // 检查文件大小（最大5MB）
                if (file.size > 5 * 1024 * 1024) {
                    Swal.fire({
                        icon: 'error',
                        title: '文件过大',
                        text: '图片大小不能超过5MB'
                    });
                    this.value = '';
                    return;
                }
                
                // 创建预览
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewContainer.innerHTML = `
                        <div class="preview-image">
                            <img src="${e.target.result}" alt="标准图示" class="img-thumbnail">
                            <button type="button" class="btn btn-sm btn-danger remove-image">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `;
                    previewContainer.style.display = 'block';
                    
                    // 添加删除按钮事件
                    const removeBtn = previewContainer.querySelector('.remove-image');
                    removeBtn.addEventListener('click', function() {
                        previewContainer.innerHTML = '';
                        previewContainer.style.display = 'none';
                        fileInput.value = '';
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // 导出为Excel文件
    function exportToExcel(filteredData) {
        // 构建导出参数
        const params = new URLSearchParams();
        if (filteredData && Array.isArray(filteredData) && filteredData.length > 0) {
            params.append('ids', filteredData.map(item => item.id).join(','));
        }
        
        // 发起导出请求
        fetch(`${CONFIG.apiEndpoints.export}?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('导出失败，请重试');
                }
                return response.blob();
            })
            .then(blob => {
                // 创建一个下载链接
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `绿建评分标准-${new Date().toISOString().split('T')[0]}.xlsx`;
                
                // 添加到页面，触发下载，然后移除
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            })
            .catch(error => {
                console.error('导出错误:', error);
                alert('导出失败: ' + (error.message || '导出过程中发生错误，请重试'));
                
                // 记录自定义错误
                if (window.GreenScoreErrorHandler) {
                    window.GreenScoreErrorHandler.logCustomError('标准导出失败', {
                        error: error.message,
                        filteredCount: filteredData ? filteredData.length : 0
                    });
                }
            });
    }
    
    // 公开API
    return {
        validateForm: validateStandardForm,
        formatForTable: formatStandardForTable,
        populateForm: populateForm,
        resetForm: resetForm,
        setupImageUpload: setupImageUploadPreview,
        exportToExcel: exportToExcel,
        formDataToJson: formDataToJson,
        getEndpoints: function() {
            return {...CONFIG.apiEndpoints};
        },
        getCategories: function() {
            return [...CONFIG.categories];
        },
        getDisciplines: function() {
            return [...CONFIG.disciplines];
        },
        getAttributes: function() {
            return [...CONFIG.attributes];
        }
    };
})();

// 导出模块
window.StandardsUtils = StandardsUtils; 