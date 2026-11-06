# pricing_engine.py
# RegioVal - Dynamic Regional Pricing Engine Core Logic

# Data indikator ekonomi (Simulasi/Mock data dari World Bank & IMF)
# Base reference: USD = 1.00
ECONOMIC_DATA = {
    'IDR': {
        'name': 'Indonesia (Rupiah)',
        'symbol': 'Rp',
        'exchange_rate': 15700.0,  # 1 USD = 15,700 IDR
        'ppp_factor': 0.38,         # Daya beli relatif ~38% dari AS
        'inflation_rate': 0.025     # Inflasi 2.5%
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
        'inflation_rate': 0.15      # Penyesuaian inflasi tinggi
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
    """
    Menghitung rekomendasi harga regional berbasis PPP dan inflasi.
    """
    if target_currency not in ECONOMIC_DATA:
        return None

    data = ECONOMIC_DATA[target_currency]
    
    # 1. Direct Conversion (Harga mentah tanpa penyesuaian daya beli)
    raw_converted_price = base_price_usd * data['exchange_rate']
    
    # 2. Formula RegioVal: Penyesuaian PPP & Inflasi
    # Mengalikan dengan ppp_factor agar harga sesuai daya beli lokal,
    # lalu disesuaikan sedikit dengan tingkat inflasi.
    adjusted_ppp = data['ppp_factor'] * (1 + (data['inflation_rate'] / 2))
    recommended_price = raw_converted_price * adjusted_ppp

    # 3. Pembulatan psikologis harga lokal (misal diakhiri dengan .000 atau .99)
    if target_currency == 'IDR':
        # Pembulatan ke ribuan terdekat (contoh: 249,000)
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

# Quick Test jika file dijalankan langsung
if __name__ == '__main__':
    res = calculate_regional_price(60.0, 'IDR')
    print("--- Testing Engine RegioVal ---")
    print(f"Base Price (USD): ${res['base_usd']}")
    print(f"Harga Konversi Mentah (IDR): {res['symbol']} {res['raw_converted']:,}")
    print(f"Rekomendasi Harga RegioVal (IDR): {res['symbol']} {res['recommended_price']:,}")
    print(f"Penyesuaian Daya Beli: {res['discount_vs_raw_percent']}% lebih terjangkau dari konversi mentah.")