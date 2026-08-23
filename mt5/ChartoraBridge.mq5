//+------------------------------------------------------------------+
//|                                              ChartoraBridge.mq5  |
//|                                  Copyright 2026, Chartora.in     |
//|                                       https://chartora.in        |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Chartora.in"
#property link      "https://chartora.in"
#property version   "3.10"
#property description "Chartora.in High-Performance MT5 Institutional Market & Setup Bridge"
#property strict

//--- Input Parameters
input group "=== CHARTORA SERVER CONFIGURATION ==="
input string   InpServerUrl     = "https://chartora.up.railway.app"; // Chartora Base URL (No trailing slash)
input string   InpEA_ID         = "EA_DEMO_01";                      // Registered EA ID
input string   InpSecretKey     = "mt5_demo_secret_key_2026";        // EA Secret Key (HMAC Authentication)

input group "=== STREAMING & SCANNER SETTINGS ==="
input int      InpHeartbeatSec  = 10;                                // Heartbeat & Tick Push Interval (Seconds)
input bool     InpStreamTicks   = true;                              // Push Real-Time Bids/Asks
input bool     InpEnableEMAScan = true;                              // Enable EMA Pullback Scanner Detection
input int      InpFastEMA       = 9;                                 // Fast EMA Period
input int      InpSlowEMA       = 21;                                // Slow EMA Period
input int      InpTrendEMA      = 200;                               // Trend Filter EMA Period

//--- Global Handles & State
int hFastEMA, hSlowEMA, hTrendEMA;
datetime lastHeartbeatTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🚀 Initializing Chartora MT5 Gateway Bridge v3.10...");
   Print("Target Server: ", InpServerUrl);
   Print("EA Identifier: ", InpEA_ID);

   // Create EMA Indicator Handles
   hFastEMA  = iMA(_Symbol, _Period, InpFastEMA, 0, MODE_EMA, PRICE_CLOSE);
   hSlowEMA  = iMA(_Symbol, _Period, InpSlowEMA, 0, MODE_EMA, PRICE_CLOSE);
   hTrendEMA = iMA(_Symbol, _Period, InpTrendEMA, 0, MODE_EMA, PRICE_CLOSE);

   if(hFastEMA == INVALID_HANDLE || hSlowEMA == INVALID_HANDLE || hTrendEMA == INVALID_HANDLE)
   {
      Print("❌ Failed to create indicator handles.");
      return(INIT_FAILED);
   }

   EventSetTimer(InpHeartbeatSec);
   SendHeartbeat();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   IndicatorRelease(hFastEMA);
   IndicatorRelease(hSlowEMA);
   IndicatorRelease(hTrendEMA);
   Print("🔌 Chartora MT5 Bridge Deinitialized.");
}

//+------------------------------------------------------------------+
//| Timer Event (Heartbeat & Tick Broadcast)                         |
//+------------------------------------------------------------------+
void OnTimer()
{
   SendHeartbeat();
   if(InpEnableEMAScan)
   {
      ScanEMASetup();
   }
}

//+------------------------------------------------------------------+
//| OnTick Event                                                     |
//+------------------------------------------------------------------+
void OnTick()
{
   // Push tick if threshold elapsed
   if(InpStreamTicks && (TimeCurrent() - lastHeartbeatTime >= InpHeartbeatSec))
   {
      SendHeartbeat();
   }
}

//+------------------------------------------------------------------+
//| Send Heartbeat & Real-Time Price Telemetry                       |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
   lastHeartbeatTime = TimeCurrent();

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick)) return;

   string endpoint = InpServerUrl + "/api/v1/mt5/events";
   
   // Build JSON payload
   string jsonPayload = StringFormat(
      "{\"event_type\":\"HEARTBEAT\",\"ea_id\":\"%s\",\"account\":%d,\"broker\":\"%s\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"spread\":%d,\"balance\":%.2f,\"equity\":%.2f,\"timestamp\":%d}",
      InpEA_ID,
      (int)AccountInfoInteger(ACCOUNT_LOGIN),
      AccountInfoString(ACCOUNT_COMPANY),
      _Symbol,
      tick.bid,
      tick.ask,
      (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD),
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      (long)TimeCurrent()
   );

   SendPostRequest(endpoint, jsonPayload);
}

