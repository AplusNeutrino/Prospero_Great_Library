# Prospero_Great_Library UI / Information Architecture 修正计划

> **Document type:** UI/IA Revision Plan / Implementation Prompt  
> **Project:** `Prospero_Great_Library`  
> **Target release:** `v0.1.0-alpha.4`（建议）  
> **Baseline:** `v0.1.0-alpha.3` privacy-hardened design  
> **Scope:** Library page information architecture, filtering/navigation, search, current activity, rating visualization, pagination, card density, Chirpy integration  
> **Out of scope:** Bangumi / NeoDB / Steam source semantics redesign, canonical entity schema redesign, privacy contract redesign  
> **Status:** Approved requirements translated into implementation plan  
> **Date:** 2026-08-18

---

# 0. 文档用途

本文件用于指导 `Prospero_Great_Library` 下一轮 UI / 信息架构重构。

后续开发者或 coding agent 在实现本轮修改前，必须同时阅读：

```text
PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md
本文件
当前仓库 IMPLEMENTATION_STATUS.md
当前仓库实际代码
```

若本文件与总架构文档不存在直接冲突，则本文件作为 **alpha.4 UI/IA 层的具体设计真源**。

本轮修改的目标不是单纯“把页面做漂亮”，而是解决当前 PGL 在真实大型个人藏品库下出现的以下问题：

```text
1. 页面标题缺乏站点归属感。
2. 所有状态混在同一浏览体系中，wishlist 干扰已品鉴记录。
3. Book / Game / Anime / Movie 等不同领域直接混排，信息结构过于平坦。
4. 当前评分分布只是数字 chip，不具备观察分布形态的能力。
5. Steam 累计排行占据页面空间但信息价值有限。
6. 当前进行中横向排列，阅读性差。
7. 搜索与多个下拉筛选堆在一起，视觉接近管理后台，不像个人图书馆。
8. Grid / List 都过度占用纵向与横向空间。
9. 60 条初始加载 + “加载更多”的交互不符合大型分类藏品的浏览习惯。
10. 当前 Library 页面与 Chirpy 主站已有的信息架构语言割裂。
```

---

# 1. 本轮锁定需求

以下要求视为 **LOCKED**，实现时不得自行修改语义。

---

## 1.1 页面名称

默认标题：

```text
[site.title]大图书馆
```

例如：

```text
site.title = 中间层
```

最终：

```text
中间层大图书馆
```

默认副标题：

```text
对曾经品鉴过的作品进行记录
```

标题与副标题都允许用户配置覆盖，但不配置时必须使用上述默认规则。

推荐配置：

```yaml
prospero_great_library:
  ui:
    title: null
    subtitle: null
```

解析：

```text
title == null
→ "#{site.title}大图书馆"

subtitle == null
→ locale 默认副标题
```

英文 locale 可使用：

```text
[Site Title] Great Library

A record of works once experienced and appreciated.
```

注意：

```text
Prospero Great Library
```

是插件名称，不应强制成为用户 Library 页面的公开标题。

---

# 2. 新的信息架构

## 2.1 不再存在“全部藏品混排页”

**LOCKED**

V1 当前的：

```text
/library/
↓
Book + Comic + Movie + Drama + Anime + Game + Music
全部卡片混排
```

必须取消。

新的 `/library/` 是 **Library Index / Dashboard**，而不是所有藏品的 flat feed。

---

## 2.2 `/library/` 默认结构

推荐页面顺序：

```text
┌─────────────────────────────────────────────────────────┐
│ [site.title]大图书馆                    [🔍 搜索藏品]   │
│ 对曾经品鉴过的作品进行记录                              │
└─────────────────────────────────────────────────────────┘

当前进行中
──────────────────────────────────────────────────────────
纵向活动条目
纵向活动条目
纵向活动条目
...

可观测评分分布图
──────────────────────────────────────────────────────────
                         ╭──────╮
                  ╭──────╯      ╰──╮
            ╭─────╯                ╰─
  ──────────╯
1    2    3    4    5    6    7    8    9    10

                                全域 游戏 动画 电影 ...

藏品分类
──────────────────────────────────────────────────────────
▸ 书籍                                   31 项
▸ 漫画                                   18 项
▸ 电影                                   45 项
▸ 剧集                                   12 项
▸ 动画                                   86 项
▸ 游戏                                  123 项
▸ 音乐                                    8 项

愿望单
──────────────────────────────────────────────────────────
计划品鉴                                 152 项

时间线
──────────────────────────────────────────────────────────
...
```

说明：

- 首页不显示跨类别 flat card feed。
- “当前进行中”允许跨类别，因为它是 **activity block**，不是藏品分类浏览结果。
- “可观测评分分布图”允许跨类别，因为它是统计模块。
- 真正的藏品浏览必须先进入一个分类。
- 愿望单单独进入，不混入默认藏品。

---

# 3. 默认状态模型的 UI 重新定义

Canonical status 不变：

```text
wishlist
in_progress
completed
on_hold
dropped
```

本轮只改变 **公开浏览逻辑与显示语言**。

---

## 3.1 默认分类浏览只包含

```text
in_progress
completed
```

默认排序必须：

```text
in_progress
↓
completed
```

也就是说即使默认主体语义是“已品鉴藏品”，只要某个分类里存在 `in_progress`，这些条目必须自动出现在 completed 前面。

