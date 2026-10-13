# P2WLAN 网络核心最终分析、实施计划与交接

本文件是 2026-10-13 的可移植交接快照，替代旧报告中已经过时的交付数字。仓库：https://github.com/yhan-sun/p2wlan 。原分析日期 2026-10-09，原审查基准 ef81fc006a500e4f9a16f2b90da89cc1eaf1f566。实现事实以当前源码、提交及对应测试为准。原附加材料中的建议、历史输出和操作示例都需要核验。

## 一、采纳结论及原分析的修正

选择性采纳：立即补可信业务基线、失败归因、身份和版本绑定；复用现有 NAT、路径 reducer、Relay、profiling、DPLPMTUD。架构改造和默认参数变化由复现与同负载 A/B 结果触发。

| 原分析的不足 | 修正后的决策 |
|---|---|
| 建议新增 NatTraversalPlanner | 已有 plan_traversal、TraversalPlan 和 runtime 准入。补输入→计划→实际执行→真实业务的映射与缺口，保持唯一权威状态所有者。 |
| 将 WireGuard-like 视作官方 WireGuard 兼容 | 协议、开销、重放窗口和互操作以本仓库实现为准。现有实现不声明官方互操作。 |
| 混合普通 socket pool 与 hh2 专用 socket | 普通 pool 默认关闭，运行时 1–4；hh2 桌面 2/4/8、Android 2/4 属于另一实验。保持平台 cap、进程上限、总预算和截止。 |
| 认为 NAT 测量隔离、发送账本、学习和 fencing 都需重建 | 已存在相关机制。定位具体漏点，区分过期、限流、预算、未发送、发送不确定；未知保持 unknown。 |
| 从队列上限或计时器直接推断 Minecraft 卡顿 | 统计 channel、pending、in-flight 与单次发送的实际驻留和总资源；区分应用 MSPT/GC、外部拥塞、TCP/MTU、本机处理。 |
| 将采样 P99 当全量业务 P99 | 当前 1/64 采样、最近最多 512 样本与累计 sample_count 口径不同。附真实窗口、样本数、限频和开销；阶段 P99 不相加。 |
| 把 TUN 拆分当已经证实的性能修复 | 两项具体取消/活锁正确性已修复；RX/TX 解耦仍需等待证据、平台语义、关闭/重建/取消和 A/B。 |
| 公平队列可能重排已加密报文 | 调度只在明文层进行，保持流内顺序及加密→发送序列化；不确定密文不得换路径重放。 |
| 将 PMTU 与预算闭环全部列为新建 | 已有 business_mtu、DPLPMTUD 与 fencing。补真实 OS/TCP、切路、黑洞、EMSGSIZE/PTB、预算变化验收。 |
| 将初始 Direct-first 窗口当全部打洞截止 | 首次业务、Direct 持续争取和单次 hh2 截止分别统计；先验证现有 auto/score/direct-sticky/direct-first。 |
| 重建恢复和跨区域 Relay 选择 | 复用 generation、session、owner、make-before-break 与已有重选机制；补精确恢复和双方协调迁移。 |
| 根据无 ACK、空闲或单尖峰判网络失活 | 分 Transport/Overlay/Dataplane/Application，先做只读 shadow 观测，避免把本机排队或应用停顿当路径故障。 |
| 同时上 UDP Relay、Peer Relay、TCP 打洞、GSO/GRO、多链路 | 分别立项。以需求、瓶颈、协议和资源/取消验收决定采用或有证据的不采纳。 |
| 对比竞品后直接宣称性能更好 | 仅借鉴机制。没有同拓扑、版本、负载与样本，不给打洞率、延迟或安全性排名。 |
| 缺依赖、失败保留和完成条件 | 使用原 22 项 ID、任务级验收、分批 CI 与实际提交/合并绑定；局部测试不升级为整体完成。 |

## 二、交付快照

产品实施已发布 24 批：第 1–18 批和第 23 批共 19 批已普通合并，5 批待合并。交接分支属于资料检查点，不增加这 24 个产品批次的完成数。

快照 remote main：4937de2de8e8b91492fe3d6e8bd83d5c51faa9ad。当前 #202 已发布源码 HEAD：d2df1627952191fe3d535d64ad6249723e1ba404，树 2c59d0916db053cc4bf9edfb298708c264215d4b。移交前旧本地主分支仍是 4bd3037b4d37780cb937d4bd57b2e2bc019ebb06；新电脑应重新读取远端状态。

