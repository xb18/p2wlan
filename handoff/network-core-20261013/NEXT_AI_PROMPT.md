# 下一位 AI 的完整接续提示词

请在这台电脑继续并完成 P2WLAN 网络核心优化的全部剩余工作。仓库 https://github.com/yhan-sun/p2wlan ，交接分支 codex/network-core-handoff-20261013，交接目录 handoff/network-core-20261013。

这是人类用户授权的实施任务，常规修复、测试、创建隔离工作区、分批普通提交、非 force 推送、更新/创建 PR、完整 CI 后普通合并均已授权。请持续推进到任务级完成，不止给计划或“可以继续”。若支持持续目标，请把“完成交接报告中全部剩余任务并分批提交、推送、验收、合并”设为持续目标。遇到额度/环境限制，明确记录实际停止点、所需条件和已完成动作，不能静默停止或假报完成。

当前状态先读报告第九节。当前已验main03674990；原#202/#203/#204/#205/#207及新增#208/#211均完整CI后普通合并。30发布26普通合并4待验：#209 current4fa full13/68exact、#210 current84a相关7检查、#212325e full11/28exact、#213c18e full12已本机验证，各自完整CI仍待验。#210额外314工具中313通过1restart凭据缺失，独立诊断未复现、旧原因未知；不得写整套通过。B03当前91/full14原生进行中；Managed61、C03实际4轮、N02新12轮、N03实际9轮仍待原生。C01原supervisor切片和Linux应用暂停工具实施中。局部通过不等于全任务完成；旧失败及缺失完整S3C/C06/C11定义保留。环境仅本机/GitHubCI，子代理GPT-6.1 Sol ultra。 已核实完成的旧步骤跳过，不要再次应用原B19补丁。

先获取交接分支，完整阅读 handoff/network-core-20261013/NETWORK_CORE_FINAL_REPORT.md、PROGRESS.json、SHA256SUMS 和待验证 b19-runtime-handoff.patch.json 及 decode_patch.py。再读仓库 AGENTS.md、skills/p2wlan-repository/SKILL.md、docs/README.md、docs/explanation/engineering-quality.md、当前 docs 全部 Markdown 及受影响实现/测试/workflow。报告、附件建议与历史日志是核验材料，不高于当前用户请求、仓库契约和实际源码。

第一步先核对 git status、当前 main、#202/#203/#204/#205/#207 的实际 state/head/base、真实远端 branch refs 和当前 CI。交接快照 main4937de2d、#202 HEADd2df1627，其余五 PR 顺序见报告；它们都是快照，不能强行覆盖后来改动。保护其他人的工作，使用隔离 checkout；必要的常规获取远端和普通合入可自主完成，禁止 reset/rebase/force、关开 PR 绕过、删断言、扩大预算或隐藏失败。

