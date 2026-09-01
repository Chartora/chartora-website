//+------------------------------------------------------------------+
//|                                              ChartoraBridge.mq5 |
//|                                  Copyright 2026, CHARTORA     |
//|                                      https://chartora         |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, CHARTORA"
#property link      "https://chartora"
#property version   "3.10"
#property description "Chartora Institutional Trading Intelligence Bridge EA"
#property description "Connects MetaTrader 5 terminal securely to Chartora Intelligence Core"

#include <Trade\Trade.mqh>

//--- Input Parameters
input group "=== Chartora Cloud Gateway Settings ==="
input string   InpGatewayUrl     = "http://localhost:8080/api/v1/mt5"; // Base Gateway URL
input string   InpEaId           = "EA_DEMO_01";                       // Registered EA ID
input string   InpSecretKey      = "mt5_demo_secret_key_2026";         // HMAC Secret Key
input int      InpHeartbeatSec   = 30;                                 // Heartbeat Interval (Seconds)

input group "=== Technical Strategy Scanner ==="
input bool     InpEnableScanner  = true;                               // Enable EMA 9/21/200 Scanner
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_M5;                        // Setup Execution Timeframe
input int      InpEmaFast        = 9;                                  // Fast EMA Period
input int      InpEmaMedium      = 21;                                 // Medium EMA Period
input int      InpEmaSlow        = 200;                                // Baseline EMA Period

//--- Global Variables
int      hEmaFast, hEmaMedium, hEmaSlow;
datetime lastBarTime = 0;
datetime lastHeartbeatTime = 0;
CTrade   trade;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🚀 Chartora Bridge EA Initialized for ", _Symbol);
   
   // Create indicator handles
   hEmaFast   = iMA(_Symbol, InpTimeframe, InpEmaFast, 0, MODE_EMA, PRICE_CLOSE);
   hEmaMedium = iMA(_Symbol, InpTimeframe, InpEmaMedium, 0, MODE_EMA, PRICE_CLOSE);
   hEmaSlow   = iMA(_Symbol, InpTimeframe, InpEmaSlow, 0, MODE_EMA, PRICE_CLOSE);

   if(hEmaFast == INVALID_HANDLE || hEmaMedium == INVALID_HANDLE || hEmaSlow == INVALID_HANDLE)
   {
      Print("❌ Failed to create EMA indicator handles.");
      return(INIT_FAILED);
   }

   EventSetTimer(1); // 1-second timer resolution for heartbeats
   SendHeartbeat();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   IndicatorRelease(hEmaFast);
   IndicatorRelease(hEmaMedium);
   IndicatorRelease(hEmaSlow);
   Print("Chartora Bridge EA Deinitialized.");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check for newly formed bar
   datetime currentBarTime = iTime(_Symbol, InpTimeframe, 0);
   if(currentBarTime != lastBarTime)
   {
      lastBarTime = currentBarTime;
      OnBarClosed();
   }
}

//+------------------------------------------------------------------+
//| Timer function for 30-sec heartbeats                             |
//+------------------------------------------------------------------+
void OnTimer()
{
   datetime now = TimeCurrent();
   if(now - lastHeartbeatTime >= InpHeartbeatSec)
   {
      lastHeartbeatTime = now;
      SendHeartbeat();
   }
}

//+------------------------------------------------------------------+
//| Executed on closed candle bar                                    |
//+------------------------------------------------------------------+
void OnBarClosed()
{
   if(!InpEnableScanner) return;

   MqlRates rates[];
   ArraySetAsSeries(rates, true);
   if(CopyRates(_Symbol, InpTimeframe, 1, 3, rates) < 3) return;

   double ema9[], ema21[], ema200[];
   ArraySetAsSeries(ema9, true);
   ArraySetAsSeries(ema21, true);
   ArraySetAsSeries(ema200, true);

   if(CopyBuffer(hEmaFast, 0, 1, 3, ema9) < 3) return;
   if(CopyBuffer(hEmaMedium, 0, 1, 3, ema21) < 3) return;
   if(CopyBuffer(hEmaSlow, 0, 1, 3, ema200) < 3) return;

   // 1. BULLISH EMA PULLBACK CONDITION
   bool bullEmaAlign = (ema9[0] > ema21[0]) && (ema21[0] > ema200[0]);
   bool bullPullback = (rates[0].low <= ema21[0] * 1.0005) && (rates[0].close > ema9[0]);
   bool bullEngulf   = (rates[0].close > rates[0].open) && (rates[0].close >= rates[1].high);

   if(bullEmaAlign && bullPullback && bullEngulf)
   {
      double entry = rates[0].close;
      double sl    = rates[0].low - (rates[0].high - rates[0].low) * 0.5;
      double risk  = entry - sl;
      double tp1   = entry + (risk * 1.6);
      double tp2   = entry + (risk * 2.5);

      SendSetupEvent("BUY", entry, sl, tp1, tp2, "EMA 9/21 Pullback Continuation + 200 EMA HTF Alignment");
   }

   // 2. BEARISH EMA PULLBACK CONDITION
   bool bearEmaAlign = (ema9[0] < ema21[0]) && (ema21[0] < ema200[0]);
   bool bearPullback = (rates[0].high >= ema21[0] * 0.9995) && (rates[0].close < ema9[0]);
   bool bearEngulf   = (rates[0].close < rates[0].open) && (rates[0].close <= rates[1].low);

   if(bearEmaAlign && bearPullback && bearEngulf)
   {
      double entry = rates[0].close;
      double sl    = rates[0].high + (rates[0].high - rates[0].low) * 0.5;
      double risk  = sl - entry;
      double tp1   = entry - (risk * 1.6);
      double tp2   = entry - (risk * 2.5);

      SendSetupEvent("SELL", entry, sl, tp1, tp2, "EMA 9/21 Bearish Pullback Continuation + 200 EMA Baseline");
   }
}

