<div align="center"><a href="README.md">English</a> | <strong>中文</strong></div>

EasyPass 是一款基于 Flask + SQLite 的本地密码管理器，采用“国家 -> 公司 -> 网站/应用 -> 账户”的层级结构组织数据。

## 从源码启动

### 推荐方式：双击 `start.bat`

1. 安装 Python 3.9 或更高版本，安装时勾选 `Add Python to PATH`。
2. 进入仓库根目录，双击 `start.bat`。
3. 脚本会自动查找本机 Python。
4. 脚本会把依赖安装到项目本地的 `libs/` 目录。
5. 启动成功后，浏览器会自动打开 `http://127.0.0.1:5000`。

### 命令行启动

如果你更习惯手动执行命令，可以在仓库根目录运行：

```powershell
python -m pip install -r requirements.txt -t libs
python -m src.app
```

说明：

- `requirements.txt` 只包含运行时依赖。
- 依赖会安装到项目本地的 `libs/` 目录，不会写入全局 Python 环境。
- 如果你的电脑没有安装 Python，上述命令将无法执行，需要先安装 Python。

### 不要直接双击 `src/app.py`

请使用 `start.bat` 或 `python -m src.app` 启动，不建议直接运行 `src/app.py` 文件。

## 首次运行会生成

- `data/passwords.db`：主数据库
- `data/flask_secret.key`：Flask 密钥文件
- `data/archive/`：归档数据
- `libs/`：本地依赖缓存

## 常用脚本

- `start.bat`：启动程序并自动处理依赖
- `reset_and_start.bat`：清理主数据库后重新启动
- `package_release.bat`：打包发布版本
- `scripts/maintenance/publish_release.ps1`：发布打包逻辑

打包需要当前 Python 环境中已安装 `PyInstaller`。如果没有，请先执行 `python -m pip install pyinstaller`。

## 发布流程

1. 确认已安装 Python 3.9+，并且可在 PATH 中直接调用。
2. 确认当前 Python 环境中已经安装 `PyInstaller`。
3. 在仓库根目录执行 `package_release.bat`。
4. 脚本会生成 `dist/EasyPass.exe`，并使用 `build/` 作为临时目录。
5. 对外发布时，直接分发生成的 `EasyPass.exe` 即可。

## 目录概览

- `src/`：源代码
- `data/`：运行时数据
- `libs/`：本地依赖缓存
- `scripts/`：维护脚本和发布脚本

## 打包版运行

如果你拿到的是打包后的版本，通常只需要直接运行生成的 `EasyPass.exe`，不需要额外安装 Python。

如果你之前用过旧版打包程序，EasyPass 首次启动时会自动把已有数据复制到新的应用数据目录中。
