//+------------------------------------------------------------------+
//|                                     Multi_Pair_Scanner_V1.mq5    |
//|                                  Copyright 2026, CHARTORA       |
//|                                      https://chartora.in         |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, CHARTORA"
#property link      "https://chartora.in"
#property version   "1.00"
#property description "CHARTORA Institutional Multi-Pair Market Scanner EA"
#property description "Scans multi-asset universe (Forex, Metals, Energies, Indices, Stocks, Crypto)"
#property description "Auto-detects broker suffixes and transmits validated data to CHARTORA Backend"

#include <Trade\Trade.mqh>

//--- Input Parameters
input group "=== Chartora Cloud Gateway Settings ==="
input string   InpGatewayUrl     = "http://localhost:8080/api/v1/mt5"; // Base Gateway URL
input string   InpEaId           = "EA_MULTIPAIR_01";                  // Registered EA ID
input string   InpSecretKey      = "mt5_production_secret_key_2026";   // HMAC Secret Key
input int      InpScanIntervalSec= 10;                                 // Multi-Pair Scan Interval (Sec)

input group "=== Universe Selection ==="
input bool     InpScanForex      = true;                               // Scan Major Forex Pairs
input bool     InpScanMetals     = true;                               // Scan Metals (Gold/Silver)
input bool     InpScanEnergies   = true;                               // Scan Energies (Crude Oil)
input bool     InpScanIndices    = true;                               // Scan Major Indices (US30/US500/USTEC)
input bool     InpScanCrypto     = true;                               // Scan Crypto (BTC/ETH)
input bool     InpScanStocks     = false;                              // Scan Selected US Equities

input group "=== Strategy Parameters ==="
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M5;                        // Setup Execution Timeframe
input int      InpMinScore       = 75;                                 // Minimum Condition Quality Score (0-100)
input double   InpMaxSpreadPips  = 5.0;                                // Maximum Spread Filter (Pips)

//--- Internal State
string activeSymbols[];
int    totalActiveSymbols = 0;
datetime lastScanTime = 0;

//+------------------------------------------------------------------+
//| Symbol discovery and normalization with suffix detection         |
//+------------------------------------------------------------------+
string DetectBrokerSymbol(string baseSym)
{
   if(SymbolSelect(baseSym, true)) return baseSym;
   
   string suffixes[] = {".m", "_i", "m", ".raw", ".pro", "c", ".ecn", "_sb"};
   for(int i = 0; i < ArraySize(suffixes); i++)
   {
      string testSym = baseSym + suffixes[i];
      if(SymbolSelect(testSym, true)) return testSym;
   }
   
   // Alias mappings (e.g. GOLD -> XAUUSD)
   if(baseSym == "XAUUSD" && SymbolSelect("GOLD", true)) return "GOLD";
   if(baseSym == "XAGUSD" && SymbolSelect("SILVER", true)) return "SILVER";
   if(baseSym == "US500" && SymbolSelect("SPX500", true)) return "SPX500";
   if(baseSym == "USTEC" && SymbolSelect("NAS100", true)) return "NAS100";
   if(baseSym == "US30" && SymbolSelect("DJ30", true)) return "DJ30";
   if(baseSym == "USOIL" && SymbolSelect("WTI", true)) return "WTI";

   return "";
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🚀 Initializing CHARTORA Multi-Pair Scanner V1...");
   
   string baseUniverse[] = {
      "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
      "XAUUSD", "XAGUSD", "USOIL", "US500", "USTEC", "US30", "BTCUSD", "ETHUSD"
   };

   ArrayResize(activeSymbols, 0);
   for(int i = 0; i < ArraySize(baseUniverse); i++)
   {
      string detected = DetectBrokerSymbol(baseUniverse[i]);
      if(detected != "")
      {
         int sz = ArraySize(activeSymbols);
         ArrayResize(activeSymbols, sz + 1);
         activeSymbols[sz] = detected;
         Print("   ✓ Added Symbol: ", detected, " (Base: ", baseUniverse[i], ")");
      }
   }

   totalActiveSymbols = ArraySize(activeSymbols);
   Print("✅ Discovered ", totalActiveSymbols, " active trading instruments on this terminal.");

   EventSetTimer(1);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("CHARTORA Multi-Pair Scanner V1 Stopped.");
}

//+------------------------------------------------------------------+
//| Timer handler for multi-pair scanning                            |
//+------------------------------------------------------------------+
void OnTimer()
{
   datetime now = TimeCurrent();
   if(now - lastScanTime >= InpScanIntervalSec)
   {
      lastScanTime = now;
      ScanMultiPairUniverse();
   }
}

//+------------------------------------------------------------------+
//| Scans all active instruments for technical conditions            |
//+------------------------------------------------------------------+
void ScanMultiPairUniverse()
{
   for(int i = 0; i < totalActiveSymbols; i++)
   {
      string sym = activeSymbols[i];
      MqlTick tick;
      if(!SymbolInfoTick(sym, tick)) continue;

      double bid = tick.bid;
      double ask = tick.ask;
      double point = SymbolInfoDouble(sym, SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
      double spread = (ask - bid) / (point * (digits == 3 || digits == 5 ? 10 : 1));

      if(spread > InpMaxSpreadPips) continue; // Skip high-spread market conditions

      // Send live market tick to backend
      TransmitTick(sym, bid, ask, spread);
   }
}

//+------------------------------------------------------------------+
//| Transmits normalized tick data to Chartora Cloud                 |
//+------------------------------------------------------------------+
void TransmitTick(string symbol, double bid, double ask, double spread)
{
   string jsonPayload = StringFormat(
      "{\"ea_id\":\"%s\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%.2f,\"timestamp\":%d}",
      InpEaId, symbol, bid, ask, spread, (int)TimeCurrent()
   );

   string endpoint = InpGatewayUrl + "/tick";
   string headers = "Content-Type: application/json\r\n";
   char postData[], resultData[];
   string resultHeaders;
   StringToCharArray(jsonPayload, postData, 0, WHOLE_ARRAY, CP_UTF8);
   ArrayResize(postData, ArraySize(postData) - 1);

   ResetLastError();
   WebRequest("POST", endpoint, headers, 3000, postData, resultData, resultHeaders);
}
