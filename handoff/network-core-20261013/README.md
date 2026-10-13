# 网络核心移交包

原始检查点说明保留如下；当前以报告第九节与PROGRESS.json.continuation为准。原#202/#203/#204/#205/#207已顺序通过完整CI并普通合并，main48febb。PR209运行时VIP与Fresh确认标记修复8d0b64d已普通提交推送：50重点、2413工作区、247隔离、四实际负控及恢复8项均通过；新17次CI开始，旧5c的NAT失败保留。PR208 a7cd902当前Linux真实TUN32/32和11组/22句柄清理、Minecraft协议24+53及契约23/runner28已验，完整17次CI仍待验。N01 e2684e6已推送PR210，完整本机通过，17次CI待验。B03本地8a4dfc7已验未推送。D03 4b1f1db实际Linux黑洞解除后16新请求成功，同次手动workflow五作业全通过，仅该切片验收。B01原child-loss六项通过，四负控执行中；C02实际首次miss selector问题最小修复新1+旧4通过，新增idle-consent测试静态通过未原生；N02两文件同预算HH时序候选静态通过，9原生及6+6cold A/B未跑，未采用。Managed/dynamic七项待原生。仅本机和GitHubCI；子代理统一GPT-6.1 Sol ultra。

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
