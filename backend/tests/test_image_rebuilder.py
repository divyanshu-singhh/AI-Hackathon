import numpy as np
from PIL import Image

from services.image_rebuilder import rebuild_catalog_image
from services.quality_analyzer import analyze_rebuilt_quality


def test_rebuild_enlarges_subject_to_fill_requested_canvas(tmp_path):
    source = tmp_path / "small_cutout.png"
    output = tmp_path / "rebuilt.png"

    image = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
    product = Image.new("RGBA", (80, 80), (180, 30, 30, 255))
    image.alpha_composite(product, (160, 160))
    image.save(source)

    rebuild_catalog_image(
        source,
        output,
        canvas_size=500,
        quality={"resolution_ok": False, "blur_score": 55, "issues": ["Resolution is below recommended 600x600"]},
    )

    rebuilt = Image.open(output).convert("RGB")
    assert rebuilt.size == (500, 500)

    pixels = np.asarray(rebuilt)
    foreground = np.any(pixels < 245, axis=2)
    rows = np.where(foreground.any(axis=1))[0]
    cols = np.where(foreground.any(axis=0))[0]

    assert rows[-1] - rows[0] + 1 >= 460
    assert cols[-1] - cols[0] + 1 >= 460


def test_rebuild_does_not_overexpose_product_when_original_background_is_dark(tmp_path):
    source = tmp_path / "dark_source_context.png"
    output = tmp_path / "rebuilt.png"

    image = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
    product = Image.new("RGBA", (220, 80), (78, 145, 142, 255))
    image.alpha_composite(product, (90, 160))
    image.save(source)

    rebuild_catalog_image(
        source,
        output,
        canvas_size=500,
        quality={"brightness": 45, "contrast": 28, "blur_score": 70, "issues": ["Image is underexposed"]},
    )

    rebuilt = Image.open(output).convert("RGB")
    pixels = np.asarray(rebuilt)
    product_pixels = pixels[np.any(pixels < 245, axis=2)]

    assert product_pixels[:, 1].mean() < 175
    assert analyze_rebuilt_quality(output)["quality_score"] >= 70
