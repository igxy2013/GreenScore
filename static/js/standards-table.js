/**
 * GreenScore系统标准规范表格管理模块
 * 提供标准数据表格化展示、排序、筛选和分页功能
 */

// 标准表格管理模块
const StandardsTable = (function() {
    // 私有变量
    let tableInstance = null;
    let currentData = [];
    let tableSelector = '#standards-table';
    let filterTimeout = null;
    
    // 表格配置
    const tableConfig = {
        language: {
            "sProcessing": "处理中...",
            "sLengthMenu": "显示 _MENU_ 条",
            "sZeroRecords": "没有找到匹配记录",
            "sInfo": "显示第 _START_ 至 _END_ 条记录，共 _TOTAL_ 条",
            "sInfoEmpty": "显示第 0 至 0 条记录，共 0 条",
            "sInfoFiltered": "(由 _MAX_ 条记录过滤)",
            "sInfoPostFix": "",
            "sSearch": "搜索:",
            "sUrl": "",
            "sEmptyTable": "表中数据为空",
            "sLoadingRecords": "载入中...",
            "sInfoThousands": ",",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "上页",
                "sNext": "下页",
                "sLast": "末页"
            },
            "oAria": {
                "sSortAscending": ": 以升序排列此列",
                "sSortDescending": ": 以降序排列此列"
            }
        },
        columns: [
            { data: '标准号', title: '标准号' },
            { data: '分类', title: '分类' },
            { data: '专业', title: '专业' },
            { data: '内容', title: '条文内容' },
            { data: '分值', title: '分值' },
            { data: '属性', title: '属性' },
            { data: '标准名称', title: '标准名称' },
            { data: '操作', title: '操作', orderable: false }
        ],
        order: [[0, 'asc']],
        pagingType: "full_numbers",
        pageLength: 10,
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "全部"]],
        responsive: true,
        dom: 'Blfrtip',
        processing: false, // 禁用处理中显示
        buttons: [
            {
                extend: 'collection',
                text: '<i class="fas fa-download"></i> 导出',
                buttons: [
                    {
                        text: '<i class="fas fa-file-excel"></i> 导出当前筛选',
                        action: function(e, dt, node, config) {
                            const filteredData = dt.rows({ search: 'applied' }).data().toArray();
                            if (filteredData.length === 0) {
                                Swal.fire({
                                    icon: 'warning',
                                    title: '无数据可导出',
                                    text: '当前筛选条件下没有可导出的数据'
                                });
                                return;
                            }
                            
                            // 调用工具函数执行导出
                            if (window.StandardsUtils) {
                                window.StandardsUtils.exportToExcel(filteredData);
                            } else {
                                console.error('StandardsUtils模块未加载');
                                Swal.fire({
                                    icon: 'error',
                                    title: '导出失败',
                                    text: '无法找到导出功能模块'
                                });
                            }
                        }
                    },
                    {
                        text: '<i class="fas fa-file-excel"></i> 导出全部数据',
                        action: function(e, dt, node, config) {
                            if (currentData.length === 0) {
                                Swal.fire({
                                    icon: 'warning',
                                    title: '无数据可导出',
                                    text: '当前没有可导出的数据'
                                });
                                return;
                            }
                            
                            // 调用工具函数执行全部导出
                            if (window.StandardsUtils) {
                                window.StandardsUtils.exportToExcel(null); // 传null表示导出全部
                            } else {
                                console.error('StandardsUtils模块未加载');
                                Swal.fire({
                                    icon: 'error',
                                    title: '导出失败',
                                    text: '无法找到导出功能模块'
                                });
                            }
                        }
                    }
                ]
            },
            {
                text: '<i class="fas fa-sync"></i> 刷新',
                action: function(e, dt, node, config) {
                    loadStandardsData();
                }
            }
        ]
    };
    
    // 初始化表格
    function initTable(selector, options = {}) {
        tableSelector = selector || tableSelector;
        
        // 合并配置选项
        const config = {...tableConfig, ...options};
        
        // 如果表格已初始化，则销毁重建
        if (tableInstance) {
            tableInstance.destroy();
            tableInstance = null;
        }
        
        // 创建表格实例
        tableInstance = $(tableSelector).DataTable(config);
        
        // 添加表格搜索延迟
        setupDelayedSearch();
        
        // 初始化事件监听
        setupEventListeners();
        
        return tableInstance;
    }
    
    // 设置表格延迟搜索，提高性能
    function setupDelayedSearch() {
        $('.dataTables_filter input').off('keyup.DT search.DT input.DT paste.DT cut.DT');
        
        $('.dataTables_filter input').on('input', function() {
            const searchValue = $(this).val();
            
            clearTimeout(filterTimeout);
            filterTimeout = setTimeout(function() {
                tableInstance.search(searchValue).draw();
            }, 300); // 300ms延迟，避免频繁搜索
        });
    }
    
    // 设置事件监听
    function setupEventListeners() {
        if (!tableInstance) return;
        
        const table = $(tableSelector);
        
        // 编辑按钮点击事件
        table.on('click', '.edit-btn', function() {
            const id = $(this).data('id');
            
            // 获取该行数据
            const rowData = getRowDataById(id);
            if (!rowData) {
                console.error('未找到ID为', id, '的标准数据');
                return;
            }
            
            // 触发编辑事件
            if (typeof events.onEditClick === 'function') {
                events.onEditClick(rowData);
            }
        });
        
        // 删除按钮点击事件
        table.on('click', '.delete-btn', function() {
            const id = $(this).data('id');
            
            // 获取该行数据
            const rowData = getRowDataById(id);
            if (!rowData) {
                console.error('未找到ID为', id, '的标准数据');
                return;
            }
            
            // 触发删除事件
            if (typeof events.onDeleteClick === 'function') {
                events.onDeleteClick(rowData);
            }
        });
    }
    
    // 根据ID获取行数据
    function getRowDataById(id) {
        return currentData.find(item => item.id === id);
    }
    
    // 根据ID获取行索引
    function getRowIndexById(id) {
        if (!tableInstance) return -1;
        
        const indexes = tableInstance.rows().indexes().toArray();
        for (let i = 0; i < indexes.length; i++) {
            const rowData = tableInstance.row(indexes[i]).data();
            if (rowData && rowData.id === id) {
                return indexes[i];
            }
        }
        return -1;
    }
    
    // 加载标准数据
    function loadStandardsData() {
        // 获取API端点
        const listEndpoint = window.StandardsUtils ? 
            window.StandardsUtils.getEndpoints().list : 
            '/api/standards';
        
        // 获取数据
        fetch(listEndpoint)
            .then(response => {
                if (!response.ok) {
                    throw new Error('获取标准数据失败');
                }
                return response.json();
            })
            .then(data => {
                // 更新当前数据
                currentData = data;
                
                // 格式化数据用于表格显示
                const tableData = data.map(standard => {
                    return window.StandardsUtils ? 
                        window.StandardsUtils.formatForTable(standard) : 
                        formatStandardForTable(standard);
                });
                
                // 清空并添加新数据
                tableInstance.clear();
                tableInstance.rows.add(tableData);
                tableInstance.draw();
            })
            .catch(error => {
                console.error('加载标准数据错误:', error);
                
                Swal.fire({
                    icon: 'error',
                    title: '加载失败',
                    text: error.message || '无法加载标准数据，请刷新页面重试'
                });
                
                // 记录自定义错误
                if (window.GreenScoreErrorHandler) {
                    window.GreenScoreErrorHandler.logCustomError('标准数据加载失败', {
                        error: error.message
                    });
                }
            });
    }
    
    // 添加一行数据
    function addRow(standard) {
        if (!tableInstance) return;
        
        // 添加到当前数据
        currentData.push(standard);
        
        // 格式化数据
        const formattedData = window.StandardsUtils ? 
            window.StandardsUtils.formatForTable(standard) : 
            formatStandardForTable(standard);
        
        // 添加到表格并重绘
        tableInstance.row.add(formattedData).draw();
    }
    
    // 更新一行数据
    function updateRow(standard) {
        if (!tableInstance) return;
        
        // 更新当前数据
        const index = currentData.findIndex(item => item.id === standard.id);
        if (index !== -1) {
            currentData[index] = standard;
        } else {
            // 如果找不到，则添加
            currentData.push(standard);
        }
        
        // 格式化数据
        const formattedData = window.StandardsUtils ? 
            window.StandardsUtils.formatForTable(standard) : 
            formatStandardForTable(standard);
        
        // 获取行索引
        const rowIndex = getRowIndexById(standard.id);
        
        if (rowIndex !== -1) {
            // 更新已存在的行
            tableInstance.row(rowIndex).data(formattedData).draw();
        } else {
            // 添加新行
            tableInstance.row.add(formattedData).draw();
        }
    }
    
    // 删除一行数据
    function deleteRow(id) {
        if (!tableInstance) return;
        
        // 从当前数据中删除
        const index = currentData.findIndex(item => item.id === id);
        if (index !== -1) {
            currentData.splice(index, 1);
        }
        
        // 获取行索引
        const rowIndex = getRowIndexById(id);
        
        if (rowIndex !== -1) {
            // 删除行并重绘
            tableInstance.row(rowIndex).remove().draw();
        }
    }
    
    // 重新加载表格数据
    function reloadTable() {
        loadStandardsData();
    }
    
    // 应用筛选
    function applyFilter(filters) {
        if (!tableInstance) return;
        
        // 清除现有筛选
        tableInstance.search('').columns().search('').draw();
        
        // 应用全局筛选
        if (filters.global) {
            tableInstance.search(filters.global).draw();
            return; // 全局筛选优先，不再应用列筛选
        }
        
        // 应用列筛选
        if (filters.columns) {
            for (const [columnName, value] of Object.entries(filters.columns)) {
                if (!value) continue;
                
                // 查找列索引
                const columnIndex = tableConfig.columns.findIndex(col => col.data === columnName);
                if (columnIndex !== -1) {
                    tableInstance.column(columnIndex).search(value);
                }
            }
            
            // 一次性重绘表格，提高性能
            tableInstance.draw();
        }
    }
    
    // 备用格式化函数，当StandardsUtils不可用时使用
    function formatStandardForTable(standard) {
        function truncateText(text, maxLength) {
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        }
        
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
    
    // 事件处理
    const events = {
        onEditClick: null,
        onDeleteClick: null
    };
    
    // 设置事件处理函数
    function on(eventName, callback) {
        if (events.hasOwnProperty(eventName)) {
            events[eventName] = callback;
        }
    }
    
    // 公开API
    return {
        init: initTable,
        load: loadStandardsData,
        addRow: addRow,
        updateRow: updateRow,
        deleteRow: deleteRow,
        reload: reloadTable,
        filter: applyFilter,
        on: on,
        getTableInstance: function() {
            return tableInstance;
        },
        getCurrentData: function() {
            return [...currentData];
        }
    };
})();

// 导出模块
window.StandardsTable = StandardsTable; 