推荐排序函数：

```python
STATUS_DISPLAY_RANK = {
    "in_progress": 0,
    "completed": 1,
}
```

同状态内部默认：

```text
canonical_updated_at DESC
```

如更新时间缺失：

```text
year DESC
→ title ASC
→ canonical_id ASC
```

最终稳定排序：

```text
status_rank
canonical_updated_at DESC
year DESC
title
id
```

---

## 3.2 Wishlist 完全脱离默认藏品浏览

`wishlist`：

```text
❌ 不出现在默认分类结果
❌ 不出现在 completed/in_progress 分页
✅ 进入独立「愿望单」
✅ 可以被全局搜索发现
```

---

## 3.3 Wishlist 的显示语言统一

不再根据媒介写：

```text
想看
想玩
想听
想读
```

统一显示：

```text
计划品鉴
```

机器值仍然是：

```text
wishlist
```

中文：

```yaml
statuses:
  wishlist: "计划品鉴"
```

英文建议：

```yaml
statuses:
  wishlist: "Planned"
```

不要改 canonical status enum。

---

## 3.4 `on_hold` 和 `dropped`

默认：

```text
❌ 不出现在分类页
❌ 不进入愿望单
❌ 不出现在默认首页藏品入口的记录数中
✅ 可被全局搜索发现
✅ 可通过“其他状态”高级入口查看
```

这属于“默认隐藏”，不是 Privacy hidden。

因此：

```text
on_hold / dropped
```

仍然存在于公开 `library.json`，除非 Privacy 配置另有规定。

---

# 4. 分类系统

## 4.1 七个一级分类继续固定

```text
Book
Comic
Movie
Drama
Anime
Game
Music
```

中文默认：

```text
书籍
漫画
电影
剧集
动画
游戏
音乐
```

分类 canonical schema 不修改。

---

## 4.2 视觉参考主站 Category Ledger

当前 My_Blog 的文章分类系统具有：

```text
一级索引
条目计数
简洁横向 ledger row
folder / chevron icon
分组边界
可展开语义
```

PGL 不应该复制 My_Blog 私有 CSS，而是借用其 **信息架构语言**。

推荐 PGL 新组件：

```text
pgl-category-ledger
pgl-category-ledger-item
pgl-category-ledger-primary
pgl-category-ledger-title
pgl-category-ledger-count
pgl-category-ledger-trigger
```

Universal Core 提供结构。

Chirpy Adapter 负责让这一结构在 Chirpy 上自然融入。

用户博客仍可通过自己的日夜主题 CSS 覆盖变量。

---

## 4.3 Category Index

首页：

```text
藏品分类
```

每个分类一行。

示意：

```text
┌──────────────────────────────────────────────┐
│ ▸ 游戏                              84 项   │
├──────────────────────────────────────────────┤
│ ▸ 动画                             126 项   │
├──────────────────────────────────────────────┤
│ ▸ 电影                              54 项   │
└──────────────────────────────────────────────┘
```

这里的数量：

```text
count(category where status in [in_progress, completed])
```

不包含：

```text
wishlist
on_hold
dropped
private
hidden
```

---

# 5. Category View

## 5.1 保持单 `/library/` 路由架构

为避免破坏既有：

```text
/library/
```

单入口设计，本轮不要求生成：

```text
/library/game/
/library/anime/
...
```

建议使用 query-state：

```text
/library/?category=game
/library/?category=anime
```

直接访问这些 URL 时，JS 初始化后应恢复对应 view。

---

## 5.2 Category View 页面结构

例如：

```text
← 返回藏品分类

游戏                                           [🔍 搜索]
84 项

[ Grid ] [ List ]

进行中（自动置顶）
────────────────────────────────────
卡片
卡片

已完成
────────────────────────────────────
卡片
卡片
卡片
...

‹ 1  2  3  4  …  7  ›
```

实际页面不一定必须渲染两个大标题：

```text
进行中
已完成
```

但排序语义必须达到：

```text
所有 in_progress
在所有 completed 前
```

推荐 UI：

- 用一个非常轻的 “进行中”分隔标签；
- completed 之后不需要每一项重复强调状态；
- 降低视觉噪声。

---

# 6. Pagination

## 6.1 固定 24 项 / 页

**LOCKED**

```text
PAGE_SIZE = 24
```

不再使用：

```text
初始 60
加载更多
```

作为主要分类浏览方式。

---

## 6.2 Pagination UI

参考 Chirpy / 主站已有分页语言：

```text
‹  1  2  3  4  5  …  12  ›
```

行为：

```text
当前页附近显示 2 个页码
首尾页始终可达
中间过长使用 …
上一页 / 下一页
```

---

## 6.3 URL

```text
/library/?category=game&page=1
/library/?category=game&page=2
```

切页必须：

```text
history.pushState()
```

这样：

- 浏览器 Back/Forward 正常；
- 可复制当前页面 URL；
- 页面不需要刷新；
- Jekyll 仍然只有一个静态入口。

---

## 6.4 切换分类时

必须重置：

```text
page = 1
```

---

## 6.5 Search 时

搜索结果也可以分页：

```text
/library/?q=final+fantasy&page=2
```

但搜索结果不是永久“全部藏品页”。

---

# 7. 愿望单设计

## 7.1 独立一级入口

首页分类 ledger 下方提供：

```text
愿望单
计划品鉴 xxx 项
```

