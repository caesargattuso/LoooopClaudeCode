# Claude 自动化开发套件 (Loooop)

基于 Claude Code CLI 的自动化开发工具，将需求文档拆解为任务列表，自动循环执行直到完成。

## 目录结构

```
skill/
├── skill.md       # Skill 定义文件
├── run.py         # 主控脚本
└── task_utils.py  # 任务管理工具函数
```

## 核心流程

1. **任务拆解** - Claude 分析 docs 目录下所有需求文档，拆解成子任务
2. **智能执行** - 按优先级和依赖关系自动选择下一个任务执行
3. **代码生成** - 所有代码文件默认放入 `src/` 目录
4. **进度跟踪** - Claude 自动将任务总结写入 `src/.looop/progress.txt`
5. **Git 提交** - Claude 自动执行 git add、git commit
6. **Git Push** - 使用 `--push` 参数可自动推送到远程仓库

## 文件存放位置

所有任务相关文件存放在 `src/.looop/` 目录下：

| 文件 | 路径 | 说明 |
|------|------|------|
| tasks.json | `src/.looop/tasks.json` | 任务列表数据 |
| progress.txt | `src/.looop/progress.txt` | 任务进度记录 |

## 参数说明

| 参数 | 必填时机 | 说明 |
|------|---------|------|
| `--docs <目录>` | 拆解需求时必填 | 需求文档目录路径 |
| `--src <目录>` | 总是必填 | 代码存放目录路径 |

## 使用方法

### 1. 拆解需求文档

```bash
# Claude 自动读取 docs 目录下所有文档并写入 tasks.json
python skill/run.py --docs docs --src src --decompose

# 拆解后提交并推送到远程仓库
python skill/run.py --docs docs --src src --decompose --push
```

### 2. 查看任务状态

```bash
python skill/run.py --src src --status
```

### 3. 自动执行任务

```bash
# 执行所有任务
python skill/run.py --src src

# 执行任务并推送到远程仓库
python skill/run.py --src src --push

# 仅执行指定数量任务（测试用）
python skill/run.py --src src --max-tasks 1
```

### 4. 人工干预管理

```bash
# 标记任务需要人工干预
python skill/run.py --src src --mark-manual 3

# 查看所有需人工干预的任务
python skill/run.py --src src --list-manual

# 处理完成后恢复任务状态
python skill/run.py --src src --resolve-manual 3
```

## 可选参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--decompose` | `-d` | 拆解 docs 目录下所有需求文档 |
| `--status` | `-s` | 显示当前任务状态 |
| `--mark-manual ID` | `-M` | 标记指定任务需要人工干预 |
| `--list-manual` | `-L` | 列出所有需人工干预的任务 |
| `--resolve-manual ID` | `-R` | 恢复任务为待执行状态 |
| `--max-tasks N` | `-m` | 最大执行任务数（0=无限制） |
| `--push` | `-P` | 任务完成后执行 git push |

## tasks.json 数据结构

```json
{
  "project": "项目名称",
  "created_at": "YYYY-MM-DD",
  "docs_dir": "docs",
  "src_dir": "src",
  "requirements_docs": ["docs/xxx.md"],
  "tasks": [
    {
      "id": 1,
      "name": "任务名称",
      "description": "详细描述",
      "priority": "high|medium|low",
      "dependencies": [],
      "status": "pending",
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

## 智能选择策略

系统自动选择下一个任务时遵循以下规则：

1. **依赖优先** - 确保所有依赖任务已完成
2. **优先级排序** - high > medium > low
3. **跳过人工** - 自动跳过 `needs_manual` 状态的任务

## 依赖

- Python 3.x
- Claude Code CLI (`claude` 命令可用)
- Git（可选，用于自动提交）

---

[English Version](README.md)