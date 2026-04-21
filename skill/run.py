#!/usr/bin/env python3
"""Claude Automated Development Toolkit - Main Controller Script"""
import argparse
import subprocess
import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add skill directory to path for imports
_skill_dir = os.path.dirname(os.path.abspath(__file__))
if _skill_dir not in sys.path:
    sys.path.insert(0, _skill_dir)

from task_utils import (
    init_looop_dir, load_tasks, save_tasks, get_next_task,
    update_task_status, get_task_summary, mark_task_manual,
    STATUS_PENDING, STATUS_COMPLETED, STATUS_NEEDS_MANUAL
)


def get_looop_dir(src_dir: str) -> str:
    """Calculate .looop directory path from src directory"""
    return os.path.join(src_dir, ".looop")


def get_tasks_file(src_dir: str) -> str:
    """Calculate tasks.json file path from src directory"""
    return os.path.join(get_looop_dir(src_dir), "tasks.json")


def get_progress_file(src_dir: str) -> str:
    """Calculate progress.txt file path from src directory"""
    return os.path.join(get_looop_dir(src_dir), "progress.txt")


def check_claude_installed() -> bool:
    """Check if Claude CLI is installed"""
    try:
        result = subprocess.run(
            'claude --version',
            capture_output=True,
            text=True,
            shell=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_claude(prompt: str, cwd: str = None, timeout: int = 600) -> str:
    """Invoke Claude CLI to execute command

    Args:
        prompt: The prompt to send to Claude
        cwd: Working directory for Claude CLI (defaults to current directory)
        timeout: Maximum execution time in seconds (default 10 minutes)
    """
    print(f"\n{'='*60}")
    print("[Claude] Executing...")
    print(f"{'='*60}\n")
    sys.stdout.flush()

    env = os.environ.copy()
    if sys.platform == 'win32' and 'CLAUDE_CODE_GIT_BASH_PATH' not in env:
        try:
            result = subprocess.run('where bash', capture_output=True, text=True, shell=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    path = line.strip()
                    if 'Git' in path and 'bash.exe' in path:
                        env['CLAUDE_CODE_GIT_BASH_PATH'] = path
                        break
        except (subprocess.TimeoutExpired, Exception):
            pass

    cmd = 'claude -p --dangerously-skip-permissions --verbose --output-format stream-json'
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        shell=True,
        env=env,
        cwd=cwd
    )

    process.stdin.write(prompt)
    process.stdin.close()

    output_lines = []
    try:
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line, end='')
                sys.stdout.flush()
                output_lines.append(line)
    except KeyboardInterrupt:
        print("\n[Interrupted] Terminating Claude process...")
        process.terminate()
        process.wait(timeout=5)
        return "Execution interrupted by user"

    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"\n[Timeout] Process exceeded {timeout} seconds, terminating...")
        process.terminate()
        process.wait(timeout=5)
        return f"Execution timeout after {timeout} seconds"

    stderr = process.stderr.read()
    if process.returncode != 0:
        print(f"\nError: {stderr}")
        return f"Execution failed: {stderr}"

    return ''.join(output_lines)


def decompose_requirements(docs_dir: str, src_dir: str, push: bool = False) -> None:
    """Let Claude decompose requirements documents and write to tasks.json"""
    if not os.path.exists(docs_dir):
        print(f"Error: Requirements document directory does not exist - {docs_dir}")
        return

    init_looop_dir(src_dir)
    tasks_file = get_tasks_file(src_dir)

    doc_files = []
    for f in os.listdir(docs_dir):
        if f.endswith(('.md', '.txt', '.json')):
            doc_files.append(os.path.join(docs_dir, f))

    if not doc_files:
        print(f"No document files found in directory {docs_dir}")
        return

    doc_list = "\n".join(f'"{f}"' for f in doc_files)
    today = str(__import__('datetime').datetime.now().date())

    git_cmds = f'- git add "{tasks_file}"\n   - git commit -m "Task decomposition completed"'
    if push:
        git_cmds += "\n   - git push"

    prompt = f"""Please analyze all requirements documents in the "{docs_dir}" directory and decompose them into a specific development task list.

Requirements document paths:
{doc_list}

Code storage directory: "{src_dir}"
Task file storage path: "{tasks_file}"

Requirements:
1. Read all requirements document content
2. Analyze comprehensively and decompose into independent small tasks
3. Set reasonable task dependencies and priorities
4. Save the task list to "{tasks_file}" file in the following format:

{{
  "project": "Project name",
  "created_at": "{today}",
  "docs_dir": "{docs_dir}",
  "src_dir": "{src_dir}",
  "requirements_docs": ["{docs_dir}/xxx.md"],
  "tasks": [
    {{
      "id": 1,
      "name": "Task name",
      "description": "Detailed description",
      "priority": "high|medium|low",
      "dependencies": [],
      "status": "pending",
      "result": null,
      "issues": [],
      "completed_at": null
    }}
  ]
}}

5. After saving, execute git operations:
{git_cmds}

Please report the number of tasks after completion.
"""

    run_claude(prompt, cwd=src_dir)


