/**
 * Word模板处理工具
 * 用于在前端处理Word模板的占位符替换
 */

// Word 模板处理器
async function processWordTemplate(templateUrl, data) {
    try {
        console.log("开始处理Word模板...", templateUrl);
        
        // 检查参数
        if (!templateUrl || !data) {
            throw new Error("模板URL和数据都是必需的");
        }
        
        // 加载JSZip库（如果还没有加载）
        if (typeof JSZip === 'undefined') {
            console.error("JSZip库未加载，请确保在HTML中引入了jszip.min.js");
            throw new Error("请先加载JSZip库");
        }
        
        console.log("正在获取模板文件...");
        // 获取模板文件
        const response = await fetch(templateUrl);
        if (!response.ok) {
            console.error("获取模板文件失败:", response.status, response.statusText);
            throw new Error(`获取模板文件失败: ${response.status} ${response.statusText}`);
        }
        
        console.log("正在读取模板文件内容...");
        const templateArrayBuffer = await response.arrayBuffer();
        
        // 创建新的ZIP实例
        console.log("正在创建ZIP实例...");
        const zip = new JSZip();
        
        // 加载docx文件（实际上是一个ZIP文件）
        console.log("正在解压Word文档...");
        await zip.loadAsync(templateArrayBuffer);
        
        // 先尝试找出模板中的占位符实际格式
        // 获取document.xml文件（包含主要内容）
        console.log("正在读取document.xml...");
        const documentXmlFile = zip.file("word/document.xml");
        if (!documentXmlFile) {
            throw new Error("无法在Word文档中找到document.xml");
        }
        const documentXml = await documentXmlFile.async("string");
        
        // 检测占位符格式
        const placeholderFormat = detectPlaceholderFormat(documentXml);
        console.log("检测到的占位符格式:", placeholderFormat);
        
        // 替换所有占位符
        console.log("正在替换占位符...");
        let modifiedXml = documentXml;
        
        // 处理普通文本占位符 - 使用检测到的格式
        for (const [key, value] of Object.entries(data)) {
            if (typeof value === 'string' || typeof value === 'number') {
                const stringValue = String(value);
                
                // 将换行符转换为Word文档的换行标记
                const formattedValue = stringValue.replace(/\n/g, '</w:t><w:br/><w:t>');
                
                if (placeholderFormat.format === 'curly') {
                    // {{key}} 格式
                    const placeholder = `{{${key}}}`;
                    modifiedXml = safeReplace(modifiedXml, placeholder, formattedValue);
                } else if (placeholderFormat.format === 'dollar-curly') {
                    // ${key} 格式
                    const placeholder = `\${${key}}`;
                    modifiedXml = safeReplace(modifiedXml, placeholder, formattedValue);
                } else if (placeholderFormat.format === 'dollar-wrapped') {
                    // $key$ 格式
                    const placeholder = `$${key}$`;
                    modifiedXml = safeReplace(modifiedXml, placeholder, formattedValue);
                } else {
                    // 尝试所有格式
                    const placeholder1 = `\${${key}}`;
                    const placeholder2 = `{{${key}}}`;
                    const placeholder3 = `$${key}$`;
                    modifiedXml = safeReplace(modifiedXml, placeholder1, formattedValue);
                    modifiedXml = safeReplace(modifiedXml, placeholder2, formattedValue);
                    modifiedXml = safeReplace(modifiedXml, placeholder3, formattedValue);
                }
            }
        }
        
        // 不处理图片和表格，只替换简单文本占位符
        // 这样可以避免破坏文档结构
        
        // 更新document.xml
        console.log("正在更新document.xml...");
        zip.file("word/document.xml", modifiedXml);
        
        // 生成新的docx文件
        console.log("正在生成新的Word文档...");
        const outputArrayBuffer = await zip.generateAsync({
            type: "blob",
            mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            compression: "DEFLATE"
        });
        
        console.log("Word模板处理完成");
        return outputArrayBuffer;
        
    } catch (error) {
        console.error("处理Word模板时出错:", error);
        throw error;
    }
}

// 检测模板中的占位符格式
function detectPlaceholderFormat(xmlContent) {
    // 检查各种格式的占位符
    const curlyRegex = /{{([^}]+)}}/g;
    const dollarCurlyRegex = /\${([^}]+)}/g;
    const dollarWrappedRegex = /\$([^$]+)\$/g;
    
    // 计算每种格式的出现次数
    let curlyCount = (xmlContent.match(curlyRegex) || []).length;
    let dollarCurlyCount = (xmlContent.match(dollarCurlyRegex) || []).length;
    let dollarWrappedCount = (xmlContent.match(dollarWrappedRegex) || []).length;
    
    // 确定使用最多的格式
    if (curlyCount >= dollarCurlyCount && curlyCount >= dollarWrappedCount) {
        return { format: 'curly', count: curlyCount };
    } else if (dollarCurlyCount >= curlyCount && dollarCurlyCount >= dollarWrappedCount) {
        return { format: 'dollar-curly', count: dollarCurlyCount };
    } else {
        return { format: 'dollar-wrapped', count: dollarWrappedCount };
    }
}

// 安全替换XML中的占位符，确保不破坏XML结构
function safeReplace(xml, placeholder, value) {
    // 转义正则表达式中的特殊字符
    const escapedPlaceholder = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    
    // 在XML中查找占位符，确保它位于<w:t>标签内
    const regex = new RegExp(`(<w:t[^>]*>(?:(?!</w:t>).)*?)${escapedPlaceholder}((?:(?!</w:t>).)*?</w:t>)`, 'g');
    
    return xml.replace(regex, (match, prefix, suffix) => {
        return `${prefix}${value}${suffix}`;
    });
}

// 将函数暴露到全局作用域
window.processWordTemplate = processWordTemplate; 