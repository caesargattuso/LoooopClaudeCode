# Claude Automated Development Toolkit (Loooop)

An automated development tool based on Claude Code CLI that decomposes requirements documents into task lists and automatically executes them in loops until completion.

## Directory Structure

```
skill/
├── skill.md       # Skill definition file
├── run.py         # Main controller script
└── task_utils.py  # Task management utility functions
```

## Core Workflow

1. **Task Decomposition** - Claude analyzes all requirements documents in docs directory and decomposes into subtasks
2. **Smart Execution** - Automatically selects next task based on priority and dependencies
3. **Code Generation** - All code files are placed in `src/` directory by default
4. **Progress Tracking** - Claude automatically writes task summaries to `src/.looop/progress.txt`
5. **Git Commit** - Claude automatically executes git add, git commit
6. **Git Push** - Use `--push` parameter to automatically push to remote repository

## File Storage Location

All task-related files are stored in `src/.looop/` directory:

| File | Path | Description |
|------|------|------|
| tasks.json | `src/.looop/tasks.json` | Task list data |
| progress.txt | `src/.looop/progress.txt` | Task progress records |

## Parameters

| Parameter | Required When | Description |
|------|---------|------|
| `--docs <DIR>` | Decomposing requirements | Requirements document directory path |
| `--src <DIR>` | Always required | Code storage directory path |

## Usage

### 1. Decompose Requirements Documents

```bash
# Claude automatically reads all documents in docs directory and writes to tasks.json
python skill/run.py --docs docs --src src --decompose

# Decompose and push to remote repository
python skill/run.py --docs docs --src src --decompose --push
```

### 2. View Task Status

```bash
python skill/run.py --src src --status
```

### 3. Automatically Execute Tasks

```bash
# Execute all tasks
python skill/run.py --src src

# Execute tasks and push to remote repository
python skill/run.py --src src --push

# Execute only specified number of tasks (for testing)
python skill/run.py --src src --max-tasks 1
```

### 4. Manual Intervention Management

```bash
# Mark task as needing manual intervention
python skill/run.py --src src --mark-manual 3

# View all tasks needing manual intervention
python skill/run.py --src src --list-manual

# Restore task status after handling
python skill/run.py --src src --resolve-manual 3
```

## Optional Parameters

| Parameter | Short | Description |
|------|------|------|
| `--decompose` | `-d` | Decompose all requirements documents in docs directory |
| `--status` | `-s` | Show current task status |
| `--mark-manual ID` | `-M` | Mark specified task as needing manual intervention |
| `--list-manual` | `-L` | List all tasks needing manual intervention |
| `--resolve-manual ID` | `-R` | Restore task to pending status |
| `--max-tasks N` | `-m` | Maximum tasks to execute (0=unlimited) |
| `--push` | `-P` | Execute git push after task completion |

## tasks.json Data Structure

```json
{
  "project": "Project name",
  "created_at": "YYYY-MM-DD",
  "docs_dir": "docs",
  "src_dir": "src",
  "requirements_docs": ["docs/xxx.md"],
  "tasks": [
    {
      "id": 1,
      "name": "Task name",
      "description": "Detailed description",
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

## Task Status

| Status | Description |
|------|------|
| `pending` | Pending execution |
| `in_progress` | Currently executing |
| `completed` | Completed |
| `blocked` | Blocked (dependencies incomplete) |
| `needs_manual` | Needs manual intervention |

## Smart Selection Strategy

The system automatically selects the next task following these rules:

1. **Dependencies First** - Ensure all dependency tasks are completed
2. **Priority Sorting** - high > medium > low
3. **Skip Manual** - Automatically skip tasks with `needs_manual` status

## Dependencies

- Python 3.x
- Claude Code CLI (`claude` command available)
- Git (optional, for automatic commits)

---

[中文版本](README.zh-CN.md)