def main():
    parser = argparse.ArgumentParser(description="Claude Automated Development Toolkit")
    parser.add_argument("--docs", "-D", metavar="DIR",
                        help="Requirements document directory path (required when decomposing)")
    parser.add_argument("--src", "-S", required=True, metavar="DIR",
                        help="Code storage directory path (required)")
    parser.add_argument("--decompose", "-d", action="store_true",
                        help="Decompose all requirements documents in the docs directory")
    parser.add_argument("--status", "-s", action="store_true",
                        help="Show current task status")
    parser.add_argument("--mark-manual", "-M", type=int, metavar="ID",
                        help="Mark specified task as needing manual intervention")
    parser.add_argument("--list-manual", "-L", action="store_true",
                        help="List all tasks needing manual intervention")
    parser.add_argument("--resolve-manual", "-R", type=int, metavar="ID",
                        help="Restore task from manual intervention to pending status")
    parser.add_argument("--max-tasks", "-m", type=int, default=0,
                        help="Maximum number of tasks to execute (0 means unlimited)")
    parser.add_argument("--push", "-P", action="store_true",
                        help="Execute git push after task completion")
    args = parser.parse_args()

    # Check Claude CLI installation before execution
    if not args.status and not args.list_manual:
        if not check_claude_installed():
            print("Error: Claude CLI is not installed or not in PATH")
            print("Please install Claude Code first: https://claude.ai/code")
            return

    init_looop_dir(args.src)
    tasks_file = get_tasks_file(args.src)
    progress_file = get_progress_file(args.src)

    # docs parameter is required when decomposing requirements
    if args.decompose:
        if not args.docs:
            print("Error: --docs parameter (requirements document directory) is required for decomposition")
            print("Usage: python skill/run.py --docs <directory> --src <directory> --decompose")
            return
        if not os.path.exists(args.docs):
            print(f"Error: Requirements document directory does not exist - {args.docs}")
            return
        decompose_requirements(args.docs, args.src, args.push)
        return

    if args.status:
        data = load_tasks(tasks_file)
        summary = get_task_summary(data)
        print(f"\nProject: {data.get('project', 'Unnamed')}")
        print(f"Requirements document directory: {data.get('docs_dir', args.docs or 'N/A')}")
        print(f"Code storage directory: {data.get('src_dir', args.src)}")
        print(f"Task file: {tasks_file}")
        print(f"Progress file: {progress_file}")
        print(f"Total tasks: {summary['total']}")
        print(f"Completed: {summary['completed']}")
        print(f"In progress: {summary['in_progress']}")
        print(f"Pending: {summary['pending']}")
        print(f"Blocked: {summary['blocked']}")
        print(f"Need manual: {summary['needs_manual']}")
        return

    if args.mark_manual:
        data = load_tasks(tasks_file)
        if mark_task_manual(data, args.mark_manual, "User manually marked", tasks_file):
            print(f"Task #{args.mark_manual} has been marked as needing manual intervention")
        else:
            print(f"Task #{args.mark_manual} not found")
        return

    if args.list_manual:
        data = load_tasks(tasks_file)
        manual_tasks = [t for t in data["tasks"] if t["status"] == STATUS_NEEDS_MANUAL]
        if not manual_tasks:
            print("No tasks needing manual intervention")
        else:
            print("\nTasks needing manual intervention:")
            for t in manual_tasks:
                print(f"  #{t['id']}: {t['name']}")
                if t.get('manual_reason'):
                    print(f"    Reason: {t['manual_reason']}")
        return

    if args.resolve_manual:
        data = load_tasks(tasks_file)
        for t in data["tasks"]:
            if t["id"] == args.resolve_manual:
                t["status"] = STATUS_PENDING
                if "manual_reason" in t:
                    del t["manual_reason"]
                save_tasks(data, tasks_file)
                print(f"Task #{args.resolve_manual} has been restored to pending status")
                return
        print(f"Task #{args.resolve_manual} not found")
        return

    # Main loop: execute tasks - first check if tasks.json exists
    if not os.path.exists(tasks_file):
        print(f"Error: Task file does not exist - {tasks_file}")
        print("Please decompose requirements documents first:")
        print(f"  python skill/run.py --docs <requirements_directory> --src {args.src} --decompose")
        return

    data = load_tasks(tasks_file)
    if not data.get("tasks"):
        print("No tasks. Please use --decompose to decompose requirements documents first")
        return

    task_count = 0
    while True:
        data = load_tasks(tasks_file)
        task = get_next_task(data)

        if task is None:
            summary = get_task_summary(data)
            if summary["pending"] > 0:
                print("There are pending tasks but all have incomplete dependencies")
            elif summary["needs_manual"] > 0:
                print(f"There are {summary['needs_manual']} tasks needing manual intervention")
                print("Use --list-manual to view, then --resolve-manual to restore after handling")
            else:
                print("All tasks completed!")
            break

        if args.max_tasks > 0 and task_count >= args.max_tasks:
            print(f"Maximum task limit reached ({args.max_tasks})")
            break

        task_count += 1
        print(f"\n{'#'*60}")
        print(f"Task #{task['id']}: {task['name']}")
        print(f"Priority: {task.get('priority', 'medium')}")
        print(f"Description: {task.get('description', 'None')}")
        print(f"{'#'*60}")

        update_task_status(data, task["id"], "in_progress", tasks_file=tasks_file)

        # Only provide file path, let Claude decide whether to read
        context_hint = ""
        if os.path.exists(progress_file):
            context_hint = f'\nProgress file path (can reference historical task records): "{progress_file}"'

        today = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        git_cmds = f'   - git add all changed files\n   - git commit -m "Completed task #{task["id"]}: {task["name"]}"'
        if args.push:
            git_cmds += "\n   - git push"

        prompt = f"""Please execute the following development task:

Task name: {task['name']}
Task description: {task.get('description', 'No description')}
Priority: {task.get('priority', 'medium')}
Code storage directory: "{args.src}"{context_hint}

Requirements:
1. Place all generated code files in "{args.src}/" directory (create if not exists)
2. Complete the task development
3. If the task cannot be completed automatically (needs manual decision, permission approval, external resources, etc.), mark status as needs_manual
4. After completion, append this task summary to the beginning of "{progress_file}" file in the following format:

========================================
Task #{task['id']}: {task['name']}
Time: {today}
Status: completed or needs_manual
----------------------------------------
Completed items:
- [List specific completed work]
----------------------------------------
Remaining issues:
- [List remaining issues if any, write "None" if none]
----------------------------------------
Manual intervention reason:
- [Explain reason if manual intervention needed, write "None" if not]
========================================

5. If task is completed and there are file changes, execute git operations:
{git_cmds}

6. Mark status at the end of output:
---STATUS---
completed or needs_manual
---END---

Please start executing the task."""

        output = run_claude(prompt, cwd=args.src)

        # Parse status from output with robust error handling
        final_status = STATUS_COMPLETED
        try:
            if "---STATUS---" in output and "---END---" in output:
                status_part = output.split("---STATUS---", 1)[1]
                if "---END---" in status_part:
                    status_value = status_part.split("---END---", 1)[0].strip().lower()
                    if status_value in ("needs_manual", "needs manual"):
                        final_status = STATUS_NEEDS_MANUAL
                else:
                    print("Warning: Status marker found but ---END--- missing, assuming completed")
            else:
                # No status markers found - check if execution failed
                if "Execution failed" in output or "Execution timeout" in output or "Execution interrupted" in output:
                    print("Warning: Execution did not complete properly, marking as needs_manual")
                    final_status = STATUS_NEEDS_MANUAL
        except Exception as e:
            print(f"Warning: Failed to parse status from output: {e}")
            final_status = STATUS_NEEDS_MANUAL

        data = load_tasks(tasks_file)
        if final_status == STATUS_NEEDS_MANUAL:
            mark_task_manual(data, task["id"], f"Needs manual intervention, see {progress_file} for details", tasks_file)
            print(f"\nTask #{task['id']} has been marked as needing manual intervention")
            print(f"See {progress_file} for details")
        else:
            update_task_status(data, task["id"], STATUS_COMPLETED, tasks_file=tasks_file)

        summary = get_task_summary(load_tasks(tasks_file))
        print(f"\nProgress: {summary['completed']}/{summary['total']} completed")


if __name__ == "__main__":
    main()