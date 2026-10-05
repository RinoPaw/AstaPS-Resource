# Genshin 7.1 养成曲线与资源经济研究 handoff

更新时间：2026-10-05
仓库：`RinoPaw/AstaPS-Resource`
目标版本：Genshin Impact 7.1.0 Global

## 目标

1. 尽量完整确认原神 7.1 原生养成曲线、资源需求和掉落经济。
2. 为私服、模拟、研究保留完整原版 7.1 数据。
3. 在原版数值之上设计“降低网游感”的 RPG 养成方案。
4. 数值优先使用当前 `AstaPS-Resource` 的原生 ExcelBin。
5. 游戏规则、时间限制、树脂规则优先使用 HoYoverse 官方资料。
6. 原生或官方资料缺失时再使用 Wiki/KQM/同类项目，并标注证据等级。
7. 当前阶段只研究和设计，不修改 AstaPS 产品代码。

## 设计原则

先保留原版 RPG 数值曲线，再单独移除现实时间门槛。

优先考虑移除：
- Original Resin 领奖门槛
- 每日限制
- 每周限制
- 星期轮换材料秘境
- 其他依赖现实时间的刷新或领取限制

暂不默认移除：
- 角色、武器、天赋升级成本
- Mora / EXP 消耗
- Boss / Domain / Ley Line 的战斗与掉落循环
- 圣遗物本身的成长与随机性

目标体验是单机/RPG 化，不是沙盒式 `/give`。

## 证据等级

- A：当前 7.1 ExcelBin / HoYoverse 官方资料
- B：AstaPS 或同类模拟器实现，且与原版行为一致
- C：Wiki、KQM、社区资料或合理推断

所有最终基线表应带证据等级。

## 已确认的重要结果

### 树脂规则

HoYoverse 官方 4.7 更新说明确认：
- Original Resin 上限从 160 提升到 200。

来源：
- https://www.hoyolab.com/article/29513513

在 7.1 之前的官方更新中，Condensed Resin 机制已经调整：
- 制作 1 个 Condensed Resin 消耗 60 Original Resin。
- 可用于最多 3 倍奖励领取。
- 对原本消耗 20 Original Resin 的领取界面：
  - 可直接消耗 40 Original Resin 领取 2 倍奖励；
  - 可使用 Primogems 快速补充 Original Resin 并最多领取 3 倍奖励；
  - Condensed Resin 为 0 时可使用 Transient Resin / Fragile Resin。

来源：
- https://genshin.hoyoverse.com/en/news/detail/159349

7.1 官方更新说明：
- Version 7.1 “Ein Requiem für die Unterwelt”
- 发布日期：2026-09-23
- https://genshin.hoyoverse.com/de/news/detail/166383

当前没有发现 7.1 将上述树脂改动回退的证据，但仍需继续检查 7.1 以及其前一版本至 7.1 之间所有官方更新中的 Resin / Condensed Resin / Trounce Domain 条目。

注意：
- 不再把旧版“Condensed Resin = 40 Resin、双倍奖励”当作 7.1 基线。
- “8 分钟恢复 1 点树脂”当前只有社区层面的已知证据，本项目还需要官方或 7.1 原生数据确认。
- 旧版 Condensed Resin 持有上限 5 也不能直接当作 7.1 结论，需要复核新版机制。

### 圣遗物

此前已确认/高可信结果：
- 5 星圣遗物从 +0 到 +20 的基础强化 EXP 总需求：270,475。
- AstaPS / 同类实现中，圣遗物强化 Mora 成本约等于 1 Mora / 1 点强化 EXP。
- 强化经验暴击倍率概率约为：90% ×1、9% ×2、1% ×5。
- 副词条选择为加权抽取、不放回，并排除与主词条冲突的属性组。

这些结论后续仍需在最终基线表里逐项绑定到 7.1 `Reliquary*ExcelConfigData` 或当前实现文件，避免只依赖旧审计结论。

## 已定位的 7.1 ExcelBin 文件

仓库中已定位：
- `ExcelBinOutput/AvatarCurveExcelConfigData.json`
- `ExcelBinOutput/AvatarPromoteExcelConfigData.json`
- `ExcelBinOutput/WeaponPromoteExcelConfigData.json`
- `ExcelBinOutput/ProudSkillExcelConfigData.json`

还需要继续定位/提取：
- `WeaponCurveExcelConfigData.json`
- `ReliquaryLevelExcelConfigData.json`
- `ReliquaryAffixExcelConfigData.json`
- `ReliquaryMainPropExcelConfigData.json`
- 角色经验素材对应的 Material 配置
- Boss / Ley Line / Domain reward/drop 相关表
- 世界等级与奖励档位相关表

`WeaponPromoteExcelConfigData.json` 曾有一次 GitHub connector 返回空内容。下一轮必须确认它是真空文件、接口截断，还是读取方式问题，不能据此认为数据不存在。

## 当前正在做、尚未完成的工作

本轮开始追两条链，但在保存 handoff 前尚未完成最终提取：

1. 角色经验书 / 升级 Mora 规则
   - 目标：确认各经验素材的 `id`、单个提供 EXP、使用规则，以及角色升级过程中 EXP→Mora 的换算规则。
   - 已尝试从 Material 配置中搜索 `104001`、`MATERIAL_EXP`、`ITEM_USE_ADD_AVATAR_EXP`、`20000` 等字段。
   - 尚未形成可引用的最终结果，下一轮应重新从对应 Material ExcelBin 精确提取。

