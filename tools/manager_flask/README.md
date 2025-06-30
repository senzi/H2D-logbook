# H2D Logbook Local Manager

一个基于 Flask 的本地 3D 打印记录管理系统，用于管理拓竹 H2D 打印机的使用记录。

## 功能特性

- **记录管理**: 支持打印记录、打印计划、耗材采购、耗材退役、维护记录等多种类型
- **本地运行**: 仅在本机运行，无需网络连接，数据安全可控
- **YAML 存储**: 使用 YAML 格式存储数据，便于版本控制和手动编辑
- **Git 集成**: 一键发布到 Git 仓库，支持版本管理和备份
- **数据验证**: 使用 JSON Schema 验证数据完整性
- **预览功能**: 提供简洁的记录浏览界面

## 安装和运行

### 1. 环境准备

确保已安装 Python 3.7 或更高版本。

### 2. 安装依赖

```bash
cd tools/manager_flask
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 运行应用

```bash
python app.py
```

应用将在 `http://127.0.0.1:5000` 启动。

### 4. 访问界面

- **管理界面**: `http://localhost:5000/` - 记录的增删改查
- **预览界面**: `http://localhost:5000/view` - 记录的浏览和搜索

## 目录结构

```
manager_flask/
├── app.py                 # Flask 应用主文件
├── requirements.txt       # Python 依赖
├── README.md             # 说明文档
├── templates/            # HTML 模板
│   ├── list.html         # 记录列表页
│   ├── edit.html         # 编辑页面
│   └── view.html         # 预览页面
├── static/               # 静态文件 (CSS/JS)
├── schemas/              # JSON Schema 验证文件
│   ├── record.json       # 打印记录 schema
│   ├── plan.json         # 打印计划 schema
│   ├── consumable_purchase.json
│   ├── consumable_retirement.json
│   └── maintenance.json
├── utils/
│   └── loader.py         # YAML 加载和处理工具
└── logs/
    └── app.log           # 应用日志
```

## 支持的记录类型

### 1. 打印记录 (record)
- 标题、模型名称、模型链接
- 评分 (1-5)
- 打印时长、层高、填充率
- 材料、支撑使用情况
- 打印成功状态

### 2. 打印计划 (plan)
- 计划标题、模型信息
- 优先级 (高/中/低)
- 预计时长

### 3. 耗材采购记录 (consumable_purchase)
- 耗材名称、品牌
- 数量、单价
- 购买日期、供应商

### 4. 耗材退役记录 (consumable_retirement)
- 耗材名称、退役日期
- 退役原因 (用完/过期/损坏/质量问题)
- 使用时长

### 5. 维护记录 (maintenance)
- 维护标题、日期
- 维护类型 (清洁/校准/维修/升级)
- 维护部件、时长、成本

## 数据存储

数据默认存储在 `../../data/` 目录下，按记录类型分类：

```
data/
├── record/               # 打印记录
├── plan/                 # 打印计划
├── consumable_purchase/  # 耗材采购
├── consumable_retirement/ # 耗材退役
└── maintenance/          # 维护记录
```

每条记录保存为独立的 YAML 文件，文件名格式为 `YYYYMMDD-keyword.yml`。

## 环境变量

- `DATA_ROOT`: 数据根目录路径，默认为 `../../data`

## Git 集成

点击"发布到 Git"按钮可以执行以下操作：
1. `git add .` - 添加所有更改
2. `git commit -m "Update records - 时间戳"` - 提交更改
3. `git push` - 推送到远程仓库

确保已配置好 Git 仓库和 SSH 密钥。

## 开发说明

### 添加新的记录类型

1. 在 `app.py` 的 `RECORD_TYPES` 中添加新类型
2. 在 `schemas/` 目录下创建对应的 JSON Schema 文件
3. 在 `templates/edit.html` 中添加对应的表单字段
4. 在 `templates/view.html` 中添加对应的显示逻辑

### 自定义样式

静态文件放在 `static/` 目录下，可以添加自定义 CSS 和 JavaScript。

## 故障排除

### 常见问题

1. **端口被占用**: 修改 `app.py` 中的端口号
2. **数据目录不存在**: 应用会自动创建必要的目录
3. **Git 发布失败**: 检查 Git 配置和网络连接
4. **依赖安装失败**: 确保 Python 版本兼容

### 日志查看

应用日志保存在 `logs/app.log` 文件中，可以查看详细的错误信息。

## 许可证

本项目遵循 MIT 许可证。
