# 网络核心移交包

原始检查点说明保留如下；当前以报告第九节与PROGRESS.json.continuation为准。原#202/#203/#204/#205/#207已顺序全CI普通合并；PR208 a7cd902也已通过17运行/18门禁、当前Linux32/32和协议采证后普通合并dbe5d67，最新main=dbe5d67f2142981e103b858cf82981696b5c1bb6。三个外部门禁首轮API403保留，依赖成功后按顺序重跑attempt2通过，1354文件封存已验。PR2098d新CI仍有Direct/Relay真实业务失败：当前Direct实证incoming source16006而reply selected endpoint16005，最终source guard会拒绝，正在做保持身份/预算的最小修复设计；不得归到API。B01原worker丢失切片完整11/4实际反例/恢复6通过，提交11d6676；C02首次miss selector与健康idle完整11通过，提交0be532f；二者均本地、未完整CI或采用。N01 e268原17CI结束但外部门禁API失败，现已普通整合新main无冲突暂存，门禁查询优化两文件108质量测试通过待组合。N02九原生+两计时反例通过，恢复及完整回归运行，6+6cold A/B未跑无收益结论。N03最小SOCKET_POOL透传候选静态通过，off/2/4固定9cold未跑。B03/Managed组合原生待验。D03手动Linux故障解除16新请求及五作业通过，完整PR采用待验。仅本机/GitHubCI，所有原失败保留；子代理GPT-6.1 Sol ultra。

本包对应产品源码检查点 d2df1627952191fe3d535d64ad6249723e1ba404。分支 codex/network-core-handoff-20261013 用于保存可移植交接资料。

在新电脑获取：

```bash
git clone https://github.com/yhan-sun/p2wlan.git
cd p2wlan
git switch --track origin/codex/network-core-handoff-20261013
cd handoff/network-core-20261013
shasum -a 256 -c SHA256SUMS
```

已有 checkout 先检查并保护现有修改，在隔离工作区读取交接分支。Windows 可用相应 SHA256 工具逐文件核对。

先读 [最终报告](NETWORK_CORE_FINAL_REPORT.md)，将 [完整提示词](NEXT_AI_PROMPT.md) 原文交给下一位 AI。任务和远端快照见 [PROGRESS.json](PROGRESS.json)。[补丁封装](b19-runtime-handoff.patch.json) 是待验证建议，产品源码尚未应用该版本。交接包的文档/脚本检查不证明补丁原生或 Linux CI 通过。

获取当前 PR 和源码后按报告接续实施。交接过程、快照和补丁不进入产品公共 docs；后续过程放对应 PR/Issue 或 Release 资产。

补丁采用 base64 JSON 无损封装，以保留标准 diff 的空白上下文。仓库根运行：

```bash
python3 handoff/network-core-20261013/decode_patch.py ../network-core-b19.patch
git apply --check ../network-core-b19.patch
```

解码器校验内层固定长度和 SHA256，拒绝覆盖已有目标。解码不代表应用或原生验收。Windows 可使用 python 替代 python3。
