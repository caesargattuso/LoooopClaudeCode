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
from logger import init_logger, get_logger, close_logger


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


def ensure_claude_md(src_dir: str) -> bool:
    """Check if CLAUDE.md exists in project directory, if not run init"""
    claude_md_path = os.path.join(src_dir, "CLAUDE.md")

    # Check parent directory too
    parent_dir = os.path.dirname(src_dir)
    parent_claude_md = os.path.join(parent_dir, "CLAUDE.md")

    if os.path.exists(claude_md_path) or os.path.exists(parent_claude_md):
        print("[Info] CLAUDE.md found")
        return True

    print("[Warn] CLAUDE.md not found, initializing...")

    try:
        result = subprocess.run(
            'claude init',
            capture_output=True,
            text=True,
            shell=True,
            cwd=src_dir,
            timeout=120
        )
        if result.returncode == 0:
            print("[Info] CLAUDE.md generated")
            return True
        else:
            print(f"[Warn] Init failed: {result.stderr}")
            return True
    except subprocess.TimeoutExpired:
        print("[Warn] Init timed out")
        return True
    except Exception as e:
        print(f"[Warn] Init error: {e}")
        return True


def run_claude(prompt: str, cwd: str = None, timeout: int = 600) -> str:
    """Invoke Claude CLI to execute command"""
    logger = get_logger()
    logger.info("Claude executing...")

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
    spinner_chars = ['.', '..', '...']
    spinner_idx = 0
    dots_printed = 0

    try:
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                logger.claude(line)  # Log to file
                output_lines.append(line)
                # Show progress dots (real-time feedback)
                dots_printed += 1
                if dots_printed % 10 == 0:  # Every 10 lines
                    print('.', end='', flush=True)
                    if dots_printed % 50 == 0:  # Line break every 50 dots
                        print()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        process.terminate()
        process.wait(timeout=5)
        return "Execution interrupted by user"

    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout after {timeout}s")
        process.terminate()
        process.wait(timeout=5)
        return f"Execution timeout after {timeout} seconds"

    stderr = process.stderr.read()
    if process.returncode != 0:
        logger.error(f"Claude failed: {stderr}")
        return f"Execution failed: {stderr}"

    # Clear progress dots and show completion
    if dots_printed > 0:
        print()  # New line after dots
    logger.info("Claude completed")

    return ''.join(output_lines)


def decompose_requirements(docs_source: str, src_dir: str, push: bool = False, is_single_doc: bool = False) -> None:
    """Let Claude decompose requirements documents and write to tasks.json"""
    # Create task-specific logger for decompose
    looop_dir = get_looop_dir(src_dir)
    init_logger(looop_dir, task_id=0, task_name="Decompose")
    logger = get_logger()

    # Handle single doc vs directory
    if is_single_doc:
        if not os.path.isfile(docs_source):
            logger.error(f"Document file not found: {docs_source}")
            close_logger()
            return
        doc_files = [docs_source]
        docs_dir = os.path.dirname(docs_source) or "."
    else:
        if not os.path.exists(docs_source):
            logger.error(f"Docs directory not found: {docs_source}")
            close_logger()
            return
        doc_files = []
        for f in os.listdir(docs_source):
            if f.endswith('.md') or f.endswith('.txt') or f.endswith('.json'):
                doc_files.append(os.path.join(docs_source, f))
        docs_dir = docs_source

    if not doc_files:
        logger.warning(f"No documents found in {docs_source}")
        close_logger()
        return

    ensure_claude_md(src_dir)
    init_looop_dir(src_dir)
    tasks_file = get_tasks_file(src_dir)

    doc_list = "\n".join(f'"{f}"' for f in doc_files)
    today = str(__import__('datetime').datetime.now().date())

    git_cmds = f'- git add "{tasks_file}"\n   - git commit -m "<请根据本次分解的任务内容自行决定commit消息>"'
    if push:
        git_cmds += "\n   - git push"

    # Build JSON example string
    json_example = f''' {{
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
}}'''

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

