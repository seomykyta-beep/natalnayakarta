"""Расчёт лунного возвращения (лунара)"""
from datetime import datetime, timedelta
import pytz


def find_lunar_return(natal_moon_pos, target_year, target_month, latitude, longitude, tz_str):
    """Находит момент лунного возвращения"""
    from .calculator import build_chart, ts, earth, moon
    
    tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
    
    # Начинаем поиск с начала месяца
    search_start = datetime(target_year, target_month, 1, 0, 0)
    search_start = tz.localize(search_start)
    
    # Ищем в течение месяца
    current = search_start
    step = timedelta(hours=6)
    
    for _ in range(30):
        utc_dt = current.astimezone(pytz.UTC)
        t = ts.utc(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute)
        
        astrometric = earth.at(t).observe(moon)
        apparent = astrometric.apparent()
        _, lon_ecl, _ = apparent.ecliptic_latlon()
        current_moon_pos = lon_ecl.degrees % 360
        
        diff = (current_moon_pos - natal_moon_pos + 180) % 360 - 180
        
        if abs(diff) < 0.01:
            break
        
        if diff > 0:
            current -= step
        else:
            current += step
        
        step /= 2
    
    # Строим карту для момента лунара
    chart = build_chart(current, latitude, longitude, 'Lunar Return')
    
    return {
        'datetime': current.strftime('%d.%m.%Y %H:%M'),
        'planets': chart['planets'],
        'houses': chart['houses'],
        'aspects': chart['aspects']
    }
