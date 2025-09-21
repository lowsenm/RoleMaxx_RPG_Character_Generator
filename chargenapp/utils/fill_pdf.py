# chargenapp/utils/fill_pdf.py

from __future__ import annotations

import io
import json
import os
import tempfile
from typing import Any, Dict, List

from decimal import Decimal
from django.conf import settings

# ReportLab for drawing text/images at precise coordinates
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

# PyPDF2 for merging overlays onto background pages
from PyPDF2 import PdfReader, PdfWriter


# ---------- Configuration loader ----------

def _load_positions_config() -> List[dict]:
    """
    Always load positions.json from:
        f"{settings.BASE_DIR}/chargenapp/data/positions.json"

    Expected shape (multi-page):
    {
      "pages": [
        {
          "meta": {
            "page_width": 612,
            "page_height": 792,
            "background_pdf": "char_sheet_template2.pdf",
            "background_pdf_page": 0
          },
          "fields": {
            "CharacterName": {"x": 90, "y": 760, "size": 12, "max_width": 200, "align": "left"},
            "Portrait": {"type":"image","x":430,"y":590,"w":140,"h":180}
          }
        },
        ...
      ]
    }

    Also supports a legacy single-page shape:
      { "meta": {...}, "<field>": {...}, ... }
    """
    cfg_path = f"{settings.BASE_DIR}/chargenapp/data/positions.json"
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(f"positions.json not found at {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    if not cfg:
        raise ValueError("positions.json is empty or invalid JSON.")

    # Normalize to pages[]
    if "pages" in cfg and isinstance(cfg["pages"], list):
        pages = cfg["pages"]
    else:
        meta = cfg.get("meta", {})
        fields = {k: v for k, v in cfg.items() if k != "meta"}
        pages = [{"meta": meta, "fields": fields}]

    # Defaults
    for p in pages:
        p.setdefault("meta", {})
        p["meta"].setdefault("page_width", 612)
        p["meta"].setdefault("page_height", 792)
        p.setdefault("fields", {})

    return pages


# ---------- Rendering helpers (ReportLab) ----------

def _rl_wrap_and_draw(c: rl_canvas.Canvas,
                      x: float,
                      y: float,
                      txt: str,
                      *,
                      size: float = 10.0,
                      align: str = "left",
                      max_width: float | None = None,
                      line_height: float | None = None) -> None:
    """
    Draws text at (x,y) with optional wrapping to max_width and custom line_height.
    align ∈ {"left","center","right"}.
    """
    c.setFont("Helvetica", size)
    if line_height is None:
        line_height = size + 2.0

    txt = "" if txt is None else str(txt)

    if max_width is None:
        # Simple multi-line with '\n'
        for i, ln in enumerate(txt.split("\n")):
            if align == "center":
                c.drawCentredString(x, y - i * line_height, ln)
            elif align == "right":
                c.drawRightString(x, y - i * line_height, ln)
            else:
                c.drawString(x, y - i * line_height, ln)
        return

    # Wrap to width using ReportLab width measurements
    words = txt.split()
    lines: List[str] = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, "Helvetica", size) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    for i, ln in enumerate(lines):
        if align == "center":
            c.drawCentredString(x, y - i * line_height, ln)
        elif align == "right":
            c.drawRightString(x, y - i * line_height, ln)
        else:
            c.drawString(x, y - i * line_height, ln)


