"""Multi-image attachment ingest + merge."""

from io import BytesIO

from PIL import Image

from tokenish_engine.config import settings
from tokenish_engine.ingest import ingest_file, merge_ingests
from tokenish_engine.pipeline import optimize


def _jpeg_bytes(color: tuple[int, int, int], name_hint: str = "x") -> bytes:
    img = Image.new("RGB", (32, 32), color)
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_merge_keeps_multiple_images():
    a = ingest_file("a.jpg", _jpeg_bytes((255, 0, 0)), prompt="look")
    b = ingest_file("b.jpg", _jpeg_bytes((0, 255, 0)), prompt="look")
    c = ingest_file("c.jpg", _jpeg_bytes((0, 0, 255)), prompt="look")
    merged = merge_ingests([a, b, c])
    assert len(merged.images) == 3
    assert merged.image_b64 == merged.images[0]["b64"]
    assert merged.metadata.get("images_kept") == 3
    assert merged.metadata.get("images_dropped") == 0


def test_merge_caps_vision_images_with_warning():
    parts = [
        ingest_file(f"{i}.jpg", _jpeg_bytes((i * 20 % 255, 40, 80)), prompt="look")
        for i in range(settings.max_vision_images + 3)
    ]
    merged = merge_ingests(parts)
    assert len(merged.images) == settings.max_vision_images
    assert merged.metadata.get("images_dropped") == 3
    assert "vision limit" in (merged.metadata.get("warning") or "")


def test_optimize_passes_multiple_images():
    files = [
        ("one.png", _jpeg_bytes((10, 20, 30))),
        ("two.png", _jpeg_bytes((40, 50, 60))),
    ]
    result = optimize(prompt="compare these images", files=files)
    assert len(result.images) == 2
    assert result.image_b64 == result.images[0]["b64"]
    assert any(s.startswith("vision_images_") for s in result.stages)
