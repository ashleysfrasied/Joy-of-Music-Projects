"""
Carnatic Bingo Sheet Generator
Run: python3 carnatic_bingo_generator.py
"""

from __future__ import annotations

import json
import os
import random
import re
from datetime import datetime, timezone
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Inches, Pt, RGBColor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CONCERT_LIST_FILENAME = "Concert list for bingo sheet.docx"
MCQ_LIST_FILENAME = "Multiple choice question and answer list.docx"
LOGO_FILENAME = "BrandLogoTJOMWords-SideBySide-WhiteBG.jpg"
LOGO_PNG_FILENAME = "logo.png"
OUTPUT_SUBDIR = "completed-bingo-sheets"
CONCERT_TITLE_SKIP = "Bingo quiz concerts"
EXPECTED_CLUES = 24
EXPECTED_MCQS = 20
SHUFFLE_MAX_RETRIES = 100

GRID_LABELS = [
    f"{r}{c}" for r in "ABCDE" for c in range(1, 6) if not (r == "C" and c == 3)
]

DEEP_TEAL = "1B6B6B"
GOLD = "C8960C"
LIGHT_TEAL = "D6EEEE"
MID_TEAL = "A8D5D5"
FREE_BG = "FFF3CD"
BORDER_CLR = "5AACAC"
WHITE = "FFFFFF"
DARK_TEXT = "1A1A2E"

_OPTION_RE = re.compile(r"^[A-D]\.\s*(.+)$", re.IGNORECASE)
_ANSWER_RE = re.compile(r"^Answer:\s*([A-D])\s*$", re.IGNORECASE)


def get_bingo_root() -> str:
    return os.environ.get("BINGO_ROOT", SCRIPT_DIR)


def get_state_path() -> str:
    return os.environ.get("BINGO_STATE_FILE", os.path.join(get_bingo_root(), "bingo_state.json"))


def get_output_dir() -> str:
    return os.environ.get(
        "BINGO_OUTPUT_DIR", os.path.join(get_bingo_root(), OUTPUT_SUBDIR)
    )


def _normalize_text(text: str) -> str:
    return text.replace("\xa0", " ").strip()


def parse_concert_clues(path: str) -> list[str]:
    doc = Document(path)
    clues: list[str] = []
    for p in doc.paragraphs:
        text = _normalize_text(p.text)
        if not text or text == CONCERT_TITLE_SKIP:
            continue
        clues.append(text)
    if len(clues) != EXPECTED_CLUES:
        raise ValueError(
            f"Expected {EXPECTED_CLUES} concert clues in {path}, found {len(clues)}"
        )
    return clues


def _parse_mcq_block(block: str) -> dict[str, Any]:
    lines = [_normalize_text(line) for line in block.split("\n") if _normalize_text(line)]
    if not lines:
        raise ValueError("Empty MCQ block")

    answer = None
    options: list[str] = []
    question_lines: list[str] = []

    for line in lines:
        m_ans = _ANSWER_RE.match(line)
        if m_ans:
            answer = m_ans.group(1).upper()
            continue
        m_opt = _OPTION_RE.match(line)
        if m_opt:
            options.append(m_opt.group(1).strip())
            continue
        if not options and answer is None:
            question_lines.append(line)

    question = " ".join(question_lines).strip()
    if not question or len(options) != 4 or answer not in "ABCD":
        raise ValueError(f"Invalid MCQ block: {block[:80]}...")
    return {"question": question, "options": options, "answer": answer}


def parse_mcqs(path: str) -> list[dict[str, Any]]:
    doc = Document(path)
    blocks: list[str] = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text or text.startswith("Bingo Sheet") or "Form" in text:
            continue
        blocks.append(text)

    mcqs = [_parse_mcq_block(b) for b in blocks]
    if len(mcqs) != EXPECTED_MCQS:
        raise ValueError(f"Expected {EXPECTED_MCQS} MCQs in {path}, found {len(mcqs)}")
    return mcqs


def default_state() -> dict[str, Any]:
    return {
        "sheet_number": 0,
        "next_mcq_index": 0,
        "past_clue_orders": [],
        "generated_sheets": [],
    }


