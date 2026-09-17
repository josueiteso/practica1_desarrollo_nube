"""
procesamiento de imágenes (resize y composicion estilo polaroid
"""
import io
from PIL import Image, ImageDraw, ImageFont

# margenes del marco polaroid (en px)
BORDER_TOP = 12
BORDER_SIDE = 12
BORDER_BOTTOM = 40

def resize_and_crop(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h))
    left = (new_w - target_w) / 2
    top = (new_h - target_h) / 2
    return img.crop((left, top, left + target_w, top + target_h))

def resize_photo(image_bytes: bytes) -> bytes:
    # devuelve la imagen redimensionada a 128x128
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = resize_and_crop(img, (128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()

def load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_text(text: str, draw: ImageDraw.ImageDraw, font, max_width: int) -> str:
    # trunca el texto con '...' si no cabe en el ancho disponible
    if not text:
        return text
    while draw.textlength(text, font=font) > max_width and len(text) > 1:
        text = text[:-1]
    if draw.textlength(text, font=font) > max_width:
        return text
    return text

def compose_polaroid(thumbnail_bytes: bytes, message: str) -> bytes:
    # arma el marco blanco con el texto
    photo = Image.open(io.BytesIO(thumbnail_bytes)).convert("RGB")

    canvas_w = photo.width + 2 * BORDER_SIDE
    canvas_h = photo.height + BORDER_TOP + BORDER_BOTTOM

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    canvas.paste(photo, (BORDER_SIDE, BORDER_TOP))

    draw = ImageDraw.Draw(canvas)
    font = load_font(size=14)

    text = message.strip() or ""
    text = fit_text(text, draw, font, max_width=canvas_w - 10)

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]
    text_x = (canvas_w - text_w) / 2
    text_y = BORDER_TOP + photo.height + (BORDER_BOTTOM - text_h) / 2 - text_bbox[1]

    draw.text((text_x, text_y), text, fill="black", font=font)

    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