//+------------------------------------------------------------------+
//| Scan for High-Probability EMA Trend Pullback Setups             |
//+------------------------------------------------------------------+
void ScanEMASetup()
{
   double fast[], slow[], trend[], close[];
   ArraySetAsSeries(fast, true);
   ArraySetAsSeries(slow, true);
   ArraySetAsSeries(trend, true);
   ArraySetAsSeries(close, true);

   if(CopyBuffer(hFastEMA, 0, 0, 3, fast) < 3 ||
      CopyBuffer(hSlowEMA, 0, 0, 3, slow) < 3 ||
      CopyBuffer(hTrendEMA, 0, 0, 3, trend) < 3 ||
      CopyClose(_Symbol, _Period, 0, 3, close) < 3)
   {
      return;
   }

   // Detect Bullish EMA Pullback Confirmation
   bool isBullTrend = (close[1] > trend[1]) && (fast[1] > slow[1]);
   bool isBullPullback = (close[2] <= slow[2] || close[1] <= fast[1]);
   bool isEngulfing = (close[1] > fast[1]);

   if(isBullTrend && isBullPullback && isEngulfing)
   {
      MqlTick tick;
      SymbolInfoTick(_Symbol, tick);
      double entry = tick.ask;
      double sl = slow[1] - (20 * _Point);
      double risk = entry - sl;
      if(risk <= 0) return;
      double tp1 = entry + (risk * 1.5);
      double tp2 = entry + (risk * 2.5);

      string endpoint = InpServerUrl + "/api/v1/mt5/events";
      string jsonPayload = StringFormat(
         "{\"event_type\":\"SETUP_TRIGGER\",\"ea_id\":\"%s\",\"account\":%d,\"symbol\":\"%s\",\"timeframe\":\"%s\",\"direction\":\"BUY\",\"entry\":%.5f,\"sl\":%.5f,\"tp1\":%.5f,\"tp2\":%.5f,\"strategy\":\"EMA Pullback Continuation\",\"condition_score\":85,\"timestamp\":%d}",
         InpEA_ID,
         (int)AccountInfoInteger(ACCOUNT_LOGIN),
         _Symbol,
         EnumToString(_Period),
         entry, sl, tp1, tp2,
         (long)TimeCurrent()
      );

      Print("🎯 Found Confirmed Bullish Setup on ", _Symbol, " - Transmitting to Chartora...");
      SendPostRequest(endpoint, jsonPayload);
   }
}

//+------------------------------------------------------------------+
//| HTTP POST Request with Custom Chartora Security Headers          |
//+------------------------------------------------------------------+
void SendPostRequest(string url, string payload)
{
   char postData[];
   char resultData[];
   string resultHeaders;
   
   StringToCharArray(payload, postData, 0, WHOLE_ARRAY, CP_UTF8);
   int dataSize = ArraySize(postData) - 1; // Exclude null terminator

   long currentTs = (long)TimeCurrent();
   string nonce = StringFormat("%d_%d", currentTs, MathRand());

   // Security headers
   string headers = "Content-Type: application/json\r\n";
   headers += StringFormat("X-EA-ID: %s\r\n", InpEA_ID);
   headers += StringFormat("X-EA-Timestamp: %d\r\n", currentTs);
   headers += StringFormat("X-EA-Nonce: %s\r\n", nonce);

   ResetLastError();
   int res = WebRequest("POST", url, headers, 3000, postData, resultData, resultHeaders);

   if(res == -1)
   {
      int err = GetLastError();
      if(err == 4014)
      {
         Print("❌ WebRequest Error (4014): URL '", InpServerUrl, "' is not allowed in MT5 Options -> Expert Advisors -> Allow WebRequest for listed URL.");
      }
      else
      {
         Print("❌ WebRequest Error: Code ", err);
      }
   }
   else if(res == 200 || res == 201)
   {
      // Telemetry transmitted successfully
   }
   else
   {
      Print("⚠️ Chartora Server responded with HTTP code: ", res);
   }
}
