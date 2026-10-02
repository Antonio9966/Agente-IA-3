import io
import re
from typing import List, Dict, Any, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets cell padding/margins in twips (1/20 of a pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_apa_table_borders(table):
    """Sets APA 7 style borders: top line, header bottom line, table bottom line, no vertical lines."""
    tblPr = table._tbl.tblPr
    # Clear existing borders
    for child in list(tblPr):
        if child.tag.endswith('tblBorders'):
            tblPr.remove(child)
            
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="1F2937"/>\n'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="1F2937"/>\n'
        f'  <w:insideH w:val="none"/>\n'
        f'  <w:insideV w:val="none"/>\n'
        f'  <w:left w:val="none"/>\n'
        f'  <w:right w:val="none"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)
    
    # Header bottom border on the header row
    header_tr = table.rows[0]._tr.get_or_add_trPr()
    # Add bottom border to header cells
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>\n'
            f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="374151"/>\n'
            f'</w:tcBorders>'
        )
        tcPr.append(tcBorders)

def generate_word_matrix_doc(
    table_rows: List[Dict[str, Any]],
    table_number: str = "Tabla 4",
    table_title: str = "Técnicas y algoritmos utilizados en estudios sobre deserción universitaria",
    narrative_text: str = "",
    lead_title: str = "Árboles de decisión.",
    references: Optional[List[str]] = None,
    journal_header: str = "VISIÓN EMPRESARIAL"
) -> io.BytesIO:
    """Generates an academic-grade Word .docx document matching Image 1 format."""
    doc = Document()
    
    # Configure page margins (1 inch / 2.54 cm all sides - APA standard)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Journal / Institutional Header (Top)
    if journal_header:
        p_hdr = doc.add_paragraph()
        r_hdr = p_hdr.add_run(journal_header.upper())
        r_hdr.font.name = 'Arial'
        r_hdr.font.size = Pt(13)
        r_hdr.font.bold = True
        r_hdr.font.color.rgb = RGBColor(55, 65, 81)
        p_hdr.paragraph_format.space_after = Pt(24)
        
    # Table Identification (APA 7: Table X in bold, next line italic description)
    p_num = doc.add_paragraph()
    r_num = p_num.add_run(table_number)
    r_num.font.name = 'Times New Roman'
    r_num.font.size = Pt(11)
    r_num.font.bold = True
    p_num.paragraph_format.space_after = Pt(2)
    
    p_title = doc.add_paragraph()
    r_title = p_title.add_run(table_title)
    r_title.font.name = 'Times New Roman'
    r_title.font.size = Pt(11)
    r_title.font.italic = True
    p_title.paragraph_format.space_after = Pt(8)
    
    # Academic Table
    table = doc.add_table(rows=len(table_rows) + 1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    
    col_widths = [Inches(1.8), Inches(3.2), Inches(1.8)]
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width
            set_cell_margins(row.cells[idx], top=80, bottom=80, left=100, right=100)
            
    # Headers
    headers = ["Autor", "Técnicas/Algoritmos", "Mejor precisión"]
    for idx, text in enumerate(headers):
        cell = table.cell(0, idx)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if idx != 1 else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10.5)
        run.font.bold = True
        
    # Fill Data Rows
    for row_idx, data in enumerate(table_rows):
        cells = table.rows[row_idx + 1].cells
        
        # 1. Autor
        p0 = cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p0.paragraph_format.space_after = Pt(4)
        r0 = p0.add_run(data.get("autor", "No especificado"))
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(10)
        
        # 2. Técnicas/Algoritmos
        p1 = cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p1.paragraph_format.space_after = Pt(2)
        p1.paragraph_format.line_spacing = 1.15
        
        techs_raw = data.get("tecnicas_algoritmos", "")
        # Handle newlines
        lines = [ln.strip() for ln in techs_raw.split("\n") if ln.strip()]
        if not lines:
            lines = ["No especifica"]
            
        for l_idx, line in enumerate(lines):
            if l_idx > 0:
                p_extra = cells[1].add_paragraph()
                p_extra.paragraph_format.space_after = Pt(2)
                p_extra.paragraph_format.line_spacing = 1.15
                r = p_extra.add_run(line)
            else:
                r = p1.add_run(line)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.5)
            
        # 3. Mejor precisión
        p2 = cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p2.paragraph_format.space_after = Pt(4)
        best_prec = data.get("mejor_precision", "No especifica")
        r2 = p2.add_run(best_prec)
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(10)
        
    set_apa_table_borders(table)
    
    # Narrative text beneath table
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    if narrative_text:
        p_narr = doc.add_paragraph()
        p_narr.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_narr.paragraph_format.line_spacing = 1.25
        p_narr.paragraph_format.space_after = Pt(18)
        
        # If narrative starts with lead_title, format lead_title in bold
        lead = lead_title.strip() if lead_title else ""
        if lead and narrative_text.startswith(lead):
            r_lead = p_narr.add_run(lead + " ")
            r_lead.font.name = 'Times New Roman'
            r_lead.font.size = Pt(10.5)
            r_lead.font.bold = True
            
            body = narrative_text[len(lead):].lstrip()
            r_body = p_narr.add_run(body)
            r_body.font.name = 'Times New Roman'
            r_body.font.size = Pt(10.5)
        else:
            r_full = p_narr.add_run(narrative_text)
            r_full.font.name = 'Times New Roman'
            r_full.font.size = Pt(10.5)
            
    # References Section
    if references:
        p_ref_title = doc.add_paragraph()
        r_ref_title = p_ref_title.add_run("Referencias")
        r_ref_title.font.name = 'Times New Roman'
        r_ref_title.font.size = Pt(11)
        r_ref_title.font.bold = True
        p_ref_title.paragraph_format.space_before = Pt(14)
        p_ref_title.paragraph_format.space_after = Pt(6)
        
        for ref in references:
            if not ref or not ref.strip():
                continue
            p_ref = doc.add_paragraph()
            p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_ref.paragraph_format.left_indent = Inches(0.5)
            p_ref.paragraph_format.first_line_indent = Inches(-0.5)
            p_ref.paragraph_format.space_after = Pt(4)
            p_ref.paragraph_format.line_spacing = 1.15
            
            r_ref = p_ref.add_run(ref.strip())
            r_ref.font.name = 'Times New Roman'
            r_ref.font.size = Pt(9.5)
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def generate_excel_matrix_sheet(
    table_rows: List[Dict[str, Any]],
    table_title: str = "Matriz de Literatura Científica",
    topic: str = ""
) -> io.BytesIO:
    """Generates a styled Excel .xlsx spreadsheet with the extracted data."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Matriz de Extracción"
    ws.views.sheetView[0].showGridLines = True
    
    # Title Row
    ws.merge_cells('A1:G1')
    title_cell = ws['A1']
    title_cell.value = f"{table_title} - {topic}" if topic else table_title
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    title_cell.alignment = Alignment(vertical="center", horizontal="left")
    ws.row_dimensions[1].height = 30
    
    # Subtitle / Generation notice
    ws.merge_cells('A2:G2')
    sub_cell = ws['A2']
    sub_cell.value = "Generado automáticamente con Antonio IA · Extractor Científico con Groq API & OpenAlex/Crossref"
    sub_cell.font = Font(name="Calibri", size=9, italic=True, color="6B7280")
    sub_cell.alignment = Alignment(vertical="center", horizontal="left")
    ws.row_dimensions[2].height = 18
    
    # Headers
    headers = [
        ("A", "Autor (Cita corta)", 18),
        ("B", "Año", 8),
        ("C", "Técnicas / Algoritmos", 35),
        ("D", "Mejor Precisión / Técnica", 25),
        ("E", "Título del Artículo", 40),
        ("F", "DOI / Enlace", 28),
        ("G", "Referencia Completa", 45)
    ]
    
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )
    
    for col_letter, header_text, col_width in headers:
        cell = ws[f"{col_letter}4"]
        cell.value = header_text
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        ws.column_dimensions[col_letter].width = col_width
        
    ws.row_dimensions[4].height = 28
    
    # Rows
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    for idx, r in enumerate(table_rows):
        row_num = idx + 5
        is_even = (idx % 2 == 1)
        row_fill = zebra_fill if is_even else None
        
        ws[f"A{row_num}"] = r.get("autor", "")
        ws[f"B{row_num}"] = r.get("year", "")
        ws[f"C{row_num}"] = r.get("tecnicas_algoritmos", "")
        ws[f"D{row_num}"] = r.get("mejor_precision", "")
        ws[f"E{row_num}"] = r.get("title", "")
        
        doi_val = r.get("doi", "") or r.get("url", "")
        ws[f"F{row_num}"] = f"https://doi.org/{doi_val}" if doi_val and not str(doi_val).startswith("http") else str(doi_val)
        ws[f"G{row_num}"] = r.get("cita_completa", "")
        
        for col_letter, _, _ in headers:
            c = ws[f"{col_letter}{row_num}"]
            c.font = Font(name="Calibri", size=10)
            c.border = thin_border
            if row_fill:
                c.fill = row_fill
            c.alignment = Alignment(vertical="top", wrap_text=True)
            if col_letter in ["A", "B", "D"]:
                c.alignment = Alignment(horizontal="center" if col_letter == "B" else "left", vertical="top", wrap_text=True)
                
        ws.row_dimensions[row_num].height = 45
        
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
