# 贡献指南

这个仓库使用 GitHub + SSH 协作。请每个人使用自己的 GitHub 账号和 SSH 密钥。

## 首次配置

先安装 Git，然后配置你的身份：

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

生成 SSH 密钥，并把公钥添加到你的 GitHub 账号：

```bash
ssh-keygen -t ed25519 -C "你的邮箱"
cat ~/.ssh/id_ed25519.pub
```

测试连接：

```bash
ssh -T git@github.com
```

## 获取代码

克隆仓库：

```bash
git clone git@github.com:Grampus-K/GRobot.git
cd GRobot
```

## 日常开发流程

开始工作前，先更新 `main`：

```bash
git switch main
git pull origin main
```

每个任务都新建一个功能分支：

```bash
git switch -c feature/your-task
```

修改完成后提交并推送：

```bash
git add .
git commit -m "简短清晰的提交信息"
git push -u origin feature/your-task
```

然后在 GitHub 上发起 Pull Request，评审通过后合并到 `main`。

## 分支命名

- `feature/xxx`：新功能
- `fix/xxx`：修复问题
- `refactor/xxx`：代码整理或重构
- `test/xxx`：测试相关工作

## 拉取最新代码

如果你只需要同步公共主分支：

```bash
git switch main
git pull origin main
```

如果你还在继续维护自己的分支：

```bash
git fetch origin
git rebase origin/main
```

## 合并冲突

如果 Git 提示冲突：

1. 先用 `git status` 查看冲突文件
2. 手动修改冲突内容
3. 提交解决后的文件
4. 完成 `git commit`

## 提交规范

- 一次提交只做一类事情
- 提交信息要短而明确
- 不要提交 `build/`、`install/`、`log/` 这类编译产物
