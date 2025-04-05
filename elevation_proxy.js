const express = require('express');
const fetch = require('node-fetch');
const app = express();
const port = 3000;

// 允许跨域请求
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE");
    res.header("Access-Control-Allow-Headers", "Content-Type");
    next();
});

// 设置代理请求
app.get('/getElevation', async (req, res) => {
    const { lat, lng } = req.query;

    if (!lat || !lng) {
        return res.status(400).json({ error: '缺少必要的参数' });
    }

    // 构建请求 URL
    const url = `https://api.opentopodata.org/v1/aster30m?locations=${lat},${lng}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.results && data.results[0]) {
            res.json({
                elevation: data.results[0].elevation,
                status: 'success'
            });
        } else {
            throw new Error('无效的海拔数据');
        }
    } catch (error) {
        console.error("请求海拔数据时发生错误:", error);
        res.status(500).json({ error: '无法获取海拔数据' });
    }
});

// 启动服务器
app.listen(port, () => {
    console.log(`海拔数据代理服务器正在运行，端口：${port}`);
});