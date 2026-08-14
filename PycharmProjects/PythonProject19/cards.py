import os
import random
import tempfile

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1080

FONT_CANDIDATES = {
    "bold": [
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ],
    "regular": [
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ],
    "emoji": [
        r"C:\Windows\Fonts\seguiemj.ttf",
    ],
}


def _resolve_font(kind):
    for path in FONT_CANDIDATES.get(kind, []):
        if os.path.exists(path):
            return path
    return None


FONT_BOLD = _resolve_font("bold")
FONT_REGULAR = _resolve_font("regular")
FONT_EMOJI = _resolve_font("emoji")

TEMP_DIR = tempfile.gettempdir()

CATEGORY_STYLES = {
    "bolalar": {
        "colors": [(255, 214, 92, 255), (255, 138, 101, 255), (255, 87, 147, 255)],
        "balloons": [(255, 87, 87), (66, 165, 245), (255, 213, 79), (102, 187, 106)],
        "title_color": (90, 45, 100),
    },
    "qizlar": {
        "colors": [(255, 183, 197, 255), (255, 143, 181, 255), (255, 105, 158, 255)],
        "balloons": [(236, 64, 122), (255, 171, 145), (255, 204, 128), (244, 143, 177)],
        "title_color": (122, 24, 74),
    },
    "ayollar": {
        "colors": [(167, 119, 227, 255), (121, 134, 203, 255), (255, 165, 186, 255)],
        "balloons": [(156, 39, 176), (66, 165, 245), (255, 138, 101), (255, 213, 79)],
        "title_color": (70, 30, 110),
    },
    "erkaklar": {
        "colors": [(28, 62, 110, 255), (56, 108, 168, 255), (134, 181, 229, 255)],
        "balloons": [(66, 165, 245), (100, 181, 246), (255, 183, 77), (129, 199, 132)],
        "title_color": (255, 255, 255),
    },
    "bobolar": {
        "colors": [(255, 190, 92, 255), (230, 126, 34, 255), (141, 76, 25, 255)],
        "balloons": [(211, 158, 96), (255, 213, 79), (230, 126, 34), (141, 110, 99)],
        "title_color": (90, 45, 10),
    },
}

DECORATION_EMOJIS = ["🎂", "🎉", "🎈", "🎊", "✨", "🎁", "🥳", "💐", "⭐"]


def _font(path, size):
    return ImageFont.truetype(path, size)


def _draw_balloon(draw, x, y, color, scale=1.0):
    r = int(28 * scale)
    draw.ellipse([x - r, y - int(34 * scale), x + r, y + int(34 * scale)], fill=color)
    draw.line([x, y + int(34 * scale), x, y + int(78 * scale)], fill=color, width=4)
    draw.polygon([(x, y + int(74 * scale)), (x - 7, y + int(86 * scale)), (x + 7, y + int(86 * scale))], fill=color)


def _draw_cake(draw, cx, top, size=1.0):
    cake_w = int(300 * size)
    cake_h = int(150 * size)
    x0 = cx - cake_w // 2
    y0 = top
    draw.rounded_rectangle([x0, y0, x0 + cake_w, y0 + cake_h], radius=20, fill=(255, 255, 255))
    draw.rectangle([x0, y0, x0 + cake_w, y0 + int(26 * size)], fill=(229, 115, 115))
    for i in range(6):
        dot_x = x0 + int(35 * size) + i * int(48 * size)
        draw.ellipse([dot_x - 5, y0 + int(10 * size) - 5, dot_x + 5, y0 + int(10 * size) + 5], fill=(255, 255, 255))
    candle_x = cx
    draw.rectangle([candle_x - 8, y0 - int(55 * size), candle_x + 8, y0 - 2], fill=(66, 165, 245))
    draw.polygon([(candle_x - 8, y0 - int(58 * size)), (candle_x + 8, y0 - int(58 * size)), (candle_x, y0 - int(86 * size))], fill=(255, 193, 7))
    draw.polygon(
        [(candle_x - 12, y0 - int(88 * size)), (candle_x + 12, y0 - int(88 * size)), (candle_x, y0 - int(116 * size))],
        fill=(255, 112, 67),
    )


def _draw_star(draw, x, y, size=1.0):
    if not FONT_EMOJI:
        return
    r = int(22 * size)
    emoji_font = _font(FONT_EMOJI, int(44 * size))
    draw.text((x - r, y - r), "✨", font=emoji_font)


def make_card(category: str, name: str) -> str:
    style = CATEGORY_STYLES[category]
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(style["colors"][0][0] * (1 - t) + style["colors"][1][0] * t)
        g = int(style["colors"][0][1] * (1 - t) + style["colors"][1][1] * t)
        b = int(style["colors"][0][2] * (1 - t) + style["colors"][1][2] * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.ellipse(
        [-300, -300, 600, 600], fill=(255, 255, 255, 25)
    )
    overlay_draw.ellipse(
        [WIDTH - 400, HEIGHT - 450, WIDTH + 150, HEIGHT + 100], fill=(255, 255, 255, 25)
    )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    random.seed(name + category)
    positions = [
        (140, 160), (WIDTH - 140, 170), (180, HEIGHT - 190), (WIDTH - 170, HEIGHT - 220),
        (WIDTH - 120, 420), (120, 480), (WIDTH - 200, 800),
    ]
    for (bx, by) in positions:
        color = random.choice(style["balloons"])
        _draw_balloon(draw, bx, by, color, scale=random.uniform(0.8, 1.2))

    _draw_cake(draw, WIDTH // 2, 210, size=1.15)

    if FONT_EMOJI:
        small_emoji_font = _font(FONT_EMOJI, 52)
        draw.text((90, 160), random.choice(DECORATION_EMOJIS), font=small_emoji_font)
        draw.text((WIDTH - 170, 200), random.choice(DECORATION_EMOJIS), font=small_emoji_font)

    title_font = _font(FONT_BOLD, 84)
    sub_font = _font(FONT_REGULAR, 56)
    name_font = _font(FONT_BOLD, 120)

    title = "TUG'ILGAN KUNINGIZ MUBORAK!"
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    draw.text(
        ((WIDTH - (title_bbox[2] - title_bbox[0])) // 2, 520),
        title,
        font=title_font,
        fill=style["title_color"],
    )

    name_bbox = draw.textbbox((0, 0), name, font=name_font)
    name_width = name_bbox[2] - name_bbox[0]
    name_size = 120
    while name_width > WIDTH - 120 and name_size > 40:
        name_size -= 8
        name_font = _font(FONT_BOLD, name_size)
        name_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]

    draw.text(
        ((WIDTH - name_width) // 2 - name_bbox[0], 660),
        name,
        font=name_font,
        fill=style["title_color"],
    )

    sub_text = "Sizga baxt, sog'liq va omad tilaymiz!"
    sub_bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    draw.text(
        ((WIDTH - (sub_bbox[2] - sub_bbox[0])) // 2, 860),
        sub_text,
        font=sub_font,
        fill=style["title_color"],
    )

    path = os.path.join(TEMP_DIR, f"card_{category}_{hash(name) % 100000}.png")
    img.save(path, "PNG")
    return path
