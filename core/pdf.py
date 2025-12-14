"""Генерация PDF отчёта натальной карты — улучшенная версия"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / 'reports'
FONT_PATH = BASE_DIR / 'DejaVuSans.ttf'

try:
    pdfmetrics.registerFont(TTFont('DejaVu', str(FONT_PATH)))
    DEFAULT_FONT = 'DejaVu'
except:
    DEFAULT_FONT = 'Helvetica'

# Цветовая схема
COLORS = {
    'primary': colors.HexColor('#1a1a2e'),
    'accent': colors.HexColor('#bf5af2'),
    'accent_light': colors.HexColor('#e8d5f5'),
    'text': colors.HexColor('#2c2c2c'),
    'text_light': colors.HexColor('#666666'),
    'bg_light': colors.HexColor('#f8f8fa'),
    'white': colors.white,
    'sun': colors.HexColor('#ffd700'),
    'moon': colors.HexColor('#c0c0c0'),
}


def generate_pdf(user_data):
    """Генерирует красивый PDF отчёт"""
    name = user_data.get('name', 'Unknown')
    safe_name = ''.join(c for c in name if c.isalnum() or c in ' _-')[:50]
    filename = REPORTS_DIR / f'report_{safe_name}.pdf'
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(filename), pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=2*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    
    # Стили
    cover_title = ParagraphStyle('CoverTitle',
        fontName=DEFAULT_FONT, fontSize=32, textColor=COLORS['primary'],
        alignment=1, spaceAfter=10, leading=38)
    
    cover_subtitle = ParagraphStyle('CoverSubtitle',
        fontName=DEFAULT_FONT, fontSize=14, textColor=COLORS['text_light'],
        alignment=1, spaceAfter=40)
    
    section_title = ParagraphStyle('SectionTitle',
        fontName=DEFAULT_FONT, fontSize=18, textColor=COLORS['primary'],
        spaceBefore=25, spaceAfter=15, borderPadding=5)
    
    subsection = ParagraphStyle('Subsection',
        fontName=DEFAULT_FONT, fontSize=13, textColor=COLORS['accent'],
        spaceBefore=15, spaceAfter=8)
    
    body_text = ParagraphStyle('BodyText',
        fontName=DEFAULT_FONT, fontSize=10, textColor=COLORS['text'],
        spaceAfter=8, leading=14)
    
    planet_header = ParagraphStyle('PlanetHeader',
        fontName=DEFAULT_FONT, fontSize=12, textColor=COLORS['primary'],
        spaceBefore=12, spaceAfter=4)
    
    interpretation = ParagraphStyle('Interpretation',
        fontName=DEFAULT_FONT, fontSize=10, textColor=COLORS['text_light'],
        spaceAfter=10, leading=14, leftIndent=10, rightIndent=10,
        backColor=COLORS['bg_light'], borderPadding=8)
    
    footer_style = ParagraphStyle('Footer',
        fontName=DEFAULT_FONT, fontSize=8, textColor=COLORS['text_light'],
        alignment=1)
    
    story = []
    
    # ========== ОБЛОЖКА ==========
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph('✧ АСТРОЛОГИЧЕСКИЙ ОТЧЁТ ✧', cover_title))
    story.append(Spacer(1, 0.5*cm))
    
    meta = user_data.get('meta', {})
    cover_info = f'''
        <b>{name}</b><br/><br/>
        Дата рождения: {meta.get('dt', 'Не указано')}<br/>
        Место: {meta.get('city', 'Не указано')}<br/><br/>
        <i>Персональный натальный анализ</i>
    '''
    story.append(Paragraph(cover_info, cover_subtitle))
    
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph('🌟', ParagraphStyle('Icon', fontSize=60, alignment=1)))
    
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph(f'Создано: {datetime.now().strftime("%d.%m.%Y")}<br/>transitsonline.ru', footer_style))
    story.append(PageBreak())
    
    # ========== ОГЛАВЛЕНИЕ ==========
    story.append(Paragraph('СОДЕРЖАНИЕ', section_title))
    story.append(Spacer(1, 0.5*cm))
    
    toc_items = [
        '1. Положение планет в знаках',
        '2. Планеты в домах',
        '3. Аспекты между планетами',
        '4. Интерпретации',
    ]
    for item in toc_items:
        story.append(Paragraph(item, body_text))
    
    story.append(PageBreak())
    
    # ========== ПЛАНЕТЫ ==========
    story.append(Paragraph('1. ПОЛОЖЕНИЕ ПЛАНЕТ', section_title))
    
    planets = user_data.get('planets', [])
    
    # Таблица планет
    planet_data = [['', 'Планета', 'Знак', 'Градус', 'Дом', 'Достоинство']]
    for p in planets[:14]:
        retro = ' R' if p.get('retrograde') or p.get('is_retro') else ''
        planet_data.append([
            p.get('icon', ''),
            p.get('name', '') + retro,
            p.get('sign', ''),
            f"{p.get('degree', 0):.1f}°",
            str(p.get('house', '')),
            p.get('dignity', '—') or '—'
        ])
    
    planet_table = Table(planet_data, colWidths=[0.8*cm, 3.5*cm, 2.5*cm, 2*cm, 1.5*cm, 3*cm])
    planet_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['white'], COLORS['bg_light']]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(planet_table)
    story.append(Spacer(1, 1*cm))
    
    # ========== АСПЕКТЫ ==========
    aspects = user_data.get('aspects', [])
    if aspects:
        story.append(Paragraph('2. АСПЕКТЫ', section_title))
        
        aspect_colors = {
            'Соединение': '#4fc3f7',
            'Conjunction': '#4fc3f7',
            'Секстиль': '#8bc34a',
            'Sextile': '#8bc34a',
            'Тригон': '#4caf50',
            'Trine': '#4caf50',
            'Квадрат': '#ff5722',
            'Square': '#ff5722',
            'Оппозиция': '#f44336',
            'Opposition': '#f44336',
        }
        
        aspect_data = [['Планета 1', 'Аспект', 'Планета 2', 'Орбис']]
        for a in aspects[:20]:
            aspect_data.append([
                a.get('p1', ''),
                a.get('name', a.get('type', '')),
                a.get('p2', ''),
                f"{a.get('orb', 0):.1f}°"
            ])
        
        aspect_table = Table(aspect_data, colWidths=[4*cm, 3.5*cm, 4*cm, 2*cm])
        aspect_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['accent']),
            ('TEXTCOLOR', (0, 0), (-1, 0), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLORS['white'], COLORS['bg_light']]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(aspect_table)
    
    story.append(PageBreak())
    
    # ========== ИНТЕРПРЕТАЦИИ ==========
    story.append(Paragraph('3. ИНТЕРПРЕТАЦИИ', section_title))
    story.append(Paragraph('Расшифровка положений планет в вашей карте:', body_text))
    story.append(Spacer(1, 0.5*cm))
    
    for p in planets[:10]:
        if p.get('text'):
            header = f"{p.get('icon', '')} {p.get('name', '')} в {p.get('sign', '')}, {p.get('house', '')} дом"
            story.append(Paragraph(header, planet_header))
            
            # Разбиваем текст на части если он слишком длинный
            text = p.get('text', '')[:600]
            if len(p.get('text', '')) > 600:
                text += '...'
            story.append(Paragraph(text, interpretation))
    
    # Интерпретации аспектов
    if aspects:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph('Значение аспектов:', subsection))
        
        for a in aspects[:8]:
            if a.get('text'):
                header = f"{a.get('p1', '')} {a.get('name', '')} {a.get('p2', '')}"
                story.append(Paragraph(header, planet_header))
                story.append(Paragraph(a.get('text', '')[:400], interpretation))
    
    # ========== ФИНАЛ ==========
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph('—' * 40, footer_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('''
        Этот отчёт создан автоматически на основе астрологических расчётов.<br/>
        Для более глубокого анализа рекомендуется консультация профессионального астролога.<br/><br/>
        <b>transitsonline.ru</b> — Ваш персональный астрологический помощник
    ''', footer_style))
    
    doc.build(story)
    return str(filename)