视觉上与 7 个媒体分类区分，但保持同一设计语言。

---

## 7.2 愿望单中仍禁止七类混成一个 flat feed

进入：

```text
/library/?view=wishlist
```

先显示：

```text
愿望单

书籍       30
漫画       12
电影       21
剧集        8
动画       34
游戏       43
音乐        4
```

再点击：

```text
/library/?view=wishlist&category=game
```

显示该领域 24 项/页。

这样同时满足：

```text
Wishlist 是独立区域
+
媒体类型不混排
```

---

## 7.3 愿望单卡片

Wishlist 本身已经表明状态，因此卡片不要重复大号：

```text
计划品鉴
```

推荐：

- status badge 可以小型化；
- 或仅 Drawer 内显示；
- 如果显示，统一为 `计划品鉴`。

---

# 8. 其他状态入口

## 8.1 不抢占主导航

`on_hold` / `dropped` 不做与 Wishlist 同级的大入口。

Category View 可提供一个低权重按钮：

```text
其他状态
```

展开：

```text
搁置
已放弃
```

或放在：

```text
···
```

菜单内。

---

## 8.2 Query contract

```text
/library/?category=game&status=on_hold
/library/?category=game&status=dropped
```

全局搜索依然可以搜索到这些条目。

---

# 9. Global Library Search

## 9.1 位置

**LOCKED**

搜索框从当前 filters block 中移除。

新位置：

```text
Library Header 右上角
```

桌面：

```text
中间层大图书馆                 [ 🔍 搜索藏品________ ]
对曾经品鉴过的作品进行记录
```

---

## 9.2 Universal 设计约束

不要修改 Chirpy 全局 topbar。

PGL 搜索只存在于：

```text
#prospero-great-library
```

内部。

这样：

- 不侵入主题；
- 仍可模仿 Chirpy 搜索风格；
- 其他 Jekyll theme adapter 可复用。

---

## 9.3 Desktop

默认显示短输入框：

```text
🔍 搜索藏品
```

focus：

- 边框/底色采用 PGL theme variables；
- 宽度平滑扩展；
- 风格接近主站文章搜索框；
- 不做大型独立搜索控制面板。

---

## 9.4 Mobile

默认：

```text
🔍
```

点击：

```text
标题区域下方/内部展开搜索输入框
```

再次点击关闭，若 query 非空则保留。

---

## 9.5 搜索范围

**LOCKED**

默认搜索：

```text
全部 7 个 Category
+
wishlist
+
on_hold
+
dropped
+
in_progress
+
completed
```

前提：

```text
item 不是 privacy hidden/private
```

搜索字段：

```text
title
title_original
alternate_titles
year
tags
category localized label
source names
```

---

## 9.6 Search Results 不建立“全部藏品”入口

虽然搜索跨类别，但结果页面是：

```text
Search Results
```

不是：

```text
All Collection
```

推荐将结果按 Category 分组渲染：

```text
游戏（3）
...
...

动画（2）
...
...

书籍（1）
...
```

若结果超过 24：

- 24 条一页；
- 每页内部继续按分类标题分组。

---

# 10. 当前进行中

## 10.1 当前问题

当前实现：

```text
最多 8 项
横向 button list
仅 status=in_progress
```

需要整体废弃。

---

## 10.2 新候选规则

**LOCKED**

全部 `in_progress`：

```text
必须进入
```

另外允许：

```text
Steam recent activity
```

即使 canonical status 不是 `in_progress`，也可以进入。

推荐候选：

```python
is_current =
    item.status == "in_progress"
    OR
    (
        item.category == "game"
        AND steam.recent_playtime_minutes > 0
    )
```

Steam `GetRecentlyPlayedGames` 本身反映近期游玩，因此不需要自行发明完成状态。

---

## 10.3 去重

如果：

```text
Game status=in_progress
+
Steam recent_playtime>0
```

只显示一次。

---

## 10.4 排序

推荐：

```text
1. explicit in_progress
2. Steam recent-only
```

各层内部：

```text
last activity / canonical update DESC
```

---

## 10.5 全部显示

取消：

```liquid
limit: 8
```

**LOCKED**

所有 current candidates 均显示。

---

## 10.6 新视觉

使用纵向 compact rows。

示意：

```text
┌──────┐  BanG Dream! YUME∞MITA
│      │  动画 · 进行中
│ cover│  8 / 13 集
│      │  █████████████░░ 61%
└──────┘  ★ 7.0 · 最近更新 2026-08-06

┌──────┐  FINAL FANTASY XIV
│      │  游戏 · 最近游玩
│ cover│  Steam 最近活动
│      │  累计 2,014 h
└──────┘  最近游玩 2026-08-18
```

---

## 10.7 阅读性

桌面端：

```text
1 column
```

不要横向 masonry。

行高目标：

```text
约 88–120 px
```

而不是大型 poster cards。

移动端：

```text
仍然 1 column
缩小 cover
```

---

# 11. 可观测评分分布图

## 11.1 模块名称

**LOCKED**

```text
可观测评分分布图
```

英文：

```text
Observable Rating Distribution
```

---

## 11.2 数据范围

默认统计：

```text
public
AND rating != null
AND status in [in_progress, completed]
```

明确排除：

```text
rating == null
wishlist
on_hold
dropped
privacy hidden/private
```

这样图表与默认“已品鉴 + 进行中”浏览语义一致。

