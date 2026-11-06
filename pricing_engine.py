# pricing_engine.py
# RegioVal - Dynamic Regional Pricing Engine Core Logic

# Data indikator ekonomi (Simulasi/Mock data dari World Bank & IMF)
# Base reference: USD = 1.00
ECONOMIC_DATA = {
    'USD': {
        'name': 'Amerika Serikat (US Dollar)',
        'symbol': '$',
        'exchange_rate': 1.0,       # mata uang acuan
        'ppp_factor': 1.00,
        'inflation_rate': 0.03
    },
    'IDR': {
        'name': 'Indonesia (Rupiah)',
        'symbol': 'Rp',
        'exchange_rate': 15700.0,   # 1 USD = 15,700 IDR
        'ppp_factor': 0.38,         # Daya beli relatif ~38% dari AS
        'inflation_rate': 0.025
    },
    'BRL': {
        'name': 'Brazil (Real)',
        'symbol': 'R$',
        'exchange_rate': 5.0,
        'ppp_factor': 0.45,
        'inflation_rate': 0.04
    },
    'ARS': {                        # sebelumnya 'ARG' -> kode ISO mata uang = ARS
        'name': 'Argentina (Peso)',
        'symbol': 'AR$',            # sebelumnya '$' (bentrok dengan USD)
        'exchange_rate': 950.0,     # TODO: cek ulang sesuai tahun data
        'ppp_factor': 0.30,
        'inflation_rate': 0.15      # TODO: inflasi aktual Argentina jauh lebih tinggi
    },
    'EUR': {
        'name': 'Eurozone (Euro)',
        'symbol': '€',
        'exchange_rate': 0.92,
        'ppp_factor': 0.95,
        'inflation_rate': 0.02
    },
    'JPY': {
        'name': 'Jepang (Yen)',
        'symbol': '¥',
        'exchange_rate': 150.0,
        'ppp_factor': 0.60,
        'inflation_rate': 0.02
    },
    'GBP': {
        'name': 'Inggris (Pound Sterling)',
        'symbol': '£',
        'exchange_rate': 0.79,
        'ppp_factor': 0.85,
        'inflation_rate': 0.03
    },
    'CNY': {
        'name': 'Tiongkok (Yuan)',
        'symbol': '¥',
        'exchange_rate': 7.2,
        'ppp_factor': 0.55,
        'inflation_rate': 0.01
    },
    'INR': {
        'name': 'India (Rupee)',
        'symbol': '₹',
        'exchange_rate': 83.0,
        'ppp_factor': 0.25,
        'inflation_rate': 0.05
    },
    'KRW': {
        'name': 'Korea Selatan (Won)',
        'symbol': '₩',
        'exchange_rate': 1350.0,
        'ppp_factor': 0.70,
        'inflation_rate': 0.025
    },
    'AUD': {
        'name': 'Australia (Dollar Australia)',
        'symbol': 'A$',
        'exchange_rate': 1.52,
        'ppp_factor': 0.85,
        'inflation_rate': 0.035
    },
    'SGD': {
        'name': 'Singapura (Dollar Singapura)',
        'symbol': 'S$',
        'exchange_rate': 1.35,
        'ppp_factor': 0.85,
        'inflation_rate': 0.03
    },
    'MYR': {
        'name': 'Malaysia (Ringgit)',
        'symbol': 'RM',
        'exchange_rate': 4.7,
        'ppp_factor': 0.40,
        'inflation_rate': 0.02
    },
    'THB': {
        'name': 'Thailand (Baht)',
        'symbol': '฿',
        'exchange_rate': 35.5,
        'ppp_factor': 0.40,
        'inflation_rate': 0.01
    },
    'VND': {
        'name': 'Vietnam (Dong)',
        'symbol': '₫',
        'exchange_rate': 24500.0,
        'ppp_factor': 0.30,
        'inflation_rate': 0.035
    },
    'PHP': {
        'name': 'Filipina (Peso)',
        'symbol': '₱',
        'exchange_rate': 56.0,
        'ppp_factor': 0.40,
        'inflation_rate': 0.04
    },
    'MXN': {
        'name': 'Meksiko (Peso)',
        'symbol': 'MX$',
        'exchange_rate': 17.2,
        'ppp_factor': 0.50,
        'inflation_rate': 0.045
    },
    'ZAR': {
        'name': 'Afrika Selatan (Rand)',
        'symbol': 'R',
        'exchange_rate': 18.5,
        'ppp_factor': 0.40,
        'inflation_rate': 0.05
    },
    'TRY': {
        'name': 'Turki (Lira)',
        'symbol': '₺',
        'exchange_rate': 32.0,
        'ppp_factor': 0.30,
        'inflation_rate': 0.45      # inflasi tinggi
    },
    'NGN': {
        'name': 'Nigeria (Naira)',
        'symbol': '₦',
        'exchange_rate': 1500.0,
        'ppp_factor': 0.35,
        'inflation_rate': 0.25      # inflasi tinggi
    },
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