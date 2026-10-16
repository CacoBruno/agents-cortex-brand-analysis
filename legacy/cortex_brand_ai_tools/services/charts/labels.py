from __future__ import annotations

from services.charts.utils import _is_number


def _labels_allowed(show_labels: bool, n: int, max_n: int = 15) -> bool:
    return bool(show_labels) and n <= max_n


def _format_number_unit(v, style_dict: dict) -> str:
    if v is None:
        return ""
    if not _is_number(v):
        return str(v)

    x = float(v)
    unit = style_dict.get("unit", None)
    decimals = int(style_dict.get("decimals", 2))
    dec_comma = bool(style_dict.get("decimal_comma", True))
    thousands_sep = bool(style_dict.get("thousands_sep", False))

    suffix = ""
    if unit:
        u = str(unit).strip().upper()
        if u == "M":
            x /= 1_000_000.0
            suffix = " M"
        elif u == "B":
            x /= 1_000_000_000.0
            suffix = " B"

    if thousands_sep:
        s = f"{x:,.{decimals}f}"
    else:
        s = f"{x:.{decimals}f}"

    if dec_comma:
        if thousands_sep:
            s = s.replace(",", "§").replace(".", ",").replace("§", ".")
        else:
            s = s.replace(".", ",")

    return f"{s}{suffix}"


def _merge_value_label_style(base: dict, override: dict | None) -> dict:
    d = dict(base)
    if isinstance(override, dict):
        for k, v in override.items():
            if k == "unit":
                d[k] = v
            elif v is not None:
                d[k] = v

    if not isinstance(d.get("fields"), (list, tuple)) or not d["fields"]:
        d["fields"] = ["y"]

    d["fields"] = [str(f).lower().strip() for f in d["fields"] if f is not None]
    allowed = {"x", "y", "z", "label"}
    d["fields"] = [f for f in d["fields"] if f in allowed]

    if not d["fields"]:
        d["fields"] = ["y"]

    return d


def _format_value_label(x=None, y=None, z=None, label=None, vls_dict=None) -> str:
    d = vls_dict or {}
    fields = d.get("fields", ["y"])
    use_prefix = bool(d.get("prefix", False))

    parts = []

    if "label" in fields and label is not None:
        parts.append(str(label))

    if "x" in fields and x is not None:
        parts.append(f"X: {x}" if use_prefix else f"{x}")

    if "y" in fields and y is not None:
        y_txt = _format_number_unit(y, d) if _is_number(y) else str(y)
        parts.append(f"Y: {y_txt}" if use_prefix else y_txt)

    if "z" in fields and z is not None:
        z_txt = _format_number_unit(z, d) if _is_number(z) else str(z)
        parts.append(f"Z: {z_txt}" if use_prefix else z_txt)

    return " | ".join(parts)


def _label_text_style_kwargs(vls_dict, font_family: str):
    return dict(
        fontsize=vls_dict["size"],
        fontfamily=font_family,
        fontweight="bold" if vls_dict.get("bold", True) else "normal",
        fontstyle="italic" if vls_dict.get("italic", False) else "normal",
        color=vls_dict.get("color", "#111827"),
    )


def _apply_labels(
    ax,
    kind: str,
    font_family: str,
    value_label_style: dict,
    x=None,
    y=None,
    z=None,
    bars=None,
    y_labels=None,
):
    if kind == "bar" and bars is not None:
        pad = float(value_label_style.get("padding", 3))
        for i, bar in enumerate(bars):
            y_val = bar.get_height()
            x_val = x[i] if x is not None and i < len(x) else None
            z_val = z[i] if z is not None and i < len(z) else None
            txt = _format_value_label(x=x_val, y=y_val, z=z_val, vls_dict=value_label_style)
            if not txt:
                continue
            ax.annotate(
                txt,
                (bar.get_x() + bar.get_width() / 2, y_val),
                xytext=(0, pad),
                textcoords="offset points",
                ha="center",
                va="bottom",
                **_label_text_style_kwargs(value_label_style, font_family)
            )

    elif kind == "barh" and bars is not None:
        pad = float(value_label_style.get("padding", 3))
        for i, b in enumerate(bars):
            v = float(b.get_width())
            if v == 0:
                continue
            ylab = y_labels[i] if y_labels is not None and i < len(y_labels) else None
            txt = _format_value_label(x=ylab, y=v, z=None, vls_dict=value_label_style)
            if not txt:
                continue
            ax.annotate(
                txt,
                (v, b.get_y() + b.get_height() / 2.0),
                xytext=(pad, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                **_label_text_style_kwargs(value_label_style, font_family)
            )

    elif kind == "line":
        offx, offy = value_label_style.get("offset_xy", (0, 6))
        for xi, yi in zip(x, y):
            txt = _format_value_label(x=xi, y=yi, z=None, vls_dict=value_label_style)
            if not txt:
                continue
            ax.annotate(
                txt,
                (xi, yi),
                textcoords="offset points",
                xytext=(offx, offy),
                ha="center",
                **_label_text_style_kwargs(value_label_style, font_family)
            )

    elif kind == "line_h":
        offx, offy = value_label_style.get("offset_xy", (6, 0))
        for yc, xv in zip(y_labels, x):
            try:
                xv_num = float(xv)
            except Exception:
                continue
            txt = _format_value_label(x=yc, y=xv_num, z=None, vls_dict=value_label_style)
            if not txt:
                continue
            ax.annotate(
                txt,
                (xv_num, yc),
                textcoords="offset points",
                xytext=(offx, offy),
                ha="left",
                va="center",
                **_label_text_style_kwargs(value_label_style, font_family)
            )

    elif kind == "scatter":
        offx, offy = value_label_style.get("offset_xy", (0, 6))
        for i, (xi, yi) in enumerate(zip(x, y)):
            lbl = None
            if isinstance(value_label_style.get("label_values"), (list, tuple)):
                try:
                    lbl = value_label_style["label_values"][i]
                except Exception:
                    lbl = None

            zi = None
            if z is not None:
                try:
                    zi = z.iloc[i]
                except Exception:
                    try:
                        zi = z[i]
                    except Exception:
                        zi = None

            txt = _format_value_label(
                x=xi,
                y=yi,
                z=zi,
                label=lbl,
                vls_dict=value_label_style)
            
            if not txt:
                continue
            ax.annotate(
                txt,
                (xi, yi),
                textcoords="offset points",
                xytext=(offx, offy),
                ha="center",
                **_label_text_style_kwargs(value_label_style, font_family)
            )