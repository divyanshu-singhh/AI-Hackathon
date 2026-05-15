"""Rebuild a catalog-ready image on a clean white square canvas."""

from pathlib import Path
from PIL import Image, ImageOps


def rebuild_catalog_image(bg_removed_path: str | Path, output_path: str | Path) -> str:
    canvas_size = 1000
    product_box = 800
    output = Path(output_path)

    with Image.open(bg_removed_path) as product:
        product = ImageOps.exif_transpose(product).convert("RGBA")
        product.thumbnail((product_box, product_box), Image.LANCZOS)

        canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
        x = (canvas_size - product.width) // 2
        y = (canvas_size - product.height) // 2
        canvas.alpha_composite(product, (x, y))
        canvas.convert("RGB").save(output, "PNG", optimize=True)

    return str(output)
