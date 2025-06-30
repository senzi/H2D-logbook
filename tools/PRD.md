# PRD – H2D Logbook Local Manager (Flask 本地工具系统)

> Path: `h2d-logbook/tools/manager_flask`  
> One-line summary: *A localhost-only Flask app for editing and browsing YAML-based 3D printing logs.*

## 一、设计目标与角色定位

本工具是为拓竹 H2D 打印机使用记录所定制的**本地内容管理系统**，运行于用户本机，通过浏览器访问，支持所有 YAML 记录的新增、编辑、删除与 Git 发布，并包含一个基础的“记录浏览视图”。与线上前端相比，这里展示功能为辅助性质，偏重开发者预览与结构审视，而非最终视觉交互。

默认绑定 `127.0.0.1:5000`，确保仅本机可访问。运行期间，用户无需连网，不依赖数据库，也不需要部署任何前端构建工具。

## 二、主要功能

### 编辑功能

用户可浏览现有记录（自动按 type 分类），点击进入表单页面进行字段编辑，支持新增、保存、删除。表单字段通过前端 HTML 表单渲染，提交后由 Flask 校验结构并保存为 YAML 文件。

支持类型包括但不限于：

- 打印记录（record）
- 打印计划（plan）
- 耗材采购记录（consumable_purchase）
- 耗材退役记录（consumable_retirement）
- 维护记录（maintenance）

表单提交时将字段结构校验与 YAML 写入分离：若字段不合法（如 rating 超范围），会阻止写入并返回提示。写入过程采用 ruamel.yaml 保持字段顺序与注释，减少 diff 干扰。

每条记录保存为 `data/<type>/<id>.yml`，id 自动生成，格式为 `YYYYMMDD-keyword`。更新记录时，会在 YAML 顶部字段中刷新 `updated_at`。

### Git 发布

提供“发布”按钮，一键执行 Git 工作流（add → commit → push）。Git 命令通过 `subprocess.run` 触发。默认提交信息为：“update <id>”，未来可支持自定义。

如发布失败（例如 SSH key 问题），会保留在页面内报错输出，并不会中断记录写入流程。

### 本地预览功能

在 `/view` 路由下，提供记录浏览界面。该页面从本地 YAML 解析汇总的数据中读取记录并渲染为卡片式视图，字段布局仿照线上前端，以简洁为主。用户可以：

- 浏览记录内容（标题、打印模型、评分等）
- 使用基本筛选项（按 type / 时间）
- 使用搜索框进行关键词匹配（在标题 / model_url / 备注中模糊匹配）

此预览页面的主要目的是：不依赖 Vite 构建、不需要发布即可看到内容呈现效果，便于用户提前预览 Markdown 格式、字段命名一致性、内容逻辑合理性等问题。

## 三、技术结构

- 使用 Flask + Jinja2 模板系统进行渲染
- 所有记录文件读取均由 Python 后端完成，模板仅做数据展示，不含 JS 动态行为
- 页面样式使用 Bootstrap 5 或 Tailwind CDN，引入即用，避免前端打包
- 字段校验使用 jsonschema 或自定义 Python 规则（可拓展）

## 四、项目结构约定

项目目录如下所示：

```

tools/
└── manager\_flask/
├── app.py                 # Flask 入口
├── templates/
│   ├── list.html          # 条目列表页（编辑入口）
│   ├── edit.html          # 表单页
│   ├── view\.html          # 本地浏览页
├── static/                # 样式与 JS
├── schemas/               # 各记录类型的 JSON Schema
├── utils/
│   └── loader.py          # YAML 加载与写入封装
└── logs/app.log           # 日志文件

````

## 五、运行方式与部署约定

用户在本地执行：

```bash
cd tools/manager_flask
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
````

然后在浏览器访问：

* `http://localhost:5000/` → 管理界面（列表与编辑入口）
* `http://localhost:5000/view` → 简洁预览页面

无需数据库，无需云资源，默认数据根目录为 `../../data/`，可通过 `DATA_ROOT` 环境变量覆盖。

## 六、后续可能拓展功能

* 表单中支持字段模板复用（常用耗材、模型等快捷填入）
* 上传 STL 或截图文件并转存至某路径
* 构建并保存 HTML 静态页面文件（提供数据预览之外的初始前端草稿）
* 增加数据统计（打印时长、耗材品牌占比、历史评分分布）


