from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict


def _set_picture_data(element: dict, image_path: str) -> None:
    element["image"]["path"] = image_path
    element["image"]["filename"] = Path(image_path).name


def _set_textbox_text(element: dict, text: str) -> None:
    if not element.get("text"):
        return

    first_paragraph = element["text"][0]
    if not first_paragraph.get("runs"):
        return

    first_paragraph["runs"][0]["text"] = text


def _set_textbox_runs(element: dict, runs: list[dict]) -> None:
    if not element.get("text"):
        element["text"] = [{
            "alignment": 1,
            "runs": runs,
            "line_spacing": 1.0,
            "line_spacing_rule": None,
            "space_before": None,
            "space_after": None,
        }]
        return

    element["text"][0]["runs"] = runs


def _set_table_cell_text(
    element: dict,
    row_idx: int,
    col_idx: int,
    paragraph_idx: int,
    run_idx: int,
    text,
) -> None:
    cells = element.get("cells", [])

    if row_idx >= len(cells):
        raise IndexError(
            f"row_idx {row_idx} fora do range. A estrutura real tem {len(cells)} linhas em cells."
        )

    row = cells[row_idx]
    if col_idx >= len(row):
        raise IndexError(
            f"col_idx {col_idx} fora do range na linha {row_idx}. "
            f"A estrutura real dessa linha tem {len(row)} colunas."
        )

    cell_wrapper = row[col_idx]

    if not isinstance(cell_wrapper, list) or len(cell_wrapper) == 0:
        raise ValueError(
            f"Célula [{row_idx}, {col_idx}] inválida. Esperado list não vazia."
        )

    cell = cell_wrapper[0]

    paragraphs = cell.get("text", [])
    if paragraph_idx >= len(paragraphs):
        raise IndexError(
            f"paragraph_idx {paragraph_idx} fora do range na célula [{row_idx}, {col_idx}]."
        )

    runs = paragraphs[paragraph_idx].get("runs", [])
    if run_idx >= len(runs):
        raise IndexError(
            f"run_idx {run_idx} fora do range na célula [{row_idx}, {col_idx}]. "
            f"Existem {len(runs)} runs."
        )

    runs[run_idx]["text"] = str(text)

def apply_element_override(element: dict, override: dict) -> dict:
    element = deepcopy(element)
    element_type = element.get("type")

    if element_type == "picture":
        if "image_path" in override:
            _set_picture_data(element, override["image_path"])

        if "crop" in override:
            element["crop"] = override["crop"]

        if "is_cropped" in override:
            element["is_cropped"] = override["is_cropped"]

        if "crop_applied" in override:
            element["crop_applied"] = override["crop_applied"]

    elif element_type == "textbox":
        if "text" in override:
            _set_textbox_text(element, override["text"])

        if "runs" in override:
            _set_textbox_runs(element, override["runs"])

    elif element_type == "table":
        for cell_update in override.get("cell_updates", []):
            _set_table_cell_text(
                element=element,
                row_idx=cell_update["row"],
                col_idx=cell_update["col"],
                paragraph_idx=cell_update.get("paragraph", 0),
                run_idx=cell_update.get("run", 0),
                text=cell_update["text"],
            )

    return element