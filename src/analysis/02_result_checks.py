"""Result consistency checks."""

from __future__ import annotations

import pandas as pd

from src.common.config_loader import load_config, project_path
from src.common.validators import validate_dispatch


def run(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    checked = []
    for scenario in ["unordered", "ordered", "v2g"]:
        path = project_path(cfg["paths"]["dispatch_dir"], f"dispatch_{scenario}.csv")
        df = pd.read_csv(path)
        validate_dispatch(df)
        checked.append(str(path))
    return {"checked_dispatch_files": ";".join(checked)}


def main() -> None:
    print(run())


if __name__ == "__main__":
    main()
