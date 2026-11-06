# pricing_engine.py
# RegioVal - Dynamic Regional Pricing Engine Core Logic

import urllib.request
import json

# Data acuan PPP dan Inflasi (Indikator World Bank/IMF)
COUNTRY_INDICATORS = {
    'IDR': {
        'name': 'Indonesia (Rupiah)',
        'symbol': 'Rp',
        'ppp_factor': 0.38,         # Purchasing Power Parity relatif terhadap USD
        'inflation_rate': 0.025     # Inflasi 2.5%
    },
    'BRL': {
        'name': 'Brazil (Real)',
        'symbol': 'R$',
        'ppp_factor': 0.45,
        'inflation_rate': 0.040
    },
    'ARG': {
        'name': 'Argentina (Peso)',
        'symbol': '$',
        'ppp_factor': 0.30,
        'inflation_rate': 0.150
    },
    'EUR': {
        'name': 'Eurozone (Euro)',
        'symbol': '€',
        'ppp_factor': 0.95,
        'inflation_rate': 0.020
    }
}

# Fallback nilai tukar statis jika koneksi internet/API terganggu (Fault Tolerance)
FALLBACK_RATES = {
    'IDR': 15700.0,
    'BRL': 5.0,
    'ARG': 950.0,
    'EUR': 0.92
}

def fetch_live_exchange_rates():
    """Mengambil data kurs mata uang terbaru real-time berbasis USD dari API open.er-api.com"""
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('result') == 'success':
                return data.get('rates', FALLBACK_RATES)
    except Exception as e:
        print(f"[Warning] Gagal mengambil Live API Rate ({e}). Menggunakan Fallback Rate.")
    return FALLBACK_RATES

def calculate_regional_price(base_price_usd, target_currency, rates=None):
    if target_currency not in COUNTRY_INDICATORS:
        return None

    if rates is None:
        rates = fetch_live_exchange_rates()

    exchange_rate = rates.get(target_currency, FALLBACK_RATES.get(target_currency, 1.0))
    indicator = COUNTRY_INDICATORS[target_currency]

    # 1. Konversi Mentah
    raw_converted_price = base_price_usd * exchange_rate
    
    # 2. Formula RegioVal (Penyesuaian PPP & Inflasi)
    adjusted_ppp = indicator['ppp_factor'] * (1 + (indicator['inflation_rate'] / 2))
    recommended_price = raw_converted_price * adjusted_ppp

    # 3. Pembulatan Psikologis
    if target_currency == 'IDR':
        final_price = round(recommended_price, -3)
    else:
        final_price = round(recommended_price, 2)

    return {
        'currency': target_currency,
        'country_name': indicator['name'],
        'symbol': indicator['symbol'],
        'base_usd': base_price_usd,
        'exchange_rate': exchange_rate,
        'raw_converted': round(raw_converted_price, 2),
        'recommended_price': final_price,
        'discount_vs_raw_percent': round((1 - (recommended_price / raw_converted_price)) * 100, 1)
    }

def calculate_all_regional_prices(base_price_usd):
    rates = fetch_live_exchange_rates()
    results = []
    for currency in COUNTRY_INDICATORS:
        res = calculate_regional_price(base_price_usd, currency, rates)
        if res:
            results.append(res)
    return results