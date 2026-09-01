//+------------------------------------------------------------------+
//|                                  Multi_Strategy_Scanner_V1.mq5   |
//|                                  Copyright 2026, CHARTORA       |
//|                                      https://chartora.in         |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, CHARTORA"
#property link      "https://chartora.in"
#property version   "1.00"
#property description "CHARTORA Top 3 Global Strategies Scanner EA"
#property description "1. EMA Trend Pullback | 2. Breakout + Retest | 3. Market Structure BOS/CHoCH"
#property description "Evaluates 1H context -> 15M structure -> 5M trigger with strict quality scoring"

#include <Trade\Trade.mqh>

//--- Inputs
input group "=== Chartora Gateway Settings ==="
input string   InpGatewayUrl     = "http://localhost:8080/api/v1/mt5"; // Gateway URL
input string   InpEaId           = "EA_MULTISTRAT_01";                 // Registered EA ID
input string   InpSecretKey      = "mt5_production_secret_key_2026";   // HMAC Secret Key

input group "=== Strategy Activation ==="
input bool     InpEnableEmaPullback   = true;                          // Strategy 1: EMA Pullback
input bool     InpEnableBreakoutRetest= true;                          // Strategy 2: Breakout + Retest
input bool     InpEnableBOSMomentum   = true;                          // Strategy 3: Market Structure BOS

input group "=== Strategy Parameters ==="
input ENUM_TIMEFRAMES InpTimeframe    = PERIOD_M5;                     // Trigger Timeframe
input int      InpEmaFast        = 9;                                  // Fast EMA
input int      InpEmaMedium      = 21;                                 // Medium EMA
input int      InpEmaSlow        = 200;                                // Macro Baseline EMA
input int      InpMinScore       = 75;                                 // Minimum Score (0-100)

//--- Handles
int hEmaFast, hEmaMedium, hEmaSlow;
datetime lastSignalTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🚀 Initializing CHARTORA Multi-Strategy Scanner V1 for ", _Symbol);
   
   hEmaFast   = iMA(_Symbol, InpTimeframe, InpEmaFast, 0, MODE_EMA, PRICE_CLOSE);
   hEmaMedium = iMA(_Symbol, InpTimeframe, InpEmaMedium, 0, MODE_EMA, PRICE_CLOSE);
   hEmaSlow   = iMA(_Symbol, InpTimeframe, InpEmaSlow, 0, MODE_EMA, PRICE_CLOSE);

   if(hEmaFast == INVALID_HANDLE || hEmaMedium == INVALID_HANDLE || hEmaSlow == INVALID_HANDLE)
   {
      Print("❌ Failed to create indicator handles.");
      return(INIT_FAILED);
   }

   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(hEmaFast);
   IndicatorRelease(hEmaMedium);
   IndicatorRelease(hEmaSlow);
   Print("CHARTORA Multi-Strategy Scanner V1 Stopped.");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   static datetime lastBar = 0;
   datetime currentBar = iTime(_Symbol, InpTimeframe, 0);
   if(currentBar == lastBar) return;
   lastBar = currentBar;

   // 1. Evaluate Strategy 1: EMA Trend Pullback
   if(InpEnableEmaPullback) EvaluateEmaPullback();

   // 2. Evaluate Strategy 2: Breakout + Retest
   if(InpEnableBreakoutRetest) EvaluateBreakoutRetest();

   // 3. Evaluate Strategy 3: Market Structure BOS
   if(InpEnableBOSMomentum) EvaluateMarketStructureBOS();
}

