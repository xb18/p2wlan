# 网络核心移交包

原始检查点说明保留如下；当前以报告第九节和PROGRESS.json为准。原#202/#203/#204/#205/#207和新增#208/#211均已完整适用CI后普通合并，最新已验main为03674990c4956df5580f2b56cb1aad83c645de36；28发布、26合并、#209/#210两批待验。#211同源Linux故障证据已验，完整D03跨平台矩阵仍未完成。#209此前66exact/13项本地通过，close严格截止修复及common两项真实canonical新请求/替换拒旧恢复已通过；现普通整合main211，68exact/13项运行中，未推送。#210旧4ab CI出现Relay3/4实际进程失败，Relay3日志明确stack overflow；已有最小Cshim修复普通组合main211，新工具检查运行中，实际CI效果待验，原失败保留。B01/C02新组合28exact尚未原生，B03/Managed待组合验收；N02新同shim12轮、N03固定9轮、C03固定4轮均尚未实际执行。C03摘要绑定缺陷修复中，X02实际IPv6测试准备中。任务级完成2、进行中12、待启动1、条件候选7；局部证据不等于全任务完成。环境仅本机/GitHubCI，子代理统一GPT-6.1 Sol ultra，全部旧失败和缺失原定义保留。

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
