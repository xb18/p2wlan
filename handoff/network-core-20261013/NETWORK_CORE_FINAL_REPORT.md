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

当前以报告第九节与PROGRESS.json.continuation为准。原#202/#203/#204/#205/#207已顺序完成完整CI并普通合并，main48febb。PR208 a7cd902完整本机通过，17次CI仍待完整验收；PR209 5c790eb的17次CI已全部结束并确认NAT失败，最小VIP/ACK日志修复6项真实正控通过，但错误目的地址控制仍有2s原前置超时待诊断。N01普通探测成本e2684e6完整本机11检查/40重点/2360工作区/247隔离/3实际负控通过，已推送并创建PR210，17次CI待验。B03本地8a4dfc7完整本机通过，未推送。D03修正4b1f1db实际Linux产物已核验基线32、8UDP超时/8TCP未发送及解除后16新请求成功，11组/22句柄各自回收，仍不代表完整D03或PR采用。API逐step元数据缺失保留，完整workflow待核实。B01真实child-loss6项原生通过，负控/全回归待验；C02 test-only统一原setup截止修复已独立审查，首次实际路径回归准备中；Managed/dynamic7项尚未原生。仅本机和GitHubCI；子代理统一GPT-6.1 Sol ultra。

### 实际进度

任务仍在实施。远端 main 当前为 `48febb538333b161fabe86135c0b8319429ab644`；未通过完整 CI 的候选均不计作采用。用户限定本机与 GitHub CI，后续子代理统一 GPT‑6.1 Sol ultra。

### 已采用的顺序任务

