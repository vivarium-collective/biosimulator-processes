
def custom_pf(d, indent=0):
    """Custom dictionary formatter to achieve specific indentation styles."""
    items = []
    for k, v in d.items():
        key_str = f"{repr(k)}: "
        if isinstance(v, dict):
            if v:  # Check if the dictionary is not empty
                value_str = custom_pf(v, indent + 3)
            else:
                value_str = "{}"
        else:
            value_str = repr(v)
        items.append(f"{' ' * indent}{key_str}{value_str}")

    # final formatting
    items_str = ','.join(items)
    if indent > 0:
        return f"{{\n{items_str}\n{' ' * (indent - 4)}}}"
    else:
        return f"{{\n{items_str}\n}}"
