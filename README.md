# Claude 自动化开发套件

基于 Claude Code CLI 的自动化开发工具，将需求文档拆解为任务列表，自动循环执行直到完成。

## 核心流程

1. **拆解需求** - Claude 分析需求文档，拆解成可独立完成的子任务
2. **智能执行** - 按优先级和依赖关系自动选择下一个任务执行
3. **进度跟踪** - Claude 自动将任务总结写入 `progress.txt`
4. **Git 提交** - Claude 自动执行 git add 和 commit
5. **人工干预** - 需要人工处理的任务自动标记，跳过执行

## 项目结构

```
LoooopClaudeCode/
├── run.py           # 主控脚本
├── task_utils.py    # 任务管理工具函数
├── tasks.json       # 任务数据文件
├── progress.txt     # 任务进度记录（Claude自动编写）
├── docs/            # 需求文档目录
│   └── example.md   # 示例需求文档
```

## 使用方法

### 1. 拆解需求文档

```bash
# Claude 自动读取 docs 目录下所有文档并写入 tasks.json
python run.py --decompose

# 或指定其他目录
python run.py --decompose my_docs
```

### 2. 查看任务状态

```bash
python run.py --status
```

输出示例：
```
项目: 示例项目
总任务: 7
已完成: 0
进行中: 0
待执行: 7
已阻塞: 0
需人工: 0
```

### 3. 自动执行任务

```bash
# 执行所有任务
python run.py

# 仅执行指定数量任务（测试用）
python run.py --max-tasks 1
```

### 4. 人工干预管理

```bash
# 标记任务需要人工干预
python run.py --mark-manual 3

# 查看所有需人工干预的任务
python run.py --list-manual

# 处理完成后恢复任务状态
python run.py --resolve-manual 3
```

## 命令参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--decompose [DIR]` | `-d` | 拆解docs目录下所有需求文档（默认docs） |
| `--status` | `-s` | 显示当前任务状态 |
| `--mark-manual ID` | `-M` | 标记指定任务需要人工干预 |
| `--list-manual` | `-L` | 列出所有需人工干预的任务 |
| `--resolve-manual ID` | `-R` | 恢复任务为待执行状态 |
| `--max-tasks N` | `-m` | 最大执行任务数（0=无限制） |

## 任务数据结构 (tasks.json)

```json
{
  "project": "项目名称",
  "created_at": "2026-04-17",
  "requirements_docs": ["docs/example.md", "docs/snake_game.md"],
  "tasks": [
    {
      "id": 1,
      "name": "任务名称",
      "description": "详细描述",
      "priority": "high|medium|low",
      "dependencies": [],
      "status": "pending|in_progress|completed|blocked|needs_manual",
      "result": null,
      "issues": [],
      "completed_at": null
    }
  ]
}
```

## 任务状态说明

| 状态 | 说明 |
|------|------|
| `pending` | 待执行 |
| `in_progress` | 正在执行 |
| `completed` | 已完成 |
| `blocked` | 已阻塞（依赖未完成） |
| `needs_manual` | 需要人工干预 |

## 进度记录 (progress.txt)

每个任务完成后，Claude 自动将进度追加到 `progress.txt` 文件开头：

```
========================================
任务 #1: 创建任务数据结构
时间: 2026-04-17 17:30:00
状态: completed
----------------------------------------
完成事项:
- 定义了Task类
- 实现了任务列表数据结构
----------------------------------------
遗留问题:
- 无
========================================
```

## 智能选择策略

系统自动选择下一个任务时遵循以下规则：

1. **依赖优先** - 确保所有依赖任务已完成
2. **优先级排序** - high > medium > low
3. **跳过人工** - 自动跳过 `needs_manual` 状态的任务

## 依赖

- Python 3.x
- Claude Code CLI (`claude` 命令可用)
- Git（可选，用于自动提交）