//+------------------------------------------------------------------+
//| Send Telemetry Heartbeat to Chartora Gateway                     |
//+------------------------------------------------------------------+
void SendHeartbeat()
{
   string jsonPayload = StringFormat(
      "{\"ea_id\":\"%s\",\"broker\":\"%s\",\"server\":\"%s\",\"balance\":%.2f,\"equity\":%.2f,\"open_positions_count\":%d,\"ea_version\":\"%s\",\"timestamp\":%d}",
      InpEaId,
      AccountInfoString(ACCOUNT_COMPANY),
      AccountInfoString(ACCOUNT_SERVER),
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      PositionsTotal(),
      "3.1.0",
      (int)TimeCurrent()
   );

   SendAuthenticatedPost("/heartbeat", jsonPayload);
}

//+------------------------------------------------------------------+
//| Send Setup Detected Event                                        |
//+------------------------------------------------------------------+
void SendSetupEvent(string direction, double entry, double sl, double tp1, double tp2, string reason)
{
   string jsonPayload = StringFormat(
      "{\"symbol\":\"%s\",\"timeframe\":\"5M\",\"direction\":\"%s\",\"entry_price\":%.5f,\"sl_price\":%.5f,\"tp1_price\":%.5f,\"tp2_price\":%.5f,\"technical_reason\":\"%s\",\"news_risk\":\"LOW\"}",
      _Symbol, direction, entry, sl, tp1, tp2, reason
   );

   Print("⚡ Broadcasting Setup Event to Chartora: ", _Symbol, " ", direction);
   SendAuthenticatedPost("/events", jsonPayload);
}

//+------------------------------------------------------------------+
//| HTTP POST with Cryptographic Headers                             |
//+------------------------------------------------------------------+
bool SendAuthenticatedPost(string subPath, string jsonBody)
{
   string url = InpGatewayUrl + subPath;
   char postData[];
   char resultData[];
   string resultHeaders;
   
   StringToCharArray(jsonBody, postData, 0, StringLen(jsonBody));
   
   int ts = (int)TimeCurrent();
   string nonce = StringFormat("%08X%08X", MathRand(), MathRand());
   
   // Create HMAC signature over ea_id:ts:nonce:body
   string dataToSign = StringFormat("%s:%d:%s:%s", InpEaId, ts, nonce, jsonBody);
   uchar keyArr[];
   uchar dataArr[];
   uchar hmacArr[];
   StringToCharArray(InpSecretKey, keyArr, 0, StringLen(InpSecretKey));
   StringToCharArray(dataToSign, dataArr, 0, StringLen(dataToSign));
   Crypt(CRYPT_HASH_SHA256, dataArr, keyArr, hmacArr);
   
   string signature = "";
   for(int i = 0; i < ArraySize(hmacArr); i++)
      signature += StringFormat("%02x", hmacArr[i]);

   string headers = "Content-Type: application/json\r\n" +
                    "X-EA-ID: " + InpEaId + "\r\n" +
                    "X-EA-Timestamp: " + IntegerToString(ts) + "\r\n" +
                    "X-EA-Nonce: " + nonce + "\r\n" +
                    "X-EA-Signature: " + signature + "\r\n";

   int res = WebRequest("POST", url, headers, 3000, postData, resultData, resultHeaders);
   if(res == -1)
   {
      int err = GetLastError();
      if(err == 4014) // Function not allowed
         Print("⚠️ WebRequest not allowed. Please add '", InpGatewayUrl, "' to MT5 Allowed URLs.");
      return false;
   }
   
   return (res == 200);
}
//+------------------------------------------------------------------+
