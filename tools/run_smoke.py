#!/usr/bin/env python
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANAGE = ROOT / "simulador_operacional" / "manage.py"


def run_step(name: str, command: list[str], cwd: Path) -> dict:
    start = time.time()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    duration = time.time() - start
    return {
        "name": name,
        "command": " ".join(command),
        "returncode": completed.returncode,
        "duration_s": duration,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def build_steps(python_bin: str, settings_ci: str, settings_test: str) -> list[tuple[str, list[str]]]:
    return [
        (
            "Migrate (clean env)",
            [python_bin, str(MANAGE), "migrate", "--noinput", "--settings", settings_ci],
        ),
        (
            "Seed base data (clean env)",
            [python_bin, str(MANAGE), "seed_dados_base", "--settings", settings_ci],
        ),
        (
            "Django check (clean env)",
            [python_bin, str(MANAGE), "check", "--settings", settings_ci],
        ),
        (
            "Close rounds sanity (clean env)",
            [python_bin, str(MANAGE), "fechar_rodadas", "--settings", settings_ci],
        ),
        (
            "Targeted smoke tests",
            [
                python_bin,
                str(MANAGE),
                "test",
                "app.tests.test_views.PainelGrupoViewTest",
                "app.tests.test_views.LoginRedirectTest",
                "app.tests.test_views.RegisterViewAccessTest",
                "app.tests.test_views.MateriaPrimaFlowTest",
                "app.tests.test_relatorios",
                "app.tests.test_ranking",
                "app.tests.test_feedback",
                "--settings",
                settings_test,
            ],
        ),
    ]


def write_report(report_path: Path, results: list[dict]) -> None:
    total = len(results)
    failed = sum(1 for r in results if r["returncode"] != 0)
    passed = total - failed
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Smoke Report",
        "",
        f"- Generated at: `{timestamp}`",
        f"- Passed: `{passed}`",
        f"- Failed: `{failed}`",
        "",
        "## Steps",
    ]

    for result in results:
        status = "PASS" if result["returncode"] == 0 else "FAIL"
        lines.extend(
            [
                "",
                f"### {result['name']} - {status}",
                f"- Command: `{result['command']}`",
                f"- Duration: `{result['duration_s']:.2f}s`",
                f"- Return code: `{result['returncode']}`",
            ]
        )
        if result["stdout"]:
            lines.extend(["- Stdout:", "```text", result["stdout"], "```"])
        if result["stderr"]:
            lines.extend(["- Stderr:", "```text", result["stderr"], "```"])

    lines.extend(
        [
            "",
            "## Manual Usability Checks Pending",
            "- Wizard UX clarity and field comprehension by real users.",
            "- Dashboard readability and navigation speed in real usage.",
            "- Perceived ease for GM and Group roles during full round operation.",
            "- Qualitative feedback notes (confusion points, friction, wording).",
            "",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run technical smoke flow and generate a report.")
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python executable used to invoke Django manage.py",
    )
    parser.add_argument(
        "--settings-ci",
        default="simulador_operacional.settings_ci",
        help="Settings module for clean environment steps",
    )
    parser.add_argument(
        "--settings-test",
        default="simulador_operacional.settings_test",
        help="Settings module for targeted test execution",
    )
    parser.add_argument(
        "--report-dir",
        default=str(ROOT / "docs" / "reports"),
        help="Directory where smoke reports will be written",
    )
    args = parser.parse_args()

    report_name = f"smoke_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path = Path(args.report_dir) / report_name

    steps = build_steps(args.python_bin, args.settings_ci, args.settings_test)
    results = []

    print("Running smoke automation...")
    for name, command in steps:
        print(f"- {name}")
        result = run_step(name, command, ROOT)
        results.append(result)
        if result["returncode"] != 0:
            print(f"  FAIL ({result['returncode']})")
        else:
            print("  PASS")

    write_report(report_path, results)
    print(f"Report written to: {report_path}")

    return 1 if any(r["returncode"] != 0 for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
