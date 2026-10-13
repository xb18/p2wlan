# 网络核心移交包

原始检查点说明保留如下；当前继续实施状态以 PROGRESS.json.continuation.task_status_current 和报告第九节为准。#202/#203/#204/#205 已完整CI并普通合并，main为 `1845d1381e46596cbc42b0a3b14b55573b8dfd2f`。#207 已完整本机验收并非force推送 `4fbe60e`，同HEAD CI进行中。#203/#204旧本机汇总受共享缓存影响的同源码声明已纠正，独立GitHubCI不受影响。原B19补丁已经采用，不再重放。

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
