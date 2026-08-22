"""Lao provinces used for the checkout address dropdown.

District names are collected as free text (not a fixed dropdown) since an
inaccurate hardcoded district list would be worse than a plain text field.
"""

LAO_PROVINCES = [
    "ນະຄອນຫຼວງວຽງຈັນ",
    "ຜົ້ງສາລີ",
    "ຫຼວງນ້ຳທາ",
    "ອຸດົມໄຊ",
    "ບໍ່ແກ້ວ",
    "ຫຼວງພະບາງ",
    "ຫົວພັນ",
    "ໄຊຍະບູລີ",
    "ຊຽງຂວາງ",
    "ວຽງຈັນ",
    "ບໍລິຄຳໄຊ",
    "ຄຳມ່ວນ",
    "ສະຫວັນນະເຂດ",
    "ສາລະວັນ",
    "ເຊກອງ",
    "ຈຳປາສັກ",
    "ອັດຕະປື",
    "ໄຊສົມບູນ",
]

LAO_PROVINCE_CHOICES = [(name, name) for name in LAO_PROVINCES]
