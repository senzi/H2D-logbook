# PRD – H2D Logbook (前端展示子系统)

> Repository: **h2d-logbook**  
> One-line summary: *A Vue-powered public site that visualises structured usage records for the H2D 3-D printer.*

## 1. 目标与范围  
本子系统面向公网访问者，仅承担“读取静态 JSON、以交互式界面展示流水账”的职责。所有写操作都发生在本地 Flask 工具中，这里只做只读渲染。站点需支持筛选、模糊搜索、时间跨度滚动以及设备友好布局；同时保持 7×24 小时无数据库、无后端依赖、可被任何 CDN 缓存。

## 2. 数据契约  
构建阶段由脚本把位于 `/data/` 目录下的若干 YAML 文件汇聚成统一的 `public/data.json`。约定所有实体都遵循同一个最小元模型，核心字段包括：  
- `id`（雪花 ID 或文件名去扩展名后的 slug，用作路由）  
- `type`（record | plan | consumable_purchase | consumable_retirement | maintenance）  
- `created_at` 与 `updated_at`（ISO 8601 时间字符串）  
- `payload`（一个嵌套对象，其内部结构依据 type 决定）  

以打印记录（type = record）为例，payload 中包含：`printer`、`model_title`、`model_url`、`slicer_profile`、`print_time_sec`、`filament_brand`、`material`、`color`、`nozzle_temp`、`bed_temp`、`rating`、`review` 以及 `notes`。字段含义一律在本文件稍后章节给出精确定义。其他类型亦同理。借助这种外层统一、内层分型的模式，前端只需先做一次 `switch (type) { … }` 便可调度对应的渲染组件。

### 2.1 示例 YAML（打印记录）  
```yaml
id: 20250629-benchmark-test
type: record
created_at: 2025-06-29T10:23:11Z
updated_at: 2025-06-29T10:25:44Z
payload:
  printer: H2D
  model_title: XYZ Calibration Cube
  model_url: https://makerworld.com/models/xyz-cube
  slicer_profile: 0.2mm-quality
  print_time_sec: 7200
  filament_brand: eSUN
  material: PLA+
  color: Marble White
  nozzle_temp: 205
  bed_temp: 60
  rating: 4.0
  review: >-
    首层稍微翘边。调高热床 5°C 后可改善。
  notes: null
````

### 2.2 字段语义详解

为避免大段列表打断阅读，下文采用段落式说明。所有记录共享的 `id` 必须在全站唯一，推荐由“日期-短横线-关键词”构成（如 `20250629-benchmark-test`），以保证可读也可排序。`created_at` 记录条目首次生成时间，不随修改而改变；`updated_at` 在每次保存时自动刷新。`type` 决定了 payload 的结构。对于打印记录而言，`printer` 是字符串枚举，目前唯一合法值是 “H2D”，但兼容未来机型；`model_title` 与 `model_url` 均为字符串，其中 URL 用于外链跳转；`slicer_profile` 与 `print_time_sec` 分别表示切片配置名称与整件打印秒数；`filament_brand`、`material`、`color` 概念自明，用于日后做耗材统计。对耗材采购条目而言，payload 中会出现 `spool_uid`（与打印记录的 filament 字段关联）、`purchase_price_cny`、`vendor`、`weight_g` 与可选的 `batch_no`；耗材退役记录则以 `spool_uid` 为外键，补充 `retirement_date` 与 `reason`。维护条目在 payload 内保留 `action`, `cost`, `duration_min` 等字段，支持后续对维修费用和停机时间做聚合分析。

## 3. 构建流程

脚本 `tools/generate_json.py` 逐文件解析 YAML，将其转换为统一数据表后写入 `public/data.json`。构建过程在本地亦可执行，但在 Cloudflare Pages 的 CI 中会被再次调用，以保证远端数据始终同步。`vite.config.ts` 里不做 SSR，仅走纯静态输出。

## 4. 前端渲染策略

Vue3 + `<script setup>` 语法胜任本项目。首页挂载后通过 `fetch('/data.json')` 获取全集，再利用 MiniSearch 建立索引。搜索框输入即刻在客户端做模糊匹配，筛选按钮触发 computed 重新过滤，避免额外网络往返。详情页使用 Vue Router 动态路由，通过 `/entry/:id` 读取同一份 JSON 中的对应对象，减少碎片化请求。站点样式可用 Tailwind，或保留最小自写 CSS。

## 5. 性能与质量门槛

完整打包内容（含 data.json）在初始化渲染时不超过 1 MB，首屏 Largest Contentful Paint 不得高于 1.5 s（4G 移动网络参考点）。搜索与筛选在一万条数据以内需保持亚百毫秒级响应。代码需通过 ESLint + Prettier 检查；Pull Request 需跑 `npm run build && npm run lint` 两步 CI 均通过方可合并。


