"""Run the complete reproducibility gate for the maintained source tree."""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def _run(label: str, command: list[str], *, cwd: Path = ROOT) -> None:
    print(f"\n==> {label}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


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

        for ontology_version, output_name in (("5.0", "ontology_5_0_graph.html"),):
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

        environment = temporary / "installed-wheel"
        _run(
            "clean installation environment",
            [sys.executable, "-m", "venv", str(environment)],
            cwd=temporary,
        )
        installed_python = environment / (
            "Scripts/python.exe" if sys.platform == "win32" else "bin/python"
        )
        wheel = next(temporary.glob("caron-*.whl"))
        _run(
            "wheel installation",
            [
                str(installed_python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(wheel),
            ],
            cwd=temporary,
        )
        smoke_test = "\n".join(
            (
                "from importlib.metadata import version",
                "from caron import career_ontology_v5_0, validate_ontology",
                "schema = career_ontology_v5_0()",
                'assert version("caron") == "0.2.0"',
                'assert (schema.id, schema.version) == ("caron.career-model", "5.0")',
                "assert len(schema.concepts) == 13",
                "assert len(schema.relations) == 31",
                "assert len(schema.requirements) == 6",
                "assert len(schema.invariants) == 8",
                "assert validate_ontology(schema) == ()",
            )
        )
        _run(
            "installed public API smoke test",
            [str(installed_python), "-I", "-c", smoke_test],
            cwd=temporary,
        )

    print("\nAll verification checks passed.", flush=True)


if __name__ == "__main__":
    main()