未来可通过配置扩展 scope，但 alpha.4 不增加复杂选项。

---

## 11.3 分箱

推荐内部：

```text
0.5 分一档
```

例如：

```text
0.5
1.0
1.5
...
9.5
10.0
```

若实际 source 只提供整数分：

- 半分档自然为 0；
- 不伪造数据。

---

## 11.4 平滑方式

**LOCKED**

图表展示为平滑曲线，但不能通过 KDE 等方式让用户误以为出现了不存在的评分观测。

因此采用：

```text
真实离散频数点
+
视觉路径平滑
```

推荐：

```text
monotone cubic interpolation
```

而不是：

```text
kernel density estimate
```

Tooltip 仍显示真实 bin：

```text
评分 8.0
34 项
```

---

## 11.5 图表实现

不引入 Chart.js / ECharts / React。

推荐：

```text
Vanilla JS + inline SVG
```

构成：

```text
SVG
├── x axis
├── optional light y guides
├── smoothed path
├── point interaction layer
└── tooltip
```

优点：

```text
零新前端框架
轻量
响应式
可用 CSS variables
易于日夜主题覆盖
```

---

## 11.6 快速领域切换

右下角：

```text
全域  游戏  动画  电影  书籍  漫画  剧集  音乐
```

不要使用 select dropdown。

推荐 compact segmented control。

桌面：

```text
右下角横向
```

手机：

```text
横向 scrollable chips
```

切换只重绘 curve。

---

## 11.7 数据结构

当前：

```json
"rating_distribution": {
  "7": 12,
  "8": 23
}
```

建议升级为：

```json
{
  "rating_distribution": {
    "bin_size": 0.5,
    "bins": [
      0.5, 1.0, 1.5, 2.0, 2.5,
      3.0, 3.5, 4.0, 4.5, 5.0,
      5.5, 6.0, 6.5, 7.0, 7.5,
      8.0, 8.5, 9.0, 9.5, 10.0
    ],
    "scopes": {
      "all":   [0,0,0,0,0,1,0,2,1,4,3,5,8,12,15,21,10,8,3,1],
      "game":  [...],
      "anime": [...],
      "movie": [...],
      "book":  [...],
      "comic": [...],
      "drama": [...],
      "music": [...]
    }
  }
}
```

如果需要保持 backward compatibility：

```text
保留旧 rating_distribution 一版
+
新增 rating_curve_distribution
```

或升级 stats schema version。

更推荐：

```text
stats_schema_version += 1
```

并在 JS 同时兼容旧格式一个版本周期。

---

# 12. Steam 排行处理

## 12.1 删除 UI

**LOCKED**

删除当前：

```text
Steam 累计游玩排行
```

`<details>`。

---

## 12.2 不必删除 backend 数据

为了：

- schema backward compatibility；
- API consumers；
- 未来其他 UI；
- Debug；

可以继续计算：

```text
stats.steam.ranking
```

只是默认 UI 不渲染。

这样本轮无需破坏 canonical/statistics contract。

---

# 13. Header / Hero 重构

新增：

```text
pgl-header
pgl-heading-block
pgl-title
pgl-subtitle
pgl-header-search
```

Desktop：

```text
display: flex
justify-content: space-between
align-items: flex-start
```

Mobile：

```text
title + search icon
subtitle
expanded search
```

---

# 14. 移除旧 Filters 控制板

当前：

```text
search
category select
status select
source select
year select
sort select
grid/list button
```

是一组典型“数据库控制栏”。

本轮需要拆解。

---

## 14.1 Category

由：

```text
select
```

改成：

```text
Category Ledger navigation
```

---

## 14.2 Status

由：

```text
select
```

改为信息架构：

```text
默认 = in_progress + completed
wishlist = 独立入口
on_hold / dropped = 其他状态
```

---

## 14.3 Search

移至 Header。

---

## 14.4 Source

不再作为主 UI 控件。

Source 应属于：

```text
Advanced Filters
```

需要时打开。

---

## 14.5 Year

不再占主控制栏。

归入：

```text
Advanced Filters
```

---

## 14.6 Sort

Category View 保留轻量 sort control。

推荐：

```text
最近更新
评分
年份
标题
Steam时长（Game only）
```

但不要和 5 个 dropdown 横排。

可实现为：

```text
排序：最近更新 ▾
```

一个 compact menu。

---

## 14.7 Grid/List

保留。

放在 Category header 右侧：

```text
[▦] [☷]
```

不要继续使用大文字 button。

---

# 15. Grid 模式压缩

## 15.1 当前问题

当前 Grid 卡片视觉层级过多：

```text
大封面
category
performance
title
original title
year
status
rating
Steam time
progress
source badges
article badge
```

对大型藏品库浏览来说过重。

---

## 15.2 新 Grid card

目标：

```text
更像“library catalogue”
而不是“大型推荐卡片”
```

推荐：

```text
card min width: 138–156 px
cover max visual width: ~140 px
cover aspect ratio: 2 / 3
```

CSS：

```css
grid-template-columns:
  repeat(auto-fill, minmax(138px, 1fr));
```

实际可根据 Chirpy content width 调至：

```text
140–165 px
```

但应以“同屏更多记录”为目标。

---

## 15.3 Grid 默认字段

直接显示：

```text
Cover
Title
Year
Status（必要时）
Rating
Progress（若存在）
```

