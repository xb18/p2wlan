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

前八节为原交接历史，本节与PROGRESS.json为当前状态。

更新时间：2026-10-14 00:44 UTC。工作仍在继续。最新已验 main：`03674990c4956df5580f2b56cb1aad83c645de36`。只使用本机和 GitHub CI；后续子代理统一 GPT‑6.1 Sol ultra。局部通过不计整个任务完成，完整适用 CI 通过前不采用候选。

### 已验收并普通合并

| PR | 已验 HEAD | 普通合并 | 完整适用 CI |
|---|---|---|---|
| [#202](https://github.com/yhan-sun/p2wlan/pull/202) | `e9edb295` | `da4edadc84c0b10a138115652cc031145dcb77c6` | 17运行、18门禁、87成功、2原跳过 |
| [#203](https://github.com/yhan-sun/p2wlan/pull/203) | `b9891472` | `221c6ba47071a8cfd7ad35cc4b7b2c5d7559bb98` | 17运行、18门禁、87成功、2原跳过 |
| [#204](https://github.com/yhan-sun/p2wlan/pull/204) | `4a2c434b` | `8fb0265537d2cf34885874a2db8b6c46769782bb` | 16运行、18门禁、81成功、2原跳过 |
| [#205](https://github.com/yhan-sun/p2wlan/pull/205) | `81e9220f` | `1845d1381e46596cbc42b0a3b14b55573b8dfd2f` | 17运行、18门禁、87成功、2原跳过 |
| [#207](https://github.com/yhan-sun/p2wlan/pull/207) | `4fbe60ee` | `48febb538333b161fabe86135c0b8319429ab644` | 17运行、18门禁、87成功、2原跳过 |
| [#208](https://github.com/yhan-sun/p2wlan/pull/208) | `a7cd9024` | `dbe5d67f2142981e103b858cf82981696b5c1bb6` | 17运行、18门禁、87成功、2原跳过 |
| [#211](https://github.com/yhan-sun/p2wlan/pull/211) | `1d357087` | `03674990c4956df5580f2b56cb1aad83c645de36` | 17运行、18门禁、87成功、2原跳过 |

原24批已全部采用。新增 #208/#211 已采用，#209/#210/#212/#213 待完整CI；合计30批发布、26批普通合并、4批待验。#204 的16次是实际路径过滤后的完整范围。合并前核对实际 head/main、最新 attempt、job/check、原跳过条件及合并 parents/tree。

#208 同源 Linux 真实 TUN 业务32/32通过，11组22原句柄收集、TUN和namespace清理通过。Minecraft Java24、Bedrock53、契约23、runner28与四份零漏洞审计通过；没有真实游戏世界的性能结论。

#211 于 00:06:13 UTC 合并。同候选 Linux 产物11859906971：32/32基线、8 UDP timeout和8 TCP not_sent故障终态、解除后16个新请求成功；原规则、FD及11组22句柄清理通过。archive SHA256：`ce8e4de820426ed54d3523875cda6342069b373799dc995a98bbf4e782434caf`。完整CI证据984文件封存摘要：`39baf04cdca09af26af675649a73d8e3ed722a2b6d006eb4cc4d4382c50951b4`。这未完成整个跨平台 D03 矩阵。

### 当前候选与测试

| 范围 | 实际状态 | 下一步及限制 |
|---|---|---|
| [#209](https://github.com/yhan-sun/p2wlan/pull/209) 原ACK、非对称和common Relay | clean `4fa8b9e`；68唯一exact、工作区2418通过/3原ignored、253隔离、NAT92、quality108、完整13检查通过；独立复核无阻断；已普通推送 | 当前完整CI进行中。common测试证明旧成员ACK拒绝及双向新请求Fresh，不证明替换merge worker重新学习路线 |
| [#210](https://github.com/yhan-sun/p2wlan/pull/210) 普通探测成本与模拟器C修复 | clean `84a76a5`；产品Rust与已验4ab相同，纳入C大栈缓冲修复及main211；当前7项相关检查通过；已普通推送 | 新完整CI进行中。额外工具314项为313通过/1旧restart凭据缺失；单项诊断18秒通过，旧原因未知，不能写整套通过 |
| [#212](https://github.com/yhan-sun/p2wlan/pull/212) B01 worker-loss / C02健康 | clean `325e294`；28exact、工作区2347通过/3原ignored、253隔离、NAT92、quality108、完整11检查通过；独立复核无阻断 | 已普通推送创建PR，完整CI待验。应用无回复、60ms RTT尖峰和ACK adoption排队均为局部已验场景；Linux真实应用暂停另行实施 |
| B03资源计量 | clean `6053681` 普通整合最新209/main211；原10文件字节保留，7静态检查通过 | 91唯一exact及完整14检查正在运行；全pipeline、channel与开销仍缺 |
| Managed/dynamic身份 | clean `c2ac414`；11文件整合、冲突最小解决、静态检查通过；原预算、容量8和身份guard保持 | 61唯一exact尚未原生验收；不把计划计为通过 |
| X02 IPv6连接修复 | clean `c18e599`；WS原测试复现括号host错误。最小修复后实际IPv6 TLS默认IP证书验证/注册、2原客户端任务join和WS测试通过 | 补兼容断言后完整12回归通过：workspace2342/3原ignored、HH253、NAT92、quality108；已发布[PR #213](https://github.com/yhan-sun/p2wlan/pull/213)，完整CI待验。旧Relay运行仅超时，不算指定反例或已归因；DNS64/NAT64未验 |
| C03启动策略工具 | 工具 `a5395c9` 普通整合新producer为clean `39e593f`；原exec策略摘要绑定已修；45离线控制及当前9静态检查通过，native marker存在 | 固定4次冷启动、零重试计划已准备；新组合原生回归和4次实际运行尚未执行，首次应用可用仍未知 |
| N02 HH第二波 | 同C模拟器修复的新候选 `324484f` 与固定12次计划准备完成 | 新组合原生及12次实际未运行。旧12次每版本2有效、4栈溢出，全部清理且零重试；不作因果收益结论 |
| N03 socket pool | clean `881d348`；工具与同C修复组合，Python35、quality108、四门禁及9项dry-run通过 | off/2/4共9次实际cold尚未执行；requested不等于usable，无收益或采用结论 |

本地每次切换源码 checkout 先清理全部11个项目crate，再从本次Cargo输出绑定实际测试二进制，避免跨checkout产物混用。未变动源码期间才承认整套验证。

### 保留的失败

- #209 旧head真实NAT失败、非对称回程问题、`Contended(Emit)`及关闭断言失败均保留。DPL readiness、原validator join及严格原截止关闭断言修正后，新head完整本机检查通过；旧失败没有删除。
- #210 旧head Relay3/4有实际Tokio线程栈溢出，原进程9/9收集且未强杀；未推断具体函数因果。原checkout超时、依赖门禁3000秒超时及aggregate `unknown_schema_version`分别记录。
- C拦截层旧大栈缓冲在有界局部测试中失败，新实现通过；这不能证明所有daemon栈问题消失。更深的栈审计曾被自动审批拒绝，已停止该动作，未换方式绕过。
- X02旧TLS用例实际执行1个、ignored0，bare IPv6控制和清理完成，但结果是连接超时，未满足预注册反例分类；独立WS指定断言失败及修后实际TLS成功分别记录。
- 历史#203/#204本机总数混入其他checkout的两项测试，严格同源码计数已撤回；独立GitHub CI有效。早期编译、夹具前置超时和源身份变化拒绝均保留。

### 原始要求与剩余边界

远端完整可获取历史确实恢复了 C06 四项原FIFO/merge/repark/停止owner控制，以及 C11 构造/API/raw路由/旧加密兼容依据。来源是提交 `2a5735568ee8767022cd509dff1112cdb969574a`；完整来源审计见同目录 `REMOTE_ACCEPTANCE_SOURCE_AUDIT.md`。S3C独立定义、完整C06/C11矩阵仍未找到；这不阻止明确要求的实施，也不再要求用户补充。

C01正在实现原supervisor网络hint驱动的loopback rebind、旧ACK拒绝与新请求闭环，尚未原生验收。D01/D02/X03须先有同负载瓶颈和收益证据；R01/R02/X01尚无已满足的引入条件，不能为了填完成状态自动开启协议或Peer转发。

真实Windows/Android设备、公网NAT/NAT64、Minecraft世界/TPS/MSPT/GC、跨平台真实TUN、性能和发布灰度/回滚仍未验证。用户已明确只使用本机和GitHub CI；MockTun、回环、内核TUN和离线协议工具按各自实际范围验收。

任务级机器可读状态、原提交与完整历史证据索引保存在同目录 `PROGRESS.json`。远端交接最近已推送 `150ada17c45b492f407e19ba922b9c5afcd7f84a`，其6项SHA及四门禁通过；本页记录随后新增工作，下一次里程碑再同步远端。