def load_state(state_path: str | None = None) -> dict[str, Any]:
    path = state_path or get_state_path()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for key, val in default_state().items():
            data.setdefault(key, val)
        return data
    return default_state()


def save_state(state: dict[str, Any], state_path: str | None = None) -> None:
    path = state_path or get_state_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _unique_clue_order(past_orders: list[list[int]], num_clues: int) -> list[int]:
    past_set = {tuple(o) for o in past_orders}
    for _ in range(SHUFFLE_MAX_RETRIES):
        order = list(range(num_clues))
        random.shuffle(order)
        if tuple(order) not in past_set:
            return order
    raise RuntimeError(
        f"Could not find a new clue permutation after {SHUFFLE_MAX_RETRIES} retries"
    )


def next_generation_params(
    num_clues: int = EXPECTED_CLUES,
    num_mcqs: int = EXPECTED_MCQS,
    state_path: str | None = None,
) -> tuple[int, list[int], int, dict[str, Any]]:
    """Advance state and return (sheet_number, clue_order, mcq_index, updated_state)."""
    state = load_state(state_path)
    clue_order = _unique_clue_order(state["past_clue_orders"], num_clues)
    sheet_number = state["sheet_number"] + 1
    mcq_index = state["next_mcq_index"] % num_mcqs

    state["sheet_number"] = sheet_number
    state["past_clue_orders"].append(clue_order)
    state["next_mcq_index"] = (mcq_index + 1) % num_mcqs

    return sheet_number, clue_order, mcq_index, state


def output_filename(sheet_number: int) -> str:
    return f"Carnatic_Bingo_Sheet_{sheet_number:03d}.docx"


def resolve_logo_path(root: str) -> str:
    """Return a python-docx-compatible logo path (PNG preferred)."""
    png_path = os.path.join(root, LOGO_PNG_FILENAME)
    if os.path.isfile(png_path):
        return png_path
    jpg_path = os.path.join(root, LOGO_FILENAME)
    if not os.path.isfile(jpg_path):
        raise FileNotFoundError(
            f"Logo not found. Expected {png_path} or {jpg_path}"
        )
    try:
        from PIL import Image
    except ImportError as e:
        raise FileNotFoundError(
            f"{png_path} missing and Pillow is required to convert {jpg_path}. "
            "Run: sips -s format png "
            f"'{LOGO_FILENAME}' --out '{LOGO_PNG_FILENAME}'"
        ) from e
    with Image.open(jpg_path) as im:
        im.convert("RGB").save(png_path, format="PNG")
    return png_path


def emu(inches: float) -> Emu:
    return Emu(int(inches * 914400))


def set_row_height(row, height_pt: float) -> None:
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    trHeight = OxmlElement("w:trHeight")
    trHeight.set(qn("w:val"), str(int(height_pt * 20)))
    trHeight.set(qn("w:hRule"), "exact")
    trPr.append(trHeight)


def set_cell_bg(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_borders(cell, color: str = "CCCCCC", size: int = 4) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcB = OxmlElement("w:tcBorders")
    for side in ["top", "left", "bottom", "right"]:
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcB.append(el)
    tcPr.append(tcB)


def set_cell_margins(cell, top=60, bottom=60, left=80, right=80) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcM = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        tcM.append(el)
    tcPr.append(tcM)


def set_cell_valign(cell, align: str = "center") -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    v = OxmlElement("w:vAlign")
    v.set(qn("w:val"), align)
    tcPr.append(v)


def add_gold_rule(doc, before_pt=0, after_pt=3) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before_pt)
    p.paragraph_format.space_after = Pt(after_pt)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single")
    b.set(qn("w:sz"), "6")
    b.set(qn("w:color"), GOLD)
    pBdr.append(b)
    pPr.append(pBdr)


def section_hdr(doc, text, size=10, before=3, after=2) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(DEEP_TEAL)


def make_header_cell(cell, text, bg=DEEP_TEAL, font_size=7.5) -> None:
    set_cell_bg(cell, bg)
    p = cell.paragraphs[0]
    p.clear()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(font_size)
    r.font.color.rgb = RGBColor.from_string(WHITE)


def make_data_cell(cell, row_idx: int) -> None:
    set_cell_bg(cell, LIGHT_TEAL if row_idx % 2 == 1 else WHITE)
    cell.paragraphs[0].clear()


