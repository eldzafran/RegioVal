# pricing_engine.py
# RegioVal - Dynamic Regional Pricing Engine Core Logic

ECONOMIC_DATA = {
    'IDR': {
        'name': 'Indonesia (Rupiah)',
        'symbol': 'Rp',
        'exchange_rate': 15700.0,
        'ppp_factor': 0.38,
        'inflation_rate': 0.025
    },
    'BRL': {
        'name': 'Brazil (Real)',
        'symbol': 'R$',
        'exchange_rate': 5.0,
        'ppp_factor': 0.45,
        'inflation_rate': 0.04
    },
    'ARG': {
        'name': 'Argentina (Peso)',
        'symbol': '$',
        'exchange_rate': 950.0,
        'ppp_factor': 0.30,
        'inflation_rate': 0.15
    },
    'EUR': {
        'name': 'Eurozone (Euro)',
        'symbol': '€',
        'exchange_rate': 0.92,
        'ppp_factor': 0.95,
        'inflation_rate': 0.02
    }
}

def calculate_regional_price(base_price_usd, target_currency):
    if target_currency not in ECONOMIC_DATA:
        return None

    data = ECONOMIC_DATA[target_currency]
    raw_converted_price = base_price_usd * data['exchange_rate']
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
        'raw_converted': round(raw_converted_price, 2),
        'recommended_price': final_price,
        'discount_vs_raw_percent': round((1 - (recommended_price / raw_converted_price)) * 100, 1)
    }

def calculate_all_regional_prices(base_price_usd):
    results = []
    for currency in ECONOMIC_DATA:
        res = calculate_regional_price(base_price_usd, currency)
        if res:
            results.append(res)
    return results