| PR | 已验 HEAD | 普通合并 | 完整适用 CI |
|---|---|---|---|
| [#202](https://github.com/yhan-sun/p2wlan/pull/202) | `e9edb2953dba677e5b85f8ef2502328353c905b6` | `da4edadc84c0b10a138115652cc031145dcb77c6` | 17次运行、18门禁、87成功、2原条件跳过 |
| [#203](https://github.com/yhan-sun/p2wlan/pull/203) | `b98914724ba6b83eb3f21beb09b69d2718bec27a` | `221c6ba47071a8cfd7ad35cc4b7b2c5d7559bb98` | 17次运行、18门禁、87成功、2原条件跳过 |
| [#204](https://github.com/yhan-sun/p2wlan/pull/204) | `4a2c434b0165693ac331acfc1ad7bc7d2a7aed4a` | `8fb0265537d2cf34885874a2db8b6c46769782bb` | 16次运行、18门禁、81成功、2原条件跳过 |
| [#205](https://github.com/yhan-sun/p2wlan/pull/205) | `81e9220fcbce7bd92cecad1d4ff734341c4fab54` | `1845d1381e46596cbc42b0a3b14b55573b8dfd2f` | 17次运行、18门禁、87成功、2原条件跳过 |
| [#207](https://github.com/yhan-sun/p2wlan/pull/207) | `4fbe60eec1ee436144df1df510a1acef6a751485` | `48febb538333b161fabe86135c0b8319429ab644` | 17次运行、18门禁、87成功、2原条件跳过 |

原24批全部普通合并。每次核对实际 head/main、最新 attempt、job/check、原跳过条件及实际合并 parents/tree。#204 空提交不匹配 Flutter push 路径，所以16次为其完整适用范围。#205 的711份证据清单 SHA256 `1dd09b7f22025246c527c9f032996fc42a26d3c87322bfb382a39137a712bf45`；#207 的1015份清单 `405f3308e3a28bb4d9dae337bf05c6d6072110ca87d98fc1960b661bc2d28a6f`。

### 当前已实施候选

- **#208 应用采证与报告发布：修复已推送，新一轮完整CI中。** 当前HEAD `a7cd90240eb36f75bc58ff85211c1e8e652f7dbc`，tree `46916b50851d105115b7bc07efda6ec69bd32465`，candidate `1b4beb18459f88a993685a9bd73e3bf42ce0a1c4`。在固定32请求Linux工具、Minecraft协议采证和已修启动取消fixture上，新增原终态报告锁竞争修复：同原100ms总截止、完整身份重核、一次seal/ledger。六项新锁控制加七项原回归13项通过；四项实际故障变体在原清理后触发指定断言，恢复全部源码后13项重跑通过。完整11检查：工作区2340、HardHard隔离253、NAT92、quality95、格式/文档/健康/脚本/Clippy均通过，保留3原特权ignored，独立审查通过。17次适用workflow运行/18门禁和本HEAD真实Linux产物待验，尚未采用。原30秒双端断言保持；历史Windows失败具体锁分支未知，不能断言唯一根因。
- **PR #209 原身份和一次记账：完整CI发现NAT失败，修复中。** 顺序提交 `dca76a6`（Relay来源）、`2b201c3`（Direct来源）、`8d67bc6`（Relay成员和关闭）、`addd758`（能力发布）、`a078354`（最终核对/once/原REQUEST回应源）。c12实际52个唯一重点控制、2400工作区、247隔离通过；普通整合最新main后提交 `5c790eb006155f266d0df13f73ffd955255eb34b`，tree `2c05070db16ea101a9c588cf87a5bf0729cb2c13`，2405工作区、247隔离、NAT92、quality95、全部门禁和Clippy通过，保留3原特权测试ignored。已创建 [PR #209](https://github.com/yhan-sun/p2wlan/pull/209)，本轮17次适用运行已全部结束，六项NAT及依赖门禁失败；已定位启动配置VIP与注册后实际VIP不一致的请求资格检查，以及Fresh成功标记缺失，最小修复和真实Direct/Relay回归正在准备，尚未采用。实际两项15秒TTL及取消/once/早ACK/高水位负控有证据。当前same-path、same-Relay-client、non-room范围；Managed/dynamic/room/rendezvous仍不冒充已验。
- **B03 五个活动buffer owner阶段：本地正反控和完整回归通过，已分批提交。** 四个slow-send阶段加原DataPlane等待许可阶段；10文件候选、11源码绑定。当前23重点控制、2350工作区、247隔离、NAT92、quality95及全部11检查通过，保留3项原特权ignored。初次编译、sender提前关闭、Relay默认Direct-first前置及Clippy失败均留档并最小修复。两项实际去掉原观察hook的负控触发指定断言，均在原owner清理之后失败；监督进程和原组全部回收，再恢复11源码hash并重跑23正控通过。已提交 `8a4dfc7379080efd4dcf082b48e5188fb44ea651`，尚未推送、通过CI或采用。channel驻留、backlog、Relay、全pipeline及开销仍有缺口。
- **N01 普通探测取消成本：40项重点与回归、3项负控及恢复后的40项复测均通过。** 21文件候选接入main48；初次编译的3模块路径、原代际变量和测试绑定问题已最小修复并保留失败。三个实际移除primary/compatibility记账或子任务abort的负控均在原owner清理后触发指定断言，进程组回收后恢复全部源码再重跑正控。原绝对截止不变；returned与retained重叠不可相加，未join子任务和无返回事实保留unknown。完整11项本机回归已通过：工作区2360、隔离247、NAT92、quality95；独立复核完成。已普通提交并推送 `e2684e64c65cd1f4f7f4eaddf5b5246bab55885a`，创建 [PR #210](https://github.com/yhan-sun/p2wlan/pull/210)；17次适用运行/18门禁开始，采用尚未完成。
- **D03 Linux黑洞→解除→新请求：首次真实内核CI失败已定位，正在修正故障注入。** 手动运行 [38464012431](https://github.com/yhan-sun/p2wlan/actions/runs/38464012431) attempt1绑定HEAD `e7a6a196ae2457a343ab288c9213a68264407f8e`；原独立基线32/32通过，11组/22句柄清理。新故障切片固定32请求中，8条UDP返回send_error而非预期超时，后24条未启动，0条fresh成功；原5组/10句柄、两精确规则、原namespace FD和网络资源均已清理。实际artifact11848608412，SHA256 `920c8a840e403071f44a7b2f850b3167a36c7b60ae6b5e6131d85e10d0306cdd` 与远端一致。具体errno未记录，不猜测。已将两条规则移至原接收端INPUT并记录实际numeric errno，保持全部32请求、同端口范围、原期限和恢复断言。修正两套Python各74项、quality95/四门禁及独立复核通过；提交 `4b1f1dbad9eb93156ef585754dc5a4e3ebcf115f` 已普通推送，新手动运行 [38468485231](https://github.com/yhan-sun/p2wlan/actions/runs/38468485231) 原Linux作业已成功且产物11851620319通过源码和哈希核验：8条UDP超时、8条TCP连接截止而未发送，解除精确规则后16条新请求成功；两套harness各11组/22句柄清理。API逐step字段为空，已保存实际job日志和此缺口；Required最终状态待确认，未宣称完整D03通过。

真实scheduler child丢失后的A2保留/A3恢复切片已冻结，6项实际测试已通过，负控和完整回归待验；Managed/dynamic的7项原生ACK候选已通过静态检查和独立复核，尚未运行Rust。C02正在编写真实UDP回归以核实首次keepalive丢失是否提前改变实际路径选择，未改生产策略。N02/N03目前只有有界本机/CI实验方案，没有策略A/B或采纳结论。

### 保留的失败与证据边界

#208历史HEAD `7e55887` 的Linux32/32与Minecraft协议24+53/契约23/runner28通过，但Windows Rust原终态报告断言及依赖门禁失败；新a7cd902必须重新验收。

#208旧HEAD `bf14f5a`：Bedrock启动取消52/53，父子信号时序输给原100ms期限；已在新fixture中修复，原失败保留。macOS Rekey无执行机、无步骤，GitHub明确为容量不足；没有把它记作产品缺陷或测试通过。依赖门禁失败均保留。

旧HEAD实际Linux报告 run `38453268580`、artifact `11842466573` 已核验：archive SHA256 `44ee0c74a5b72549a2a471f74237b566e5b4d8007730af7638b4f8c6e2cde523`，实际candidate `25273368b6de782e7db7653f4052d3c7031408cc` 与该HEAD同tree；UDP/TCP双向32/32成功，11原child/11anchor实际回收，原组消失，TUN在命名空间删除前已检查消失。它只证明旧HEAD的同机Linux应用范围，新HEAD必须重验。

#203/#204历史本机workspace总数2340/2341混入两条其他checkout测试，严格同源码总数声明已撤回，不能减2冒充重跑。独立GitHubCI没有污染，完整CI与合并证据仍有效；原日志保留并已纠正PR。后续每次切换checkout均清理全部11个本项目crate，再重新绑定实际测试二进制和源码；本次B28和B03遵守此规则。

Minecraft真实世界、固定服务端负载、TPS/MSPT/GC和跨设备结果未验。此前动态Bedrock重传复核被工具风险检查中断，未绕过；普通协议/纯控制不能替代未完成的动态范围。

### 原始定义和剩余任务

远端检索覆盖178branches、167tags、187PRrefs、2192commits、10586文本blob及PR/Issue/评论/Release，在 `2a5735568ee8767022cd509dff1112cdb969574a` 找到C06 FIFO/容量/Weak/代际/停止和C11旧入口/UnknownAny/crypto局部要求。S3C独立定义、完整C06矩阵及完整C11接口矩阵仍未找到；检索结论见 REMOTE_ACCEPTANCE_SOURCE_AUDIT.md。

任务级最新状态与依赖见 PROGRESS.json 的 continuation.task_status_current。历史完成2项、进行中8项、待启动5项、条件候选7项。条件任务不能因缺环境自动算完成；需有实际触发/不采用依据。实体设备、公网NAT/NAT64、全平台真实TUN/TCP、完整故障矩阵、Minecraft世界、性能A/B、发布灰度与回滚继续明确未验。
