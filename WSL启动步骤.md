# WSL 启动步骤

打开 PowerShell:

1. 输入 `cd c:\GreenScore`
2. 输入 `wsl`，一般情况可忽略第 3 步
3. MySQL 服务会自动启动。检查状态：`sudo service mysql status`
   - 如果未运行，手动启动：`sudo service mysql start`

## 创建虚拟环境

```bash
python3 -m venv venv
```

## 激活虚拟环境

```bash
source venv/bin/activate
```

## 在激活的虚拟环境中安装 Gunicorn

```bash
pip install gunicorn
```

## 验证安装

```bash
gunicorn --version
```

## 进入 GreenScore 目录

```bash
cd /mnt/c/GreenScore
```

## 安装依赖

```bash
python3 -m pip install -r requirements.txt
```

## 用国内源安装依赖

```bash
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple
```

## WSL 中服务器启动顺序

1. 先运行 gunicorn

   ```bash
   python start.py
   ```

2. 再启动 Nginx

   ```bash
   sudo systemctl start nginx
   ```

## 查看 WSL IP 地址

在 WSL 终端运行：

```bash
hostname -I
```

## 映射 WSL 端口到主机端口

在 PowerShell 中运行：

```powershell
$wslIp = (wsl -e hostname -I).Trim()
netsh interface portproxy add v4tov4 listenport=5050 listenaddress=0.0.0.0 connectport=5050 connectaddress=$wslIp
``` 