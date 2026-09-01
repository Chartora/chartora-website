#!/usr/bin/env python3
"""
CHARTORA — Canonical Symbol Registry & Multi-Asset Universe
Manages normalized instrument definitions across:
- Forex (Majors, Minors, Crosses)
- Metals (Gold, Silver, Platinum, Palladium)
- Indices (US500, US100, US30, GER40, UK100, JP225)
- Commodities (Crude Oil, Brent, Natural Gas)
- Crypto (Bitcoin, Ethereum, Solana, Ripple)
- Equities & ETFs (Apple, Microsoft, Nvidia, Tesla, S&P 500 ETF)
"""

from typing import Dict, Any, List, Optional

CANONICAL_MARKET_REGISTRY: Dict[str, Dict[str, Any]] = {
    # 1. METALS
    "XAUUSD": {
        "canonical_symbol": "XAUUSD",
        "display_name": "Gold / US Dollar",
        "category": "Metals",
        "base_currency": "XAU",
        "quote_currency": "USD",
        "pip_size": 0.01,
        "pip_value": 1.0,
        "default_spread": 0.20,
        "digits": 2,
        "trading_hours": "Sun 23:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["XAUUSD", "XAUUSDm", "GOLD", "XAUUSD.raw"],
            "twelvedata": "XAU/USD",
            "finnhub": "OANDA:XAU_USD",
            "polygon": "C:XAUUSD"
        }
    },
    "XAGUSD": {
        "canonical_symbol": "XAGUSD",
        "display_name": "Silver / US Dollar",
        "category": "Metals",
        "base_currency": "XAG",
        "quote_currency": "USD",
        "pip_size": 0.001,
        "pip_value": 5.0,
        "default_spread": 0.02,
        "digits": 3,
        "trading_hours": "Sun 23:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["XAGUSD", "XAGUSDm", "SILVER"],
            "twelvedata": "XAG/USD",
            "finnhub": "OANDA:XAG_USD",
            "polygon": "C:XAGUSD"
        }
    },
    "XPTUSD": {
        "canonical_symbol": "XPTUSD",
        "display_name": "Platinum / US Dollar",
        "category": "Metals",
        "base_currency": "XPT",
        "quote_currency": "USD",
        "pip_size": 0.01,
        "pip_value": 1.0,
        "default_spread": 1.50,
        "digits": 2,
        "trading_hours": "Sun 23:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["XPTUSD", "PLATINUM"],
            "twelvedata": "XPT/USD",
            "finnhub": "OANDA:XPT_USD"
        }
    },

    # 2. FOREX MAJORS & CROSSES
    "EURUSD": {
        "canonical_symbol": "EURUSD",
        "display_name": "Euro / US Dollar",
        "category": "Forex",
        "base_currency": "EUR",
        "quote_currency": "USD",
        "pip_size": 0.0001,
        "pip_value": 10.0,
        "default_spread": 0.00012,
        "digits": 5,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["EURUSD", "EURUSDm", "EURUSD.raw"],
            "twelvedata": "EUR/USD",
            "finnhub": "OANDA:EUR_USD",
            "polygon": "C:EURUSD"
        }
    },
    "GBPUSD": {
        "canonical_symbol": "GBPUSD",
        "display_name": "British Pound / US Dollar",
        "category": "Forex",
        "base_currency": "GBP",
        "quote_currency": "USD",
        "pip_size": 0.0001,
        "pip_value": 10.0,
        "default_spread": 0.00015,
        "digits": 5,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["GBPUSD", "GBPUSDm", "GBPUSD.raw"],
            "twelvedata": "GBP/USD",
            "finnhub": "OANDA:GBP_USD",
            "polygon": "C:GBPUSD"
        }
    },
    "USDJPY": {
        "canonical_symbol": "USDJPY",
        "display_name": "US Dollar / Japanese Yen",
        "category": "Forex",
        "base_currency": "USD",
        "quote_currency": "JPY",
        "pip_size": 0.01,
        "pip_value": 6.80,
        "default_spread": 0.014,
        "digits": 3,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["USDJPY", "USDJPYm", "USDJPY.raw"],
            "twelvedata": "USD/JPY",
            "finnhub": "OANDA:USD_JPY",
            "polygon": "C:USDJPY"
        }
    },
    "USDCHF": {
        "canonical_symbol": "USDCHF",
        "display_name": "US Dollar / Swiss Franc",
        "category": "Forex",
        "base_currency": "USD",
        "quote_currency": "CHF",
        "pip_size": 0.0001,
        "pip_value": 11.20,
        "default_spread": 0.00018,
        "digits": 5,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["USDCHF", "USDCHFm"],
            "twelvedata": "USD/CHF",
            "finnhub": "OANDA:USD_CHF"
        }
    },
    "AUDUSD": {
        "canonical_symbol": "AUDUSD",
        "display_name": "Australian Dollar / US Dollar",
        "category": "Forex",
        "base_currency": "AUD",
        "quote_currency": "USD",
        "pip_size": 0.0001,
        "pip_value": 10.0,
        "default_spread": 0.00014,
        "digits": 5,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["AUDUSD", "AUDUSDm"],
            "twelvedata": "AUD/USD",
            "finnhub": "OANDA:AUD_USD"
        }
    },
    "USDCAD": {
        "canonical_symbol": "USDCAD",
        "display_name": "US Dollar / Canadian Dollar",
        "category": "Forex",
        "base_currency": "USD",
        "quote_currency": "CAD",
        "pip_size": 0.0001,
        "pip_value": 7.40,
        "default_spread": 0.00016,
        "digits": 5,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["USDCAD", "USDCADm"],
            "twelvedata": "USD/CAD",
            "finnhub": "OANDA:USD_CAD"
        }
    },
    "EURJPY": {
        "canonical_symbol": "EURJPY",
        "display_name": "Euro / Japanese Yen",
        "category": "Forex",
        "base_currency": "EUR",
        "quote_currency": "JPY",
        "pip_size": 0.01,
        "pip_value": 6.80,
        "default_spread": 0.018,
        "digits": 3,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["EURJPY", "EURJPYm"],
            "twelvedata": "EUR/JPY",
            "finnhub": "OANDA:EUR_JPY"
        }
    },
    "GBPJPY": {
        "canonical_symbol": "GBPJPY",
        "display_name": "British Pound / Japanese Yen",
        "category": "Forex",
        "base_currency": "GBP",
        "quote_currency": "JPY",
        "pip_size": 0.01,
        "pip_value": 6.80,
        "default_spread": 0.022,
        "digits": 3,
        "trading_hours": "Sun 22:00 - Fri 22:00 UTC",
        "provider_mappings": {
            "mt5": ["GBPJPY", "GBPJPYm"],
            "twelvedata": "GBP/JPY",
            "finnhub": "OANDA:GBP_JPY"
        }
    },

    # 3. INDICES
    "US500": {
        "canonical_symbol": "US500",
        "display_name": "S&P 500 Index",
        "category": "Indices",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 0.10,
        "pip_value": 1.0,
        "default_spread": 0.40,
        "digits": 2,
        "trading_hours": "Mon-Fri 00:00 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["US500", "SPX500", "US500m", "SP500"],
            "twelvedata": "SPX",
            "finnhub": "^GSPC",
            "polygon": "I:SPX"
        }
    },
    "US100": {
        "canonical_symbol": "US100",
        "display_name": "Nasdaq 100 Index",
        "category": "Indices",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 0.10,
        "pip_value": 1.0,
        "default_spread": 1.20,
        "digits": 2,
        "trading_hours": "Mon-Fri 00:00 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["US100", "NAS100", "USTEC", "US100m"],
            "twelvedata": "NDX",
            "finnhub": "^NDX",
            "polygon": "I:NDX"
        }
    },
    "US30": {
        "canonical_symbol": "US30",
        "display_name": "Dow Jones 30 Index",
        "category": "Indices",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 1.0,
        "pip_value": 1.0,
        "default_spread": 2.50,
        "digits": 1,
        "trading_hours": "Mon-Fri 00:00 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["US30", "DJ30", "US30m", "WALLSTREET"],
            "twelvedata": "DJI",
            "finnhub": "^DJI"
        }
    },
    "GER40": {
        "canonical_symbol": "GER40",
        "display_name": "Germany DAX 40",
        "category": "Indices",
        "base_currency": "EUR",
        "quote_currency": "EUR",
        "pip_size": 1.0,
        "pip_value": 1.0,
        "default_spread": 1.50,
        "digits": 1,
        "trading_hours": "Mon-Fri 07:00 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["GER40", "DAX40", "GERMANY40"],
            "twelvedata": "GDAXI",
            "finnhub": "^GDAXI"
        }
    },

    # 4. COMMODITIES
    "USOIL": {
        "canonical_symbol": "USOIL",
        "display_name": "WTI Crude Oil",
        "category": "Commodities",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 0.01,
        "pip_value": 10.0,
        "default_spread": 0.04,
        "digits": 2,
        "trading_hours": "Mon-Fri 00:00 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["USOIL", "WTI", "USOILm", "CL"],
            "twelvedata": "WTI/USD",
            "finnhub": "USOIL"
        }
    },
    "NATGAS": {
        "canonical_symbol": "NATGAS",
        "display_name": "Natural Gas",
        "category": "Commodities",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 0.001,
        "pip_value": 10.0,
        "default_spread": 0.008,
        "digits": 3,
        "trading_hours": "Mon-Fri 00:00 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["NATGAS", "NGAS", "NG"],
            "twelvedata": "NG/USD"
        }
    },

    # 5. CRYPTO
    "BTCUSD": {
        "canonical_symbol": "BTCUSD",
        "display_name": "Bitcoin / US Dollar",
        "category": "Crypto",
        "base_currency": "BTC",
        "quote_currency": "USD",
        "pip_size": 1.0,
        "pip_value": 1.0,
        "default_spread": 12.0,
        "digits": 2,
        "trading_hours": "24/7",
        "provider_mappings": {
            "mt5": ["BTCUSD", "BTCUSDm", "BITCOIN"],
            "twelvedata": "BTC/USD",
            "finnhub": "BINANCE:BTCUSDT",
            "polygon": "X:BTCUSD"
        }
    },
    "ETHUSD": {
        "canonical_symbol": "ETHUSD",
        "display_name": "Ethereum / US Dollar",
        "category": "Crypto",
        "base_currency": "ETH",
        "quote_currency": "USD",
        "pip_size": 0.10,
        "pip_value": 1.0,
        "default_spread": 1.50,
        "digits": 2,
        "trading_hours": "24/7",
        "provider_mappings": {
            "mt5": ["ETHUSD", "ETHUSDm", "ETHEREUM"],
            "twelvedata": "ETH/USD",
            "finnhub": "BINANCE:ETHUSDT",
            "polygon": "X:ETHUSD"
        }
    },
    "SOLUSD": {
        "canonical_symbol": "SOLUSD",
        "display_name": "Solana / US Dollar",
        "category": "Crypto",
        "base_currency": "SOL",
        "quote_currency": "USD",
        "pip_size": 0.01,
        "pip_value": 1.0,
        "default_spread": 0.15,
        "digits": 2,
        "trading_hours": "24/7",
        "provider_mappings": {
            "mt5": ["SOLUSD", "SOLUSDm"],
            "twelvedata": "SOL/USD",
            "finnhub": "BINANCE:SOLUSDT"
        }
    },

    # 6. EQUITIES & ETFS
    "AAPL": {
        "canonical_symbol": "AAPL",
        "display_name": "Apple Inc.",
        "category": "Equities",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 0.01,
        "pip_value": 1.0,
        "default_spread": 0.05,
        "digits": 2,
        "trading_hours": "Mon-Fri 14:30 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["AAPL", "AAPL.US"],
            "twelvedata": "AAPL",
            "finnhub": "AAPL",
            "polygon": "AAPL"
        }
    },
    "NVDA": {
        "canonical_symbol": "NVDA",
        "display_name": "NVIDIA Corporation",
        "category": "Equities",
        "base_currency": "USD",
        "quote_currency": "USD",
        "pip_size": 0.01,
        "pip_value": 1.0,
        "default_spread": 0.08,
        "digits": 2,
        "trading_hours": "Mon-Fri 14:30 - 21:00 UTC",
        "provider_mappings": {
            "mt5": ["NVDA", "NVDA.US"],
            "twelvedata": "NVDA",
            "finnhub": "NVDA",
            "polygon": "NVDA"
        }
    }
}

