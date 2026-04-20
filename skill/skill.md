---
name: looop
description: Claude Automated Development Toolkit - Decompose requirements documents into task lists and automatically execute in loops until project completion
---

# Claude Automated Development Toolkit

You are an automated development assistant responsible for decomposing project requirements documents into executable task lists and automatically executing each task in loops until the project is complete.

## Parameters

| Parameter | Required When | Description |
|------|---------|------|
| `--docs <DIR>` | Decomposing requirements | Requirements document directory path |
| `--src <DIR>` | Always required | Code storage directory path |

## File Storage Location

All task-related files are stored in `src/.looop/` directory:

| File | Path | Description |
|------|------|------|
| tasks.json | `src/.looop/tasks.json` | Task list data |
| progress.txt | `src/.looop/progress.txt` | Task progress records |

## Execute Script

```bash
python skill/run.py --src <DIR> [--docs <DIR>] [other parameters]
```

## Core Workflow

### Phase 1: Task Decomposition (requires docs + src)

Command: `python skill/run.py --docs <requirements_dir> --src <code_dir> --decompose`

The script will automatically:
1. Create `src/.looop/` directory
2. Read all documents in requirements directory (.md, .txt, .json files)
3. Call Claude to analyze and decompose into independent small tasks
4. Set ID, name, description, priority, dependencies for each task
5. Save task list to `src/.looop/tasks.json`

### Phase 2: Task Execution (only requires src)

Command: `python skill/run.py --src <code_dir>`

The script will first check if `src/.looop/tasks.json` exists:
- Not exists → Prompt to run `--decompose` first
- Exists → Automatically execute tasks in loops

Execution process:
1. Select next executable task from tasks.json
2. Call Claude to execute task, code goes into src directory
3. Record progress to progress.txt
4. Update task status, execute git commit
5. Continue next round until all tasks complete

## Optional Parameters

| Parameter | Short | Description |
|------|------|------|
| `--decompose` | `-d` | Decompose requirements documents into task list |
| `--status` | `-s` | View task status statistics |
| `--max-tasks <N>` | `-m <N>` | Maximum N tasks to execute |
| `--push` | `-P` | Execute git push after completion |
| `--mark-manual <ID>` | `-M <ID>` | Mark task as needing manual intervention |
| `--list-manual` | `-L` | List tasks needing manual intervention |
| `--resolve-manual <ID>` | `-R <ID>` | Restore task to pending status |

## Usage Examples

```
# Decompose requirements (requires docs + src)
python skill/run.py --docs docs --src src --decompose

# Execute tasks (only requires src)
python skill/run.py --src src

# View status
python skill/run.py --src src --status

# Execute max 3 tasks and push
python skill/run.py --src src --max-tasks 3 --push
```

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
      "status": "pending"
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
| `blocked` | Blocked |
| `needs_manual` | Needs manual intervention |

## Execution Flow

1. **Receive parameters** - Parse src (required) and optional docs
2. **Build command** - Build python command based on parameters
3. **Execute script** - Run skill/run.py using Bash tool
4. **Output results** - Display execution output and progress