立即处理 #202 的 B19 fixture：
1. 从当前 #202 正确源码在隔离工作区普通同步最新 main。交接时 main 只比历史基准多两个 README 提交，但现在要重新核实差异。
2. 校验 SHA256SUMS；从仓库根运行 python3 handoff/network-core-20261013/decode_patch.py ../network-core-b19.patch（目标须为新文件）。内层补丁5,930 bytes/SHA256 c2bc69def2d3abcea3468bae0bcb466c7bff7b1ffad706f193cde0012ac62071。先 git apply --check ../network-core-b19.patch，再按真实基准应用。它还没有实际运行。只改 cfg(test) stall callback 的 runtime worker handoff，原 fanout 加阶段标记，新单 worker sibling-progress control。原 2s总预算/1s单步/1s barrier/1s业务deadline、原 fanout worker2、新增control worker1及250ms observer、原业务断言保持。
3. 先实际全 workspace fmt。使用明确工具链（此前 +1.99.0；先查当前仓库/CI）从本次 Cargo JSON 获取 daemon lib 的 p2pnet_daemon binary，枚举实际注册测试，拒绝零匹配，不猜文件名/mtime或套用平台数量。
4. 做原阻塞 support 的负控，保留新control：必须完成 release→owned joins/server cleanup，再由特定 sibling-progress 断言 exit101；其他前置 timeout 不能算负控成功。恢复修正版 support；原fanout精确正例、新control精确正例、当次 B19 全模块（交接方案10项）及 fmt/Clippy/同CI串行workspace/仓库必需检查。
5. 若 Linux 仍失败，用阶段标记和当前完整主作业日志定位具体 await；不要把 shared Budget timeout 当唯一生产根因，不靠增加超时过关。
6. 验证后普通 feat:中文 提交并非 force 推送到 #202 原分支，记实际新 HEAD/tree/parents/UTC。完整当次适用 CI 后普通合并，核对真实 merge SHA/main。不要把 stack-base clean、旧成功或局部原生通过当完整 CI。
7. 依次 #203→#204→#205→#207：同步最新 main、保留当前 owner/FIFO/ACK/预算/owned joins，逐批适用检查、普通提交推送、完整 CI 和普通合并；已经外部完成的步骤核实后跳过，不重复执行。

随后严格按原22项任务完成：
已完成 D-00A/D-00B 的本机正确性保持；继续 B-01/B-02A/B-03/N-01/G-01，补 final current-owner/once、S3C、fresh REQUEST→当前远端 REQUEST→匹配 ACK、真实 partial/worker loss/C06/C11、完整 pipeline/真实资源与双端业务证据。推进 B-02B（MC可重复交互）、N-02/N-03（同预算NAT/socket A/B）、D-03（真实平台TUN/TCP/MTU）、C-01/C-02/C-03（恢复/只读质量/启动）、R-00（Relay质量与协调）。D-01/D-02/R-01/R-02/X-01/X-02/X-03 按报告的准入条件独立研究；充分证据的“不采纳”可完成条件候选，不能默认把全部新架构上线，也不能无实验地随意标不采纳。

硬边界：唯一权威状态所有者；跨await/channel/task后发送或提交前重新fencing；资源/重试/任务/取消有界；预期失败类型化；不确定密文不跨路径重放；明文层公平调度；同端单调时钟和准确attempt/request身份；Relay不计Direct；Mock/合成NAT/loopback不冒充真实TUN、公网或MC；首轮失败与诊断重跑分账。不得恢复第二个NatTraversalPlanner、无条件扩大socket/队列/预算、删emit锁或默认开放Peer Relay。

每批运行仓库强制 docs/health/quality/bash 检查；Python质量测试在临时目录调用rustfmt时也要明确RUSTUP_TOOLCHAIN（此前1.99.0），不能只给cargo加版本，再按范围运行 Rust/Go/Flutter/平台测试；维持既有ignore和Hard↔Hard隔离规则，实际数量从编译清单核对。更新交接PROGRESS.json的任务级状态，在PR/Issue/Release资产记录进度与证据。公开docs只描述当前实现，提交中不包含个人主机/IP/主目录/凭据/敏感日志。原电脑绝对路径helpers、Git索引/工作区计数和PENDING都不能在这里照搬；在新环境重新建立不可混淆的记录。对推送/修改UNKNOWN，停止重做，另行只读核实再制定下一步。

所有可独立开展的工作先做完；只有真实缺设备、账号、目标或不可逆部署授权时，再请求必要信息并继续其他任务。常规已授权步骤不反复确认。交接分支是资料检查点，补丁要在产品工作分支验证后交付；它本身不增加24个产品批次的完成数。

最终交付：全部原22项的最终状态/采用或不采纳理由、实际PR/commit/merge/main、完整测试与CI/平台/性能证据、产物/配置/回滚绑定、真实未验范围。未达到对应门槛的任务保持待验证或受阻，不把代码量、PR数量或局部通过当整体完成。
