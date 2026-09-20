"""Run the complete reproducibility gate for the maintained source tree."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, command: list[str]) -> None:
    print(f"\n==> {label}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    _run("format", ["ruff", "format", "--check", "."])
    _run("lint", ["ruff", "check", "."])
    _run("types", ["mypy", "caron", "tests", "examples", "tools"])
    _run("tests", ["pytest"])
    _run("semantic example", [sys.executable, "-m", "examples.semantic_spine"])
    _run("temporal example", [sys.executable, "-m", "examples.temporal_queries"])

    with TemporaryDirectory(prefix="caron-verify-") as temporary_directory:
        temporary = Path(temporary_directory)
        for example_name, output_name in (
            ("career", "career_graph.html"),
            ("two-contexts", "two_contexts_graph.html"),
            ("temporal-window", "temporal_window_graph.html"),
        ):
            command = [
                sys.executable,
                "-m",
                "examples.cytoscape_html",
                "--output",
                str(temporary / output_name),
            ]
            if example_name != "career":
                command.extend(("--example", example_name))
            _run(f"{example_name} viewer", command)

        _run("distribution build", ["uv", "build", "--out-dir", str(temporary)])

    print("\nAll M0 verification checks passed.", flush=True)


if __name__ == "__main__":
    main()
