# bash-exe 独立持续备份设计

用户于 2026-11-17 批准执行：以 GitHub Actions 每 5 分钟检查代替秒级实时，允许 GitHub 调度延迟。

## 目标与约束
- 公开独立仓库 Liu-fu-gui/bash-exe 保存 baocode-dev/bash-exe 的全部分支、标签和 Git 历史，不建立 fork 依赖。
- 公开管理仓库 Liu-fu-gui/bash-exe-sync 存放可信工作流、同步脚本、测试、文档。目标仓库关闭 Actions，不执行上游代码。
- 专用可写 SSH deploy key 仅授权目标仓库，私钥只放控制仓库 Actions Secret。
- 上游读取失败、空仓库、分支/标签删除均不得删除备份；不使用 push --mirror 或 --prune。上游已有分支/标签的更新（包括 force push）同步到同名引用。
- 强推或移动标签时，将旧对象归档到 `refs/tags/__backup_history/<SHA>`，与新引用原子提交，防止旧历史失去可达引用；正常快进不需要额外归档。
- 每 5 分钟安排一次检查，提供 workflow_dispatch；并发串行、任务超时、失败可见。管理仓库每 30 天产生保活提交以避免公开仓库 60 天不活动停用。
- 当前上游没有 Releases；本期复制 Git 数据，不包括 GitHub issues、PR、Release 附件、外部 LFS 对象或子模块仓库。GitHub 本身故障或两次轮询之间删库无法保证最后一次更新被抓取。

## Approaches
- 秒级常开服务器监听：更快，但用户选择不依赖服务器。
- GitHub Actions 每 5 分钟轮询：用户已选择，免费公开 Linux runner，无秒级保证。
- 单纯 fork/手动同步：无法满足自动更新及隔离运行上游工作流的要求，不采用。

## 验收
本地使用临时 Git 仓库测试分支、标签、完整历史、更新、删除保留、上游不可访问、空上游；部署后手动运行真实 Actions 并逐一核对上游所有 refs 的 SHA。检查目标 Actions 关闭、deploy key 权限、工作流启用，并在本地索引记录执行结果。