2. 角色 → `avatarPromoteId` → 突破材料
   - 目标：建立可复用映射，将角色配置连接到 `AvatarPromoteExcelConfigData`，得到每个突破阶段的材料 ID、数量、Mora、等级门槛等。
   - 当前仍处于定位阶段，尚未生成完整映射表。

不要把这两块当作已经完成。

## 下一轮优先级

### P0：完成角色 1→90 原生基线

需要从 `AvatarCurveExcelConfigData.json`、`AvatarPromoteExcelConfigData.json`、角色配置和 Material 表中得到：
- 每级所需角色 EXP
- 1→90 总 EXP
- 各次突破等级门槛
- 各阶段 Mora
- 宝石材料 ID / 数量
- 世界 Boss 材料 ID / 数量
- 地方特产 ID / 数量
- 普通敌人材料 ID / 数量
- 经验书种类及单本 EXP
- 角色升级 Mora 规则
- 一个 5 星角色 1→90 的总 Mora、总 EXP、总材料

最好生成“角色无关的通用曲线 + 每角色材料映射”两层数据，避免为每个角色复制相同曲线。

### P0：完成天赋 1→10

使用 `ProudSkillExcelConfigData.json` 以及角色 skill depot / proud skill group 映射：
- 每级 Mora
- 普通敌人材料
- 天赋书
- 周本材料
- Crown of Insight
- 单技能 1→10 总成本
- 3 个战斗天赋 1/1/1→10/10/10 总成本

需要注意角色特殊天赋或等级异常，不能只假设所有角色完全共用一条表。

### P1：武器 1→90

提取：
- `WeaponCurveExcelConfigData`
- `WeaponPromoteExcelConfigData`
- 各星级 EXP 曲线
- 突破 Mora 和材料
- 3/4/5 星武器分别的 1→90 总成本

### P1：圣遗物完整原生随机模型

继续绑定到 7.1 原始表：
- 主词条成长曲线
- 初始 3/4 副词条概率
- 副词条权重
- 每次 roll 的档位权重
- 强化 EXP
- ×2 / ×5 强化暴击
- Mora
- 套装 / 部位 / 主词条掉落关系

### P1：掉落经济

定位并提取：
- Ley Line：Mora / Character EXP materials
- 普通 Domain
- Artifact Domain
- Normal Boss
- Weekly Boss / Trounce Domain
- 世界等级 / 秘境等级对应奖励档位

在能得到原版均值后，计算：
- 角色 1→90 需要多少次 Ley Line / Boss 领取
- 天赋 10/10/10 需要多少次 Domain / Weekly Boss
- 5 星武器 1→90 需要多少次 Domain
- 原版按 Resin 限制需要的理论自然恢复时间
- 移除 Resin 后的纯战斗次数

## AstaPS 实现审计：后续再做

研究数值基线后，再回到 `RinoPaw/AstaPS` 最新 `play/rino` 审计真正的限制点。

开始前必须重新 fetch 并确认 `origin/play/rino`，不要沿用旧 SHA。

需要分别定位：
- Original Resin 领取扣除
- Condensed Resin 多倍领取
- Weekly Boss 领取次数 / 折扣次数
- Domain 星期开放限制
- Boss respawn / reward respawn
- 每日 / 每周刷新
- Resin item 使用逻辑

最终应把这些门槛拆成独立开关，不要用一个“无限树脂”选项混掉所有时间机制。

## RPG 化方案当前方向

建议的第一版规则：

- 角色/武器/天赋/圣遗物的原版数值曲线保持不变。
- Resin 不再作为领奖资格门槛。
- 战斗完成一次，按原版基础档领取一次奖励。
- 不默认提供无限多倍领取；多倍机制需要单独设计，避免战斗本身失去意义。
- Weekly Boss 取消现实周领取限制，但保留 Boss 难度和原版掉落结构。
- 星期材料秘境全周开放。
- 现实时间刷新限制逐项移除。
- Resin 客户端 UI 可以先保留；服务器端可忽略其领奖 gating。是否同步显示满值以后再决定。

后续在拿到原版完整掉落均值后，再判断是否需要调整数量。不要提前凭感觉砍材料需求。

## 最终应形成的成果

1. `7.1-native-progression-baseline`
   - 角色 / 武器 / 天赋 / 圣遗物原版数值
2. `7.1-native-drop-economy`
   - Boss / Domain / Ley Line 原版掉落
3. `7.1-time-gates`
   - Resin / daily / weekly / weekday / respawn 等现实时间门槛
4. `rpg-progression-proposal`
   - 原版曲线 → 去时间门槛后的 RPG 方案
5. 最终矩阵建议列：
   - 系统
   - 原版 7.1 数值
   - 原版时间门槛
   - RPG 版本
   - 证据等级
   - 数据来源 / 文件

## 注意事项

- 旧版 Wiki 数字不能覆盖 7.1 ExcelBin。
- 同类私服实现只能做 B 级交叉验证，不能反向定义原版。
- 官方版本更新可能修改长期沿用的常识，Condensed Resin 已经是实际例子。
- 任何“当前版本规则”都应检查时间顺序，优先使用 7.1 前最近一次官方改动。
- 当前阶段不要修改 AstaPS 产品代码。