def build_bingo_docx(
    sheet_number: int,
    clues: list[str],
    clue_order: list[int],
    mcq: dict[str, Any],
    logo_path: str,
    output_path: str,
) -> str:
    grid_labels = GRID_LABELS
    clue_map = {grid_labels[i]: clues[clue_order[i]] for i in range(len(grid_labels))}

    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    sec.left_margin = Inches(0.65)
    sec.right_margin = Inches(0.65)
    sec.top_margin = Inches(0.40)
    sec.bottom_margin = Inches(0.40)

    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10)

    # PAGE 1
    lp = doc.add_paragraph()
    lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lp.paragraph_format.space_before = Pt(0)
    lp.paragraph_format.space_after = Pt(0)
    lp.add_run().add_picture(logo_path, width=Inches(2.6))

    sp = doc.add_paragraph()
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sp.paragraph_format.space_before = Pt(1)
    sp.paragraph_format.space_after = Pt(2)
    r = sp.add_run(f"Carnatic Bingo  |  Bingo Sheet #{sheet_number}")
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor.from_string(DEEP_TEAL)

    add_gold_rule(doc, before_pt=0, after_pt=2)

    INFO_COL = 3456
    info = doc.add_table(rows=2, cols=3)
    info.alignment = WD_TABLE_ALIGNMENT.CENTER
    rows_data = [
        [
            "Student Name: ___________________",
            "Teacher: ___________________",
            "City, State: ___________________",
        ],
        [
            "Parent Name: ____________________",
            "Parent Email: ___________________",
            "Parent WhatsApp: ________________",
        ],
    ]
    for ri, row in enumerate(info.rows):
        set_row_height(row, 14)
        for ci, cell in enumerate(row.cells):
            cell.width = emu(INFO_COL / 1440)
            set_cell_borders(cell, color=BORDER_CLR, size=4)
            set_cell_margins(cell, top=40, bottom=40, left=80, right=80)
            set_cell_bg(cell, LIGHT_TEAL if ri == 0 else WHITE)
            p = cell.paragraphs[0]
            p.clear()
            run = p.add_run(rows_data[ri][ci])
            run.font.size = Pt(8.5)
            run.font.name = "Calibri"

    doc.add_paragraph().paragraph_format.space_after = Pt(2)

    GRID_LABEL_W = 403
    GRID_CELL_W = 1037
    GRID_ROW_H = 19
    bingo = doc.add_table(rows=6, cols=6)
    bingo.alignment = WD_TABLE_ALIGNMENT.CENTER
    col_widths_g = [GRID_LABEL_W] + [GRID_CELL_W] * 5

    for ri, row in enumerate(bingo.rows):
        set_row_height(row, GRID_ROW_H)
        for ci, cell in enumerate(row.cells):
            cell.width = emu(col_widths_g[ci] / 1440)
            set_cell_borders(cell, color=BORDER_CLR, size=6)
            set_cell_margins(cell, top=25, bottom=25, left=40, right=40)
            set_cell_valign(cell, "center")

    for ci, hdr in enumerate(["", "1", "2", "3", "4", "5"]):
        make_header_cell(bingo.rows[0].cells[ci], hdr, bg=DEEP_TEAL, font_size=9)

    for ri in range(1, 6):
        lc = bingo.rows[ri].cells[0]
        set_cell_bg(lc, MID_TEAL)
        p = lc.paragraphs[0]
        p.clear()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("ABCDE"[ri - 1])
        r.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor.from_string(DARK_TEXT)

        for ci in range(1, 6):
            cell = bingo.rows[ri].cells[ci]
            if ri == 3 and ci == 3:
                set_cell_bg(cell, FREE_BG)
                p = cell.paragraphs[0]
                p.clear()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run("★ Answer MCQ ★")
                r.bold = True
                r.font.size = Pt(6.5)
                r.font.color.rgb = RGBColor.from_string(GOLD)
            else:
                set_cell_bg(cell, LIGHT_TEAL if ri % 2 == 1 else WHITE)
                cell.paragraphs[0].clear()

    note = doc.add_paragraph()
    note.paragraph_format.space_before = Pt(2)
    note.paragraph_format.space_after = Pt(2)
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nr = note.add_run(
        "★  The FREE space (C3) may be crossed off by correctly answering "
        "the multiple choice question on the back."
    )
    nr.italic = True
    nr.font.size = Pt(7)
    nr.font.color.rgb = RGBColor.from_string("555555")

    add_gold_rule(doc, before_pt=0, after_pt=2)
    section_hdr(doc, "I Heard", size=11, before=2, after=2)

    CLUE_COL = 5126
    CLUE_ROW_H = 15
    half = 12
    grid_l = grid_labels[:half]
    grid_r = grid_labels[half:]

    ct = doc.add_table(rows=half, cols=2)
    ct.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(ct.rows):
        set_row_height(row, CLUE_ROW_H)
        for ci, cell in enumerate(row.cells):
            cell.width = emu(CLUE_COL / 1440)
            set_cell_borders(cell, color=BORDER_CLR, size=4)
            set_cell_margins(cell, top=30, bottom=30, left=65, right=65)

    for i in range(half):
        for ci, lbl in enumerate([grid_l[i], grid_r[i]]):
            cell = ct.rows[i].cells[ci]
            set_cell_bg(cell, LIGHT_TEAL if i % 2 == 0 else WHITE)
            p = cell.paragraphs[0]
            p.clear()
            br = p.add_run(f"{lbl}.  ")
            br.bold = True
            br.font.size = Pt(7.5)
            br.font.color.rgb = RGBColor.from_string(DEEP_TEAL)
            tr = p.add_run(clue_map[lbl])
            tr.font.size = Pt(7.5)

    # PAGE 2
    doc.add_page_break()

    lp2 = doc.add_paragraph()
    lp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    lp2.paragraph_format.space_before = Pt(0)
    lp2.paragraph_format.space_after = Pt(1)
    lp2.add_run().add_picture(logo_path, width=Inches(2.4))

    sp2 = doc.add_paragraph()
    sp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sp2.paragraph_format.space_before = Pt(0)
    sp2.paragraph_format.space_after = Pt(2)
    r2 = sp2.add_run(f"Carnatic Bingo  |  Bingo Sheet #{sheet_number}")
    r2.bold = True
    r2.font.size = Pt(10)
    r2.font.color.rgb = RGBColor.from_string(DEEP_TEAL)

    add_gold_rule(doc, before_pt=0, after_pt=3)
    section_hdr(doc, "Concert Tracking", size=10, before=2, after=2)

    CT_HDRS = [
        "Cell",
        "Song",
        "Ragam",
        "Thalam",
        "Composer",
        "Improv\n(A/T/N/K)",
        "Comp. Type",
        "Concert",
    ]
    CT_WIDTHS = [576, 1296, 1152, 864, 1152, 720, 1296, 720]
    ctt = doc.add_table(rows=8, cols=8)
    ctt.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(ctt.rows):
        set_row_height(row, 14 if ri > 0 else 18)
        for ci, cell in enumerate(row.cells):
            cell.width = emu(CT_WIDTHS[ci] / 1440)
            set_cell_borders(cell, color=BORDER_CLR, size=4)
            set_cell_margins(cell, top=25, bottom=25, left=45, right=45)
            set_cell_valign(cell, "center")
    for ci, hdr in enumerate(CT_HDRS):
        make_header_cell(ctt.rows[0].cells[ci], hdr, font_size=7)
    for ri in range(1, 8):
        for ci in range(8):
            make_data_cell(ctt.rows[ri].cells[ci], ri)

    section_hdr(doc, "Concert Details", size=10, before=5, after=2)
    CD_HDRS = ["Concert #", "Date", "Artist", "Accompanists", "Notes", "Venue", "Location"]
    CD_WIDTHS = [648, 864, 1296, 1296, 1296, 1188, 1188]
    cdt = doc.add_table(rows=8, cols=7)
    cdt.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ri, row in enumerate(cdt.rows):
        set_row_height(row, 14 if ri > 0 else 18)
        for ci, cell in enumerate(row.cells):
            cell.width = emu(CD_WIDTHS[ci] / 1440)
            set_cell_borders(cell, color=BORDER_CLR, size=4)
            set_cell_margins(cell, top=25, bottom=25, left=45, right=45)
            set_cell_valign(cell, "center")
    for ci, hdr in enumerate(CD_HDRS):
        make_header_cell(cdt.rows[0].cells[ci], hdr, font_size=7.5)
    for ri in range(1, 8):
        for ci in range(7):
            make_data_cell(cdt.rows[ri].cells[ci], ri)

    section_hdr(doc, "Multiple Choice Question", size=10, before=5, after=2)
    mcq_t = doc.add_table(rows=1, cols=1)
    mcq_t.alignment = WD_TABLE_ALIGNMENT.CENTER
    mcq_cell = mcq_t.rows[0].cells[0]
    mcq_cell.width = emu(7776 / 1440)
    set_cell_bg(mcq_cell, FREE_BG)
    set_cell_borders(mcq_cell, color=GOLD, size=8)
    set_cell_margins(mcq_cell, top=80, bottom=80, left=140, right=140)

    p0 = mcq_cell.paragraphs[0]
    p0.clear()
    qr = p0.add_run(mcq["question"])
    qr.bold = True
    qr.font.size = Pt(9.5)

    for idx, opt in enumerate(mcq["options"]):
        cp = mcq_cell.add_paragraph()
        cp.paragraph_format.space_before = Pt(1)
        cr = cp.add_run(f"  \u25a1  {chr(65 + idx)})  {opt}")
        cr.font.size = Pt(9.5)

    htp = doc.add_paragraph()
    htp.paragraph_format.space_before = Pt(6)
    htp.paragraph_format.space_after = Pt(0)
    pPr = htp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    top_el = OxmlElement("w:top")
    top_el.set(qn("w:val"), "single")
    top_el.set(qn("w:sz"), "6")
    top_el.set(qn("w:color"), GOLD)
    pBdr.append(top_el)
    pPr.append(pBdr)

    ht1 = htp.add_run("How to play:  ")
    ht1.bold = True
    ht1.font.size = Pt(8.5)
    ht1.font.color.rgb = RGBColor.from_string(DEEP_TEAL)
    ht2 = htp.add_run(
        'At a concert, when you hear or see something that matches one of the hints on page 1 '
        '("I Heard"), put a check or X in the matching empty square (A1-E5). '
        "Get 5 in a row - horizontally, vertically, or diagonally - to complete your Bingo! "
        "The FREE space (C3) is unlocked by correctly answering the multiple choice question above."
    )
    ht2.font.size = Pt(8.5)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    doc.save(output_path)
    return output_path