弱化或移至 Drawer：

```text
Source badges
Original title
Steam detailed telemetry
Article count
All alternate titles
```

Game 可保留一个很小的：

```text
Steam 120h
```

但不能让 metadata 行无限增长。

---

# 16. List 模式压缩

推荐：

```text
Thumbnail: 56–72 px width
```

结构：

```text
[cover] Title
        Year · Status · ★ 8.5
        progress / Steam activity
```

桌面每项目标：

```text
76–96 px
```

移动：

```text
68–88 px
```

列表应更接近主站文章索引的纵向阅读节奏。

---

# 17. Grid/List 状态记忆

继续保留：

```text
grid
list
```

默认由配置：

```yaml
ui:
  layout: grid
```

用户切换后：

```text
localStorage:
pgl.layout = grid|list
```

不需要写入 URL。

---

# 18. Card Interaction

Drawer 继续保留。

点击：

```text
card
→ drawer
```

不要因为压缩 card 而丢失：

```text
source links
full metadata
Steam telemetry
blog associations
history excerpt
```

这些信息更适合 Drawer。

---

# 19. URL / View State Contract

推荐统一 controller state：

```js
{
  view: "index" | "category" | "wishlist" | "other" | "search",
  category: null | "book" | ...,
  status: null | "on_hold" | "dropped",
  query: "",
  page: 1,
  sort: "updated",
  layout: "grid"
}
```

Query examples：

```text
/library/
```

```text
/library/?category=game
```

```text
/library/?category=game&page=2
```

```text
/library/?view=wishlist
```

```text
/library/?view=wishlist&category=anime&page=3
```

```text
/library/?category=game&status=on_hold
```

```text
/library/?q=final+fantasy
```

避免：

```text
/library/?category=all
```

因为本轮明确取消 All Collection view。

---

# 20. Browser Navigation

所有 UI navigation：

```text
category
wishlist
page
search
other status
```

必须更新 History API。

要求：

```text
Back
Forward
复制链接
刷新
```

都能恢复 view。

`popstate` 必须有测试。

---

# 21. Search 与 Category 状态交互

从 Category 页面点击 Header Search：

```text
默认搜索全部 Category
```

不是：

```text
只搜索当前 category
```

如果未来需要当前 category 搜索，可以作为 optional scope，但不是 alpha.4 默认。

Search close：

```text
回到进入 Search 前的 view
```

或者：

```text
/library/
```

建议保存 previous state，提升体验。

---

# 22. 当前首页统计信息

现有顶部：

```text
总条目
Steam lifetime
本年 observed Steam
```

可以保留，但应进一步弱化为小型 summary。

推荐：

```text
记录总量
已品鉴
正在进行
```

Steam 数字不一定要继续占最顶层。

但用户本轮只明确要求：

```text
删 Steam累计游玩排行折叠
```

因此 alpha.4 最低实现：

```text
保留 summary metrics
删除 ranking details
```

若后续再做 dashboard 视觉升级，再改变指标构成。

---

# 23. Timeline

Timeline 继续存在。

本轮不修改 History event semantics。

位置建议：

```text
Category Ledger / Wishlist 后
```

不要插在 Category 浏览卡片之间。

Category view 下 Timeline 可不重复展示。

---

# 24. 响应式设计

## Desktop >= 992px

```text
Header title left
Search right

Current: one-column compact list

Rating chart: full width
Category ledger: full width

Grid: 4–6 compact columns depending container
List: one column
```

---

## Tablet 576–991px

```text
Header search narrower
Current one column
Chart control scroll if needed
Grid 3–4 columns
```

---

## Mobile < 576px

```text
Title + search icon
Subtitle

Search expands full row

Current list:
small thumbnail

Rating chart:
full width SVG
category selector horizontal scroll

Category ledger:
full width rows

Grid:
2 compact columns

List:
thumbnail 56–64px
```

---

# 25. Theme Contract

不要把 My_Blog 的具体色值写入 PGL Core。

新增/扩展：

```css
--pgl-header-text
--pgl-subtitle
--pgl-control-bg
--pgl-control-border
--pgl-ledger-hover
--pgl-chart-line
--pgl-chart-grid
--pgl-chart-point
--pgl-current-bg
--pgl-pagination-active
```

已有：

```css
--pgl-bg
--pgl-surface
--pgl-border
--pgl-text
--pgl-muted
--pgl-heading
--pgl-accent
...
```

继续作为 base。

---

# 26. Chirpy Adapter 策略

Chirpy Adapter 参考：

```text
主站 categories ledger 的信息层次
主站搜索框的 compact search language
Chirpy pagination language
```

但：

```text
不要复制整个 My_Blog layout
不要覆盖 Chirpy topbar
不要硬编码“中间层”
不要依赖 My_Blog 私有 CSS class
```

用户自己的博客可以在：

```text
NormaiNight.css
ProsperoLight.css
或独立 PGL override
```

继续覆盖。

---

# 27. 数据层需要增加的派生信息

Canonical `library.json` 不需要破坏性修改。

主要变化放在：

```text
stats.json
```

以及前端 selector。

推荐新增：

```json
{
  "navigation": {
    "default_by_category": {
      "book": 0,
      "comic": 0,
      "movie": 0,
      "drama": 0,
      "anime": 0,
      "game": 0,
      "music": 0
    },
    "wishlist_by_category": {
      "...": 0
    },
    "other_status_by_category": {
      "on_hold": {},
      "dropped": {}
    }
  }
}
```

