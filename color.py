type_colors = {
    "class": 16,
    "comment": 17,
    "concept": 18,
    "dependent": 19,
    "enum": 20,
    "enumMember": 21,
    "function": 22,
    "macro": 23,
    "method": 24,
    "namespace": 25,
    "parameter": 26,
    "property": 27,
    "type": 28,
    "typeParameter": 29,
    "variable": 30,
}

color_names = {}


def color_name(n: int):
    if n in color_names:
        return color_names.get(n)
    return f'Color {n}'


class Color:
    TEXT = 1
    TEXT_HIGHLIGHT = 2
    FOCUS = 3
    BORDER = 4
    BORDER_HIGHLIGHT = 5
    ERROR = 7


for name in dir(Color):
    value = getattr(Color, name)
    if isinstance(value, int):
        color_names[value] = name
for name in type_colors.keys():
    color_names[type_colors.get(name)] = name
