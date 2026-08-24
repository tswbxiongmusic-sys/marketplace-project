from django import template

register = template.Library()


@register.simple_tag
def category_icon(name):
    """Return a useful visual fallback when a category has no uploaded image."""
    label = (name or "").lower()
    icons = {
        "electronics": "💻", "electronic": "💻", "ເອເລັກໂຕຣນິກ": "💻",
        "phone": "📱", "mobile": "📱", "ໂທລະສັບ": "📱",
        "computer": "🖥️", "laptop": "💻", "ຄອມພິວເຕີ": "🖥️",
        "music": "🎸", "instrument": "🎹", "guitar": "🎸", "piano": "🎹", "ເຄື່ອງດົນຕີ": "🎸", "ດົນຕີ": "🎸",
        "fashion": "👕", "clothes": "👕", "clothing": "👗", "ຕູ້ເສື້ອຜ້າ": "👕",
        "beauty": "💄", "cosmetic": "💄", "ຄວາມງາມ": "💄",
        "food": "🍎", "drink": "🥤", "ອາຫານ": "🍎",
        "home": "🏠", "furniture": "🛋️", "ເຮືອນ": "🏠",
        "sport": "⚽", "fitness": "🏋️", "ກິລາ": "⚽",
        "book": "📚", "education": "📚", "ປື້ມ": "📚",
        "car": "🚗", "vehicle": "🚗", "ລົດ": "🚗",
        "pet": "🐾", "ສັດລ້ຽງ": "🐾",
    }
    return next((icon for keyword, icon in icons.items() if keyword in label), "🛍️")


@register.simple_tag
def star_icons(rating):
    """Return 5 booleans (filled or not) for rendering a star rating."""
    try:
        filled = round(float(rating))
    except (TypeError, ValueError):
        filled = 0
    return [i <= filled for i in range(1, 6)]


@register.simple_tag
def product_icon(name, category_name=""):
    label = f"{name or ''} {category_name or ''}".lower()
    icons = {
        "iphone": "📱", "samsung": "📱", "phone": "📱", "ໂທລະສັບ": "📱",
        "laptop": "💻", "computer": "🖥️", "keyboard": "⌨️", "headphone": "🎧",
        "guitar": "🎸", "piano": "🎹", "drum": "🥁", "music": "🎸", "ດົນຕີ": "🎸",
        "camera": "📷", "watch": "⌚", "shoe": "👟", "shirt": "👕",
        "book": "📚", "chair": "🪑", "table": "🪑", "car": "🚗",
    }
    return next((icon for keyword, icon in icons.items() if keyword in label), category_icon(category_name))