作用：

- Root ledger 无需浏览器扫描上千条 item 才显示计数；
- Jekyll/Liquid 可 SSR category ledger；
- no-JS 情况下首页仍然有意义。

---

# 28. Current Activity 派生

推荐在 Python stats 阶段生成：

```json
{
  "current_activity": [
    {
      "entity_id": "...",
      "reason": "in_progress"
    },
    {
      "entity_id": "...",
      "reason": "steam_recent"
    }
  ]
}
```

而不是每次前端自行重新判断。

优点：

```text
规则集中
更容易测试
Liquid SSR
减少 JS 分歧
```

---

# 29. No-JS behavior

虽然分类详情使用 client state，但无 JS 时 `/library/` 至少必须展示：

```text
标题
副标题
Current summary/list
评分静态 fallback summary
分类 Ledger
Wishlist count
```

可以在：

```text
<noscript>
```

中提示：

```text
启用 JavaScript 以浏览分类分页和搜索。
```

不再需要为了 no-JS 强行预渲染 60 张大型混排卡片。

这是比当前实现更符合新 IA 的降级行为。

---

# 30. Accessibility

Header search：

```text
role=search
proper label
Escape closes mobile expanded search
```

Category ledger：

```text
button/link semantics
aria-current for selected category
```

Pagination：

```text
<nav aria-label="Library pagination">
aria-current="page"
```

Rating chart：

SVG 提供：

```text
aria-label
<desc>
```

并在图表下提供 screen-reader table / textual summary：

```text
8.0: 24 项
8.5: 19 项
...
```

Current rows：

- row button 或 link；
- 不要整块 `<div>` 模拟按钮。

---

# 31. 性能目标

真实个人库可能数百至上千条。

因此：

```text
Root:
不渲染全部 cards

Category:
只渲染当前 24 项

Wishlist category:
只渲染当前 24 项

Search:
只渲染当前 page
```

不要像当前模式：

```text
Liquid SSR 60
+
JS 继续扩 DOM
```

新的 controller 应：

```text
library.json
→ filter
→ sort
→ slice(page)
→ render 24
```

---

# 32. 前端数据索引

页面初始化时构建：

```js
Map<entityId, item>
category buckets
status buckets
normalized search strings
```

这样每次：

```text
切换页
切分类
切 layout
```

不重新遍历/normalize 全部字符串。

---

# 33. 文件级修改计划

## `jekyll/_includes/pgl/library.html`

重构为：

```text
header
current
rating-chart
category-ledger
view-container
pagination
timeline
drawer
```

移除：

```text
旧 flat pgl-grid 初始渲染
limit:60
旧 filters 作为主入口
```

---

## `jekyll/_includes/pgl/filters.html`

建议废弃为旧组件，或重构成：

```text
advanced-filters.html
sort-and-layout.html
```

不再承载 Search / Category / Status 主导航。

---

## 新增建议

```text
jekyll/_includes/pgl/header.html
jekyll/_includes/pgl/category-ledger.html
jekyll/_includes/pgl/current.html
jekyll/_includes/pgl/rating-chart.html
jekyll/_includes/pgl/pagination.html
jekyll/_includes/pgl/view-toolbar.html
```

---

## `jekyll/_includes/pgl/stats.html`

删除：

```text
rating chips details
Steam ranking details
```

拆分：

```text
summary metrics
```

评分图交给独立 `rating-chart.html`。

---

## `jekyll/_includes/pgl/card.html`

创建更紧凑 markup。

推荐支持：

```text
variant=grid
variant=list
```

或者仅输出统一语义结构，由 CSS layout 控制。

避免两套数据逻辑。

---

## `jekyll/assets/pgl/pgl.js`

建议重构为模块化 section：

```js
state
router
search
category navigation
wishlist navigation
pagination
sorting
layout
current interaction
rating chart
drawer
timeline
```

如果继续单文件，至少用内部 functions 清晰分区。

---

## `jekyll/assets/pgl/pgl.css`

重点：

```text
Header
Search
Ledger
Current list
Chart
Compact Grid
Compact List
Pagination
Mobile
```

---

## `pgl/history/stats.py`

新增：

```text
rating curve bins by category
navigation counts
current activity candidates
```

不修改 event semantics。

---

## `pgl/output/jekyll.py`

确保：

```text
new stats fields
public JSON
```

正确同步。

---

## locales

```text
jekyll/locales/zh-CN.yml
jekyll/locales/en.yml
pgl/resources/chirpy/locales/*
demo/site/_data/pgl_locales/*
```

新增/修改：

```text
great_library_suffix
subtitle
planned
wishlist
observable_rating_distribution
all_domains
other_status
back_to_categories
search_results
recent_play
pagination labels
```

---

# 34. Resource Mirror

PGL 当前存在：

```text
jekyll/
pgl/resources/chirpy/
demo/site/
```

多份 mirrored resources。

实现后必须运行：

```text
scripts/sync_chirpy_resources.py
```

并通过：

```text
test_resource_mirror
```

不能只修改其中一份。

---

# 35. Configuration 增量

建议：

