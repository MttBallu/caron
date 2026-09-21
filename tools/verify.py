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

        for ontology_version, output_name in (
            ("4", "ontology_4_graph.html"),
            ("0.5", "ontology_0_5_graph.html"),
        ):
            _run(
                f"ontology {ontology_version} schema viewer",
                [
                    sys.executable,
                    "-m",
                    "examples.ontology_schema_html",
                    "--version",
                    ontology_version,
                    "--output",
                    str(temporary / output_name),
                ],
            )

        _run("distribution build", ["uv", "build", "--out-dir", str(temporary)])

    print("\nAll verification checks passed.", flush=True)


if __name__ == "__main__":
    main()