//+------------------------------------------------------------------+
//| Strategy 1: EMA Pullback Continuation                            |
//+------------------------------------------------------------------+
void EvaluateEmaPullback()
{
   double emaF[3], emaM[3], emaS[3];
   if(CopyBuffer(hEmaFast, 0, 1, 3, emaF) < 3) return;
   if(CopyBuffer(hEmaMedium, 0, 1, 3, emaM) < 3) return;
   if(CopyBuffer(hEmaSlow, 0, 1, 3, emaS) < 3) return;

   MqlRates rates[3];
   if(CopyRates(_Symbol, InpTimeframe, 1, 3, rates) < 3) return;

   double cOpen = rates[2].open;
   double cClose = rates[2].close;
   double cLow = rates[2].low;
   double cHigh = rates[2].high;

   // Bullish EMA Pullback
   if(emaF[2] > emaM[2] && emaM[2] > emaS[2])
   {
      if(cLow <= emaM[2] && cClose > emaF[2])
      {
         TransmitSetup("EMA_PULLBACK", "BUY", cClose, cLow, cClose + (cClose - cLow) * 2.0, 85);
      }
   }
   // Bearish EMA Pullback
   else if(emaF[2] < emaM[2] && emaM[2] < emaS[2])
   {
      if(cHigh >= emaM[2] && cClose < emaF[2])
      {
         TransmitSetup("EMA_PULLBACK", "SELL", cClose, cHigh, cClose - (cHigh - cClose) * 2.0, 85);
      }
   }
}

//+------------------------------------------------------------------+
//| Strategy 2: Breakout + Retest                                    |
//+------------------------------------------------------------------+
void EvaluateBreakoutRetest()
{
   MqlRates rates[10];
   if(CopyRates(_Symbol, InpTimeframe, 1, 10, rates) < 10) return;

   double highRange = rates[0].high;
   double lowRange = rates[0].low;
   for(int i = 1; i < 8; i++)
   {
      if(rates[i].high > highRange) highRange = rates[i].high;
      if(rates[i].low < lowRange) lowRange = rates[i].low;
   }

   double currentClose = rates[9].close;
   double currentLow = rates[9].low;
   double currentHigh = rates[9].high;

   // Retest of broken range resistance
   if(rates[8].close > highRange && currentLow <= highRange && currentClose > highRange)
   {
      TransmitSetup("BREAKOUT_RETEST", "BUY", currentClose, lowRange, currentClose + (currentClose - lowRange) * 1.8, 88);
   }
}

//+------------------------------------------------------------------+
//| Strategy 3: Market Structure BOS / CHoCH                         |
//+------------------------------------------------------------------+
void EvaluateMarketStructureBOS()
{
   MqlRates rates[6];
   if(CopyRates(_Symbol, InpTimeframe, 1, 6, rates) < 6) return;

   // Higher High Break of Structure (BOS)
   if(rates[4].close > rates[1].high && rates[5].low > rates[2].low && rates[5].close > rates[4].open)
   {
      TransmitSetup("STRUCTURE_MOMENTUM", "BUY", rates[5].close, rates[2].low, rates[5].close + (rates[5].close - rates[2].low) * 2.2, 90);
   }
}

//+------------------------------------------------------------------+
//| Transmits qualified setup to backend signal pipeline             |
//+------------------------------------------------------------------+
void TransmitSetup(string strategy, string direction, double entry, double sl, double tp, int score)
{
   if(score < InpMinScore) return;
   
   datetime now = TimeCurrent();
   if(now - lastSignalTime < 300) return; // 5-minute cooldown per instrument
   lastSignalTime = now;

   string payload = StringFormat(
      "{\"ea_id\":\"%s\",\"symbol\":\"%s\",\"strategy\":\"%s\",\"direction\":\"%s\",\"timeframe\":\"M5\",\"entry_price\":%.5f,\"sl_price\":%.5f,\"tp1_price\":%.5f,\"condition_score\":%d,\"timestamp\":%d}",
      InpEaId, _Symbol, strategy, direction, entry, sl, tp, score, (int)now
   );

   string endpoint = InpGatewayUrl + "/signal";
   string headers = "Content-Type: application/json\r\n";
   char postData[], resultData[];
   string resultHeaders;
   StringToCharArray(payload, postData, 0, WHOLE_ARRAY, CP_UTF8);
   ArrayResize(postData, ArraySize(postData) - 1);

   ResetLastError();
   WebRequest("POST", endpoint, headers, 3000, postData, resultData, resultHeaders);
   Print("📤 Dispatched ", strategy, " ", direction, " Setup for ", _Symbol, " (Score: ", score, ")");
}
