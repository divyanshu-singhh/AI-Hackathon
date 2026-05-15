import base64
from io import BytesIO

from PIL import Image

from main import process_csv_rows
from services.image_processor import normalize_image_url


def test_normalize_image_formula_url():
    value = '=IMAGE("https://example.com/product.jpg?x=1")'
    assert normalize_image_url(value) == "https://example.com/product.jpg?x=1"


def test_process_csv_rows_accepts_data_image_url():
    image = Image.new("RGB", (80, 80), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    response = process_csv_rows(
        [{"Image URL": data_url, "Image Name": "inline.png", "Expected Category": "Demo"}],
        {"quality", "rebuild"},
        crop_size=125,
    )

    assert response["total"] == 1
    assert response["success"] == 1
    assert response["failed"] == 0
    assert response["results"][0]["status"] == "success"
    assert response["results"][0]["rebuilt_image_url"]
