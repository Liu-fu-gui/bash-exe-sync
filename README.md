# bash-exe 自动独立备份

[![Backup bash-exe](https://github.com/Liu-fu-gui/bash-exe-sync/actions/workflows/sync.yml/badge.svg)](https://github.com/Liu-fu-gui/bash-exe-sync/actions/workflows/sync.yml)

- **上游：** https://github.com/baocode-dev/bash-exe
- **独立备份：** https://github.com/Liu-fu-gui/bash-exe
- **运行记录 / 手动同步：** https://github.com/Liu-fu-gui/bash-exe-sync/actions/workflows/sync.yml

## 行为

每 5 分钟安排检查（UTC 每小时 02、07、12……57 分），有变更时复制全部 Git 分支、标签和完整历史。GitHub 调度可能延迟或漏跑，**不是秒级实时，也不是五分钟 SLA**。电脑关机不影响云端运行。

上游删除仓库、访问失败或变成空仓库时，任务报错但不修改备份。上游删除的分支和标签仍保留。分支强推或标签移动前，将旧对象保存为 `__backup_history/<旧对象SHA>` 归档标签；正常快进更新无需另建归档，因为历史仍可达。保留 `__backup_history/` 标签命名空间，上游若使用它则安全停止并报错。

备份仓库不是 fork，且仓库级 Actions 已关闭。同步只在本管理仓库中运行，绝不 checkout、执行上游脚本或工作流。私钥以 `BACKUP_SSH_KEY` Secret 保存，对应 deploy key 只对备份仓库可写；SSH 固定 GitHub ED25519 主机公钥。

管理仓库每 30 天自动生成一次保活提交，包括上游读取失败的情况，用于预防公开仓库 60 天无活动时定时任务被停用。如果 GitHub 已停用工作流，需在 Actions 页面手动启用；任务无法自救 GitHub 平台故障或账号/仓库停用。

## 范围与注意事项

这是 Git 数据备份，不备份 issues、PR、Release 附件、wiki、LFS 外部实体或子模块所指向的其他仓库。部署时上游没有 Release。两次检查之间刚推送又删库的内容无法保证捕获。

请勿直接修改备份仓库中与上游同名的分支或标签：下一次同步会以源库为准（旧 tip 会被归档）。要自行开发，请使用独立命名的分支。

公开仓库使用 GitHub 标准 Linux runner。GitHub 现行政策下该 runner 用于公开仓库不计费；未来政策变化以 GitHub 为准。

## 检查与恢复

1. 打开运行记录，确认最近任务成功；需要立即检查时点击 **Run workflow**。
2. 失败通知由 GitHub 账号的 Actions 通知设置决定，建议开启。
3. 上游删库后直接使用独立备份，停用管理仓库的工作流即可停止重复报错。
4. 完整下载：`git clone --mirror https://github.com/Liu-fu-gui/bash-exe.git`（这里是本地 clone，不是会传播远端删除的 push --mirror）。
5. 密钥轮换：给备份仓库安装新的可写 deploy key，更新本仓库 `BACKUP_SSH_KEY`，验证成功后删除旧 deploy key。

## 本地测试

运行 `python3 -I -m unittest discover -s tests -v`。测试只使用临时本地 Git 仓库，不需要 GitHub 凭据。
