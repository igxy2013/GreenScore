// 测试模板占位符脚本
async function checkTemplateFormat() {
    try {
        console.log("开始检查模板格式...");
        
        // 获取模板文件
        const templateUrl = '/static/templates/公共交通站点分析报告.docx';
        const response = await fetch(templateUrl);
        if (!response.ok) {
            console.error("获取模板文件失败:", response.status, response.statusText);
            throw new Error(`获取模板文件失败: ${response.status} ${response.statusText}`);
        }
        
        // 读取模板文件
        const templateArrayBuffer = await response.arrayBuffer();
        
        // 创建ZIP实例
        const zip = new JSZip();
        
        // 加载docx文件
        await zip.loadAsync(templateArrayBuffer);
        
        // 读取document.xml
        const documentXmlFile = zip.file("word/document.xml");
        if (!documentXmlFile) {
            throw new Error("无法在Word文档中找到document.xml");
        }
        const documentXml = await documentXmlFile.async("string");
        
        // 输出XML内容以检查占位符格式
        console.log("文档XML内容片段:");
        console.log(documentXml.substring(0, 5000)); // 只显示前5000个字符
        
        // 查找所有可能的占位符
        const placeholderRegex1 = /\${([^}]+)}/g; // ${xxx} 格式
        const placeholderRegex2 = /{{([^}]+)}}/g; // {{xxx}} 格式
        
        let match;
        console.log("查找${xxx}格式的占位符:");
        const placeholders1 = [];
        while ((match = placeholderRegex1.exec(documentXml)) !== null) {
            placeholders1.push(match[0]);
        }
        console.log(placeholders1);
        
        console.log("查找{{xxx}}格式的占位符:");
        const placeholders2 = [];
        while ((match = placeholderRegex2.exec(documentXml)) !== null) {
            placeholders2.push(match[0]);
        }
        console.log(placeholders2);
        
        // 查找表格行标记
        const tableRowRegex = /<w:tr[^>]*>(?:(?!<w:tr|<\/w:tbl>).)*?\${station\.[^}]+}.*?<\/w:tr>/gs;
        const tableRowMatches = documentXml.match(tableRowRegex);
        console.log("表格行标记:", tableRowMatches);
        
        console.log("检查完成");
    } catch (error) {
        console.error("检查模板格式时出错:", error);
    }
}

// 暴露测试函数
window.checkTemplateFormat = checkTemplateFormat; 