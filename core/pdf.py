"""Генерация PDF отчёта"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / 'reports'
FONT_PATH = BASE_DIR / 'DejaVuSans.ttf'

# Регистрация шрифта
try:
    pdfmetrics.registerFont(TTFont('DejaVu', str(FONT_PATH)))
except:
    pass


def generate_pdf(user_data):
    """Генерирует PDF отчёт по натальной карте"""
    name = user_data.get('name', 'Unknown')
    filename = REPORTS_DIR / f'report_{name}.pdf'
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    c = canvas.Canvas(str(filename), pagesize=A4)
    width, height = A4
    
    try:
        c.setFont('DejaVu', 16)
    except:
        c.setFont('Helvetica', 16)
    
    # Заголовок
    c.drawString(50, height - 50, f'Натальная карта: {name}')
    
    try:
        c.setFont('DejaVu', 10)
    except:
        c.setFont('Helvetica', 10)
    
    y = height - 80
    
    # Метаданные
    meta = user_data.get('meta', {})
    c.drawString(50, y, f"Город: {meta.get('city', 'N/A')}")
    y -= 15
    c.drawString(50, y, f"Дата: {meta.get('dt', 'N/A')}")
    y -= 30
    
    # Планеты
    c.drawString(50, y, 'ПЛАНЕТЫ:')
    y -= 20
    
    for planet in user_data.get('planets', [])[:10]:
        line = f"{planet.get('icon', '')} {planet.get('name', '')}: {planet.get('sign', '')} {planet.get('degree', 0):.1f}° (дом {planet.get('house', '')}"
        if planet.get('dignity'):
            line += f" - {planet.get('dignity')}"
        line += ')'
        
        c.drawString(50, y, line)
        y -= 15
        
        if y < 100:
            c.showPage()
            y = height - 50
    
    # Аспекты
    y -= 20
    c.drawString(50, y, 'АСПЕКТЫ:')
    y -= 20
    
    for aspect in user_data.get('aspects', [])[:15]:
        line = f"{aspect.get('p1', '')} - {aspect.get('p2', '')} ({aspect.get('name', '')})"
        c.drawString(50, y, line)
        y -= 15
        
        if y < 100:
            c.showPage()
            y = height - 50
    
    c.save()
    return str(filename)
