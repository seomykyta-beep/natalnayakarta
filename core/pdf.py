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
            header = f"{p.get('icon', '')} {p.get('name', '')} в {p.get('sign_locative', p.get('sign', ''))}, {p.get('house', '')} дом"
            story.append(Paragraph(header, planet_header))
            
            # Разбиваем текст на части если он слишком длинный
            text = p.get('text', '')[:5000]
            if len(p.get('text', '')) > 5000:
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
                story.append(Paragraph(a.get('text', '')[:5000], interpretation))
    
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


def generate_pdf_by_mode(user_data, mode='full'):
    """Генерирует PDF для конкретного режима"""
    if mode == 'full':
        return generate_pdf(user_data)
    
    name = user_data.get('name', 'Unknown')
    safe_name = ''.join(c for c in name if c.isalnum() or c in ' _-')[:50]
    filename = REPORTS_DIR / f'report_{safe_name}_{mode}.pdf'
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    doc = SimpleDocTemplate(str(filename), pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=2*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    
    # Стили
    title_style = ParagraphStyle('Title',
        fontName=DEFAULT_FONT, fontSize=24, textColor=COLORS['primary'],
        alignment=1, spaceAfter=20)
    
    section_title = ParagraphStyle('SectionTitle',
        fontName=DEFAULT_FONT, fontSize=16, textColor=COLORS['primary'],
        spaceBefore=20, spaceAfter=12)
    
    body_text = ParagraphStyle('BodyText',
        fontName=DEFAULT_FONT, fontSize=10, textColor=COLORS['text'],
        spaceAfter=8, leading=14)
    
    planet_header = ParagraphStyle('PlanetHeader',
        fontName=DEFAULT_FONT, fontSize=11, textColor=COLORS['primary'],
        spaceBefore=10, spaceAfter=4)
    
    interpretation = ParagraphStyle('Interpretation',
        fontName=DEFAULT_FONT, fontSize=9, textColor=COLORS['text_light'],
        spaceAfter=8, leading=13, leftIndent=8, rightIndent=8,
        backColor=COLORS['bg_light'], borderPadding=6)
    
    footer_style = ParagraphStyle('Footer',
        fontName=DEFAULT_FONT, fontSize=8, textColor=COLORS['text_light'], alignment=1)
    
    story = []
    meta = user_data.get('meta', {})
    
    mode_titles = {
        'natal': '🌟 НАТАЛЬНАЯ КАРТА',
        'transit': '✨ ТРАНЗИТЫ',
        'solar': '☀️ СОЛЯР',
        'lunar': '🌙 ЛУНАР',
        'synastry': '💕 СИНАСТРИЯ'
    }
    
    # Заголовок
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(mode_titles.get(mode, 'Отчёт'), title_style))
    story.append(Paragraph(f'<b>{name}</b> • {meta.get("dt", "")}', body_text))
    story.append(Spacer(1, 0.5*cm))
    
    planets = user_data.get('planets', [])
    
    if mode == 'natal':
        # Натальная карта
        story.append(Paragraph('Положение планет', section_title))
        for p in planets:
            if p.get('text') and p.get('key') not in ['ASC', 'MC']:
                header = f"{p.get('icon', '')} {p.get('name', '')} в {p.get('sign_locative', p.get('sign', ''))}, {p.get('house', '')} дом"
                story.append(Paragraph(header, planet_header))
                text = p.get('text', '')[:5000]
                story.append(Paragraph(text, interpretation))
        
        # Натальные аспекты
        aspects = user_data.get('aspects', [])
        if aspects:
            story.append(Paragraph('Аспекты', section_title))
            for a in aspects[:12]:
                if a.get('text'):
                    story.append(Paragraph(f"{a.get('p1')} {a.get('name', '')} {a.get('p2')}", planet_header))
                    story.append(Paragraph(a.get('text', '')[:300], interpretation))
    
    elif mode == 'transit':
        # Транзиты
        transit_planets = user_data.get('transit_planets', [])
        transit_aspects = user_data.get('transit_aspects', [])
        
        story.append(Paragraph(f'Транзиты на {meta.get("transit_dt", "")}', section_title))
        
        if transit_planets:
            story.append(Paragraph('Положение транзитных планет:', body_text))
            for tp in transit_planets[:10]:
                house_info = f" ({tp.get('natal_house', '')} дом)" if tp.get('natal_house') else ""
                story.append(Paragraph(f"{tp.get('icon', '')} {tp.get('name', '')}: {tp.get('sign', '')} {tp.get('degree', 0):.0f}°{house_info}", body_text))
        
        if transit_aspects:
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph('Транзитные аспекты:', section_title))
            for a in transit_aspects[:15]:
                text = a.get('text', '')
                if text:
                    story.append(Paragraph(f"тр.{a.get('p2', '')} → нат.{a.get('p1', '')} ({a.get('name', '')})", planet_header))
                    story.append(Paragraph(text[:300], interpretation))
    
    elif mode == 'solar':
        # Соляр
        solar = user_data.get('solar', {})
        if solar:
            story.append(Paragraph(f"Соляр на {solar.get('date', '')}", section_title))
            story.append(Paragraph(f"Место: {solar.get('city', 'город рождения')}", body_text))
            
            solar_planets = solar.get('planets', [])
            for sp in solar_planets[:10]:
                story.append(Paragraph(f"{sp.get('icon', '')} {sp.get('name', '')}: {sp.get('sign', '')} {sp.get('degree', 0):.0f}°", body_text))
            
            solar_aspects = solar.get('aspects', [])
            if solar_aspects:
                story.append(Paragraph('Аспекты соляр → натал:', section_title))
                for a in solar_aspects[:12]:
                    if a.get('text'):
                        story.append(Paragraph(f"сол.{a.get('p2', '')} → нат.{a.get('p1', '')} ({a.get('name', '')})", planet_header))
                        story.append(Paragraph(a.get('text', '')[:300], interpretation))
    
    elif mode == 'lunar':
        # Лунар
        lunar = user_data.get('lunar', {})
        if lunar:
            story.append(Paragraph(f"Лунар на {lunar.get('date', '')}", section_title))
            
            lunar_planets = lunar.get('planets', [])
            for lp in lunar_planets[:10]:
                story.append(Paragraph(f"{lp.get('icon', '')} {lp.get('name', '')}: {lp.get('sign', '')} {lp.get('degree', 0):.0f}°", body_text))
            
            lunar_aspects = lunar.get('aspects', [])
            if lunar_aspects:
                story.append(Paragraph('Аспекты лунар → натал:', section_title))
                for a in lunar_aspects[:12]:
                    if a.get('text'):
                        story.append(Paragraph(f"лун.{a.get('p2', '')} → нат.{a.get('p1', '')} ({a.get('name', '')})", planet_header))
                        story.append(Paragraph(a.get('text', '')[:300], interpretation))
    
    elif mode == 'synastry':
        # Синастрия
        synastry = user_data.get('synastry', {})
        if synastry:
            story.append(Paragraph(f"Совместимость: {synastry.get('score', 0)}%", section_title))
            story.append(Paragraph(f"Уровень: {synastry.get('level', '')}", body_text))
            story.append(Paragraph(synastry.get('description', ''), interpretation))
            
            syn_aspects = synastry.get('aspects', [])
            if syn_aspects:
                story.append(Spacer(1, 0.5*cm))
                story.append(Paragraph('Ключевые аспекты:', section_title))
                for a in syn_aspects[:10]:
                    aspect_type = '✓' if a.get('is_positive') else '✗'
                    story.append(Paragraph(f"{aspect_type} {a.get('p1', '')} — {a.get('p2', '')} ({a.get('aspect', '')})", planet_header))
                    if a.get('text'):
                        story.append(Paragraph(a.get('text', '')[:250], interpretation))
    
    # Футер
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph('transitsonline.ru', footer_style))
    
    doc.build(story)
    return str(filename)