def _draw_image(c: rl_canvas.Canvas, src: str, x: float, y: float, w: float, h: float) -> None:
    """
    Draw an image from local path or URL at (x,y) with width w and height h.
    Silently ignores failures (to avoid breaking PDF production).
    """
    try:
        if src.lower().startswith(("http://", "https://")):
            import requests  # optional dependency
            r = requests.get(src, timeout=10)
            r.raise_for_status()
            img = ImageReader(io.BytesIO(r.content))
        else:
            img = ImageReader(src)
        c.drawImage(img, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
    except Exception:
        # Ignore image errors to ensure we still produce a PDF
        pass


# ---------- Public API ----------

def fillpdf(input_pdf_path: str, output_pdf_path: str, data_dict: Dict[str, Any]) -> None:
    """
    Render fields from data_dict onto one or more pages using coordinates from positions.json,
    then merge each overlay page on top of the background PDF page(s) declared per page in positions.json.

    - Loads config from: f"{settings.BASE_DIR}/chargenapp/data/positions.json".
    - Uses ReportLab to create per-page overlay(s).
    - Uses PyPDF2 to merge overlays onto background PDFs.
    - Coordinate system: bottom-left, units = points (1/72 inch). US Letter = 612×792.

    Supported field config keys:
      x, y, size, align ("left"|"center"|"right"), max_width, line_height,
      type: "text" (default) or "image"; for images, also w, h.

    Special support:
      - If you don’t define an explicit image field for a portrait, we’ll still honor
        data_dict["Appearance"] or data_dict["CharacterAppearance"] only if your positions.json
        includes a field named "Portrait" (recommended). Otherwise it’s ignored.
    """
    if data_dict is None:
        data_dict = {}

    # Optional portrait discovery (used only if you include a "Portrait" image slot in positions.json)
    portrait_url = data_dict.get("Appearance") or data_dict.get("CharacterAppearance") or ""

    # Load page definitions
    pages_cfg = _load_positions_config()

    # Helper to resolve a value for a field name from data_dict
    def _value_for(field: str) -> str:
        return "" if data_dict.get(field) is None else str(data_dict.get(field))

    # Build a temporary overlays PDF (same number of pages as config pages)
    tmp_overlay = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp_overlay_path = tmp_overlay.name
    tmp_overlay.close()

    # Create the overlays with ReportLab. Each page size matches its meta.
    first_meta = pages_cfg[0]["meta"]
    c = rl_canvas.Canvas(
        tmp_overlay_path,
        pagesize=(float(first_meta.get("page_width", 612)), float(first_meta.get("page_height", 792))),
    )

    for page_idx, page_def in enumerate(pages_cfg):
        meta = page_def.get("meta", {})
        fields = page_def.get("fields", {})

        PAGE_W = float(meta.get("page_width", 612))
        PAGE_H = float(meta.get("page_height", 792))

        if page_idx > 0:
            c.showPage()
            c.setPageSize((PAGE_W, PAGE_H))

        # Draw all fields onto this transparent overlay page
        for field, cfg in fields.items():
            typ = str(cfg.get("type", "text")).lower()
            x = float(cfg.get("x", 0))
            y = float(cfg.get("y", 0))

            if typ == "image":
                # Source: prefer data_dict[field]; else portrait_url (if the slot is literally "Portrait")
                src = str(data_dict.get(field) or (portrait_url if field.lower() == "portrait" else "")).strip()
                if not src:
                    continue
                w = float(cfg.get("w", 100))
                h = float(cfg.get("h", 100))
                _draw_image(c, src, x, y, w, h)
            else:
                val = _value_for(field)
                size = float(cfg.get("size", 10))
                align = str(cfg.get("align", "left")).lower()
                max_width = cfg.get("max_width")
                line_height = cfg.get("line_height")
                _rl_wrap_and_draw(
                    c, x, y, val,
                    size=size,
                    align=align,
                    max_width=float(max_width) if max_width is not None else None,
                    line_height=float(line_height) if line_height is not None else None
                )

    c.save()

    # Merge each overlay page onto the desired background PDF page
    overlay_reader = PdfReader(tmp_overlay_path)
    writer = PdfWriter()

    for page_idx, page_def in enumerate(pages_cfg):
        meta = page_def.get("meta", {})
        bg_pdf_path = meta.get("background_pdf")
        bg_pdf_page = int(meta.get("background_pdf_page", page_idx))  # default: same index

        if not bg_pdf_path:
            raise ValueError(
                f"positions.json page {page_idx}: 'background_pdf' is required for PDF-based templates."
            )
        if not os.path.isabs(bg_pdf_path):
            # resolve relative to BASE_DIR if needed
            candidate = os.path.join(settings.BASE_DIR, bg_pdf_path)
            bg_pdf_use = candidate if os.path.exists(candidate) else bg_pdf_path
        else:
            bg_pdf_use = bg_pdf_path

        if not os.path.exists(bg_pdf_use):
            raise FileNotFoundError(
                f"positions.json page {page_idx}: background PDF not found at '{bg_pdf_use}'."
            )

        bg_reader = PdfReader(bg_pdf_use)
        if bg_pdf_page < 0 or bg_pdf_page >= len(bg_reader.pages):
            raise IndexError(
                f"positions.json page {page_idx}: background_pdf_page {bg_pdf_page} out of range for '{bg_pdf_use}'."
            )

        tpl_page = bg_reader.pages[bg_pdf_page]
        ovl_page = overlay_reader.pages[page_idx]

        # IMPORTANT: PyPDF2's merge_page draws overlay content ON TOP of template
        tpl_page.merge_page(ovl_page)
        writer.add_page(tpl_page)

    # Write final output
    os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)
    with open(output_pdf_path, "wb") as fh:
        writer.write(fh)

    # Cleanup temp overlay
    try:
        os.remove(tmp_overlay_path)
    except Exception:
        pass