| 批次 / PR | 快照 HEAD | 当前 base | 后续顺序 |
|---|---|---|---|
| 19 / [#202](https://github.com/yhan-sun/p2wlan/pull/202) | d2df1627952191fe3d535d64ad6249723e1ba404 | main | 修复 fixture、完整当次 CI、普通合并 |
| 20 / [#203](https://github.com/yhan-sun/p2wlan/pull/203) | 5c65a4304b678a0a8cdf5090f10d431d467de2fa | codex/network-core-publish-19 | #202 合并后依次同步 main、验收、合并 |
| 21 / [#204](https://github.com/yhan-sun/p2wlan/pull/204) | 06410c5e1094332974b5697d0662458a6b38e67e | codex/network-core-publish-20 | 同上 |
| 22 / [#205](https://github.com/yhan-sun/p2wlan/pull/205) | 67b21b1cb54301b4a5810b2d3be48021e2b7a775 | codex/network-core-publish-21 | 同上，保留原 keepalive/ACK 断言 |
| 24 / [#207](https://github.com/yhan-sun/p2wlan/pull/207) | 0e3d53f49c81afd84baa00c4368639d152e638b3 | codex/network-core-publish-22 | 同上，限定为已有优雅排空控制 |

五个 PR 在移交查询时都打开、未合并。#202 为 unstable；后四个对 stack base 的 clean 不代表对最新 main 已通过完整验收。GitHub PR.base.sha 曾滞后于 main；以实际 ref 和提交父链为准。

最新 main 是从 4bd3037b 经 fe8ffa111d6cda1f3ad8d7897f0bc23f0f693310 到 4937de2d 的两个提交，仅改 README.md。已从完整签名提交、根树和 README blob 重建并核对 Git SHA1；其他根目录项的 mode/type/SHA 和子树 SHA 相等。当前 README blob 为 344515965451d4f86ab0c3366fbf01f497d371f8，23,320 bytes。该校验没有执行本地对象导入、主分支同步或新的产品源码应用。

## 三、立即接续 #202

### 已知失败与已完成的第一版修复

原测试 b19_original_fanout_first_full_with_other_unknown 手动 poll 一次 caller future 后仅等 Full，可能不能推进首次 Pending 后的发送。第一版修复已在 d2df1627 提交并推送，改为有界 select 同时推进 caller 与观察 Full，保留原断言。

第一版在原机器的精确测试 1 项、B19 模块 9 项、fmt、Clippy 和串行 workspace 命令通过，daemon 为 1,700 pass / 1 ignore / 247 filter、Relay 128 pass。验证器曾错误套用 Linux 数量而停止；原记录保留，平台差值为 8 项 Linux 专属 route 测试。

随后同 HEAD 的两个 Linux 作业仍失败：

- [CI Rust Check](https://github.com/yhan-sun/p2wlan/actions/runs/38247099316/job/114803612944)
- [Business MTU Linux](https://github.com/yhan-sun/p2wlan/actions/runs/38247099290/job/114803612964)

均为上述 B19 测试的有界前置等待超时，shared panic 位于 relay/send_origin.rs 的 Budget.step；daemon 1,707 pass / 1 fail / 1 ignore / 247 filter。该共享行无法确定具体 await 阶段，也不能证明唯一生产根因。新电脑须读取当前作业，不把旧失败或旧成功当最新状态。

### 待验证补丁

[b19-runtime-handoff.patch.json](b19-runtime-handoff.patch.json) 已静态审查并校验，仅覆盖：

1. client/daemon/src/relay/send_origin.rs：cfg(test) 的 synthetic PREWRITE stall callback 用 block_in_place 交还 Tokio worker，继续保持原生产写锁和拒绝语义。
2. client/daemon/src/network_outbound/tests/relay_publication.rs：原 fanout 新增 11 个阶段标记；新增 b19_stall_writer_allows_runtime_sibling_progress。单 worker 正例与原阻塞 support 负控验证 sibling 在释放前能否推进。

补丁尚未应用、编译、运行或作为产品修复提交。仅交接资料保存了补丁文件。

保持总预算 2s、单步 1s、stall barrier 1s、业务 deadline 1s；新增 observer 250ms，低于 barrier。保持原 fanout worker=2，新增 control worker=1。保持 receive 1024 / max frame 65535、Relay 128、既有 ignore=1 和 hard_hard_ 隔离规则。负控使用原阻塞 stall_writer；新 control 与阶段标记保留。observer 必须释放 callback；join sibling、stall task 和 fixture server 后，再断言 progressed。负控需要特定 sibling assertion 失败，其他 timeout 不算证明。

后续验证顺序：

1. 核对实际 main、#202 HEAD 与源码；普通同步到隔离工作区，保留旧失败记录和原改动。
2. 使用 SHA256SUMS 核对交接包；运行 python3 handoff/network-core-20261013/decode_patch.py ../network-core-b19.patch，将补丁解码到包外新文件（已有文件会拒绝覆盖）。内层长度 5,930、SHA256 c2bc69def2d3abcea3468bae0bcb466c7bff7b1ffad706f193cde0012ac62071。先 git apply --check，再应用；基准变化时逐项重审，不强行覆盖。
3. 实际全 workspace fmt check。
4. 构建 THIS-build 的 daemon lib test binary；从 Cargo JSON 精确获取 p2pnet_daemon，不按文件名/mtime 猜二进制。枚举实际测试清单并拒绝零匹配。
5. 原 support 负控：仅撤去 block_in_place wrapper，新 control 保留；特定断言 exit 101，释放与回收完成。随后恢复修正 support。
6. 原 fanout 精确正例、新 control 精确正例、当次全部 B19 注册测试；本补丁预期 10 项，但以实际注册清单核验。
7. Clippy、与 CI 相同的串行 workspace 命令及仓库必需检查。实际平台数量由清单推导，不固定套用 macOS/Linux 历史值。
8. 普通提交、非 force 推送到 #202 的原分支；记录实际新 HEAD、tree、有序 parents、推送 UTC。完整当次 CI 后普通合并并核实 merge SHA 与 main。
9. #203→#204→#205→#207 逐批执行最新 main 同步、局部与完整 CI、普通提交/推送/合并。每批独立验收。

原机器的绝对路径 Python 操作工具、缓存 target、索引和工作区计数只适用于原机器。它们未打包为执行入口。新电脑重新建立自己的证据目录、工具链与 Git 状态，保留失败并重新验证，不复制旧 PENDING 或接受旧 ROOT 门作为新操作授权。

## 四、原 22 项任务与完成门槛

状态：2 完成、5 进行中、8 待启动、7 条件候选。D-00A/B 仅完成本机正确性范围。条件候选未满足立项条件时不默认改代码，可用充分证据形成不采纳结论。

| ID | 当前状态 | 下一步 / 依赖 | 完成门槛 |
|---|---|---|---|
| D-00A | 完成（本机） | 维持 fallback 读/路由取消保护、feedback 关闭回归 | 确定性回归保持；真实 TUN 归 B-02A/D-03 |
| D-00B | 完成（本机） | 维持 per-peer 唯一 owner 准入、公平锁活锁修复、FIFO/截止 | 本机四锁争用、超时/关闭/活锁回归保持；真实性能另验 |
| B-01 | 进行中 / P0 | 先交付 #202–#207；补最终 current-owner/once、S3C、故障后 fresh REQUEST→远端当前 REQUEST→匹配 ACK；完整 canonical pipeline、真实 partial/worker loss、C06/C11 | 原请求/密文/attempt/owner 身份贯通，拒绝旧身份和重复信用；正反例、owned joins、精确业务证据 |
| B-02A | 进行中 / P0 | B-01；补双端真实 TUN 请求链、路径/session/socket 精确归属与当前请求证据 | Transport、Overlay、Dataplane、Application 分层；历史 Mock/RX/TX 观察不作全任务验收 |
| B-02B | 待启动 / P0 | B-01、B-02A；实现 Minecraft 可重复交互工具 | Java TCP 与 Bedrock UDP 分开；同端请求/确认 RTT，固定世界/版本，TPS/MSPT/GC/重传与超时保留 |
| B-03 | 进行中 / P0 | B-01；12 个既有 Vec 站点及 actor/FIFO 局部事实保持，补全 pipeline/coverage/lease/copy/serialized 计量 | channel+pending+in-flight 总资源、真实操作及覆盖/开销可解释；未知 bytes 不伪造 atomic 总量或改进率 |
| N-01 | 进行中 / P0 | B-01、B-03；六个本机子项完成记录保持，补真实执行/失败/成本对应 | 计划与实际发送可核对；过期、预算、限流、未发送、发送不确定分开；公网结论有实际样本 |
| N-02 | 待启动 / P1 | N-01；同预算 hh2 时序/候选 A/B | 规律/跳号/随机映射、冷/热/背景分层；可复现收益或不采纳结论 |
| N-03 | 待启动 / P1 | B-01、N-01；普通 pool 与 hh2 socket 独立实验 | 保持平台 cap、全进程预算、deadline；requested/attached/usable、竞争、清理/映射副作用完整 |
| D-01 | 条件候选 / P1 | B-02A/B-03 且复现 TUN 串行等待；平台 split API 原型 | 双向/outbound-only、关闭/重建/取消安全；同负载尾延迟改善，否则不合入 |
| D-02 | 条件候选 / P1 | B-02A/B-03 且复现可控多流排队；明文 DRR 原型 | 流内有序、密文不重排、backlog/fast path 不绕过、公平与资源有界；收益不足不合入 |
| D-03 | 待启动 / P1 | B-01/B-03；通用采证复用 B-02A，无需等待 MC | Linux/macOS/Windows/Android 真实 TUN/TCP、切路/黑洞/EMSGSIZE/PTB/预算变化；不错误降级健康或超预算发包 |
| C-01 | 待启动 / P1 | B-01/B-03；补同网关重映射、切网、休眠、撤权/rekey 并发 | 恢复时间、失包、旧 owner 拒绝、资源回收及跨路径不重放 |
| C-02 | 待启动 / P1 | B-02A/B-03；MC 误报参考 B-02B；健康只读 shadow | 空闲、UDP 无 ACK、单尖峰、服务器卡顿、本机排队不误判路径失活 |
| C-03 | 待启动 / P1 | B-01/B-02A/C-02；先 A/B 现有启动策略，再按证据扩展唯一 reducer | 首次可用改善，Direct 不回归，Relay 成本可见；不重置截止或降低验证 |
| R-00 | 待启动 / P1 | B-01/B-02A/B-03；现有多区域/重选与持续业务质量、协调迁移 | 双端同 Relay rendezvous、验证/续期/撤权保持，有业务证据才改选择机制 |
| R-01 | 条件候选 / P2 | B-02A/R-00 证明 TLS Relay 的问题；UDP Relay RFC 与单区域原型 | 双向加密业务、TLS 回退、票据/撤权、防放大、限速、MTU/拥塞与成本 |
| R-02 | 条件候选 / P2 | R-01 结论及用户需求；自愿 Peer Relay RFC/配额 | 显式参与/退出、权限、配额、兼容可验证；不自动开放转发 |
| X-01 | 条件候选 / P2 | 明确 TCP 打洞需求；simultaneous-open 独立实验 | OS/NAT 矩阵、取消与资源上界，失败保持 UDP/TLS 主线 |
| X-02 | 条件候选（按部署影响提级） | IPv6-only/NAT64 实际样本 | STUN/控制/Relay、IPv4 literal/DNS64 的可达性矩阵；目标部署受影响则提级实施 |
| X-03 | 条件候选 / P2 | CPU/系统调用/多出口瓶颈证据 | GSO/GRO、batch、多队列、多链路分别实验；CPU/吞吐/尾延迟，乱序与 replay 有界 |
| G-01 | 进行中 / P0 | 贯穿所有任务，当前先完成五个 pending 产品 PR | 同 SHA 回归/完整 CI/实际合并/产物版本与哈希/灰度/回滚；设备与性能独立验收 |

实施顺序：P0 已修复保持 → M0（B-01/B-02A/B-02B/B-03） → M1（N-01～03）/M2（D-01～03）/M3（C-01～03/R-00）按依赖推进 → M4（R-01） → M5（R-02/X-01～03）。G-01 每批执行。同一状态所有者的改变分批，避免同时改 TUN、FIFO、路径评分和 hh2 后无法归因。

## 五、实验、正确性与统计契约

每轮绑定 run_id、task/variant、双方 source commit、产物 SHA256、配置、OS/架构、网络行为/地址族、冷/热启动、seed、总预算/截止、负载、有效性分类及完整原始结果。公网和真实设备不能由本机 Mock 或合成 NAT 代替。

NAT 按两端 mapping×filtering×端口分配模型分层，额外区分 CGNAT/家宽/校园/热点、IPv4/IPv6/NAT64；不要将 CGNAT 当固定 NAT 类型。覆盖空闲小流、单向/反向/双向下载、多 peer、探测、随机/突发丢包、带宽/时延变化、MTU 黑洞与切网。

关键指标：

- Direct@10s：固定起点口径下，当前身份路径提交为对应 Direct 且本轮真实 TUN 双向业务成功；Relay 不能计 Direct。LAN、IPv6、公网 IPv4 分开。
- 首次业务：t0 到第一笔真实双向请求/响应，Direct/Relay 均可；失败和超时留在分母。缺精确 attempt 起点时 connection_to_first_business_ms 保持 unknown。
- 本机尾延迟：同包 TUN 读完成→本地发送边界，RX socket 收到→TUN 写完成；不是远端到达或 MC RTT。
- MC：同端可重复交互请求→服务端确认；统计 >200/500/1000ms、有效请求/失败/超时，并关联 TPS/MSPT/GC。
- 会话保持与 Direct 保持分开：合法 Relay 回退可能保业务可用，但不能算全程 Direct。
- 恢复：故障注入→连续 K 次双向业务成功，预冻结 K、间隔和超时。
- 成本：物理 UDP/HTTP/确认、CPU/内存/任务/socket 峰值、Relay 字节、清理残留。

先各 30 轮筛查，正式结论按目标效应估算样本，建议主要分层各至少 100 轮。现有 matrix runner 单批最多 32 executions，使用独立批次和 seed/汇总，不能直接改成 100 或重复默认 seed 充数。按网络/场次配对或聚类，报告成功率和差值置信区间；P95/P99 附窗口、样本量和区间。首轮失败与诊断重跑分账。

M0 可冻结一次工程门槛，再开始实验。原建议收益为业务尾延迟/卡顿率改善 20% 或 Direct@10s 提升 5 个百分点；回归容忍建议 Direct -2 个百分点、尾延迟/CPU/内存 +10%。这些是待冻结的建议，尚无全环境达标结论。正确性硬门槛：旧身份提交、撤权后发送、密文跨路径重放、超预算发送、无界资源及取消泄漏均为 0。

## 六、可复用验证入口

从实际仓库根运行，先读 AGENTS.md、skills/p2wlan-repository/SKILL.md、docs/README.md、docs/explanation/engineering-quality.md 和当前 docs 全部 Markdown，再检查实现、测试和 workflow。

```bash
python3 scripts/docs/verify_repository.py
python3 scripts/quality/check_code_health.py --base-ref main
RUSTUP_TOOLCHAIN=1.99.0 python3 -m unittest discover -s scripts/quality/tests -p 'test_*.py'
bash -n scripts/install-server.sh scripts/deploy-server.sh scripts/p2wlan-server

cargo +1.99.0 fmt --all -- --check
cargo +1.99.0 clippy --workspace --all-targets --all-features -- -D warnings
cargo +1.99.0 test --workspace --all-features -- --test-threads=1 --skip hard_hard_

python3 scripts/quality/run_rust_tests.py path_state_machine
python3 scripts/quality/run_rust_tests.py network_outbound
python3 scripts/quality/run_rust_tests.py hard_hard_ --each
python3 scripts/quality/run_rust_tests.py dplpmtud
python3 scripts/quality/run_rust_tests.py tests::direct_business_budget_production_path_e2e --exact
bash scripts/nat-sim/run-ci-topology.sh unit
```

原生验证需确认工具链，不能悄悄用默认旧 cargo。上次明确使用 +1.99.0；新环境优先核对仓库/当前 CI 的要求。测试选择器拒绝零匹配、ignored-only；THIS-build 的编译/list 不当作测试通过。真实 TUN、Windows lifecycle、移动端、公网 NAT、MC、性能 A/B、最终产物与回滚仍未整体验收。

旧 16 workflow / 至少 80 checks / 2 个原规则条件 skip 是历史验收契约，应核对当前 workflow、事件、head/候选父链、全量分页、最新 attempt/job 和原 skip 条件。完整 CI 不能靠 summary、旧 run、stack-base clean 或删过滤器证明。未知结果先只读核实，禁止盲目重推或重做修改。

## 七、交接资料和后续进度更新

本包包含：

- 本报告：采纳结论、准确快照、全部 22 项、实施/统计/验收契约。
- [NEXT_AI_PROMPT.md](NEXT_AI_PROMPT.md)：交给下一位 AI 的完整指令。
- [PROGRESS.json](PROGRESS.json)：可继续更新的机器可读任务状态与 PR 快照。
- [b19-runtime-handoff.patch.json](b19-runtime-handoff.patch.json) 与 [decode_patch.py](decode_patch.py)：无损封装的待验证补丁及校验解码入口。
- [SHA256SUMS](SHA256SUMS)：包内内容完整性。
- [README.md](README.md)：获取和使用方法。

源代码以 GitHub 远端为迁移依据；新电脑通过交接分支取得此包。无需原电脑的下载目录、绝对路径工具或编译缓存。原本机历史证据保留，但未上传原始日志和个人路径。本包对历史通过数字作有限摘要；缺少可独立复核证据的范围必须在新环境重验。

每个后续批次更新 task ID、依赖、状态、真实 source/HEAD/tree/parents、测试平台/完整命令及退出码、CI run/attempt/job、PR/merge SHA、产物/配置哈希、证据位置、失败与下一步。更新 PROGRESS.json，并在对应 PR/Issue 或 Release 资产记录过程；公共 docs 只描述已实现行为。

交付原则：小范围实现→针对性正反例→仓库检查→普通提交（feat:中文，冒号后无空格）→非 force 推送→当次完整适用 CI→普通合并→核对 main 与产物/回滚。授权已覆盖这些常规步骤。任务验收未完成时如实标待验证/受阻，实验无收益可有证据地不采纳。

## 八、本次移交包检查结果

文档门禁通过（19份公共文档，1,518份tracked文本）；代码健康通过（648份Rust文件，0历史例外）；明确Rust 1.99.0后质量95项全部通过；3个脚本语法、staged差异空白检查通过。补丁无损解码回原5,930 bytes，SHA256一致；git apply --check通过，已有输出文件拒绝覆盖。首次质量检查的5个rustfmt环境错误保留；未改产品源码、未运行新补丁的Rust测试或Linux CI。


## 九、继续实施的当前记录

本节是继续实施的当前状态，前八节保留原交接时的历史记录。授权验收环境为本机和 GitHub CI；无真实环境的任务如实保留限制。

### 已验收并普通合并

| PR | 采用 HEAD | 普通合并 | 完整 CI |
|---|---|---|---|
| [#202](https://github.com/yhan-sun/p2wlan/pull/202) | `e9edb2953dba677e5b85f8ef2502328353c905b6` | `da4edadc84c0b10a138115652cc031145dcb77c6` | 17次运行、18门禁、87成功作业、2原条件跳过 |
| [#203](https://github.com/yhan-sun/p2wlan/pull/203) | `b98914724ba6b83eb3f21beb09b69d2718bec27a` | `221c6ba47071a8cfd7ad35cc4b7b2c5d7559bb98` | 17次运行、18门禁、87成功作业、2原条件跳过 |
| [#204](https://github.com/yhan-sun/p2wlan/pull/204) | `4a2c434b0165693ac331acfc1ad7bc7d2a7aed4a` | `8fb0265537d2cf34885874a2db8b6c46769782bb` | 16次运行、18门禁、81成功作业、2原条件跳过 |

每项均重新核对当前 HEAD/main、所有运行与最新 attempt/job、checks ID、原条件跳过、候选 parents/tree 及实际 merge。#204 的空提交不匹配 Flutter push 路径条件，16个 PR workflow 是完整适用范围；未借用旧 HEAD 的 push 运行。#204 的806份本地证据已逐项校验。三个通用 CI 主作业实际通过原15项B19、3项B20及新增1项B21，DPLPMTUD实际10场景通过。

### 本机缓存证据纠正与 #205

#203/#204 历史本机 workspace 总数2340/2341，各含两个来自后续候选 B25 的 Relay 测试名；共享 target 曾被其他 checkout 覆盖。本机总数的严格同源码声明已撤回，原始日志保留，不能简单减2后当作重新运行。独立 GitHub CI 的当前源码环境不含这两个外来测试，定向回归和实际合并身份仍有效，PR 中已记录纠正。后续每次 checkout 切换，先清理全部本项目 workspace crate 产物、保留第三方依赖缓存；仅靠本次 Cargo JSON 不能证明共享产物没有串用。

[#205](https://github.com/yhan-sun/p2wlan/pull/205) 已普通同步上述 main，提交并非 force 推送 `81e9220fcbce7bd92cecad1d4ff734341c4fab54`，tree `763525a7412bf1d8a1c4784fa51cc5b0134d1fb6`。只修改原保活测试：原 peer ACK 接纳 barrier 和健康样本恰好+1断言保留，未完成 responder 保持所有权，成功、错误及超时均实际取消/等待两个工作任务；已完成 handle 不重复 poll。原500ms回合、生产 consent 时限和全部业务断言保持。fixture body 上界2s，清理共用1s截止，不计入业务成功窗口。

清理全部本地 crate 后的冻结源码完整重验：workspace2339 passed/0 failed/3原ignored、hard_hard逐项隔离247、重点回归21、NAT92、quality95及fmt/include-format/全workspace Clippy/四项强制检查通过。原 responder 永不完成负控，在两个owned任务清理断言通过后由指定超时断言退出101；恢复源码与独立审查一致。初始编译错误及首轮日志保留。当前17次适用CI（16 PR workflow + Flutter push）进行中，未合并；之后依次 #207。

### 远端原定义

完整历史检索恢复部分原始定义：commit `2a5735568ee8767022cd509dff1112cdb969574a` 的 `client/daemon/src/network_outbound/queue/request_carriage_tests.rs` 包含C06四项FIFO/容量/Weak/代际/停止控制；`lib/daemon/overlay_validate/b14_carriage_read_tests.rs` 与 `client/daemon/src/transport/tests/request_carriage_crypto.rs` 包含C11旧入口/UnknownAny/加密兼容局部范围。覆盖178 branches、167 tags、187 PR refs、2192 commits、10586文本blob及远端Issue/PR/评论/Release信息。S3C独立定义、完整C06矩阵及冻结完整C11旧接口矩阵仍未找到；不将局部控制冒充原完整验收。

### 本地候选与未完成边界

以下均未推送、未通过独立同HEAD CI、未采用：

- Relay历史reader/client身份 `dca76a6bf80929b515843b9e695e6cea16cd6305`：53项目标、workspace2338、隔离247及审查通过。
- Direct原始收发身份与发布边界 `2b201c300c9611767af4f631733887679c5e1539`：91项目标、workspace2344、隔离247及审查通过。
- Relay成员/关闭/停止原边界 `8d67bc66bc7703fb80ccc6edad26c8898c3cdb14`：98项精确控制、workspace2353、隔离247及审查通过。首次旧缓存构建失败保留，最终完整重验通过。
- 能力发布保护 `addd75862593e41ff257c013d62f39dd06e625ba`：10项目标、2项具体失败负控、workspace2356、隔离247、NAT92、quality95和全部检查及审查通过。原watch唯一所有者中串行化发布；最终 current-owner/once/ACK 事务和原 REQUEST来源传递正在实施，尚未验收。
- Minecraft契约 `3dc0819a7a15d82152874a4d2b25b0627108c91e`：23项；有界监督器 `afb3577972c1d7f0be1ace4dd3b0774055a9b789`：两个Python版本各28项；Java1.20.4适配器 `5c126c209564ff431144128de9a6d5533b81812c`：24项Node22.16及15项独立控制。普通组合 HEAD `5e51bcd6dff5449c9f6781caa9e9e25c04696046` 已通过Python3.12.12/3.14.6各28项、Java24、契约23、UDP16、quality95及四门禁；原runner CLI→原adapter→本机协议服务器→原reducer的成功、超时、取消场景保持固定分母并实际回收进程组。
- Bedrock1.18.30/protocol503/RakNet10候选 `cdf7cf2dad43d97cbc73c8905c9c6d35b84c90b5`：原排队未发即计成功、隐式ping、原物品快照过期及第二轮可靠重传丢失归属问题均修复。53项常规测试、独立10项进程内正控及2项旧源码具体断言负控通过，409份证据校验一致。动态复核曾被工具风险检查中断，未绕过或继续原动态重传实验；修复后该动态范围仍未验收。正在普通集成全部工具、独立Node固定版本CI及原runner→Bedrock CLI控制。

这些协议fixture不是真实游戏世界；Java/Bedrock真实交互、双端实体设备TUN、公网NAT/NAT64、Windows/Android实体设备、最终发布灰度和回滚仍未整体验收。B-03/N-01已完成后续计量缺口只读审计，尚未实施；其余22项状态/依赖见PROGRESS.json。无证据不宣称最终收益或整体完成。

用户偏好：后续子代理统一 GPT-6.1 Sol、ultra，不再安排 Astra。
