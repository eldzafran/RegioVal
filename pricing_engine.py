# pricing_engine.py
# RegioVal - Dynamic Regional Pricing Engine & Economic Visualizer

import urllib.request
import json

# Data Indikator Ekonomi Berdasarkan World Bank & IMF
ECONOMIC_DATA = {
    'IDR': {
        'name': 'Indonesia (Rupiah)',
        'symbol': 'Rp',
        'gdp_nominal': 5060,
        'gdp_ppp': 17720,
        'ppp_factor': 0.38,
        'inflation_rate': 0.025
    },
    'BRL': {
        'name': 'Brazil (Real)',
        'symbol': 'R$',
        'gdp_nominal': 9030,
        'gdp_ppp': 23360,
        'ppp_factor': 0.45,
        'inflation_rate': 0.040
    },
    'ARG': {
        'name': 'Argentina (Peso)',
        'symbol': '$',
        'gdp_nominal': 13500,
        'gdp_ppp': 31500,
        'ppp_factor': 0.30,
        'inflation_rate': 0.150
    },
    'EUR': {
        'name': 'Eurozone (Euro)',
        'symbol': '€',
        'gdp_nominal': 45000,
        'gdp_ppp': 62960,
        'ppp_factor': 0.95,
        'inflation_rate': 0.020
    }
}

FALLBACK_RATES = {
    'IDR': 15700.0,
    'BRL': 5.0,
    'ARG': 950.0,
    'EUR': 0.92
}

def fetch_live_exchange_rates():
    """Penarikan data kurs real-time via API open.er-api.com"""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('result') == 'success':
                return data.get('rates', FALLBACK_RATES)
    except Exception as e:
        print(f"[Warning] Gagal penarikan API: {e}. Menggunakan Fallback Rate.")
    return FALLBACK_RATES

def calculate_regional_price(base_price_usd, target_currency, rates=None):
    if target_currency not in ECONOMIC_DATA:
        return None

    if rates is None:
        rates = fetch_live_exchange_rates()

    exchange_rate = rates.get(target_currency, FALLBACK_RATES.get(target_currency, 1.0))
    data = ECONOMIC_DATA[target_currency]

    raw_converted_price = base_price_usd * exchange_rate
    adjusted_ppp = data['ppp_factor'] * (1 + (data['inflation_rate'] / 2))
    recommended_price = raw_converted_price * adjusted_ppp

    if target_currency == 'IDR':
        final_price = round(recommended_price, -3)
    else:
        final_price = round(recommended_price, 2)

    return {
        'currency': target_currency,
        'country_name': data['name'],
        'symbol': data['symbol'],
        'base_usd': base_price_usd,
        'exchange_rate': exchange_rate,
        'gdp_nominal': data['gdp_nominal'],
        'gdp_ppp': data['gdp_ppp'],
        'raw_converted': round(raw_converted_price, 2),
        'recommended_price': final_price,
        'discount_vs_raw_percent': round((1 - (recommended_price / raw_converted_price)) * 100, 1)
    }

def calculate_all_regional_prices(base_price_usd):
    rates = fetch_live_exchange_rates()
    results = []
    for currency in ECONOMIC_DATA:
        res = calculate_regional_price(base_price_usd, currency, rates)
        if res:
            results.append(res)
    return results

def generate_svg_chart(base_price_usd=59.99):
    """Menghasilkan Diagram Batang Visual dalam format SVG"""
    results = calculate_all_regional_prices(base_price_usd)
    
    svg = f'''
    <svg width="100%" height="260" viewBox="0 0 600 260" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a; border-radius:8px; padding:10px;">
        <text x="20" y="30" fill="#38bdf8" font-size="16" font-family="sans-serif" font-weight="bold">Diagram Perbandingan PPP Factor & Diskon Regional (Base: ${base_price_usd})</text>
    '''
    
    y = 60
    for res in results:
        ppp_pct = res['discount_vs_raw_percent']
        bar_width = int((100 - ppp_pct) * 3.5)  # Scale width
        
        svg += f'''
        <g transform="translate(0, {y})">
            <text x="20" y="18" fill="#f8fafc" font-size="13" font-family="sans-serif">{res['country_name']} ({res['currency']})</text>
            <rect x="220" y="4" width="350" height="20" rx="4" fill="#334155" />
            <rect x="220" y="4" width="{bar_width}" height="20" rx="4" fill="#0284c7" />
            <text x="{230 + bar_width}" y="19" fill="#38bdf8" font-size="12" font-family="sans-serif" font-weight="bold">Diskon: -{ppp_pct}%</text>
        </g>
        '''
        y += 45

    svg += '</svg>'
    return svg