```yaml
prospero_great_library:
  ui:
    title: null
    subtitle: null

    page_size: 24

    layout: grid
    allow_grid_list_toggle: true

    default_statuses:
      - in_progress
      - completed

    wishlist:
      enabled: true

    other_statuses:
      enabled: true
      expose_in_primary_navigation: false

    current:
      enabled: true
      include_all_in_progress: true
      include_steam_recent: true

    rating_chart:
      enabled: true
      bin_size: 0.5

    search:
      enabled: true
      global_scope: true
```

默认值必须符合本文件要求。

---

# 36. Backward Compatibility

## 36.1 旧配置

现有：

```yaml
ui:
  layout:
  lazy_render:
  show_stats:
  show_timeline:
  show_sources:
  show_steam_playtime:
  show_achievements:
```

处理：

```text
layout                      保留
show_timeline               保留
show_sources                保留但主要影响 Drawer
show_steam_playtime         保留
show_achievements           保留
lazy_render                 deprecated
```

`lazy_render`：

- alpha.4 可继续读取；
- 但分类分页 controller 已取代旧的“加载更多”语义；
- 发出 deprecation note，不必立即删除。

---

## 36.2 Old URLs

当前已有：

```text
/library/?type=game
```

如果历史版本支持，应在 router 中兼容：

```text
type
→ category
```

并：

```text
replaceState()
```

到新格式。

---

# 37. UI 行为摘要

## Root

```text
不显示藏品 flat feed
```

---

## Category

```text
in_progress first
completed second
24/page
```

---

## Wishlist

```text
独立入口
先选 category
24/page
```

---

## On Hold / Dropped

```text
默认隐藏
search / advanced state 可见
```

---

## Search

```text
全局
全 Category
全公开 status
按 Category 分组
```

---

# 38. 测试计划

至少新增以下自动测试。

---

## Title

```text
site.title="中间层"
→ 中间层大图书馆

explicit ui.title
→ override works
```

---

## Subtitle

```text
default zh-CN
→ 对曾经品鉴过的作品进行记录
```

---

## Default visibility

Fixture：

```text
completed
in_progress
wishlist
on_hold
dropped
```

Category default：

```text
只返回 in_progress + completed
```

---

## Ordering

输入：

```text
completed newer date
in_progress older date
```

输出仍必须：

```text
in_progress first
completed second
```

---

## Wishlist

```text
不出现在 default
出现在 wishlist
label == 计划品鉴
```

---

## Hidden states

```text
on_hold
dropped
```

不出现在 default/wishlist。

但 global search 可以找到。

---

## Category isolation

```text
Game view
```

绝不能出现 Anime / Movie 等。

---

## No All Collection

主导航中不存在：

```text
全部藏品
All Collection
```

---

## Pagination

```text
25 items
page_size=24
```

结果：

```text
page 1 = 24
page 2 = 1
```

---

## Query restore

```text
?category=game&page=2
```

初始化后保持正确状态。

---

## Popstate

Back/Forward：

```text
category -> page2 -> wishlist -> back
```

恢复正确。

---

## Rating distribution

无评分：

```text
excluded
```

Wishlist：

```text
excluded
```

On hold/dropped：

```text
excluded
```

Category switch：

```text
game curve != anime curve
```

---

## Chart bins

评分：

```text
8
8.5
9
```

必须进入真实 bin。

平滑只影响 path，不修改 count。

---

## Steam ranking

HTML 中不再出现：

```text
pgl-ranking
steam_top_games
```

默认 UI。

---

## Current

包含：

```text
all in_progress
+
steam recent-only
```

无 8 条 limit。

---

## Current duplicate

```text
in_progress + steam recent
```

只出现一次。

---

## Search

搜索：

```text
Final Fantasy
```

应跨 Category / status 搜索公开 item。

---

## Compact layout contract

CSS 检查：

```text
grid min card target
list thumbnail target
mobile two-column grid
```

---

# 39. Demo 数据更新

Demo 必须新增足够 fixture 验证：

```text
>24 个同分类 item
```

用于 pagination。

另外确保：

```text
completed
in_progress
wishlist
on_hold
dropped
unrated
rated
Steam recent but completed
```

均存在。

---

# 40. Acceptance Criteria

alpha.4 UI/IA revision 完成必须满足：

```text
[ ] 页面默认标题自动成为 “[site.title]大图书馆”
[ ] 显示副标题“对曾经品鉴过的作品进行记录”
[ ] Root 不再混排七类藏品
[ ] Root 使用 Category Ledger
[ ] 默认 Category 只显示 in_progress + completed
[ ] in_progress 永远位于 completed 前
[ ] Wishlist 完全脱离 default browse
[ ] Wishlist 中文统一为“计划品鉴”
[ ] on_hold/dropped 默认隐藏
[ ] on_hold/dropped 可通过 Search/Advanced 状态访问
[ ] 不存在 All Collection 浏览入口
[ ] Global Search 可跨全部 Category
[ ] Search 移到 Library Header 右上角
[ ] Mobile Search 可展开/收起
[ ] Category 一页 24 项
[ ] 分页替代“加载更多”
[ ] URL 可表达 Category/Page/Search/Wishlist state
[ ] Browser Back/Forward 正常
[ ] Current 改为纵向 compact list
[ ] Current 不再 limit 8
[ ] Steam recent-only Game 可进入 Current
[ ] Current 去重
[ ] 评分模块名称为“可观测评分分布图”
[ ] 无评分 item 不进入评分统计
[ ] Wishlist/on_hold/dropped 不进入默认评分图
[ ] 评分图为 SVG 平滑真实频数曲线
[ ] 可快速切换全域与七个领域
[ ] 删除 Steam累计游玩排行折叠 UI
[ ] Grid 明显更紧凑
[ ] List 明显更紧凑
[ ] Grid/List 双模式保留
[ ] Drawer 保留完整信息
[ ] zh-CN / en locale 完整
[ ] Personal Blog theme override 不进入 Universal Core
[ ] Privacy contract 不回退
[ ] Existing Entity/History semantics 不回退
```

