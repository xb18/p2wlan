# 网络核心移交包

原始检查点说明保留如下；当前以报告第九节与PROGRESS.json.continuation为准。原#202/#203/#204/#205/#207及新增#208均已完整适用CI后普通合并；最新已验main为dbe5d67f2142981e103b858cf82981696b5c1bb6。原24批加#208共25批采用，#209/#210/#211三批待验。#209原8d真实Direct/Relay失败保留；新非对称46923b61及common-reader最小guard0b01d67各自原生正反例通过，但普通组合0632146首组22通过、1失败、1未运行，恢复新请求未进入echo捕获，14/14任务清理通过；正在诊断，未推送采用。#2104ab与#2111d当前完整CI进行中；#210 Ubuntu Rekey在checkout阶段超原30分钟取消、Rust未启动，同源原预算重跑失败作业，原记录保留。B01/C02原局部完整回归通过，main208组合与单RTT尖峰原生待验；B03/Managed组合待验。N02固定12轮已全部执行、零重试，各版本2轮证据有效及4轮栈溢出，全回收，无收益结论；模拟C拦截层修复3ce672d已通过实际旧C失败/新C正控、双Python及四门禁，daemon新矩阵/CI未验。N03固定9轮未跑。R00完整canonical与替换reader控制正在隔离实施。仅本机/GitHubCI，全部原失败与限制保留；子代理统一GPT-6.1 Sol ultra。

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
