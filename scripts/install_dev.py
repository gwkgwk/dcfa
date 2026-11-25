"""Install DCFA's development environment using the current virtual interpreter."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    pip = [sys.executable, "-m", "pip", "install"]
    if os.name == "nt" and sys.version_info[:5] == (3, 14, 0, "alpha", 5):
        # Stable cp314 extension wheels do not target this prerelease ABI.
        subprocess.run([*pip, "setuptools", "wheel"], check=True)
        subprocess.run(
            [*pip, "--no-cache-dir", "--no-build-isolation", "--no-binary=PyYAML", "PyYAML==6.0.4"],
            env={**os.environ, "PYYAML_FORCE_LIBYAML": "0"},
            check=True,
        )
    subprocess.run([*pip, "-e", f"{root}[dev]"], check=True)
    subprocess.run([sys.executable, "-I", "-c", "import dcfa.scs"], check=True)


if __name__ == "__main__":
    main()
