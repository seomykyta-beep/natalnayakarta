"""Генерация PDF отчёта натальной карты"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / 'reports'
FONT_PATH = BASE_DIR / 'DejaVuSans.ttf'

try:
    pdfmetrics.registerFont(TTFont('DejaVu', str(FONT_PATH)))
    DEFAULT_FONT = 'DejaVu'
except:
    DEFAULT_FONT = 'Helvetica'

COLORS = {
    'primary': colors.HexColor('#1a1a2e'),
    'accent': colors.HexColor('#ffd700'),
    'text': colors.HexColor('#333333'),
    'light': colors.HexColor('#f5f5f5'),
}


def generate_pdf(user_data):
    """Генерирует PDF отчёт"""
    name = user_data.get('name', 'Unknown')
    filename = REPORTS_DIR / f'report_{name}.pdf'
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(filename), pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    
    # Кастомные стили с уникальными именами
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
        fontName=DEFAULT_FONT, fontSize=24, textColor=COLORS['primary'],
        spaceAfter=20, alignment=1)
    
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'],
        fontName=DEFAULT_FONT, fontSize=14, textColor=colors.gray,
        spaceAfter=30, alignment=1)
    
    section_style = ParagraphStyle('CustomSection', parent=styles['Heading2'],
        fontName=DEFAULT_FONT, fontSize=16, textColor=COLORS['primary'],
        spaceBefore=20, spaceAfter=10)
    
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'],
        fontName=DEFAULT_FONT, fontSize=10, textColor=COLORS['text'], spaceAfter=8)
    
    small_style = ParagraphStyle('CustomSmall', parent=styles['Normal'],
        fontName=DEFAULT_FONT, fontSize=9, textColor=colors.gray)
    
    story = []
    
    # Заголовок
    story.append(Paragraph('НАТАЛЬНАЯ КАРТА', title_style))
    meta = user_data.get('meta', {})
    story.append(Paragraph(f'{name}<br/>{meta.get("dt", "")} • {meta.get("city", "")}', subtitle_style))
    story.append(Spacer(1, 20))
    
    # Планеты
    story.append(Paragraph('ПОЛОЖЕНИЕ ПЛАНЕТ', section_style))
    planets = user_data.get('planets', [])
    planet_data = [['Планета', 'Знак', 'Градус', 'Дом', 'Достоинство']]
    
    for p in planets[:13]:
        planet_data.append([
            f"{p.get('icon', '')} {p.get('name', '')}",
            p.get('sign', ''),
            f"{p.get('degree', 0):.1f}",
            str(p.get('house', '')),
            p.get('dignity', '-') or '-'
        ])
    
    planet_table = Table(planet_data, colWidths=[4*cm, 3*cm, 2*cm, 2*cm, 3*cm])
    planet_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLORS['light']]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(planet_table)
    story.append(Spacer(1, 20))
    
    # Аспекты
    aspects = user_data.get('aspects', [])
    if aspects:
        story.append(Paragraph('ОСНОВНЫЕ АСПЕКТЫ', section_style))
        aspect_data = [['Аспект', 'Тип', 'Орбис']]
        for a in aspects[:15]:
            aspect_data.append([
                f"{a.get('p1', '')} - {a.get('p2', '')}",
                a.get('name', a.get('type', '')),
                f"{a.get('orb', 0):.1f}"
            ])
        
        aspect_table = Table(aspect_data, colWidths=[6*cm, 4*cm, 2*cm])
        aspect_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLORS['light']]),
        ]))
        story.append(aspect_table)
    
    story.append(Spacer(1, 40))
    story.append(Paragraph('Сгенерировано на natalnayakarta.ru', small_style))
    
    doc.build(story)
    return str(filename)
