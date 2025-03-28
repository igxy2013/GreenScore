// 加载器相关函数
let loaderTimeout;

function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'flex';
    }
}

function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'none';
    }
    if (loaderTimeout) {
        clearTimeout(loaderTimeout);
    }
}

// 设置自动隐藏超时
function setLoaderTimeout(duration = 30000) {
    if (loaderTimeout) {
        clearTimeout(loaderTimeout);
    }
    loaderTimeout = setTimeout(hideLoader, duration);
}