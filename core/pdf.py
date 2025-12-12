"""Генерация красивого PDF отчёта натальной карты"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / 'reports'
FONT_PATH = BASE_DIR / 'DejaVuSans.ttf'

# Регистрация шрифта
try:
    pdfmetrics.registerFont(TTFont('DejaVu', str(FONT_PATH)))
    DEFAULT_FONT = 'DejaVu'
except:
    DEFAULT_FONT = 'Helvetica'


# Цвета для элементов
COLORS = {
    'primary': colors.HexColor('#1a1a2e'),
    'accent': colors.HexColor('#ffd700'),
    'text': colors.HexColor('#333333'),
    'light': colors.HexColor('#f5f5f5'),
    'fire': colors.HexColor('#ef5350'),
    'earth': colors.HexColor('#8bc34a'),
    'air': colors.HexColor('#ffee58'),
    'water': colors.HexColor('#4fc3f7'),
}

ELEMENT_SIGNS = {
    'Овен': 'fire', 'Лев': 'fire', 'Стрелец': 'fire',
    'Телец': 'earth', 'Дева': 'earth', 'Козерог': 'earth',
    'Близнецы': 'air', 'Весы': 'air', 'Водолей': 'air',
    'Рак': 'water', 'Скорпион': 'water', 'Рыбы': 'water',
}


def get_element_color(sign):
    element = ELEMENT_SIGNS.get(sign, 'earth')
    return COLORS.get(element, COLORS['light'])


def generate_pdf(user_data):
    """Генерирует красивый PDF отчёт по натальной карте"""
    name = user_data.get('name', 'Unknown')
    filename = REPORTS_DIR / f'report_{name}.pdf'
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # Кастомные стили
    styles.add(ParagraphStyle(
        name='Title',
        fontName=DEFAULT_FONT,
        fontSize=24,
        textColor=COLORS['primary'],
        spaceAfter=20,
        alignment=1  # Center
    ))
    
    styles.add(ParagraphStyle(
        name='Subtitle',
        fontName=DEFAULT_FONT,
        fontSize=14,
        textColor=colors.gray,
        spaceAfter=30,
        alignment=1
    ))
    
    styles.add(ParagraphStyle(
        name='Section',
        fontName=DEFAULT_FONT,
        fontSize=16,
        textColor=COLORS['primary'],
        spaceBefore=20,
        spaceAfter=10,
        borderColor=COLORS['accent'],
        borderWidth=2,
        borderPadding=5
    ))
    
    styles.add(ParagraphStyle(
        name='Normal',
        fontName=DEFAULT_FONT,
        fontSize=10,
        textColor=COLORS['text'],
        spaceAfter=8
    ))
    
    styles.add(ParagraphStyle(
        name='Small',
        fontName=DEFAULT_FONT,
        fontSize=9,
        textColor=colors.gray
    ))
    
    story = []
    
    # === ЗАГОЛОВОК ===
    story.append(Paragraph('🌌 НАТАЛЬНАЯ КАРТА', styles['Title']))
    
    meta = user_data.get('meta', {})
    story.append(Paragraph(
        f'{name}<br/>{meta.get("dt", "")} • {meta.get("city", "")}',
        styles['Subtitle']
    ))
    
    story.append(Spacer(1, 20))
    
    # === ТАБЛИЦА ПЛАНЕТ ===
    story.append(Paragraph('☉ ПОЛОЖЕНИЕ ПЛАНЕТ', styles['Section']))
    
    planets = user_data.get('planets', [])
    planet_data = [['Планета', 'Знак', 'Градус', 'Дом', 'Достоинство']]
    
    for p in planets[:13]:  # Основные планеты
        dignity = p.get('dignity', '—')
        planet_data.append([
            f"{p.get('icon', '')} {p.get('name', '')}",
            p.get('sign', ''),
            f"{p.get('degree', 0):.1f}°",
            str(p.get('house', '')),
            dignity if dignity else '—'
        ])
    
    planet_table = Table(planet_data, colWidths=[4*cm, 3*cm, 2*cm, 2*cm, 3*cm])
    planet_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLORS['light']]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(planet_table)
    
    story.append(Spacer(1, 20))
    
    # === АСПЕКТЫ ===
    aspects = user_data.get('aspects', [])
    if aspects:
        story.append(Paragraph('⭐ ОСНОВНЫЕ АСПЕКТЫ', styles['Section']))
        
        aspect_data = [['Аспект', 'Тип', 'Орбис']]
        for a in aspects[:20]:  # Топ 20 аспектов
            aspect_data.append([
                f"{a.get('p1', '')} — {a.get('p2', '')}",
                a.get('name', a.get('type', '')),
                f"{a.get('orb', 0):.1f}°"
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
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(aspect_table)
    
    story.append(Spacer(1, 30))
    
    # === ИНТЕРПРЕТАЦИИ ===
    story.append(Paragraph('📖 ИНТЕРПРЕТАЦИИ', styles['Section']))
    
    for p in planets[:10]:
        text = p.get('text', '').strip()
        if text and text not in ['Кармическая задача', 'Прошлый опыт', 'Теневая сторона', 'Ваше внешнее Я', 'Цель жизни']:
            story.append(Paragraph(
                f"<b>{p.get('icon', '')} {p.get('name', '')} в {p.get('sign', '')}</b>",
                styles['Normal']
            ))
            story.append(Paragraph(text[:500] + ('...' if len(text) > 500 else ''), styles['Small']))
            story.append(Spacer(1, 10))
    
    # === ФУТЕР ===
    story.append(Spacer(1, 40))
    story.append(Paragraph(
        '✨ Сгенерировано на natalnayakarta.ru',
        styles['Small']
    ))
    
    doc.build(story)
    return str(filename)
