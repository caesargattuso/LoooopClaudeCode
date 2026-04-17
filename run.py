#!/usr/bin/env python3
"""Claude自动化开发套件主控脚本"""
import argparse
import subprocess
import sys
import os
import io

# 设置stdout为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from task_utils import (
    load_tasks, save_tasks, get_next_task,
    update_task_status, get_task_summary, mark_task_manual,
    STATUS_PENDING, STATUS_COMPLETED, STATUS_NEEDS_MANUAL
)


def run_claude(prompt: str) -> str:
    """调用Claude CLI执行命令"""
    print(f"\n{'='*60}")
    print(f"[Claude] 执行中...")
    print(f"{'='*60}\n")

    # 构建 subprocess 环境变量
    env = os.environ.copy()
    if sys.platform == 'win32' and 'CLAUDE_CODE_GIT_BASH_PATH' not in env:
        # 动态检测 bash 路径
        try:
            result = subprocess.run('where bash', capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    path = line.strip()
                    if 'Git' in path and 'bash.exe' in path:
                        env['CLAUDE_CODE_GIT_BASH_PATH'] = path
                        break
        except Exception:
            pass

    # 使用 Popen 实现实时流式输出
    cmd = 'claude -p --dangerously-skip-permissions'
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        shell=True,
        env=env
    )

    # 写入 prompt
    process.stdin.write(prompt)
    process.stdin.close()

    # 实时读取输出
    output_lines = []
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            print(line, end='')  # 实时打印到命令行
            output_lines.append(line)

    # 读取错误输出
    stderr = process.stderr.read()
    if process.returncode != 0:
        print(f"\n错误: {stderr}")
        return f"执行失败: {stderr}"

    return ''.join(output_lines)


def decompose_requirements(docs_dir: str = "docs") -> None:
    """让Claude拆解docs目录下所有需求文档并写入tasks.json"""
    if not os.path.exists(docs_dir):
        print(f"错误: 目录不存在 - {docs_dir}")
        return

    # 获取所有文档文件
    doc_files = []
    for f in os.listdir(docs_dir):
        if f.endswith(('.md', '.txt', '.json')):
            doc_files.append(os.path.join(docs_dir, f))

    if not doc_files:
        print(f"目录 {docs_dir} 下没有文档文件")
        return

    doc_list = "\n".join(doc_files)
    today = str(__import__('datetime').datetime.now().date())

    prompt = f"""请分析 docs 目录下的所有需求文档，将其拆解成具体的开发任务列表。

需求文档路径:
{doc_list}

要求:
1. 读取所有需求文档内容
2. 综合分析，拆解成可独立完成的小任务
3. 设置合理的任务依赖关系和优先级
4. 将任务列表保存到 tasks.json 文件，格式如下:

{{
  "project": "项目名称",
  "created_at": "{today}",
  "requirements_docs": ["docs/xxx.md", "docs/yyy.md"],
  "tasks": [
    {{
      "id": 1,
      "name": "任务名称",
      "description": "详细描述",
      "priority": "high|medium|low",
      "dependencies": [],
      "status": "pending",
      "result": null,
      "issues": [],
      "completed_at": null
    }}
  ]
}}

完成后请告知任务数量。
"""

    run_claude(prompt)