{json_example}

5. After saving, execute git operations:
{git_cmds}

Please report the number of tasks after completion.
"""

    run_claude(prompt, cwd=src_dir)
    close_logger()


def main():
    parser = argparse.ArgumentParser(description="Claude Automated Development Toolkit")
    parser.add_argument("--docs", "-D", metavar="DIR",
                        help="Requirements document directory path")
    parser.add_argument("--doc", metavar="FILE",
                        help="Single requirements document file path")
    parser.add_argument("--src", "-S", required=True, metavar="DIR",
                        help="Code storage directory path")
    parser.add_argument("--decompose", "-d", action="store_true",
                        help="Decompose requirements documents")
    parser.add_argument("--status", "-s", action="store_true",
                        help="Show current task status")
    parser.add_argument("--mark-manual", "-M", type=int, metavar="ID",
                        help="Mark task as needing manual intervention")
    parser.add_argument("--list-manual", "-L", action="store_true",
                        help="List tasks needing manual intervention")
    parser.add_argument("--resolve-manual", "-R", type=int, metavar="ID",
                        help="Restore task from manual intervention")
    parser.add_argument("--max-tasks", "-m", type=int, default=0,
                        help="Maximum tasks to execute (0 = unlimited)")
    parser.add_argument("--push", "-P", action="store_true",
                        help="Git push after task completion")
    args = parser.parse_args()

    # Initialize directories
    init_looop_dir(args.src)
    looop_dir = get_looop_dir(args.src)
    tasks_file = get_tasks_file(args.src)
    progress_file = get_progress_file(args.src)

    # === Non-task operations: direct console output, no log file ===

    # Status mode
    if args.status:
        data = load_tasks(tasks_file)
        summary = get_task_summary(data)
        print("=" * 60)
        print(f"Project: {data.get('project', 'Unnamed')}")
        print(f"Requirements: {data.get('docs_dir', 'N/A')}")
        print(f"Source: {data.get('src_dir', args.src)}")
        print()
        print(f"Total: {summary['total']} | Done: {summary['completed']} | "
              f"Pending: {summary['pending']} | Manual: {summary['needs_manual']}")
        print("=" * 60)
        return

    # Mark manual
    if args.mark_manual:
        data = load_tasks(tasks_file)
        if mark_task_manual(data, args.mark_manual, "User marked", tasks_file):
            print(f"[Done] Task #{args.mark_manual} marked for manual intervention")
        else:
            print(f"[Warn] Task #{args.mark_manual} not found")
        return

    # List manual
    if args.list_manual:
        data = load_tasks(tasks_file)
        manual_tasks = [t for t in data["tasks"] if t["status"] == STATUS_NEEDS_MANUAL]
        if not manual_tasks:
            print("[Info] No tasks need manual intervention")
        else:
            print("[Info] Tasks needing manual intervention:")
            for t in manual_tasks:
                print(f"  #{t['id']}: {t['name']}")
        return

    # Resolve manual
    if args.resolve_manual:
        data = load_tasks(tasks_file)
        for t in data["tasks"]:
            if t["id"] == args.resolve_manual:
                t["status"] = STATUS_PENDING
                if "manual_reason" in t:
                    del t["manual_reason"]
                save_tasks(data, tasks_file)
                print(f"[Done] Task #{args.resolve_manual} restored to pending")
                return
        print(f"[Warn] Task #{args.resolve_manual} not found")
        return

    # === Task execution operations: create log file ===

    # Check Claude CLI
    if not check_claude_installed():
        print("[Error] Claude CLI not installed")
        print("[Info] Install: https://claude.ai/code")
        return

    # Decompose mode
    if args.decompose:
        if not args.docs and not args.doc:
            print("[Error] --docs or --doc required for decomposition")
            return
        if args.doc:
            # Single document mode
            if not os.path.isfile(args.doc):
                print(f"[Error] Document file not found: {args.doc}")
                return
            decompose_requirements(args.doc, args.src, args.push, is_single_doc=True)
        else:
            # Directory mode
            if not os.path.exists(args.docs):
                print(f"[Error] Docs directory not found: {args.docs}")
                return
            decompose_requirements(args.docs, args.src, args.push, is_single_doc=False)
        return

    # Main execution loop
    if not os.path.exists(tasks_file):
        print(f"[Error] Task file not found: {tasks_file}")
        print("[Info] Run --decompose first")
        return

    data = load_tasks(tasks_file)
    if not data.get("tasks"):
        print("[Warn] No tasks. Run --decompose first")
        return

    ensure_claude_md(args.src)

    summary = get_task_summary(data)
    total = summary['total']
    print(f"[Info] Starting: {total} tasks")
    print()

    task_count = 0
    try:
        while True:
            data = load_tasks(tasks_file)
            task = get_next_task(data)
            summary = get_task_summary(data)

            if task is None:
                print(f"[=====>          ] {summary['completed']}/{total} ({int(summary['completed']/total*100 if total > 0 else 0)}%)")
                if summary["pending"] > 0:
                    print("[Warn] Pending tasks blocked by dependencies")
                elif summary["needs_manual"] > 0:
                    print(f"[Warn] {summary['needs_manual']} tasks need manual intervention")
                else:
                    print("[Info] All tasks completed!")
                break

            if args.max_tasks > 0 and task_count >= args.max_tasks:
                print(f"[Info] Max limit reached: {args.max_tasks}")
                break

            task_count += 1

            # Create task-specific logger
            init_logger(looop_dir, task['id'], task['name'])
            logger = get_logger()

            logger.progress(summary['completed'], total, task['name'])
            logger.task_start(task['id'], task['name'], task.get('priority', 'medium'))

            update_task_status(data, task["id"], "in_progress", tasks_file=tasks_file)

            context_hint = ""
            if os.path.exists(progress_file):
                context_hint = f'\nProgress file: "{progress_file}"'

            now = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            git_cmds = '- git add all\n- git commit -m "<请根据任务内容自行决定commit消息>"'
            if args.push:
                git_cmds += "\n- git push"

            prompt = f"""Execute task:

