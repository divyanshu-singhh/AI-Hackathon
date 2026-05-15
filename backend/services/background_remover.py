"""Background removal with graceful fallback when rembg is unavailable or fails."""

import shutil
from pathlib import Path


def remove_background(input_path: str | Path, output_path: str | Path) -> tuple[str, str | None]:
    output = Path(output_path)
    try:
        from rembg import remove

        data = Path(input_path).read_bytes()
        output.write_bytes(remove(data))
        return str(output), None
    except Exception as exc:
        shutil.copy2(input_path, output)
        return str(output), f"Background removal failed: {exc}"
