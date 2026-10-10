# 出海招标雷达

按行业、采购方所在地、服务目标区域检索跨境法律与咨询服务采购信息。支持关键词搜索、来源证据筛选、截止状态、排序、浏览器收藏、分享筛选链接、CSV 导出和手机阅读。

## 数据

`data/tenders.json` 为公告发布数据源，`data/sources.json` 为29个渠道及检索词矩阵。首期观察窗口为 2026-07-10 至 2026-10-10；25 条收录（22 条采购、招募及前期询价，3 条采购结果），5 条待核验线索。公开网络检索样本不代表全网完整覆盖。官方来源、转载、信息不完整分别标注。未知字段保持未知；不把发行规模写成预算、不把采购所在地推定成服务国别。

`meta.updatedAt` 仅在完成真实检索与核验后更新。`nextPlannedUpdate` 为计划日期，未按期完成时页面自动显示逾期提示。截止状态按北京时间计算；只披露日期时注明时刻待核验。报名与响应截止是不同时间，请阅读原公告。

## 更新机制

通过当前 Codex 聊天的每 5 天自动任务执行：多搜索引擎与官方源检索、读取公告、去重、证据核验、更新 JSON 并发布到本仓库。任务在本机 Codex 中运行，依赖本机可运行状态、网络和 GitHub 连接；不是 GitHub Actions 内置联网检索。GitHub 连接器已发现对新仓库写入返回 403，已有 Git SSH 认证完成首次发布；后续任务优先使用 git@github.com:cricket119/crossborder-tender-radar.git 克隆最新 main，再提交并推送数据。提交身份使用 cricket119 / 256142090+cricket119@users.noreply.github.com。GitHub Pages 在 main 分支提交后自动重新发布。失败不伪造最近更新时间，通知用户处理。

更新时按当地日期向前取三个日历月，将旧公告移入 `data/archive/`，滚动窗口保留相关采购、结果与变更（同一项目标包关联，不重复统计）。摘要来源与核验日期随条目记录，待核验线索独立展示。

## 本机预览及校验

```sh
python3 -m http.server 8765 --bind 127.0.0.1
python3 scripts/validate.py
node --check app.js
```

GitHub Pages：Settings → Pages → Deploy from a branch → main / root。

## 文件边界

只有本项目目录里的网站文件与公开信息上传；不读取或发布父目录里的个人材料或凭据。纯静态网站，无登录、无跟踪服务、无付费依赖。收藏仅存于访问者当前浏览器。

## 扩源与采集

详见 [采集逻辑与公开来源研究](docs/collection-method.md)。来源登记不等于全站完整覆盖。地图中的“已读取”仅指本轮或首轮读到栏目或具体详情；动态空壳、超时、405和会员遮蔽均保留真实状态。

每次更新先读取 sources.json，使用 scripts/discover.py --plan 生成“渠道域名 × 专项检索词”矩阵。对 crawl=true 的渠道运行低频公开栏目发现；按三个月窗口继续翻页、全文关键词检索与反查原文。仅列表标题无法覆盖正文中的涉外需求，不能将爬虫零候选当作无采购。列出本轮检索渠道、查询词、读取失败与新增情况，更新来源核验日期。

```sh
python3 scripts/discover.py --plan
python3 scripts/discover.py --source exim --source nbgodo
python3 scripts/discover.py --input output/tinyfish-html.json
```

脚本只发现候选链接，三组词（跨境、服务、采购）均匹配才候选入队。robots限制或读取失败会记录并跳过。动态页使用 TinyFish fetch_content 批量读取（每批≤10个URL），必要时用浏览器公开页面；PDF用文档读取工具。英文渠道需以英文检索并核验具体采购范围，脚本的中文列表规则不覆盖全部国际机会。不得绕过登录、付费或验证码；不自动订购付费爬虫任务。

output/ 是本地临时采集记录，不上传完整转载正文或个人资料。候选必须人工/代理核验采购人、公告日、响应与报名日期、币种、标包以及变更后才能进入 tenders.json；待核验留 leads。results 独立展示，不标成尚可报名的采购。仅披露结果日期时按结果披露日计入窗口。