class SymbolRegistry:
    """Canonical registry mapping broker & provider symbols to Chartora standards."""

    @staticmethod
    def get_symbol_info(symbol: str) -> Optional[Dict[str, Any]]:
        norm = SymbolRegistry.normalize_symbol(symbol)
        return CANONICAL_MARKET_REGISTRY.get(norm)

    @staticmethod
    def normalize_symbol(raw_symbol: str) -> str:
        clean = raw_symbol.upper().replace("/", "").replace(".", "").replace("-", "").strip()
        for canonical, info in CANONICAL_MARKET_REGISTRY.items():
            if clean == canonical:
                return canonical
            # Check mappings
            for provider, aliases in info.get("provider_mappings", {}).items():
                if isinstance(aliases, list):
                    for alias in aliases:
                        if clean == alias.upper().replace("/", "").replace(".", "").replace("-", "").strip():
                            return canonical
                elif isinstance(aliases, str):
                    if clean == aliases.upper().replace("/", "").replace(".", "").replace("-", "").strip():
                        return canonical
        return clean

    @staticmethod
    def get_all_canonical_symbols() -> List[str]:
        return list(CANONICAL_MARKET_REGISTRY.keys())

    @staticmethod
    def get_by_category(category: str) -> List[Dict[str, Any]]:
        cat_lower = category.lower()
        return [
            info for info in CANONICAL_MARKET_REGISTRY.values()
            if info["category"].lower() == cat_lower
        ]