def generate_sheet(
    bingo_root: str | None = None,
    state_path: str | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Generate one bingo sheet; update state; return manifest entry."""
    root = bingo_root or get_bingo_root()
    state_file = state_path or get_state_path()
    out_dir = output_dir or get_output_dir()
    os.makedirs(out_dir, exist_ok=True)

    concert_path = os.path.join(root, CONCERT_LIST_FILENAME)
    mcq_path = os.path.join(root, MCQ_LIST_FILENAME)
    logo_path = resolve_logo_path(root)

    clues = parse_concert_clues(concert_path)
    mcqs = parse_mcqs(mcq_path)

    sheet_number, clue_order, mcq_index, state = next_generation_params(
        num_clues=len(clues),
        num_mcqs=len(mcqs),
        state_path=state_file,
    )

    filename = output_filename(sheet_number)
    output_path = os.path.join(out_dir, filename)

    build_bingo_docx(
        sheet_number=sheet_number,
        clues=clues,
        clue_order=clue_order,
        mcq=mcqs[mcq_index],
        logo_path=logo_path,
        output_path=output_path,
    )

    entry = {
        "sheet_number": sheet_number,
        "filename": filename,
        "path": output_path,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mcq_index": mcq_index,
        "mcq_question": mcqs[mcq_index]["question"],
        "clue_order": clue_order,
    }
    state["generated_sheets"].append(entry)
    save_state(state, state_file)
    return entry


def main() -> None:
    entry = generate_sheet()
    print(f"Generated : {entry['filename']}")
    print(f"Sheet #   : {entry['sheet_number']}")
    print(f"MCQ used  : #{entry['mcq_index'] + 1} — {entry['mcq_question'][:65]}...")
    print(f"Saved to  : {entry['path']}")


if __name__ == "__main__":
    main()
