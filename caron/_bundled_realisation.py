"""Load the package-maintained career realisation from its installed file."""

from pathlib import Path

from caron.ontology import career_ontology_v5_0
from caron.yaml_reader import LoadResult, load_realisation_yaml


def load_bundled_career_realisation() -> LoadResult:
    """Read and validate the single career file against the exact 5.0 schema."""
    path = Path(__file__).parent / "data" / "career-across-contexts-v0.1.yaml"
    return load_realisation_yaml(path, ontology=career_ontology_v5_0())