---

# 41. 推荐实施顺序

## Phase A — State / data preparation

```text
navigation counts
rating curve stats
current activity candidates
pagination helpers
```

先做数据，不改 UI。

---

## Phase B — Router

实现：

```text
view state
query parsing
pushState
popstate
pagination
```

先有可靠行为，再画 UI。

---

## Phase C — Root IA

实现：

```text
Header
Search
Current vertical list
Rating chart
Category Ledger
Wishlist entry
```

---

## Phase D — Category / Wishlist

实现：

```text
category isolation
default status ordering
24/page
wishlist category index
other status
```

---

## Phase E — Compact cards

实现：

```text
Grid
List
Drawer integration
layout memory
```

---

## Phase F — Responsive / Chirpy

实现：

```text
Desktop
Tablet
Mobile
Light
Dark
```

---

## Phase G — Tests / Demo / migration

```text
fixtures >24
router tests
stats tests
resource mirror
Chirpy build
README screenshots/demo
```

---

# 42. 建议版本定位

本轮属于明显的 UI / Information Architecture overhaul。

但：

```text
canonical schema
source adapters
history
privacy
```

都没有 major break。

因此推荐：

```text
v0.1.0-alpha.4
```

而不是：

```text
v0.2.0
```

等 UI 稳定、真实 Chirpy runtime 与真实个人库验证完成，再考虑进入 beta。

---

# 43. 不应在本轮顺带做的事情

不要因为重构 UI 同时加入：

```text
新媒体 source
写回 Bangumi
写回 NeoDB
新的 canonical categories
item detail pages
React
Vue
Chart.js
server backend
```

本轮必须专注：

```text
Large-library usability
+
Information Architecture
+
Chirpy visual integration
```

---

# 44. 对当前代码的核心替换关系

```text
CURRENT
─────────────────────────────
filters.html
├ search
├ category select
├ status select
├ source select
├ year select
├ sort
└ layout

flat pgl-grid
└ 60 items + load more

stats
├ chips rating
└ Steam top ranking

current
└ horizontal buttons limit 8
```

变为：

```text
ALPHA.4
─────────────────────────────
header
└ global search

current
└ vertical activity ledger

observable rating chart
└ SVG + domain switch

category ledger
├ Book
├ Comic
├ Movie
├ Drama
├ Anime
├ Game
└ Music

wishlist
└ category ledger

category view
├ compact toolbar
├ 24 cards
└ pagination

advanced
├ on_hold
├ dropped
├ source
└ year

drawer
└ full detail
```

---

# 45. 最终视觉目标

PGL 不应该再像：

```text
“把 API 数据塞进一组卡片，再加几个 dropdown”
```

而应该表现成：

```text
一个真正的个人收藏索引
```

视觉关键词：

```text
Library
Catalogue
Ledger
Archive
Compact
Readable
Classified
Personal
Static
```

对 Chirpy 用户来说，它应该看起来像：

> “这个站点原本就有一个大图书馆模块。”

而不是：

> “网页里嵌了另一个第三方 Dashboard。”

---

# 46. Future Coding Agent Prompt

实现本计划时：

```text
1. 读取 PROSPERO_GREAT_LIBRARY_ARCHITECTURE.md。
2. 读取本 UI 修正计划。
3. 读取当前 main 实际代码，不使用旧 ZIP 作为假定基线。
4. 先检查 privacy hardening 是否仍完整。
5. 不修改 canonical status enum。
6. 不修改七类互斥规则。
7. 不改变 Bangumi-first source precedence。
8. 先实现 stats/state，再实现视觉。
9. Default category browse 只允许 in_progress + completed。
10. 无论更新时间如何，in_progress 必须排在 completed 前。
11. Wishlist 的公开中文统一为“计划品鉴”。
12. 不创建 All Collection 入口。
13. Search 是唯一默认跨七类检索入口。
14. Search 结果按 Category 分组。
15. Category page 固定 24/page。
16. Rating curve 只平滑路径，不伪造 rating observations。
17. 无评分作品完全排除。
18. 删除 Steam ranking UI，但不要无必要破坏统计 schema。
19. Current 不限制 8 条。
20. Current 允许 Steam recent-only Game。
21. Grid/List 都必须明显压缩。
22. Universal PGL 不复制 My_Blog 私有配色。
23. 同步 jekyll / resources / demo mirrors。
24. 添加对应 regression tests。
25. 完成后区分 fixture PASS、CI PASS、真实 Chirpy runtime PASS。
```

---

# 47. 一句话目标

> **将 Prospero_Great_Library 从“带筛选器的混排媒体卡片页”，重构成一个以分类索引、愿望单、活动记录、可观测评分分布和高密度分页藏品为核心的真正 Personal Great Library，同时保持 Jekyll 静态、Chirpy 兼容与 Universal 插件属性。**
