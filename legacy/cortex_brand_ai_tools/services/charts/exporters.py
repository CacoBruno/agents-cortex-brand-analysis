from __future__ import annotations

import io
import os
import base64
from pathlib import Path
import matplotlib.pyplot as plt


def export_figure(
    fig,
    output_format: str = "png",
    return_as: str = "path",
    output_dir: str = "charts",
    filename: str | None = None,
    dpi: int = 200,
    transparent_bg: bool = True,
    close_figure: bool = True,
):
    output_format = (output_format or "png").lower().strip()
    return_as = (return_as or "path").lower().strip()

    valid_formats = {"png", "svg", "pdf", "jpg", "jpeg", "webp"}
    valid_returns = {"path", "bytes", "buffer", "base64", "figure"}

    if output_format not in valid_formats:
        raise ValueError(f"output_format inválido: {output_format}. Use um de {sorted(valid_formats)}")

    if return_as not in valid_returns:
        raise ValueError(f"return_as inválido: {return_as}. Use um de {sorted(valid_returns)}")

    if return_as == "figure":
        return fig

    savefig_kwargs = {
        "format": output_format,
        "transparent": transparent_bg,
        "bbox_inches": "tight",
        "pad_inches": 0.15,
    }
    if output_format in {"png", "jpg", "jpeg", "webp"}:
        savefig_kwargs["dpi"] = dpi

    if return_as in {"bytes", "buffer", "base64"}:
        buffer = io.BytesIO()
        fig.savefig(buffer, **savefig_kwargs)
        buffer.seek(0)

        if return_as == "buffer":
            return buffer

        data = buffer.getvalue()

        if close_figure:
            plt.close(fig)

        if return_as == "bytes":
            return data

        return base64.b64encode(data).decode("utf-8")

    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        filename = f"chart.{output_format}"
    else:
        ext = Path(filename).suffix.lower()
        if not ext:
            filename = f"{filename}.{output_format}"
        elif ext != f".{output_format}":
            filename = str(Path(filename).with_suffix(f".{output_format}"))

    out_path = os.path.join(output_dir, filename)
    fig.savefig(out_path, **savefig_kwargs)

    if close_figure:
        plt.close(fig)

    return out_path