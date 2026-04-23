# Claude Automated Development Toolkit (Loooop)

An automated development tool based on Claude Code CLI that decomposes requirements (from documents, single files, or inline text) into task lists and automatically executes them in loops until completion.

## Directory Structure

```
skill/
├── skill.md       # Skill definition file
├── run.py         # Main controller script
└── task_utils.py  # Task management utility functions
```

## Core Workflow

1. **Task Decomposition** - Claude analyzes requirements (documents/single file/inline text) and decomposes into subtasks
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
| `--docs <DIR>` | Decomposing requirements directory | Requirements document directory path |
| `--doc <FILE>` | Decomposing single doc file | Single requirements document file path |
| `--requirement <TEXT>` | Decomposing inline requirement | Direct requirement text string |
| `--src <DIR>` | Always required | Code storage directory path |

**Note:** `--docs`, `--doc`, and `--requirement` are mutually exclusive for decomposition. Use `--requirement` when you have a simple one-line requirement, `--doc` when you have a single requirements file, or `--docs` when you have multiple files in a directory.

## Usage

### 1. Decompose Requirements

```bash
# Decompose from requirements directory
python skill/run.py --docs docs --src src --decompose

# Decompose from single document file
python skill/run.py --doc docs/feature-x.md --src src --decompose

# Decompose from inline requirement text
python skill/run.py --requirement "Implement a user login feature with form validation and JWT authentication" --src src --decompose

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
| `--decompose` | `-d` | Decompose requirements documents or text into task list |
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
      "name": "Task name (concise, imperative)",
      "description": "Detailed technical description including: what to build, files to create/modify, key implementation points",
      "priority": "high|medium|low",
      "dependencies": [],
      "task_type": "setup|core|feature|refactor|test|docs",
      "estimated_files": ["expected_file_path_1"],
      "acceptance_criteria": ["Specific verifiable criteria"],
      "status": "pending",
      "result": null,
      "issues": [],
      "completed_at": null
    }
  ]
}
```

**Task Fields:**
| Field | Description |
|-------|-------------|
| `id` | Unique task identifier |
| `name` | Concise imperative name (e.g. 'Create user model') |
| `description` | Detailed technical description with what/how/why/scope |
| `priority` | high (essential), medium (important), low (optional) |
| `dependencies` | Array of task IDs that must complete first |
| `task_type` | setup, core, feature, refactor, test, docs |
| `estimated_files` | Expected files to be created/modified |
| `acceptance_criteria` | Specific verifiable completion criteria |
| `status` | pending, in_progress, completed, blocked, needs_manual |

**Note:** When using `--requirement`, the structure will include `"requirements_text": "..."` and `"docs_dir": null` instead of `"requirements_docs"` and `"docs_dir"`.

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

## Test Consolidation Strategy

Tests are unified into a single phase at the end instead of scattered throughout:

- **During development**: Focus on core functionality only, no per-task tests
- **Final testing phase**: ONE comprehensive test task covers all completed features
- **Benefits**: Faster iteration, unified test coverage, less task fragmentation

This is reflected in task decomposition:
- Test tasks are NOT created for individual features
- ONE unified test task is created at the end with dependencies on ALL feature tasks
- Example: "Write comprehensive tests for all completed features" (depends on IDs: 1,2,3,4,5...)

## Dependencies

- Python 3.x
- Claude Code CLI (`claude` command available)
- Git (optional, for automatic commits)

---

[中文版本](README.zh-CN.md)