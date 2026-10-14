# 网络核心移交包

原始检查点说明保留如下；当前以报告第九节和PROGRESS.json为准。当前已验main03674990；原#202/#203/#204/#205/#207及新增#208/#211均完整CI后普通合并。30发布26普通合并4待验：#209 current4fa full13/68exact、#210 current84a相关7检查、#212325e full11/28exact、#213c18e full12已本机验证，各自完整CI仍待验。#210额外314工具中313通过1restart凭据缺失，独立诊断未复现、旧原因未知；不得写整套通过。B03当前91/full14原生进行中；Managed61、C03实际4轮、N02新12轮、N03实际9轮仍待原生。C01原supervisor切片和Linux应用暂停工具实施中。局部通过不等于全任务完成；旧失败及缺失完整S3C/C06/C11定义保留。环境仅本机/GitHubCI，子代理GPT-6.1 Sol ultra。

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