Task: {task['name']}
Description: {task.get('description', 'None')}
Priority: {task.get('priority', 'medium')}
Directory: "{args.src}"{context_hint}

Requirements:
1. Place files in "{args.src}/"
2. Complete development
3. If cannot complete automatically, mark needs_manual
4. Append summary to "{progress_file}":

========================================
Task #{task['id']}: {task['name']}
Time: {now}
Status: completed or needs_manual
----------------------------------------
Done:
- [items]
----------------------------------------
Issues:
- [None or list]
----------------------------------------
Manual reason:
- [None or reason]
========================================

5. Git operations if completed:
{git_cmds}

6. End output with:
---STATUS---
completed or needs_manual
---END---
"""

            output = run_claude(prompt, cwd=args.src)

            final_status = STATUS_COMPLETED
            try:
                if "---STATUS---" in output and "---END---" in output:
                    status_part = output.split("---STATUS---", 1)[1]
                    if "---END---" in status_part:
                        val = status_part.split("---END---", 1)[0].strip().lower()
                        if val in ("needs_manual", "needs manual"):
                            final_status = STATUS_NEEDS_MANUAL
                elif "Execution failed" in output or "Execution timeout" in output:
                    final_status = STATUS_NEEDS_MANUAL
            except Exception:
                final_status = STATUS_NEEDS_MANUAL

            data = load_tasks(tasks_file)
            if final_status == STATUS_NEEDS_MANUAL:
                mark_task_manual(data, task["id"], f"See {progress_file}", tasks_file)
                logger.task_end(task['id'], task['name'], "needs_manual")
                logger.info(f"See {progress_file}")
            else:
                update_task_status(data, task["id"], STATUS_COMPLETED, tasks_file=tasks_file)
                logger.task_end(task['id'], task['name'], "completed")

            close_logger()

    except KeyboardInterrupt:
        print("[Warn] Interrupted")


if __name__ == "__main__":
    main()