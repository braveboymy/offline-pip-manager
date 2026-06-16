# 离线 Pip 包管理器

一个基于 CustomTkinter 的桌面 GUI 工具，用于在有网络的电脑上下载 Python 包及其依赖，然后迁移到无法联网的电脑上进行离线安装。

## 功能

| 功能 | 说明 |
|------|------|
| **包下载** | 搜索 PyPI 包 → 选择版本 → 一键下载包及所有传递依赖 |
| **自动换源** | 内置 6 个国内镜像源，下载失败自动按优先级切换（清华 → 阿里云 → 中科大 → 豆瓣 → 华为云 → 官方） |
| **本地包管理** | 查看已下载的包列表（名称/版本/大小/日期），支持检查更新、删除旧版本 |
| **离线安装** | 指定本地包目录和目标 Python 环境，勾选后一键安装，无需联网 |
| **源管理** | 增删镜像源、启用/禁用、拖拽排序优先级、测试连接状态 |

## 界面预览

```
┌─────────────────────────────────────────────┐
│  Tab: 下载 │ 本地包管理 │ 离线安装 │ 源管理   │
├─────────────────────────────────────────────┤
│                                             │
│   [当前活跃面板内容区]                        │
│                                             │
├─────────────────────────────────────────────┤
│  状态栏：当前存储目录 │ 包数量 │ 上次刷新      │
└─────────────────────────────────────────────┘
```

### 四个 Tab

1. **下载** — 搜索包名 → 选择版本 → 下载 + 实时日志和进度
2. **本地包管理** — 列表展示，绿/橙色标识更新状态，批量删除
3. **离线安装** — 选择本地目录 + 指定 Python → 勾选安装
4. **源管理** — 6 个预置镜像源，可自由增删排序

## 运行环境

- **操作系统**: Windows
- **Python**: 3.10+
- **依赖**: customtkinter, packaging（自动安装）

## 快速开始

```bash
# 1. 安装依赖
uv pip install -r offline_pip_manager/requirements.txt
# 或者
pip install -r offline_pip_manager/requirements.txt

# 2. 启动
cd offline_pip_manager
python main.py
```

## 典型使用流程

### 联网端（下载）

1. 打开「源管理」→ 确认镜像源可用
2. 打开「下载」→ 搜索包名 → 选版本 → 点击「下载包及所有依赖」
3. 所有 .whl 文件保存到 `offline_packages/` 目录

### 离线端（安装）

1. 将整个 `offline_pip_manager` 文件夹拷贝到离线电脑
2. 打开「离线安装」→ 指定包目录和 Python 路径
3. 勾选需要的包 → 点击「安装选中的包」

## 打包为单文件 EXE

```bash
pip install pyinstaller
cd offline_pip_manager
python build.py
# 输出: dist/离线pip包管理器.exe
```

打包后的 exe 可直接拷贝运行，无需安装 Python。

## 项目结构

```
offline_pip_manager/
├── main.py                  # 入口
├── app.py                   # 主窗口
├── config.json              # 配置（镜像源列表等）
├── build.py                 # PyInstaller 打包脚本
├── requirements.txt
├── offline_packages/        # 默认包存储目录
├── core/
│   ├── source_manager.py    # 镜像源增删查改 + 连接测试
│   ├── package_index.py     # 本地 wheel 文件扫描
│   ├── downloader.py        # pip download 封装 + 自动换源
│   ├── installer.py         # pip install --no-index 封装
│   └── checker.py           # PyPI JSON API 版本检查
└── ui/
    ├── download_tab.py      # 下载面板
    ├── local_tab.py         # 本地包管理面板
    ├── install_tab.py       # 离线安装面板
    └── source_tab.py        # 源管理面板
```

## 预置镜像源

| 序号 | 名称 | URL | 默认 |
|------|------|-----|------|
| 1 | 清华 | https://pypi.tuna.tsinghua.edu.cn/simple | ✓ |
| 2 | 阿里云 | https://mirrors.aliyun.com/pypi/simple | ✓ |
| 3 | 中科大 | https://pypi.mirrors.ustc.edu.cn/simple | ✓ |
| 4 | 豆瓣 | https://pypi.douban.com/simple | |
| 5 | 华为云 | https://repo.huaweicloud.com/repository/pypi/simple | |
| 6 | PyPI 官方 | https://pypi.org/simple | ✓ |

## License

MIT
