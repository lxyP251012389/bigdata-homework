#!/usr/bin/env bash
# verify_push.sh —— 判定本地分支是否已真正同步到远程
# 核心原则：推送是否成功只看远程 SHA 是否等于本地 SHA，不看 push 命令退出码
# 用法: bash verify_push.sh [remote] [branch]   （默认 origin + 当前分支）

set -u
remote="${1:-origin}"
branch="${2:-$(git branch --show-current)}"

local_sha=$(git rev-parse HEAD 2>/dev/null) || { echo "ERROR: 当前目录不是 git 仓库"; exit 2; }
[ -n "$branch" ] || { echo "ERROR: 无法确定当前分支"; exit 2; }

remote_sha=$(git ls-remote "$remote" "refs/heads/$branch" 2>/dev/null | head -1 | cut -f1)

if [ -z "$remote_sha" ]; then
  echo "REMOTE_MISSING: 远程分支 $remote/$branch 不存在，或网络不可达（可用 api.github.com 通道二次确认）"
  exit 3
fi

short_local="${local_sha:0:7}"
short_remote="${remote_sha:0:7}"

if [ "$local_sha" = "$remote_sha" ]; then
  echo "SYNCED: 本地 $short_local = 远程 $short_remote ($remote/$branch)，已同步"
  exit 0
else
  unpushed=$(git rev-list --count "$remote_sha..$local_sha" 2>/dev/null)
  unpulled=$(git rev-list --count "$local_sha..$remote_sha" 2>/dev/null)
  echo "NOT_SYNCED: 本地 $short_local != 远程 $short_remote ($remote/$branch)"
  echo "本地有 $unpushed 个提交未推送；远程有 $unpulled 个提交未拉取"
  exit 1
fi