def main():
    parser = argparse.ArgumentParser(description="Claude自动化开发套件")
    parser.add_argument("--decompose", "-d", nargs="?", const="docs", default=None,
                        help="拆解docs目录下所有需求文档（默认docs目录）")
    parser.add_argument("--status", "-s", action="store_true",
                        help="显示当前任务状态")
    parser.add_argument("--mark-manual", "-M", type=int, metavar="ID",
                        help="标记指定任务为需要人工干预")
    parser.add_argument("--list-manual", "-L", action="store_true",
                        help="列出所有需要人工干预的任务")
    parser.add_argument("--resolve-manual", "-R", type=int, metavar="ID",
                        help="将任务从人工干预状态恢复为待执行")
    parser.add_argument("--max-tasks", "-m", type=int, default=0,
                        help="最大执行任务数（0表示无限制）")
    args = parser.parse_args()

    if args.decompose:
        decompose_requirements(args.decompose)
        return

    if args.status:
        data = load_tasks()
        summary = get_task_summary(data)
        print(f"\n项目: {data.get('project', '未命名')}")
        print(f"总任务: {summary['total']}")
        print(f"已完成: {summary['completed']}")
        print(f"进行中: {summary['in_progress']}")
        print(f"待执行: {summary['pending']}")
        print(f"已阻塞: {summary['blocked']}")
        print(f"需人工: {summary['needs_manual']}")
        return

    if args.mark_manual:
        data = load_tasks()
        if mark_task_manual(data, args.mark_manual, "用户手动标记"):
            print(f"任务 #{args.mark_manual} 已标记为需要人工干预")
        else:
            print(f"未找到任务 #{args.mark_manual}")
        return

    if args.list_manual:
        data = load_tasks()
        manual_tasks = [t for t in data["tasks"] if t["status"] == STATUS_NEEDS_MANUAL]
        if not manual_tasks:
            print("没有需要人工干预的任务")
        else:
            print("\n需要人工干预的任务:")
            for t in manual_tasks:
                print(f"  #{t['id']}: {t['name']}")
                if t.get('manual_reason'):
                    print(f"    原因: {t['manual_reason']}")
        return

    if args.resolve_manual:
        data = load_tasks()
        for t in data["tasks"]:
            if t["id"] == args.resolve_manual:
                t["status"] = STATUS_PENDING
                if "manual_reason" in t:
                    del t["manual_reason"]
                save_tasks(data)
                print(f"任务 #{args.resolve_manual} 已恢复为待执行状态")
                return
        print(f"未找到任务 #{args.resolve_manual}")
        return

    # 主循环：执行任务
    data = load_tasks()
    if not data.get("tasks"):
        print("没有任务。请先使用 --decompose 拆解docs目录下的需求文档")
        return

    task_count = 0
    while True:
        # 获取下一个任务
        data = load_tasks()
        task = get_next_task(data)

        if task is None:
            summary = get_task_summary(data)
            if summary["pending"] > 0:
                print("存在待执行任务，但都有未完成的依赖")
            elif summary["needs_manual"] > 0:
                print(f"还有 {summary['needs_manual']} 个任务需要人工干预")
                print("使用 --list-manual 查看，处理后用 --resolve-manual 恢复")
            else:
                print("所有任务已完成！")
            break

        if args.max_tasks > 0 and task_count >= args.max_tasks:
            print(f"已达到最大任务数限制 ({args.max_tasks})")
            break

        task_count += 1
        print(f"\n{'#'*60}")
        print(f"任务 #{task['id']}: {task['name']}")
        print(f"优先级: {task.get('priority', 'medium')}")
        print(f"描述: {task.get('description', '无')}")
        print(f"{'#'*60}")

        # 标记为进行中
        update_task_status(data, task["id"], "in_progress")

        # 获取已完成任务上下文
        completed_tasks = [t for t in data["tasks"] if t["status"] == STATUS_COMPLETED]
        completed_info = ""
        if completed_tasks:
            completed_info = "\n已完成的任务:\n" + "\n".join(
                [f"  #{t['id']}: {t['name']}" for t in completed_tasks[-5:]]  # 最近5个
            )
            if len(completed_tasks) > 5:
                completed_info += f"\n  ... 等共 {len(completed_tasks)} 个已完成任务"

        # 获取 progress.txt 内容（最近记录）
        progress_info = ""
        if os.path.exists("progress.txt"):
            with open("progress.txt", "r", encoding="utf-8") as f:
                content = f.read()
                # 取最近一条记录（第一个 ======================================== 到下一个）
                if content.startswith("========================================"):
                    first_record = content.split("========================================")[1]
                    if first_record:
                        progress_info = "\n最近完成的任务记录:\n========================================" + first_record.split("========================================")[0] + "========================================"

        # 构建执行提示
        today = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prompt = f"""请执行以下开发任务:

任务名称: {task['name']}
任务描述: {task.get('description', '无描述')}
优先级: {task.get('priority', 'medium')}

{completed_info}{progress_info}

要求:
1. 参考已完成任务的上下文，确保代码风格和结构一致
2. 所有生成的代码文件默认放在 src/ 目录下（如果不存在则创建）
3. 完成任务开发
4. 如果任务无法自动完成（需要人工决策、权限审批、外部资源等），标记状态为 needs_manual
5. 执行完成后，将本次任务总结追加到 progress.txt 文件开头，格式如下:

========================================
任务 #{task['id']}: {task['name']}
时间: {today}
状态: completed 或 needs_manual
----------------------------------------
完成事项:
- [列出完成的具体工作]
----------------------------------------
遗留问题:
- [如有遗留问题列出，无则写"无"]
----------------------------------------
人工干预原因:
- [如需人工干预说明原因，无则写"无"]
========================================

6. 如果任务已完成且有文件变更，执行 git commit:
   - git add 所有变更文件
   - commit message: "完成任务 #{task['id']}: {task['name']}"

7. 输出末尾仅标记状态:
---STATUS---
completed 或 needs_manual
---END---

请开始执行任务。"""

        # 调用Claude执行
        output = run_claude(prompt)

        # 解析状态
        final_status = STATUS_COMPLETED
        if "---STATUS---" in output:
            status_part = output.split("---STATUS---")[1]
            status_value = status_part.split("---END---")[0].strip().lower()
            if status_value == "needs_manual":
                final_status = STATUS_NEEDS_MANUAL

        # 更新状态
        data = load_tasks()
        if final_status == STATUS_NEEDS_MANUAL:
            mark_task_manual(data, task["id"], "需要人工干预，详情见 progress.txt")
            print(f"\n任务 #{task['id']} 已标记为需要人工干预")
            print("详情见 progress.txt")
        else:
            update_task_status(data, task["id"], STATUS_COMPLETED)

        summary = get_task_summary(load_tasks())
        print(f"\n进度: {summary['completed']}/{summary['total']} 完成")


if __name__ == "__main__":
    main()