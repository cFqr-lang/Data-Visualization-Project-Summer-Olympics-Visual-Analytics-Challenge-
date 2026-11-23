# 团队权限与分支保护

本文档约定四个任务的 GitHub 权限、目录归属与分支保护规则。用户名确认后，把表格中的“待填”替换为真实 GitHub 用户名。

## 1. 角色建议

| 角色 | GitHub 权限 | 适用对象 | 能做什么 |
| --- | --- | --- | --- |
| Admin | Admin | 仓库所有者 / 组长 | 管理协作者、分支保护、仓库设置 |
| Write | Write | 四名任务负责人 | 推送分支、开 PR、合并已审批 PR |
| Triage | Triage | 指导老师 / 外部评审（可选） | 管理 Issue 与 PR，不能推代码 |
| Read | Read | 围观成员（可选） | 只读 |

建议：组长 Admin，其余三名组员 Write。不建议给组员 Admin。

## 2. 成员与目录归属

| 成员 | GitHub 用户名 | 角色 | 负责目录 | CODEOWNERS |
| --- | --- | --- | --- | --- |
| 组长 / 仓库所有者 | @cFqr-lang | Admin | 统筹、`.github/`、`scripts/` | `*` |
| 任务一 | @chuhaowang | Write | `task1-data/`、`contracts/` | `/task1-data/`、`/contracts/` |
| 任务二 | @cFqr-lang（兼） | Write | `task2-visual/` | `/task2-visual/` |
| 任务三 | @shengmy-git | Write | `task3-insights/` | `/task3-insights/` |
| 任务四 | @Smoggyzz | Write | `task4-bonus/` | `/task4-bonus/` |

> CODEOWNERS 位于 `.github/CODEOWNERS`。填入真实用户名后取消对应注释，并在分支保护中开启 “Require review from Code Owners”。

## 3. 分支保护规则（main）

建议在 GitHub 网页或脚本中开启：

- Require a pull request before merging
- Required approvals：1
- Dismiss stale pull request approvals when new commits are pushed
- Require conversation resolution before merging
- Require linear history
- Do not allow force pushes
- Do not allow deletions
- 可选：Require review from Code Owners
- 可选：Require status checks to pass（等 CI 就绪后再开）

## 4. 网页操作步骤

### 添加协作者

1. 打开仓库 → **Settings** → **Collaborators and teams**；
2. 点击 **Add people**；
3. 输入组员 GitHub 用户名，权限选择 **Write**；
4. 重复添加其余组员；
5. 组员接受邮件邀请后生效。

### 开启分支保护

1. 仓库 → **Settings** → **Branches**；
2. **Add branch protection rule**；
3. Branch name pattern 填 `main`；
4. 勾选第 3 节的规则；
5. 保存。

## 5. 脚本操作（推荐）

仓库提供 `scripts/github_setup.ps1`，可批量添加协作者并开启 main 分支保护。

```powershell
# 1. 生成一个有 repo / administration 权限的 GitHub PAT
#    经典 PAT 勾选 repo；细粒度 PAT 至少需要：
#    Administration: Read and write、Contents: Read、Metadata: Read
# 2. 不要把 token 写入文件或提交到仓库
$env:GITHUB_TOKEN = "<你的 PAT>"

# 3. 预览
.\scripts\github_setup.ps1 -Collaborators "user1","user2","user3" -DryRun

# 4. 执行：添加写权限 + 保护 main
.\scripts\github_setup.ps1 -Collaborators "user1","user2","user3" -Permission push -ProtectMain

# 5. CODEOWNERS 填好后，再强制 Code Owner 审批
.\scripts\github_setup.ps1 -ProtectMain -RequireCodeOwnerReviews
```

脚本默认绕过系统代理（本机代理可能未启动）；如你的网络必须走代理，加 `-UseSystemProxy`。

## 6. 安全约定

- PAT 只放在环境变量或脚本的安全输入中，不写入仓库、不截图、不粘贴到 Issue。
- 发现 token 泄露，立即在 GitHub Settings → Developer settings 撤销。
- `.env`、`*.pem`、`*.key` 已被 `.gitignore` 忽略。
- 原始数据与清洗后大文件不入库，避免超出 GitHub 单文件限制。

## 7. 仍需补充的信息

- [x] 任务一 @chuhaowang、任务三 @shengmy-git、任务四 @Smoggyzz（已邀请 Write）
- [ ] 是否需要外部指导老师只读权限
- [ ] 是否启用 Code Owner 强制审批
