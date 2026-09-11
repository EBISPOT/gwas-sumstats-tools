#!/bin/sh
set -eu

# Run from the repository root. Keep wheel builds separate from other releases.
wheel_dir=$(mktemp -d)
trap 'rm -rf "$wheel_dir"' EXIT
uv build --wheel --out-dir "$wheel_dir"

# This directory contains generated output only (also ignored by Git).
rm -rf public
mkdir -p public
cp -R apps/ssf-morph/. public/
cp -R docs/gwas-sumstats-tools-doc public/docs
cp "$wheel_dir"/gwas_sumstats_tools-*.whl public/wheels/

# Check the payload, including every local wheel requested by the browser worker.
python - "$wheel_dir" <<'PY'
import re
import sys
from pathlib import Path
from zipfile import ZipFile

site = Path("public")
wheel_name, = [path.name for path in Path(sys.argv[1]).glob("*.whl")]
worker = site / "webworker.js"
source, replacements = re.subn(
    r'gwas_sumstats_tools[^"/]*\.whl', wheel_name, worker.read_text()
)
assert replacements == 1, "Expected one application wheel reference"
worker.write_text(source)
assert (site / "index.html").is_file()
assert (site / "docs/index.html").is_file()
for name in re.findall(r'wheel\("([^"]+)"\)', (site / "webworker.js").read_text()):
    distribution, version, python_tag, abi_tag, platform_tag = Path(name).stem.rsplit("-", 4)
    assert all((distribution, version, python_tag, abi_tag, platform_tag)), name
    with ZipFile(site / "wheels" / name) as wheel:
        assert f"{distribution}-{version}.dist-info/WHEEL" in wheel.namelist(), name
        assert wheel.testzip() is None, name
for route in re.findall(r'href="docs/([^"]+)"', (site / "index.html").read_text()):
    assert (site / "docs" / f"{route}.md").is_file(), route
PY
