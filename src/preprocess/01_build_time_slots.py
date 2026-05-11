"""Build canonical 56-slot and 96-slot time tables."""

from __future__ import annotations

from src.common.config_loader import load_config, output_path
from src.common.io_utils import write_csv
from src.common.time_utils import build_day_time_slots, build_main_time_slots


def build_time_slot_files(config: dict | None = None) -> dict[str, str]:
    cfg = config or load_config()
    time_56 = build_main_time_slots()
    time_96 = build_day_time_slots()
    path_56 = write_csv(time_56, output_path("time_slots_56", cfg))
    path_96 = write_csv(time_96, output_path("time_slots_96", cfg))
    return {"time_slots_56": str(path_56), "time_slots_96": str(path_96)}


def main() -> None:
    outputs = build_time_slot_files()
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
