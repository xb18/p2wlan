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


任务仍在实施。最新已验 main 为 `03674990c4956df5580f2b56cb1aad83c645de36`。只使用本机和 GitHub CI；后续子代理统一 GPT‑6.1 Sol ultra。未通过完整 CI 的候选不计采用，局部通过不升级为整个任务完成。

### 已通过完整 CI 并普通合并

| PR | 已验 HEAD | 普通合并 | 完整适用 CI |
|---|---|---|---|
| [#202](https://github.com/yhan-sun/p2wlan/pull/202) | `e9edb2953dba677e5b85f8ef2502328353c905b6` | `da4edadc84c0b10a138115652cc031145dcb77c6` | 17运行、18门禁、87成功、2原跳过 |
| [#203](https://github.com/yhan-sun/p2wlan/pull/203) | `b98914724ba6b83eb3f21beb09b69d2718bec27a` | `221c6ba47071a8cfd7ad35cc4b7b2c5d7559bb98` | 17运行、18门禁、87成功、2原跳过 |
| [#204](https://github.com/yhan-sun/p2wlan/pull/204) | `4a2c434b0165693ac331acfc1ad7bc7d2a7aed4a` | `8fb0265537d2cf34885874a2db8b6c46769782bb` | 16运行、18门禁、81成功、2原跳过 |
| [#205](https://github.com/yhan-sun/p2wlan/pull/205) | `81e9220fcbce7bd92cecad1d4ff734341c4fab54` | `1845d1381e46596cbc42b0a3b14b55573b8dfd2f` | 17运行、18门禁、87成功、2原跳过 |
| [#207](https://github.com/yhan-sun/p2wlan/pull/207) | `4fbe60eec1ee436144df1df510a1acef6a751485` | `48febb538333b161fabe86135c0b8319429ab644` | 17运行、18门禁、87成功、2原跳过 |
| [#208](https://github.com/yhan-sun/p2wlan/pull/208) | `a7cd90240eb36f75bc58ff85211c1e8e652f7dbc` | `dbe5d67f2142981e103b858cf82981696b5c1bb6` | 17运行、18门禁、87成功、2原跳过 |

| [#211](https://github.com/yhan-sun/p2wlan/pull/211) | `1d357087271397b10e53ebf4d7fc521beba89286` | `03674990c4956df5580f2b56cb1aad83c645de36` | 17运行、18门禁、87成功、2原跳过 |

原24批已全部采用。新增#208/#211已采用，#209/#210待验；合计28批发布、26批普通合并、2批待验。#204 的空提交不匹配 Flutter push 路径，16次为完整适用范围。每次核对实际head/main、最新attempt、job/check、原跳过条件和合并parents/tree。

#208于2026-10-13 22:36:08 UTC合并。其三套完整Rust作业逐项验证原22项关键回归和13项终态报告控制；DPLPMTUD十个实际场景通过。首轮三个外部门禁在GitHub API查询阶段403失败，保留原日志；依赖实际成功后按Path→Business→DPL顺序重跑，三者attempt2通过。最终1354文件封存SHA256 `20f25aadd69e6026cbfa61e6f19a82e028a4396c5bb8c43167050d7d30a8fc94`，89个当前job/check ID完全对应。

同HEAD Linux产物run38468770963/artifact11849753073已验：UDP/TCP双向32/32、11组/22原句柄清理、TUN在namespace删除前消失、网络残留为空。远端/本地archive SHA256 `b221f9b4fcb7d990524a1a3369e0b89391a56cffd51a3587e41757b2f8956e12`。API逐step为空的缺口保留，实际job日志/源码/产物齐全。Minecraft同HEAD协议检查Java24、Bedrock53、契约23、runner28和四份零漏洞审计通过；真实世界未验。


### 2026-10-14 00:06 UTC 已验更新

#211 已于 00:06:13 UTC 普通合并，合并 parents/tree 与验收候选完全对应。全部17次运行均为首次attempt成功，18门禁通过，89个当前job/check ID对应（87成功、2原跳过）。984文件证据封存SHA256 `39baf04cdca09af26af675649a73d8e3ed722a2b6d006eb4cc4d4382c50951b4`。同候选Linux产物11859906971的32/32基线、16故障终态、16新请求成功和原规则/FD/11组22句柄清理已验；完整D03矩阵仍未完成。

#209 的66个定向用例与完整13项本地检查已通过。随后仅按独立复核收紧close测试的原截止检查，5次定向和7项静态/Clippy检查通过，三项测试修复提交 `762a69e`。之前完整检查不冒充修改后同源验收；common canonical的两项新增测试正在首次原生运行，尚未发布。

#210 出现Relay3/4实际测试失败，正在读取原日志和产物诊断；原依赖等待超时保持记录，不按单行PASS宣布成功。N02双方同一模拟器修复的新候选 `324484f` 已准备固定12轮、零重试计划，实际仍为0轮，未宣布收益。

### 当前实施与验收边界

| 范围 | 实际完成 | 尚未完成 |
|---|---|---|
| PR #209 原身份/原ACK/一次记账 | 原非对称源/原成员修复各自反例→正控、66exact/完整13通过；进一步close截止控制和common两项真实canonical通过，已普通整合main211 | 新组合68exact/完整13运行中，未推送采用；全部旧8d CI及fixture失败保留 |
| B01 原子任务丢失 | 本地提交 `11d66765ede2698945eef625cb0b6da3ba16735e`；6精确、2342工作区、247隔离、NAT92、quality95、完整11检查、4接受反例及恢复6项通过 | 未推送/完整CI/采用；私有Relay内部任务仅abort，不冒称独立join；不代表完整未知C06矩阵 |
| C02 保活与空闲 | 本地提交 `0be532f5d24deff502f6ec04467a983c9ac92bfe`；6精确、2342工作区、247隔离、NAT92、quality95、完整11检查通过；前两次miss保留Selected，第三次仍降级；实际健康consent在应用空闲时保持selector | 未完整CI/采用；单60ms RTT尖峰测试已静态冻结但原生未跑；业务无ACK、服务器停顿、本机排队仍缺 |
| B03 活动buffer | 原提交 `8a4dfc7379080efd4dcf082b48e5188fb44ea651` 的23精确、2350工作区、247隔离、完整11、2实际反例及恢复23项通过；已普通整合PR2098d并暂存，静态7检查通过 | 组合73精确和完整回归未运行；channel/backlog/全pipeline与开销尚缺；未采用 |
| Managed/dynamic | 在PR2098d上独立整合11文件，组合tree `d6cf2fa1b8165d3c65cb1f00d78cc5ecdecd7afc`，静态7检查通过 | 57项原生计划未运行；没有把计划算通过 |
| N01 普通探测取消成本 | #210 4ab的40重点+13终态/完整12通过；新3ce Cshim修复已普通整合main211 | 旧CI Relay3/4实际进程崩溃，Relay3日志明确栈溢出；新源工具验证运行中，真实CI效果待验，不提前归因 |
| N02 HH第二波时序 | 本地候选 `ee36f299ef7b3eb7935412c6cc38a43d3056874c`；9重点、2计时反例及恢复完整11通过 | 固定6+6共12轮全部执行、零重试；每版本2轮证据有效（含Relay）、4轮线程栈溢出；全部回收，无因果收益结论，未采用 |
| N03 pool采证 | 最小工具修复 `e764bf5ad831bd14c857901af34655a19f06ce3a` 已保存；Python35+35、quality95与四门禁通过 | off/2/4固定9次仍未执行；requested不等于usable；未采用 |
| D03 Linux黑洞恢复 | #211 1d完整17 CI/18门禁后普通合并03674990；同源Linux32/32基线、16故障终态、16新请求成功、11组22句柄/原规则/FD清理均验收 | 完整跨平台、MTU/PTB与公网故障矩阵未验 |

B01与C02已经和main208无冲突普通组合为 `f8cc39cfcf16dd073b12fa0176ee8505e83b0ef7`，原16个改动文件逐字保留，四必需门禁通过；组合新增单尖峰和ACK接收后adoption排队两项，当前应按27项重点及完整11检查验收；只通过静态检查，原生尚未运行。

#211当前HEAD `1d357087271397b10e53ebf4d7fc521beba89286` 的同candidate `23b3f5cd59fc4d7bb920375753b587de921c3c54` Linux产物已验收：run38482887330/attempt1/job115589465246/artifact11859906971，远端与本地archive SHA256 `ce8e4de820426ed54d3523875cda6342069b373799dc995a98bbf4e782434caf`。baseline32/32、黑洞8 UDP timeout+8 TCP not_sent、解除后16新请求成功；每套11组22句柄、原规则和namespace均清理。当前逐step API记录完整。完整PR CI尚未通过，未合并。

旧D03实际artifact11851620319，远端/本地SHA256 `8cbdec2bff153aee5c634d39068207398fed67b7c205041aea371d1956757487`。原INPUT两规则计数为8 UDP包/1752字节及1 TCP包/60字节，规则删除与FD关闭在fresh请求前完成。此前OUTPUT故障注入产生UDP send_error的首次失败完整保留，不猜未记录的errno。

N02固定12轮已经全部完成，基线与候选各2轮证据有效、4轮发生Tokio线程栈溢出。12轮所有原进程已回收，没有强制终止或重试。证据有效不等于Direct：negative-wrap基线Direct、候选Relay；random-high-entropy-negative两者均Relay。缺失成本不记0，单轮观察不能作因果收益结论；原线程栈、构建模式、场景和全部失败均保留。

NAT模拟C拦截层修复本地提交 `3ce672d63e4a43360da63aeb58199e7eb3fe0204`：移除发送路径的大栈缓冲，保留原UDP来源、头部、计数和错误语义。旧C在实际有界线程测试中SIGBUS失败，新C通过；双Python重点及四门禁共8检查通过，独立审查通过。宽范围314测试运行期间源码曾变化，明确仅作诊断，不算最终源码验收。实际daemon新矩阵、完整CI和采用未完成，不能据此认定N02收益或全部栈问题解决。

#210当前Ubuntu Rekey作业在checkout阶段超过原30分钟而取消，Rust安装/测试未开始；macOS同运行通过。原作业、注释和日志接口404均保留，深层原因未知；同HEAD按原预算重跑失败作业，未将取消计为通过。

#209组合进一步采证：原恢复请求实际被 `Contended(Emit)` 拒绝，只等待恢复validator结束仍在固定五次的第三次失败。新test-only前提在原截止内等待双端原DPL路径均SearchComplete、无outstanding/confirmation，固定五次恢复和原正例六次均通过；最终66项精确及13步完整本地检查正在运行。旧Relay关闭断言失败没有具体enum，两种构建的诊断批次未复现；现测试先保留同一member，仅在原截止内等待保守锁争用，最终必须Closed、任何Open立即失败，五次定向通过。旧失败不被诊断通过覆盖。

#210原Rekey Ubuntu checkout超时后，同HEAD原预算的第二次运行已成功；Path的外部门禁等满原3000s时NAT/Mobile仍pending而失败。该失败属于真实依赖等待超时，保留原记录；待依赖实际成功后再顺序重跑，不扩大门禁预算。

### 保留的失败与限制

B01旧abort-bypass控制在原take_loss前置步骤超时，仍不接受；替代的真实子任务panic反例按原清理后cancelled断言失败。随后工具raw-index字节变化拒绝继续，源码和完整暂存语义未变，原因未知；单独续跑第四反例且恢复正控通过。C02新增测试首次编译因nonce返回类型u64与实际[u8;8]不匹配失败，仅修正该类型后全套通过。

#209旧5c六NAT零确认失败保留；8d已出现native overlay，仍存在实际场景失败，不能宣称原修复解决全部CI。三个当前PR共十项原API查询失败已审计，其中发布审计明确为GitHub installation配额耗尽，其余403类别未有原响应body/headers，保留未知；没有据此把真正业务失败归为基础设施。

历史#203/#204本机workspace总数混入其它checkout的两条测试，严格同源码总数已撤回。独立GitHubCI有效，原日志保留；此后每次切换checkout清理全部11个本项目crate，重新绑定实际二进制与源码。所有早期启动取消、Windows报告缺失、macOS容量和首次编译/断言失败均保留。

真实设备、公网NAT/NAT64、全平台TUN、Minecraft世界/TPS/MSPT/GC、性能A/B和发布灰度/回滚尚未验证。所用资源限定为本机和GitHubCI；协议fixture、同机loopback和kernelTUN各自按实际范围记账。

### 其余任务及原定义

任务级状态见PROGRESS.json的continuation.task_status_current：完成2、进行中11、待启动2、条件候选7。C01/C03已有最小后续切片方案；R00真实common-hub原reader来源回归已实际复现native Echo拒绝；最小修复提交`0b01d67082a61a1a44dd94cd53e58f7356cd1544`同exact正控通过，原primary外壳和最终ACK检查保持。完整canonical native once和替换reader负控在隔离实现，尚未原生运行。

D01/D02/R01/R02/X01/X02/X03未因缺环境自动完成。现阶段不默认启用无收益证据的split/DRR/UDP Relay/用户转发/TCP打洞/batch/多链路；先按原任务需求与现路径数据决定。原代码支持IPv6不等于NAT64已验。

远端检索覆盖178branches、167tags、187PRrefs、2192commits、10586文本blob以及PR/Issue/评论/Release，在 `2a5735568ee8767022cd509dff1112cdb969574a` 找到C06 FIFO/容量/Weak/代际/停止和C11旧入口/UnknownAny/crypto局部要求。S3C独立定义、完整C06和C11矩阵仍未找到；详见REMOTE_ACCEPTANCE_SOURCE_AUDIT.md。

C02 三个新切片已与B01/main211普通组合，28个定向计划尚未原生运行。C03已开始工具实施，固定四case实际0轮；独立审查发现policy摘要与原exec未绑定的问题并正在修复。X02静态找到IPv6括号host传递问题，::1实际RED测试准备中，尚未证明运行时缺陷或DNS64兼容。任务级当前完成2、进行中12、待启动1、条件候选7。
