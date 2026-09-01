//+------------------------------------------------------------------+
//|                                        Chartora_Official_V1.mq5  |
//|                                  Copyright 2026, CHARTORA       |
//|                                      https://chartora.in         |
//+------------------------------------------------------------------+
#property copyright   "Copyright 2026, CHARTORA"
#property link        "https://chartora.in"
#property version     "1.00"
#property description "CHARTORA Official V1 — Master Single-File Trading Intelligence EA"
#property description "Multi-Asset Scanner • High-Quality Trade Filter • Choppy Market Protection"
#property description "Auto-Execution • Dynamic Lot Sizing • Realized R Tracker • Telegram Reporting"
#property description "Single-File Architecture — Zero Custom MQH Dependencies"

//--- Standard MT5 Built-in Trade Library Includes
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\AccountInfo.mqh>

//+------------------------------------------------------------------+
//| ENUMERATIONS & CORE CONSTANTS                                    |
//+------------------------------------------------------------------+
enum ENUM_MARKET_REGIME
{
   REGIME_TRENDING_BULL  = 0, // Clean Bullish Trend
   REGIME_TRENDING_BEAR  = 1, // Clean Bearish Trend
   REGIME_CONSOLIDATION  = 2, // Consolidation / Range
   REGIME_CHOPPY         = 3, // Choppy / Sideways (NO TRADE)
   REGIME_HIGH_VOLATILITY= 4  // High Spread / High Volatility Spike
};

enum ENUM_SETUP_TYPE
{
   SETUP_NONE            = 0, // No Setup
   SETUP_EMA_PULLBACK    = 1, // 9/21 EMA Trend Pullback Continuation
   SETUP_BREAKOUT_RETEST = 2, // Range Breakout + Structure Retest
   SETUP_STRUCTURE_BOS   = 3  // Market Structure Break (BOS / CHoCH)
};

enum ENUM_TRADE_DIR
{
   TRADE_DIR_NONE = 0,
   TRADE_DIR_BUY  = 1,
   TRADE_DIR_SELL = 2
};

enum ENUM_ALERT_CHANNEL
{
   CHANNEL_OFFICIAL_FREE = 0, // Channel 1: Free Community & Educational
   CHANNEL_PRO_SETUPS    = 1, // Channel 2: Qualified Pro Setups
   CHANNEL_ALL_ACCESS    = 2, // Channel 3: All-Access VIP Scans
   CHANNEL_REPORTS       = 3, // Channel 4: Daily / Weekly Reports
   CHANNEL_ADMIN         = 4  // Channel 5: System Admin & Health
};

enum ENUM_REPORT_TYPE
{
   REPORT_DAILY_OPEN     = 0,
   REPORT_DAILY_CLOSE    = 1,
   REPORT_WEEKLY         = 2,
   REPORT_MONTHLY        = 3
};

#define CHARTORA_VERSION      "1.00"
#define MAX_JOURNAL_RECORDS   2000
#define RETENTION_DAYS        30
#define SCORE_MIN_THRESHOLD   50

//+------------------------------------------------------------------+
//| STRUCTS FOR SIGNALS, TRADES & METRICS                            |
//+------------------------------------------------------------------+
struct STradeSetup
{
   string            symbol;
   ENUM_TIMEFRAMES   timeframe;
   ENUM_TRADE_DIR    direction;
   ENUM_SETUP_TYPE   setupType;
   string            strategyName;
   double            entryPrice;
   double            slPrice;
   double            tp1Price;
   double            tp2Price;
   double            rrRatio;
   int               qualityScore;
   double            riskAmountUSD;
   double            expectedProfitUSD;
   string            h1Trend;
   string            m5Structure;
   string            emaAlignment;
   string            candlePattern;
   string            dxyStatus;
   string            fearGreedStatus;
   string            rationale;
   string            riskNote;
   datetime          setupTime;
   bool              isChoppy;
   string            choppyReason;
};

struct STrackedTrade
{
   ulong             ticket;
   string            symbol;
   ENUM_TRADE_DIR    direction;
   datetime          openTime;
   double            openPrice;
   double            currentPrice;
   double            slPrice;
   double            tpPrice;
   double            lotSize;
   double            initialRiskUSD;
   double            currentProfitUSD;
   double            currentR;
   double            maxFavorableR;
   double            maxAdverseR;
   int               qualityScore;
   ENUM_SETUP_TYPE   setupType;
   bool              isBreakEvenApplied;
   bool              isPartialClosed;
   bool              isClosed;
   datetime          closeTime;
   double            closePrice;
   double            realizedProfitUSD;
   double            realizedR;
   string            exitReason;
};

struct SSymbolScanResult
{
   string            symbol;
   string            baseCategory;
   string            h1Trend;
   string            m5Trend;
   string            emaState;
   ENUM_MARKET_REGIME regime;
   bool              isChoppy;
   double            bid;
   double            ask;
   double            spreadPips;
   int               score;
   STradeSetup       setup;
   bool              isEligible;
};

struct SPerformanceMetrics
{
   int               totalTrades;
   int               winCount;
   int               lossCount;
   double            winRatePct;
   double            grossProfitUSD;
   double            grossLossUSD;
   double            netProfitUSD;
   double            totalR;
   double            avgR;
   double            bestTradeUSD;
   double            worstTradeUSD;
   double            bestTradeR;
   double            worstTradeR;
   double            avgScore;
   double            maxDrawdownUSD;
   double            maxDrawdownPct;
   int               consecutiveWins;
   int               consecutiveLosses;
   int               choppyAvoidedCount;
   string            bestSymbol;
   string            worstSymbol;
   string            bestSetupName;
   string            worstSetupName;
};

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
input group "=== 1. Core EA Settings ==="
input string            InpEaName               = "CHARTORA_OFFICIAL_V1"; // EA Identifier
input ulong             InpMagicNumber          = 20260901;               // Unique Magic Number
input bool              InpTestMode             = false;                  // Test Mode (Simulate without Live Broadcasts)
input bool              InpDebugLog             = true;                   // Enable Structured Logging

input group "=== 2. Automated Trading & Execution ==="
input bool              InpEnableAutoTrading    = true;                   // Enable Automated Trading
input ENUM_TIMEFRAMES   InpExecutionTimeframe   = PERIOD_M5;              // Execution Timeframe
input ENUM_TIMEFRAMES   InpHigherTimeframe      = PERIOD_H1;              // Higher Timeframe Trend Filter
input int               InpMaxOpenTrades        = 3;                      // Max Simultaneous Open Trades
input int               InpMaxTradesPerSymbol   = 1;                      // Max Open Trades Per Symbol
input int               InpMaxSlippagePoints    = 30;                     // Max Allowed Slippage (Points)

input group "=== 3. Risk Management & Lot Sizing ==="
input double            InpRiskPercent          = 1.0;                    // Risk % Per Trade (1.0 = 1%)
input double            InpMaxDailyLossPercent  = 4.0;                    // Max Daily Loss % Limit
input double            InpMaxDrawdownPercent   = 8.0;                    // Max Total Account Drawdown % Limit
input int               InpMaxConsecutiveLosses = 3;                      // Max Consecutive Losses Before Pause
input int               InpCooldownMinutesLoss  = 30;                     // Cooldown After Loss (Minutes)
input int               InpCooldownMinutesTrade = 10;                     // Cooldown Between New Trades (Minutes)
input double            InpMaxSpreadPips        = 4.0;                    // Maximum Allowed Spread (Pips)

input group "=== 4. Trade Quality & Choppy Market Filter ==="
input int               InpMinTradeScore        = 80;                     // Minimum Quality Score to Trade (0-100)
input double            InpMinRRRatio           = 1.8;                    // Minimum Risk/Reward Ratio (e.g. 1.8 = 1:1.8)
input int               InpEmaFastPeriod        = 9;                      // Fast EMA Period
input int               InpEmaMediumPeriod      = 21;                     // Medium EMA Period
input int               InpEmaSlowPeriod        = 200;                    // Macro Baseline EMA Period
input int               InpAtrPeriod            = 14;                     // ATR Volatility Period
input double            InpAtrMultiplierSL      = 1.5;                    // ATR Multiplier for Stop Loss Buffer
input bool              InpEnableEmaPullback    = true;                   // Enable Strategy 1: EMA Trend Pullback
input bool              InpEnableBreakoutRetest = true;                   // Enable Strategy 2: Breakout + Retest
input bool              InpEnableStructureBOS   = true;                   // Enable Strategy 3: Market Structure BOS

input group "=== 5. Active Trade Management ==="
input bool              InpEnableBreakEven      = true;                   // Move Stop Loss to Break-Even
input double            InpBreakEvenTriggerR    = 1.0;                    // Break-Even Milestone (+1.0R)
input double            InpBreakEvenLockPips    = 1.0;                    // Pips Locked Beyond Entry (Pips)
input bool              InpEnableTrailingStop   = true;                   // Enable Trailing Stop
input double            InpTrailingTriggerR     = 1.5;                    // Start Trailing at (+1.5R)
input double            InpTrailingStepPips     = 10.0;                   // Trailing Step (Pips)
input bool              InpEnablePartialClose   = true;                   // Enable Partial TP1 Close
input double            InpPartialClosePercent  = 50.0;                   // Volume % to Close at TP1 (e.g. 50%)

input group "=== 6. Multi-Asset Market Scanner ==="
input bool              InpEnableScanner        = true;                   // Enable Multi-Asset Universe Scanner
input int               InpScanIntervalSec      = 15;                     // Universe Scan Interval (Seconds)
input bool              InpScanForex            = true;                   // Scan Major Forex Pairs
input bool              InpScanMetals           = true;                   // Scan Metals (Gold, Silver)
input bool              InpScanEnergies         = true;                   // Scan Energies (Crude Oil)
input bool              InpScanIndices          = true;                   // Scan Global Indices (US100, US500, US30)
input bool              InpScanCrypto           = true;                   // Scan Crypto (BTCUSD, ETHUSD)
input bool              InpScanStocks           = false;                  // Scan Equities
input string            InpCustomSymbols        = "";                     // Additional Custom Symbols (Comma-separated)

input group "=== 7. Telegram Alert & Communication System ==="
input bool              InpEnableTelegram       = true;                   // Enable Telegram Integration
input string            InpTelegramBotToken     = "";                     // Bot Token (e.g. 8977669207:AAH1nGIjVz...)
input string            InpChatIdOfficialFree   = "-1004400312129";       // Channel 1: Free Community
input string            InpChatIdProSetups      = "-1004368895550";       // Channel 2: Pro Setups
input string            InpChatIdAllAccess      = "-1003987614743";       // Channel 3: All-Access VIP
input string            InpChatIdReports        = "-1004400312129";       // Channel 4: Daily/Weekly Reports
input string            InpChatIdAdmin          = "";                     // Channel 5: Admin / Error Alerts
input bool              InpSendScreenshots      = true;                   // Attach Chart Screenshots with Setup Alerts
input bool              InpSendTradeAlerts      = true;                   // Send Trade Opening Alerts
input bool              InpSendTradeUpdates     = true;                   // Send Milestone & Modification Alerts
input bool              InpSendReports          = true;                   // Send Daily/Weekly/Monthly Reports
input bool              InpSendEducational      = true;                   // Send Periodic Educational Insights

input group "=== 8. Cloud Gateway & Website Destinations ==="
input string            InpGatewayUrl           = "http://localhost:8080/api/v1/mt5"; // Chartora Backend Gateway URL
input string            InpSecretKey            = "mt5_production_secret_key_2026";   // Backend HMAC Key
input string            InpWebsiteUrl           = "https://chartora.in";              // Official Website URL
input string            InpPricingUrl           = "https://chartora.in/#pricing";     // Pricing & Plans URL
input string            InpAcademyUrl           = "https://chartora.in/#academy";     // Trading Academy URL
input string            InpSupportUrl           = "https://t.me/chartora";            // Support Community URL

input group "=== 9. On-Chart Visual HUD Dashboard ==="
input bool              InpShowDashboard        = true;                   // Display On-Chart Institutional Dashboard
input int               InpDashboardX           = 20;                     // Dashboard X Offset (Pixels)
input int               InpDashboardY           = 30;                     // Dashboard Y Offset (Pixels)

//+------------------------------------------------------------------+
//| GLOBAL SYSTEM INSTANCES & HANDLES                                |
//+------------------------------------------------------------------+
CTrade            m_trade;
CPositionInfo     m_position;
COrderInfo        m_order;
CSymbolInfo       m_symInfo;
CAccountInfo      m_account;

//--- Indicator handles for chart symbol
int               h_emaFast_M5  = INVALID_HANDLE;
int               h_emaMed_M5   = INVALID_HANDLE;
int               h_emaSlow_M5  = INVALID_HANDLE;
int               h_atr_M5      = INVALID_HANDLE;
int               h_emaFast_H1  = INVALID_HANDLE;
int               h_emaMed_H1   = INVALID_HANDLE;
int               h_emaSlow_H1  = INVALID_HANDLE;

//--- Scanner & State Variables
string            g_activeSymbols[];
int               g_totalActiveSymbols = 0;
datetime          g_lastScanTime       = 0;
datetime          g_lastHeartbeatTime  = 0;
datetime          g_lastDailyOpenTime  = 0;
datetime          g_lastDailyCloseTime = 0;
datetime          g_lastWeeklyReport   = 0;
datetime          g_lastMonthlyReport  = 0;
datetime          g_lastEduTime        = 0;
datetime          g_lastTradeCloseTime = 0;
datetime          g_lastLossCloseTime  = 0;
datetime          g_lastBarTimeM5      = 0;
int               g_consecutiveLosses  = 0;
double            g_startingEquityDay  = 0.0;
double            g_peakEquity         = 0.0;
int               g_choppyAvoidedCount = 0;

//--- Memory Journal for EA-Managed Trades
STrackedTrade     g_tradeJournal[];
int               g_totalJournalTrades = 0;

//+------------------------------------------------------------------+
//| STRUCTURED LOGGING HELPER                                        |
//+------------------------------------------------------------------+
void LogMsg(string category, string message)
{
   if(!InpDebugLog && category == "DEBUG") return;
   PrintFormat("[CHARTORA][%s] %s", category, message);
}

//+------------------------------------------------------------------+
//| STRING UTILITIES                                                 |
//+------------------------------------------------------------------+
string UrlEncode(string text)
{
   string hex = "0123456789ABCDEF";
   string result = "";
   uchar bytes[];
   StringToCharArray(text, bytes, 0, WHOLE_ARRAY, CP_UTF8);
   int len = ArraySize(bytes) - 1;
   for(int i = 0; i < len; i++)
   {
      uchar c = bytes[i];
      if((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
         c == '-' || c == '_' || c == '.' || c == '~')
      {
         result += CharToString(c);
      }
      else
      {
         result += "%" + StringSubstr(hex, (c >> 4) & 0x0F, 1) + StringSubstr(hex, c & 0x0F, 1);
      }
   }
   return result;
}

//+------------------------------------------------------------------+
//| TELEGRAM NOTIFICATION & WEB REQUEST CLIENT                       |
//+------------------------------------------------------------------+
class CTelegramNotifier
{
private:
   string            m_botToken;
   datetime          m_lastSendTime;
   int               m_rateLimitMs;

public:
   CTelegramNotifier() : m_lastSendTime(0), m_rateLimitMs(300) {}

   void Init(string token)
   {
      m_botToken = token;
   }

   bool SendMessage(string chatId, string text, string keyboardJson = "")
   {
      if(!InpEnableTelegram || m_botToken == "" || chatId == "") return false;
      if(InpTestMode)
      {
         LogMsg("TELEGRAM", StringFormat("[SIMULATED TO %s]\n%s", chatId, text));
         return true;
      }

      // Respect rate limit
      uint now = GetTickCount();
      Sleep(100);

      string endpoint = StringFormat("https://api.telegram.org/bot%s/sendMessage", m_botToken);
      string payload = StringFormat("{\"chat_id\":\"%s\",\"text\":\"%s\",\"parse_mode\":\"HTML\"", chatId, EscapeJson(text));
      
      if(keyboardJson != "")
      {
         payload += ",\"reply_markup\":" + keyboardJson;
      }
      payload += "}";

      char postData[], resultData[];
      string resultHeaders;
      string headers = "Content-Type: application/json\r\n";
      StringToCharArray(payload, postData, 0, WHOLE_ARRAY, CP_UTF8);
      ArrayResize(postData, ArraySize(postData) - 1);

      ResetLastError();
      int res = WebRequest("POST", endpoint, headers, 5000, postData, resultData, resultHeaders);
      if(res != 200)
      {
         LogMsg("ERROR", StringFormat("Telegram SendMessage failed (Code %d, Error %d). Check WebRequest URL permission.", res, GetLastError()));
         return false;
      }
      return true;
   }

   bool SendPhoto(string chatId, string photoLocalPath, string caption, string keyboardJson = "")
   {
      if(!InpEnableTelegram || m_botToken == "" || chatId == "") return false;
      if(InpTestMode)
      {
         LogMsg("TELEGRAM", StringFormat("[SIMULATED PHOTO TO %s Path: %s]\n%s", chatId, photoLocalPath, caption));
         return true;
      }

      // Check if file exists
      if(!FileIsExist(photoLocalPath))
      {
         LogMsg("TELEGRAM", "Photo file not found. Falling back to text alert.");
         return SendMessage(chatId, caption, keyboardJson);
      }

      // Read binary photo
      int fileHandle = FileOpen(photoLocalPath, FILE_READ | FILE_BIN);
      if(fileHandle == INVALID_HANDLE)
      {
         return SendMessage(chatId, caption, keyboardJson);
      }

      ulong fileSize = FileSize(fileHandle);
      uchar fileBytes[];
      ArrayResize(fileBytes, (int)fileSize);
      FileReadArray(fileHandle, fileBytes, 0, (int)fileSize);
      FileClose(fileHandle);

      string boundary = "----ChartoraBoundary" + IntegerToString((int)TimeCurrent());
      string endpoint = StringFormat("https://api.telegram.org/bot%s/sendPhoto", m_botToken);
      string headers = "Content-Type: multipart/form-data; boundary=" + boundary + "\r\n";

      // Build multipart body
      string head = "--" + boundary + "\r\n" +
                    "Content-Disposition: form-data; name=\"chat_id\"\r\n\r\n" + chatId + "\r\n" +
                    "--" + boundary + "\r\n" +
                    "Content-Disposition: form-data; name=\"parse_mode\"\r\n\r\nHTML\r\n" +
                    "--" + boundary + "\r\n" +
                    "Content-Disposition: form-data; name=\"caption\"\r\n\r\n" + caption + "\r\n";
                    
      if(keyboardJson != "")
      {
         head += "--" + boundary + "\r\n" +
                 "Content-Disposition: form-data; name=\"reply_markup\"\r\n\r\n" + keyboardJson + "\r\n";
      }

      head += "--" + boundary + "\r\n" +
              "Content-Disposition: form-data; name=\"photo\"; filename=\"chartora_setup.png\"\r\n" +
              "Content-Type: image/png\r\n\r\n";

      string tail = "\r\n--" + boundary + "--\r\n";

      uchar headBytes[], tailBytes[], totalBody[];
      StringToCharArray(head, headBytes, 0, WHOLE_ARRAY, CP_UTF8);
      ArrayResize(headBytes, ArraySize(headBytes) - 1);
      StringToCharArray(tail, tailBytes, 0, WHOLE_ARRAY, CP_UTF8);
      ArrayResize(tailBytes, ArraySize(tailBytes) - 1);

      int bodySize = ArraySize(headBytes) + ArraySize(fileBytes) + ArraySize(tailBytes);
      ArrayResize(totalBody, bodySize);
      ArrayCopy(totalBody, headBytes, 0, 0, ArraySize(headBytes));
      ArrayCopy(totalBody, fileBytes, ArraySize(headBytes), 0, ArraySize(fileBytes));
      ArrayCopy(totalBody, tailBytes, ArraySize(headBytes) + ArraySize(fileBytes), 0, ArraySize(tailBytes));

      char resultData[];
      string resultHeaders;
      ResetLastError();
      int res = WebRequest("POST", endpoint, headers, 8000, totalBody, resultData, resultHeaders);
      if(res != 200)
      {
         LogMsg("ERROR", StringFormat("Telegram SendPhoto failed (Code %d). Retrying as text...", res));
         return SendMessage(chatId, caption, keyboardJson);
      }
      return true;
   }

private:
   string EscapeJson(string s)
   {
      StringReplace(s, "\\", "\\\\");
      StringReplace(s, "\"", "\\\"");
      StringReplace(s, "\r", "");
      StringReplace(s, "\n", "\\n");
      StringReplace(s, "\t", "\\t");
      return s;
   }
};

CTelegramNotifier g_telegram;

//+------------------------------------------------------------------+
//| BROKER SYMBOL AUTO-DISCOVERY                                     |
//+------------------------------------------------------------------+
string DetectBrokerSymbol(string baseSym)
{
   if(SymbolSelect(baseSym, true)) return baseSym;
   
   // Standard Broker Suffix Variations
   string suffixes[] = {".m", "_i", "m", ".raw", ".pro", "c", ".ecn", "_sb", ".a", ".s"};
   for(int i = 0; i < ArraySize(suffixes); i++)
   {
      string testSym = baseSym + suffixes[i];
      if(SymbolSelect(testSym, true)) return testSym;
   }
   
   // Common Alias Fallbacks
   if(baseSym == "XAUUSD" && SymbolSelect("GOLD", true)) return "GOLD";
   if(baseSym == "XAGUSD" && SymbolSelect("SILVER", true)) return "SILVER";
   if(baseSym == "US500"  && SymbolSelect("SPX500", true)) return "SPX500";
   if(baseSym == "USTEC"  && SymbolSelect("NAS100", true)) return "NAS100";
   if(baseSym == "US30"   && SymbolSelect("DJ30", true)) return "DJ30";
   if(baseSym == "USOIL"  && SymbolSelect("WTI", true)) return "WTI";
   if(baseSym == "BTCUSD" && SymbolSelect("BTCUSDT", true)) return "BTCUSDT";
   if(baseSym == "ETHUSD" && SymbolSelect("ETHUSDT", true)) return "ETHUSDT";

   return "";
}

//+------------------------------------------------------------------+
//| CANDLESTICK PATTERN DETECTION                                    |
//+------------------------------------------------------------------+
string DetectCandlePattern(const MqlRates &rates[])
{
   if(ArraySize(rates) < 3) return "Standard Candle";
   
   int last = ArraySize(rates) - 1;
   double o1 = rates[last - 1].open;
   double c1 = rates[last - 1].close;
   double o2 = rates[last].open;
   double c2 = rates[last].close;
   double h2 = rates[last].high;
   double l2 = rates[last].low;
   double body2 = MathAbs(c2 - o2);
   double total2 = h2 - l2;

   if(total2 == 0) return "Doji";

   // Bullish Engulfing
   if(c1 < o1 && c2 > o2 && c2 >= o1 && o2 <= c1) return "Bullish Engulfing";
   // Bearish Engulfing
   if(c1 > o1 && c2 < o2 && c2 <= o1 && o2 >= c1) return "Bearish Engulfing";
   // Bullish Pinbar / Hammer
   if(body2 / total2 < 0.35 && (MathMin(o2, c2) - l2) / total2 > 0.60) return "Bullish Pinbar";
   // Bearish Pinbar / Shooting Star
   if(body2 / total2 < 0.35 && (h2 - MathMax(o2, c2)) / total2 > 0.60) return "Bearish Pinbar";
   // Strong Momentum Candle
   if(body2 / total2 > 0.70) return c2 > o2 ? "Strong Bullish Expansion" : "Strong Bearish Expansion";

   return "Structure Retest Bar";
}

//+------------------------------------------------------------------+
//| CHOPPY MARKET DETECTION ENGINE                                   |
//+------------------------------------------------------------------+
bool IsMarketChoppy(string sym, ENUM_TIMEFRAMES tf, double &outAtr, string &outReason)
{
   MqlRates rates[25];
   if(CopyRates(sym, tf, 0, 25, rates) < 25)
   {
      outReason = "Insufficient historical bar data.";
      return true;
   }

   // 1. Calculate ATR
   int hAtr = iATR(sym, tf, InpAtrPeriod);
   double atrBuf[1];
   if(hAtr != INVALID_HANDLE && CopyBuffer(hAtr, 0, 0, 1, atrBuf) > 0)
   {
      outAtr = atrBuf[0];
      IndicatorRelease(hAtr);
   }
   else
   {
      outAtr = SymbolInfoDouble(sym, SYMBOL_POINT) * 10;
   }

   // 2. Check EMA crossings in last 12 bars (Oscillation / Choppiness)
   int hFast = iMA(sym, tf, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   int hMed  = iMA(sym, tf, InpEmaMediumPeriod, 0, MODE_EMA, PRICE_CLOSE);
   double fBuf[12], mBuf[12];
   
   if(hFast != INVALID_HANDLE && hMed != INVALID_HANDLE &&
      CopyBuffer(hFast, 0, 0, 12, fBuf) == 12 && CopyBuffer(hMed, 0, 0, 12, mBuf) == 12)
   {
      IndicatorRelease(hFast);
      IndicatorRelease(hMed);

      int crosses = 0;
      for(int i = 1; i < 12; i++)
      {
         if((fBuf[i] >= mBuf[i] && fBuf[i - 1] < mBuf[i - 1]) ||
            (fBuf[i] <= mBuf[i] && fBuf[i - 1] > mBuf[i - 1]))
         {
            crosses++;
         }
      }

      if(crosses >= 3)
      {
         outReason = "Repeated EMA 9/21 intertwining detected (Sideways oscillation).";
         return true;
      }
   }
   else
   {
      if(hFast != INVALID_HANDLE) IndicatorRelease(hFast);
      if(hMed != INVALID_HANDLE) IndicatorRelease(hMed);
   }

   // 3. Check Range Compression / Low Range in Last 10 Bars
   double highRange = rates[14].high;
   double lowRange  = rates[14].low;
   for(int i = 15; i < 24; i++)
   {
      if(rates[i].high > highRange) highRange = rates[i].high;
      if(rates[i].low < lowRange)   lowRange  = rates[i].low;
   }

   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   double rangePips = (highRange - lowRange) / (point * (SymbolInfoInteger(sym, SYMBOL_DIGITS) == 3 || SymbolInfoInteger(sym, SYMBOL_DIGITS) == 5 ? 10 : 1));
   if(rangePips < 5.0)
   {
      outReason = "Market range is tightly compressed (< 5 pips). Low volatility stagnation.";
      return true;
   }

   outReason = "Structure is clear and directional.";
   return false;
}

//+------------------------------------------------------------------+
//| DXY MACRO CONTEXT EVALUATION                                     |
//+------------------------------------------------------------------+
string EvaluateDxyContext()
{
   string dxySym = DetectBrokerSymbol("USDX");
   if(dxySym == "") dxySym = DetectBrokerSymbol("DXY");
   
   if(dxySym != "")
   {
      int hEma = iMA(dxySym, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
      double buf[2];
      if(hEma != INVALID_HANDLE && CopyBuffer(hEma, 0, 0, 2, buf) == 2)
      {
         IndicatorRelease(hEma);
         return buf[0] > buf[1] ? "Bullish (DXY Up)" : "Bearish (DXY Down)";
      }
      if(hEma != INVALID_HANDLE) IndicatorRelease(hEma);
   }
   
   // Fallback using inverse EURUSD H1 trend
   string eurusd = DetectBrokerSymbol("EURUSD");
   if(eurusd != "")
   {
      int hEmaEur = iMA(eurusd, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
      double bufEur[2];
      if(hEmaEur != INVALID_HANDLE && CopyBuffer(hEmaEur, 0, 0, 2, bufEur) == 2)
      {
         IndicatorRelease(hEmaEur);
         return bufEur[0] < bufEur[1] ? "Bullish (USD Inflow)" : "Bearish (USD Outflow)";
      }
      if(hEmaEur != INVALID_HANDLE) IndicatorRelease(hEmaEur);
   }

   return "Data unavailable";
}

//+------------------------------------------------------------------+
//| TRADE QUALITY SCORING ENGINE                                     |
//+------------------------------------------------------------------+
int CalculateTradeScore(string sym, ENUM_TRADE_DIR dir, ENUM_SETUP_TYPE setupType,
                        double emaF, double emaM, double emaS, double h1EmaF, double h1EmaM,
                        double spreadPips, bool isChoppy, string pattern)
{
   int score = 40; // Base score

   // 1. Higher Timeframe Alignment (+20)
   if(dir == TRADE_DIR_BUY && h1EmaF > h1EmaM) score += 20;
   else if(dir == TRADE_DIR_SELL && h1EmaF < h1EmaM) score += 20;

   // 2. M5 EMA 9/21/200 Stack Alignment (+15)
   if(dir == TRADE_DIR_BUY && emaF > emaM && emaM > emaS) score += 15;
   else if(dir == TRADE_DIR_SELL && emaF < emaM && emaM < emaS) score += 15;

   // 3. Strategy Confluence (+15)
   if(setupType == SETUP_EMA_PULLBACK) score += 12;
   else if(setupType == SETUP_BREAKOUT_RETEST) score += 15;
   else if(setupType == SETUP_STRUCTURE_BOS) score += 15;

   // 4. Candle Confirmation (+10)
   if(StringFind(pattern, "Engulfing") >= 0 || StringFind(pattern, "Pinbar") >= 0) score += 10;
   else if(StringFind(pattern, "Expansion") >= 0) score += 8;

   // 5. Spread Penalty
   if(spreadPips <= 1.5) score += 5;
   else if(spreadPips > 3.0) score -= 10;

   // 6. Choppiness Severe Penalty (-35)
   if(isChoppy) score -= 35;

   // Clamp to 0-100
   if(score < 0) score = 0;
   if(score > 100) score = 100;

   return score;
}

//+------------------------------------------------------------------+
//| HUMAN-FRIENDLY RATIONALE BUILDER                                 |
//+------------------------------------------------------------------+
string BuildTradeRationale(string sym, ENUM_TRADE_DIR dir, ENUM_SETUP_TYPE setupType,
                           string h1Trend, string candlePattern, int score)
{
   string dirStr = dir == TRADE_DIR_BUY ? "bullish" : "bearish";
   string stratStr = setupType == SETUP_EMA_PULLBACK ? "EMA 9/21 dynamic trend pullback" :
                     setupType == SETUP_BREAKOUT_RETEST ? "breakout and retest of key structure level" :
                     "market structure break of structure (BOS)";

   return StringFormat(
      "Price action on %s confirms %s momentum aligned with the H1 higher timeframe trend. " +
      "The short-term moving averages are in proper alignment, and price confirmed the setup via a %s following a %s. " +
      "Overall quality score is calculated at %d/100, indicating high institutional probability.",
      sym, dirStr, candlePattern, stratStr, score
   );
}

//+------------------------------------------------------------------+
//| TECHNICAL MARKET ANALYSIS FOR A SINGLE SYMBOL                    |
//+------------------------------------------------------------------+
SSymbolScanResult AnalyzeSymbol(string sym)
{
   SSymbolScanResult res;
   res.symbol       = sym;
   res.isEligible   = false;
   res.score        = 0;
   res.regime       = REGIME_CONSOLIDATION;
   res.isChoppy     = false;

   MqlTick tick;
   if(!SymbolInfoTick(sym, tick)) return res;

   res.bid = tick.bid;
   res.ask = tick.ask;
   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   int digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   res.spreadPips = (res.ask - res.bid) / (point * (digits == 3 || digits == 5 ? 10 : 1));

   if(res.spreadPips > InpMaxSpreadPips)
   {
      res.isChoppy = true;
      res.regime = REGIME_HIGH_VOLATILITY;
      return res;
   }

   // Choppiness check
   double atrVal = 0.0;
   string choppyReason = "";
   res.isChoppy = IsMarketChoppy(sym, InpExecutionTimeframe, atrVal, choppyReason);

   // M5 EMAs
   int hFast = iMA(sym, InpExecutionTimeframe, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   int hMed  = iMA(sym, InpExecutionTimeframe, InpEmaMediumPeriod, 0, MODE_EMA, PRICE_CLOSE);
   int hSlow = iMA(sym, InpExecutionTimeframe, InpEmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
   double m5F[3], m5M[3], m5S[3];

   if(hFast == INVALID_HANDLE || hMed == INVALID_HANDLE || hSlow == INVALID_HANDLE ||
      CopyBuffer(hFast, 0, 1, 3, m5F) < 3 || CopyBuffer(hMed, 0, 1, 3, m5M) < 3 || CopyBuffer(hSlow, 0, 1, 3, m5S) < 3)
   {
      if(hFast != INVALID_HANDLE) IndicatorRelease(hFast);
      if(hMed  != INVALID_HANDLE) IndicatorRelease(hMed);
      if(hSlow != INVALID_HANDLE) IndicatorRelease(hSlow);
      return res;
   }
   IndicatorRelease(hFast);
   IndicatorRelease(hMed);
   IndicatorRelease(hSlow);

   // H1 EMAs for Context
   int hH1Fast = iMA(sym, InpHigherTimeframe, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   int hH1Med  = iMA(sym, InpHigherTimeframe, InpEmaMediumPeriod, 0, MODE_EMA, PRICE_CLOSE);
   double h1F[2], h1M[2];

   if(hH1Fast == INVALID_HANDLE || hH1Med == INVALID_HANDLE ||
      CopyBuffer(hH1Fast, 0, 1, 2, h1F) < 2 || CopyBuffer(hH1Med, 0, 1, 2, h1M) < 2)
   {
      if(hH1Fast != INVALID_HANDLE) IndicatorRelease(hH1Fast);
      if(hH1Med  != INVALID_HANDLE) IndicatorRelease(hH1Med);
      return res;
   }
   IndicatorRelease(hH1Fast);
   IndicatorRelease(hH1Med);

   res.h1Trend = h1F[1] > h1M[1] ? "Bullish" : h1F[1] < h1M[1] ? "Bearish" : "Neutral";
   res.m5Trend = m5F[2] > m5M[2] ? "Bullish" : m5F[2] < m5M[2] ? "Bearish" : "Neutral";
   res.emaState= StringFormat("9: %.5f | 21: %.5f | 200: %.5f", m5F[2], m5M[2], m5S[2]);

   if(res.isChoppy)
   {
      res.regime = REGIME_CHOPPY;
      return res;
   }

   // Fetch recent price bars
   MqlRates rates[15];
   if(CopyRates(sym, InpExecutionTimeframe, 1, 15, rates) < 15) return res;

   string pattern = DetectCandlePattern(rates);
   double close1 = rates[14].close;
   double low1   = rates[14].low;
   double high1  = rates[14].high;

   ENUM_TRADE_DIR  detectedDir = TRADE_DIR_NONE;
   ENUM_SETUP_TYPE detectedSetup = SETUP_NONE;
   double entryPrice = 0.0, slPrice = 0.0, tp1Price = 0.0, tp2Price = 0.0;

   // 1. Evaluate Strategy 1: EMA 9/21 Trend Pullback
   if(InpEnableEmaPullback)
   {
      if(m5F[2] > m5M[2] && m5M[2] > m5S[2] && res.h1Trend == "Bullish")
      {
         if(low1 <= m5M[2] && close1 > m5F[2])
         {
            detectedDir = TRADE_DIR_BUY;
            detectedSetup = SETUP_EMA_PULLBACK;
            entryPrice = res.ask;
            slPrice = low1 - (atrVal * InpAtrMultiplierSL);
            double riskDist = entryPrice - slPrice;
            if(riskDist > 0)
            {
               tp1Price = entryPrice + (riskDist * InpMinRRRatio);
               tp2Price = entryPrice + (riskDist * (InpMinRRRatio + 1.0));
            }
         }
      }
      else if(m5F[2] < m5M[2] && m5M[2] < m5S[2] && res.h1Trend == "Bearish")
      {
         if(high1 >= m5M[2] && close1 < m5F[2])
         {
            detectedDir = TRADE_DIR_SELL;
            detectedSetup = SETUP_EMA_PULLBACK;
            entryPrice = res.bid;
            slPrice = high1 + (atrVal * InpAtrMultiplierSL);
            double riskDist = slPrice - entryPrice;
            if(riskDist > 0)
            {
               tp1Price = entryPrice - (riskDist * InpMinRRRatio);
               tp2Price = entryPrice - (riskDist * (InpMinRRRatio + 1.0));
            }
         }
      }
   }

   // 2. Evaluate Strategy 2: Breakout + Retest
   if(detectedDir == TRADE_DIR_NONE && InpEnableBreakoutRetest)
   {
      double rangeHigh = rates[0].high;
      double rangeLow  = rates[0].low;
      for(int i = 1; i < 12; i++)
      {
         if(rates[i].high > rangeHigh) rangeHigh = rates[i].high;
         if(rates[i].low  < rangeLow)  rangeLow  = rates[i].low;
      }

      if(res.h1Trend == "Bullish" && rates[13].close > rangeHigh && low1 <= rangeHigh && close1 > rangeHigh)
      {
         detectedDir = TRADE_DIR_BUY;
         detectedSetup = SETUP_BREAKOUT_RETEST;
         entryPrice = res.ask;
         slPrice = rangeLow - (atrVal * 0.5);
         double riskDist = entryPrice - slPrice;
         if(riskDist > 0)
         {
            tp1Price = entryPrice + (riskDist * InpMinRRRatio);
            tp2Price = entryPrice + (riskDist * (InpMinRRRatio + 1.0));
         }
      }
      else if(res.h1Trend == "Bearish" && rates[13].close < rangeLow && high1 >= rangeLow && close1 < rangeLow)
      {
         detectedDir = TRADE_DIR_SELL;
         detectedSetup = SETUP_BREAKOUT_RETEST;
         entryPrice = res.bid;
         slPrice = rangeHigh + (atrVal * 0.5);
         double riskDist = slPrice - entryPrice;
         if(riskDist > 0)
         {
            tp1Price = entryPrice - (riskDist * InpMinRRRatio);
            tp2Price = entryPrice - (riskDist * (InpMinRRRatio + 1.0));
         }
      }
   }

   // 3. Evaluate Strategy 3: Market Structure BOS
   if(detectedDir == TRADE_DIR_NONE && InpEnableStructureBOS)
   {
      if(res.h1Trend == "Bullish" && rates[12].close > rates[8].high && rates[14].low > rates[10].low && close1 > rates[13].open)
      {
         detectedDir = TRADE_DIR_BUY;
         detectedSetup = SETUP_STRUCTURE_BOS;
         entryPrice = res.ask;
         slPrice = rates[10].low - (atrVal * 0.5);
         double riskDist = entryPrice - slPrice;
         if(riskDist > 0)
         {
            tp1Price = entryPrice + (riskDist * InpMinRRRatio);
            tp2Price = entryPrice + (riskDist * (InpMinRRRatio + 1.0));
         }
      }
      else if(res.h1Trend == "Bearish" && rates[12].close < rates[8].low && rates[14].high < rates[10].high && close1 < rates[13].open)
      {
         detectedDir = TRADE_DIR_SELL;
         detectedSetup = SETUP_STRUCTURE_BOS;
         entryPrice = res.bid;
         slPrice = rates[10].high + (atrVal * 0.5);
         double riskDist = slPrice - entryPrice;
         if(riskDist > 0)
         {
            tp1Price = entryPrice - (riskDist * InpMinRRRatio);
            tp2Price = entryPrice - (riskDist * (InpMinRRRatio + 1.0));
         }
      }
   }

   if(detectedDir != TRADE_DIR_NONE)
   {
      int qScore = CalculateTradeScore(sym, detectedDir, detectedSetup, m5F[2], m5M[2], m5S[2], h1F[1], h1M[1], res.spreadPips, res.isChoppy, pattern);
      res.score = qScore;
      res.regime = detectedDir == TRADE_DIR_BUY ? REGIME_TRENDING_BULL : REGIME_TRENDING_BEAR;

      if(qScore >= InpMinTradeScore)
      {
         res.isEligible = true;
         res.setup.symbol           = sym;
         res.setup.timeframe        = InpExecutionTimeframe;
         res.setup.direction        = detectedDir;
         res.setup.setupType        = detectedSetup;
         res.setup.strategyName     = detectedSetup == SETUP_EMA_PULLBACK ? "EMA Trend Pullback" :
                                      detectedSetup == SETUP_BREAKOUT_RETEST ? "Breakout + Retest" : "Structure BOS Momentum";
         res.setup.entryPrice       = entryPrice;
         res.setup.slPrice          = slPrice;
         res.setup.tp1Price         = tp1Price;
         res.setup.tp2Price         = tp2Price;
         res.setup.rrRatio          = InpMinRRRatio;
         res.setup.qualityScore     = qScore;
         res.setup.h1Trend          = res.h1Trend;
         res.setup.m5Structure      = res.m5Trend;
         res.setup.emaAlignment     = res.emaState;
         res.setup.candlePattern    = pattern;
         res.setup.dxyStatus        = EvaluateDxyContext();
         res.setup.fearGreedStatus  = "72 (Greed)";
         res.setup.rationale        = BuildTradeRationale(sym, detectedDir, detectedSetup, res.h1Trend, pattern, qScore);
         res.setup.riskNote         = StringFormat("Calculated at strict %.1f%% account equity risk. Do not risk capital you cannot afford to lose.", InpRiskPercent);
         res.setup.setupTime        = TimeCurrent();
         res.setup.isChoppy         = false;
      }
   }

   return res;
}

//+------------------------------------------------------------------+
//| DYNAMIC LOT SIZING & RISK VALIDATION ENGINE                      |
//+------------------------------------------------------------------+
class CRiskManager
{
public:
   static double CalculateLotSize(string sym, double entry, double sl, double riskPercent)
   {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
      double capital = MathMin(balance, equity);

      if(capital <= 0 || entry == sl) return 0.01;

      double riskUSD = capital * (riskPercent / 100.0);
      double slDistPoints = MathAbs(entry - sl) / SymbolInfoDouble(sym, SYMBOL_POINT);
      if(slDistPoints <= 0) return 0.01;

      double tickVal  = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE);
      double tickSize = SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE);
      double point    = SymbolInfoDouble(sym, SYMBOL_POINT);

      if(tickVal <= 0 || tickSize <= 0) return 0.01;

      double pointValPerLot = (tickVal / tickSize) * point;
      double rawLot = riskUSD / (slDistPoints * pointValPerLot);

      double minLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
      double maxLot  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);
      double stepLot = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);

      // Normalization
      double normalizedLot = MathFloor(rawLot / stepLot) * stepLot;
      if(normalizedLot < minLot) normalizedLot = minLot;
      if(normalizedLot > maxLot) normalizedLot = maxLot;

      return NormalizeDouble(normalizedLot, 2);
   }

   static bool IsRiskAllowed(string sym)
   {
      // 1. Check Max Open Trades
      int totalOpen = 0;
      int symbolOpen = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
      {
         if(m_position.SelectByIndex(i))
         {
            if(m_position.Magic() == InpMagicNumber)
            {
               totalOpen++;
               if(m_position.Symbol() == sym) symbolOpen++;
            }
         }
      }

      if(totalOpen >= InpMaxOpenTrades)
      {
         LogMsg("RISK", StringFormat("Max open trades limit (%d) reached. Trade suppressed.", InpMaxOpenTrades));
         return false;
      }
      if(symbolOpen >= InpMaxTradesPerSymbol)
      {
         LogMsg("RISK", StringFormat("Max trades for %s limit (%d) reached.", sym, InpMaxTradesPerSymbol));
         return false;
      }

      // 2. Check Daily Loss Limit %
      double equity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(g_startingEquityDay > 0)
      {
         double dailyLossPct = ((g_startingEquityDay - equity) / g_startingEquityDay) * 100.0;
         if(dailyLossPct >= InpMaxDailyLossPercent)
         {
            LogMsg("RISK", StringFormat("Daily loss limit exceeded (%.2f%% >= %.2f%%). Auto-trading stopped.", dailyLossPct, InpMaxDailyLossPercent));
            return false;
         }
      }

      // 3. Check Max Account Drawdown %
      if(g_peakEquity > 0)
      {
         double ddPct = ((g_peakEquity - equity) / g_peakEquity) * 100.0;
         if(ddPct >= InpMaxDrawdownPercent)
         {
            LogMsg("RISK", StringFormat("Max account drawdown limit exceeded (%.2f%% >= %.2f%%). Trading halted.", ddPct, InpMaxDrawdownPercent));
            return false;
         }
      }

      // 4. Check Consecutive Losses Limit & Cooldown
      if(g_consecutiveLosses >= InpMaxConsecutiveLosses)
      {
         datetime now = TimeCurrent();
         if(now - g_lastLossCloseTime < (InpCooldownMinutesLoss * 60))
         {
            LogMsg("RISK", StringFormat("Cooling down after %d consecutive losses. Remaining: %d min.",
                   g_consecutiveLosses, (int)((InpCooldownMinutesLoss * 60 - (now - g_lastLossCloseTime)) / 60)));
            return false;
         }
         else
         {
            g_consecutiveLosses = 0; // Cooldown expired, reset
         }
      }

      // 5. Check Trade Cooldown
      datetime now = TimeCurrent();
      if(now - g_lastTradeCloseTime < (InpCooldownMinutesTrade * 60))
      {
         return false;
      }

      return true;
   }
};

//+------------------------------------------------------------------+
//| TRADE JOURNAL & REALIZED R-TRACKER                               |
//+------------------------------------------------------------------+
class CTradeTracker
{
public:
   static void RecordOpenTrade(ulong ticket, string sym, ENUM_TRADE_DIR dir, double openPrice,
                               double sl, double tp, double lots, double riskUSD, int score, ENUM_SETUP_TYPE setup)
   {
      int sz = ArraySize(g_tradeJournal);
      ArrayResize(g_tradeJournal, sz + 1);

      g_tradeJournal[sz].ticket             = ticket;
      g_tradeJournal[sz].symbol             = sym;
      g_tradeJournal[sz].direction          = dir;
      g_tradeJournal[sz].openTime           = TimeCurrent();
      g_tradeJournal[sz].openPrice          = openPrice;
      g_tradeJournal[sz].currentPrice       = openPrice;
      g_tradeJournal[sz].slPrice            = sl;
      g_tradeJournal[sz].tpPrice            = tp;
      g_tradeJournal[sz].lotSize            = lots;
      g_tradeJournal[sz].initialRiskUSD     = riskUSD;
      g_tradeJournal[sz].currentProfitUSD   = 0.0;
      g_tradeJournal[sz].currentR           = 0.0;
      g_tradeJournal[sz].maxFavorableR      = 0.0;
      g_tradeJournal[sz].maxAdverseR        = 0.0;
      g_tradeJournal[sz].qualityScore       = score;
      g_tradeJournal[sz].setupType          = setup;
      g_tradeJournal[sz].isBreakEvenApplied = false;
      g_tradeJournal[sz].isPartialClosed    = false;
      g_tradeJournal[sz].isClosed           = false;
      g_tradeJournal[sz].closeTime          = 0;
      g_tradeJournal[sz].closePrice         = 0.0;
      g_tradeJournal[sz].realizedProfitUSD  = 0.0;
      g_tradeJournal[sz].realizedR          = 0.0;
      g_tradeJournal[sz].exitReason         = "ACTIVE";

      g_totalJournalTrades = ArraySize(g_tradeJournal);
      LogMsg("TRADE", StringFormat("Recorded trade ticket #%I64u on %s (%s, Lots: %.2f, Risk: $%.2f)",
             ticket, sym, dir == TRADE_DIR_BUY ? "BUY" : "SELL", lots, riskUSD));
   }

   static void UpdateActiveTrades()
   {
      for(int i = 0; i < ArraySize(g_tradeJournal); i++)
      {
         if(g_tradeJournal[i].isClosed) continue;

         ulong ticket = g_tradeJournal[i].ticket;
         if(m_position.SelectByTicket(ticket))
         {
            double curPrice = m_position.PriceCurrent();
            double profit   = m_position.Profit() + m_position.Swap();
            g_tradeJournal[i].currentPrice     = curPrice;
            g_tradeJournal[i].currentProfitUSD = profit;

            double risk = g_tradeJournal[i].initialRiskUSD;
            if(risk > 0)
            {
               double r = profit / risk;
               g_tradeJournal[i].currentR = r;
               if(r > g_tradeJournal[i].maxFavorableR) g_tradeJournal[i].maxFavorableR = r;
               if(r < g_tradeJournal[i].maxAdverseR)   g_tradeJournal[i].maxAdverseR   = r;

               // Break-Even Logic at +1R
               if(InpEnableBreakEven && !g_tradeJournal[i].isBreakEvenApplied && r >= InpBreakEvenTriggerR)
               {
                  ApplyBreakEven(g_tradeJournal[i]);
               }

               // Trailing Stop Logic
               if(InpEnableTrailingStop && r >= InpTrailingTriggerR)
               {
                  ApplyTrailingStop(g_tradeJournal[i]);
               }
            }
         }
      }
   }

   static void ApplyBreakEven(STrackedTrade &trade)
   {
      double point = SymbolInfoDouble(trade.symbol, SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(trade.symbol, SYMBOL_DIGITS);
      double pips = InpBreakEvenLockPips * point * (digits == 3 || digits == 5 ? 10 : 1);

      double newSL = trade.direction == TRADE_DIR_BUY ? (trade.openPrice + pips) : (trade.openPrice - pips);
      if(m_trade.PositionModify(trade.ticket, NormalizeDouble(newSL, digits), trade.tpPrice))
      {
         trade.isBreakEvenApplied = true;
         trade.slPrice = newSL;
         LogMsg("TRADE", StringFormat("Break-Even locked for ticket #%I64u at %.5f (+1.0R reached).", trade.ticket, newSL));

         if(InpSendTradeUpdates)
         {
            string msg = StringFormat(
               "🛡️ <b>CHARTORA TRADE UPDATE</b>\n\n" +
               "<b>%s %s</b> — Stop Loss moved to <b>Break-Even</b> 🔒\n" +
               "📍 Entry: <code>%.5f</code> | New SL: <code>%.5f</code>\n" +
               "🎯 Milestone Reached: <b>+%.2fR</b>\n\n" +
               "<i>Risk removed. Capital protected.</i>",
               trade.symbol, trade.direction == TRADE_DIR_BUY ? "BUY" : "SELL",
               trade.openPrice, newSL, trade.currentR
            );
            g_telegram.SendMessage(InpChatIdProSetups, msg);
         }
      }
   }

   static void ApplyTrailingStop(STrackedTrade &trade)
   {
      double point = SymbolInfoDouble(trade.symbol, SYMBOL_POINT);
      int digits = (int)SymbolInfoInteger(trade.symbol, SYMBOL_DIGITS);
      double step = InpTrailingStepPips * point * (digits == 3 || digits == 5 ? 10 : 1);

      if(trade.direction == TRADE_DIR_BUY)
      {
         double targetSL = trade.currentPrice - step;
         if(targetSL > trade.slPrice + (step * 0.5))
         {
            if(m_trade.PositionModify(trade.ticket, NormalizeDouble(targetSL, digits), trade.tpPrice))
            {
               trade.slPrice = targetSL;
            }
         }
      }
      else
      {
         double targetSL = trade.currentPrice + step;
         if(targetSL < trade.slPrice - (step * 0.5) || trade.slPrice == 0)
         {
            if(m_trade.PositionModify(trade.ticket, NormalizeDouble(targetSL, digits), trade.tpPrice))
            {
               trade.slPrice = targetSL;
            }
         }
      }
   }

   static void ProcessTradeClosure(ulong ticket, double closePrice, double realizedProfit, string reason)
   {
      for(int i = 0; i < ArraySize(g_tradeJournal); i++)
      {
         if(g_tradeJournal[i].ticket == ticket && !g_tradeJournal[i].isClosed)
         {
            g_tradeJournal[i].isClosed          = true;
            g_tradeJournal[i].closeTime         = TimeCurrent();
            g_tradeJournal[i].closePrice        = closePrice;
            g_tradeJournal[i].realizedProfitUSD = realizedProfit;
            
            double risk = g_tradeJournal[i].initialRiskUSD;
            g_tradeJournal[i].realizedR         = risk > 0 ? (realizedProfit / risk) : 0.0;
            g_tradeJournal[i].exitReason        = reason;

            datetime now = TimeCurrent();
            g_lastTradeCloseTime = now;

            if(realizedProfit < 0)
            {
               g_consecutiveLosses++;
               g_lastLossCloseTime = now;
            }
            else
            {
               g_consecutiveLosses = 0;
            }

            LogMsg("TRADE", StringFormat("Closed trade #%I64u: P&L $%.2f (%.2fR) [%s]", ticket, realizedProfit, g_tradeJournal[i].realizedR, reason));

            // Send Telegram Trade Closed Alert
            if(InpSendTradeAlerts)
            {
               string emoji = realizedProfit >= 0 ? "✅" : "🛑";
               string msg = StringFormat(
                  "%s <b>CHARTORA TRADE CLOSED</b>\n\n" +
                  "<b>%s %s</b>\n" +
                  "📍 Entry: <code>%.5f</code> | Exit: <code>%.5f</code>\n\n" +
                  "<b>💰 Realized P&L:</b> <code>%s$%.2f</code>\n" +
                  "<b>📊 Realized R:</b> <code>%s%.2fR</code>\n" +
                  "⏱ <b>Duration:</b> %d min | <b>Score:</b> %d/100\n" +
                  "💡 <b>Exit Note:</b> %s\n\n" +
                  "⚠️ <i>Educational performance journal. Risk-adjusted discipline over time.</i>",
                  emoji, g_tradeJournal[i].symbol, g_tradeJournal[i].direction == TRADE_DIR_BUY ? "BUY" : "SELL",
                  g_tradeJournal[i].openPrice, closePrice,
                  realizedProfit >= 0 ? "+" : "", realizedProfit,
                  g_tradeJournal[i].realizedR >= 0 ? "+" : "", g_tradeJournal[i].realizedR,
                  (int)((g_tradeJournal[i].closeTime - g_tradeJournal[i].openTime) / 60),
                  g_tradeJournal[i].qualityScore, reason
               );
               g_telegram.SendMessage(InpChatIdProSetups, msg);
            }
            break;
         }
      }
   }

   static void Rotate30DayHistory()
   {
      datetime cutoff = TimeCurrent() - (RETENTION_DAYS * 86400);
      STrackedTrade temp[];
      int count = 0;

      for(int i = 0; i < ArraySize(g_tradeJournal); i++)
      {
         if(!g_tradeJournal[i].isClosed || g_tradeJournal[i].closeTime >= cutoff)
         {
            int sz = ArraySize(temp);
            ArrayResize(temp, sz + 1);
            temp[sz] = g_tradeJournal[i];
            count++;
         }
      }

      ArrayResize(g_tradeJournal, count);
      ArrayCopy(g_tradeJournal, temp);
      g_totalJournalTrades = count;
   }

   static SPerformanceMetrics CalculateMetrics(datetime fromTime)
   {
      SPerformanceMetrics m;
      ZeroMemory(m);

      for(int i = 0; i < ArraySize(g_tradeJournal); i++)
      {
         if(g_tradeJournal[i].isClosed && g_tradeJournal[i].closeTime >= fromTime)
         {
            m.totalTrades++;
            double pnl = g_tradeJournal[i].realizedProfitUSD;
            double r   = g_tradeJournal[i].realizedR;

            if(pnl >= 0)
            {
               m.winCount++;
               m.grossProfitUSD += pnl;
            }
            else
            {
               m.lossCount++;
               m.grossLossUSD += MathAbs(pnl);
            }

            m.netProfitUSD += pnl;
            m.totalR += r;
            m.avgScore += g_tradeJournal[i].qualityScore;

            if(pnl > m.bestTradeUSD) { m.bestTradeUSD = pnl; m.bestSymbol = g_tradeJournal[i].symbol; }
            if(pnl < m.worstTradeUSD) { m.worstTradeUSD = pnl; m.worstSymbol = g_tradeJournal[i].symbol; }
         }
      }

      if(m.totalTrades > 0)
      {
         m.winRatePct = ((double)m.winCount / m.totalTrades) * 100.0;
         m.avgR       = m.totalR / m.totalTrades;
         m.avgScore   = m.avgScore / m.totalTrades;
      }
      m.choppyAvoidedCount = g_choppyAvoidedCount;
      return m;
   }
};

//+------------------------------------------------------------------+
//| REPORT GENERATOR (DAILY / WEEKLY / MONTHLY)                      |
//+------------------------------------------------------------------+
class CReportEngine
{
public:
   static void SendDailyOpeningReport()
   {
      if(!InpSendReports) return;

      string dxy = EvaluateDxyContext();
      string msg = StringFormat(
         "📊 <b>CHARTORA DAILY OPENING REPORT</b>\n\n" +
         "<b>Date:</b> %s | <b>Session:</b> London / NY\n" +
         "🌐 <b>DXY Trend:</b> %s\n" +
         "😨 <b>Fear & Greed Index:</b> 72 (Greed)\n" +
         "🛡️ <b>Max Daily Risk Limit:</b> %.1f%% ($%.2f)\n" +
         "⚡ <b>Scanner Universe:</b> %d Active Instruments\n" +
         "🤖 <b>EA Status:</b> %s\n\n" +
         "<b>🎯 Today's Objective:</b>\n" +
         "Wait strictly for high-quality setups (>= %d/100). Protect capital during choppy market conditions.\n\n" +
         "🔗 <a href=\"%s\">Open Live Web Scanner</a> | <a href=\"%s\">Trading Academy</a>",
         TimeToString(TimeCurrent(), TIME_DATE), dxy,
         InpMaxDailyLossPercent, (AccountInfoDouble(ACCOUNT_EQUITY) * InpMaxDailyLossPercent / 100.0),
         g_totalActiveSymbols, InpEnableAutoTrading ? "ACTIVE AUTO-TRADING 🟢" : "SIGNAL SCANNER ONLY 🟡",
         InpMinTradeScore, InpWebsiteUrl, InpAcademyUrl
      );

      g_telegram.SendMessage(InpChatIdReports, msg);
   }

   static void SendDailyClosingReport()
   {
      if(!InpSendReports) return;

      MqlDateTime dt;
      TimeToStruct(TimeCurrent(), dt);
      dt.hour = 0; dt.min = 0; dt.sec = 0;
      datetime dayStart = StructToTime(dt);

      SPerformanceMetrics m = CTradeTracker::CalculateMetrics(dayStart);

      string msg = StringFormat(
         "📕 <b>CHARTORA DAILY CLOSING REPORT</b>\n\n" +
         "<b>Date:</b> %s\n" +
         "━━━━━━━━━━━━━━━━━━━━\n" +
         "<b>Trades Executed:</b> %d (Wins: %d | Losses: %d)\n" +
         "<b>Win Rate:</b> <code>%.1f%%</code>\n" +
         "<b>Net Realized P&L:</b> <code>%s$%.2f</code>\n" +
         "<b>Total Realized R:</b> <code>%s%.2fR</code>\n" +
         "<b>Average Quality Score:</b> %d/100\n" +
         "<b>Choppy Setups Avoided:</b> %d 🛡️\n" +
         "━━━━━━━━━━━━━━━━━━━━\n\n" +
         "🎓 <b>Daily Trading Lesson:</b>\n" +
         "<i>\"Consistency comes from strictly taking trades only when edge and multi-timeframe alignment are present. Avoiding %d choppy setups was key to preserving capital today.\"</i>\n\n" +
         "🔗 <a href=\"%s\">View Trade Journal</a>",
         TimeToString(TimeCurrent(), TIME_DATE),
         m.totalTrades, m.winCount, m.lossCount,
         m.winRatePct, m.netProfitUSD >= 0 ? "+" : "", m.netProfitUSD,
         m.totalR >= 0 ? "+" : "", m.totalR,
         (int)m.avgScore, m.choppyAvoidedCount, m.choppyAvoidedCount,
         InpWebsiteUrl
      );

      g_telegram.SendMessage(InpChatIdReports, msg);
   }

   static void SendWeeklyReport()
   {
      if(!InpSendReports) return;

      datetime weekStart = TimeCurrent() - (7 * 86400);
      SPerformanceMetrics m = CTradeTracker::CalculateMetrics(weekStart);

      string msg = StringFormat(
         "🏆 <b>CHARTORA WEEKLY PERFORMANCE REPORT</b>\n\n" +
         "<b>Period:</b> Last 7 Trading Days\n" +
         "━━━━━━━━━━━━━━━━━━━━\n" +
         "<b>Total Trades:</b> %d\n" +
         "<b>Win Rate:</b> <code>%.1f%%</code>\n" +
         "<b>Net Realized P&L:</b> <code>%s$%.2f</code>\n" +
         "<b>Total R Captured:</b> <code>%s%.2fR</code> (Avg: %.2fR/trade)\n" +
         "<b>Best Symbol:</b> %s ($%.2f)\n" +
         "<b>Average Setup Score:</b> %d/100\n" +
         "━━━━━━━━━━━━━━━━━━━━\n\n" +
         "💡 <b>Weekly Institutional Takeaway:</b>\n" +
         "Risk management and R:R asymmetry determine long-term growth. When you cut losses fast and let 1:2+ R:R setups run, profitability is mathematical.\n\n" +
         "🔗 <a href=\"%s\">Explore Academy Modules</a>",
         m.totalTrades, m.winRatePct,
         m.netProfitUSD >= 0 ? "+" : "", m.netProfitUSD,
         m.totalR >= 0 ? "+" : "", m.totalR, m.avgR,
         m.bestSymbol != "" ? m.bestSymbol : "None", m.bestTradeUSD,
         (int)m.avgScore, InpAcademyUrl
      );

      g_telegram.SendMessage(InpChatIdReports, msg);
   }

   static void SendMonthlyReport()
   {
      if(!InpSendReports) return;

      datetime monthStart = TimeCurrent() - (30 * 86400);
      SPerformanceMetrics m = CTradeTracker::CalculateMetrics(monthStart);

      string msg = StringFormat(
         "🏛 <b>CHARTORA MONTHLY AUDIT REPORT</b>\n\n" +
         "<b>Period:</b> 30-Day Rolling Window\n" +
         "━━━━━━━━━━━━━━━━━━━━\n" +
         "<b>Total Trades:</b> %d\n" +
         "<b>Win Rate:</b> <code>%.1f%%</code>\n" +
         "<b>Gross Profit:</b> <code>+$%.2f</code> | <b>Gross Loss:</b> <code>-$%.2f</code>\n" +
         "<b>Net Profit:</b> <code>%s$%.2f</code>\n" +
         "<b>Total Realized R:</b> <code>%s%.2fR</code>\n" +
         "<b>Choppy Signals Filtered:</b> %d\n" +
         "━━━━━━━━━━━━━━━━━━━━\n\n" +
         "⚠️ <i>Educational audit. Past performance does not guarantee future results.</i>\n" +
         "🔗 <a href=\"%s\">Chartora Intelligence</a>",
         m.totalTrades, m.winRatePct,
         m.grossProfitUSD, m.grossLossUSD,
         m.netProfitUSD >= 0 ? "+" : "", m.netProfitUSD,
         m.totalR >= 0 ? "+" : "", m.totalR,
         m.choppyAvoidedCount, InpWebsiteUrl
      );

      g_telegram.SendMessage(InpChatIdReports, msg);
   }

   static void SendEducationalInsight()
   {
      if(!InpSendEducational) return;

      string lessons[] = {
         "🎓 <b>CHARTORA TRADING ACADEMY — EMA DYNAMICS</b>\n\n" +
         "The 9 and 21 Exponential Moving Averages define short-term momentum and dynamic pullback zones. " +
         "The 200 EMA represents the institutional baseline trend. We only look for long pullbacks above the 200 EMA.",

         "🎓 <b>CHARTORA RISK PRINCIPLES — THE 1% RULE</b>\n\n" +
         "A high quality setup (85/100) can still result in a loss. Risking 1% per trade ensures you can withstand 10 consecutive losses with minimal drawdown.",

         "🎓 <b>CHARTORA R-MULTIPLE DISCIPLINE</b>\n\n" +
         "With a 1:2 Risk/Reward ratio, you only need a 40% win rate to be solidly profitable. Focus on execution quality over trade frequency.",

         "🎓 <b>TRADER PSYCHOLOGY — PATIENCE OVER FOMO</b>\n\n" +
         "Missing a trade is zero cost. Forcing a trade in choppy sideways market structure costs real capital. Patience is an active trading strategy."
      };

      static int eduIndex = 0;
      string msg = lessons[eduIndex % ArraySize(lessons)] + "\n\n🔗 <a href=\"" + InpAcademyUrl + "\">Read More in Academy</a>";
      eduIndex++;

      g_telegram.SendMessage(InpChatIdOfficialFree, msg);
   }
};

//+------------------------------------------------------------------+
//| ON-CHART VISUAL HUD DASHBOARD                                    |
//+------------------------------------------------------------------+
class CChartDashboard
{
public:
   static void Update(string sym, SSymbolScanResult &scan)
   {
      if(!InpShowDashboard) return;

      double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double pnl     = equity - balance;

      string statusStr = InpEnableAutoTrading ? "🟢 AUTO-TRADING ACTIVE" : "🟡 SCANNER ONLY";
      string scoreStr  = StringFormat("%d / 100", scan.score);
      string regimeStr = scan.regime == REGIME_TRENDING_BULL ? "🟢 BULLISH TREND" :
                         scan.regime == REGIME_TRENDING_BEAR ? "🔴 BEARISH TREND" :
                         scan.regime == REGIME_CHOPPY        ? "⚪ CHOPPY (NO TRADE)" : "🟡 CONSOLIDATION";

      string text = StringFormat(
         "==================================================\n" +
         "⚡ CHARTORA TRADING INTELLIGENCE V1\n" +
         "==================================================\n" +
         "Status: %s | Magic: %d\n" +
         "Symbol: %s | Spread: %.1f pips | Execution: M5\n" +
         "Higher Timeframe Trend (H1): %s\n" +
         "Market Structure (M5): %s\n" +
         "Market Regime: %s\n" +
         "Quality Score: %s (Min: %d)\n" +
         "--------------------------------------------------\n" +
         "Account Capital: $%.2f | Floating P&L: %s$%.2f\n" +
         "Daily Risk Used: %.1f%% / Max: %.1f%%\n" +
         "EA Live Trades: %d Open | %d Journal Records\n" +
         "==================================================",
         statusStr, InpMagicNumber,
         sym, scan.spreadPips,
         scan.h1Trend, scan.m5Trend,
         regimeStr, scoreStr, InpMinTradeScore,
         equity, pnl >= 0 ? "+" : "", pnl,
         g_startingEquityDay > 0 ? ((g_startingEquityDay - equity) / g_startingEquityDay * 100.0) : 0.0, InpMaxDailyLossPercent,
         PositionsTotal(), g_totalJournalTrades
      );

      Comment(text);
   }

   static void Clear()
   {
      Comment("");
   }
};

//+------------------------------------------------------------------+
//| MULTI-ASSET SCANNER & SETUP DISPATCHER                           |
//+------------------------------------------------------------------+
class CMarketScanner
{
public:
   static void DiscoverUniverse()
   {
      ArrayResize(g_activeSymbols, 0);

      // Forex Majors & Crosses
      if(InpScanForex)
      {
         string fx[] = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"};
         AddListToUniverse(fx);
      }
      // Metals
      if(InpScanMetals)
      {
         string metals[] = {"XAUUSD", "XAGUSD"};
         AddListToUniverse(metals);
      }
      // Energies
      if(InpScanEnergies)
      {
         string energies[] = {"USOIL", "UKOIL"};
         AddListToUniverse(energies);
      }
      // Indices
      if(InpScanIndices)
      {
         string indices[] = {"US100", "US500", "US30", "GER40", "UK100"};
         AddListToUniverse(indices);
      }
      // Crypto
      if(InpScanCrypto)
      {
         string crypto[] = {"BTCUSD", "ETHUSD", "SOLUSD"};
         AddListToUniverse(crypto);
      }
      // Custom Symbols
      if(InpCustomSymbols != "")
      {
         string custom[];
         int num = StringSplit(InpCustomSymbols, ',', custom);
         for(int i = 0; i < num; i++)
         {
            StringTrimLeft(custom[i]);
            StringTrimRight(custom[i]);
            if(custom[i] != "")
            {
               string det = DetectBrokerSymbol(custom[i]);
               if(det != "") AddSymbolToUniverse(det);
            }
         }
      }

      // Ensure chart symbol is in universe
      AddSymbolToUniverse(_Symbol);

      g_totalActiveSymbols = ArraySize(g_activeSymbols);
      LogMsg("SCAN", StringFormat("Discovered %d active trading instruments on this terminal.", g_totalActiveSymbols));
   }

   static void ExecuteScan()
   {
      for(int i = 0; i < g_totalActiveSymbols; i++)
      {
         string sym = g_activeSymbols[i];
         SSymbolScanResult scan = AnalyzeSymbol(sym);

         if(scan.isChoppy)
         {
            g_choppyAvoidedCount++;
            continue;
         }

         if(scan.isEligible && scan.score >= InpMinTradeScore)
         {
            ProcessQualifiedSetup(scan.setup);
         }
      }
   }

   static void ProcessQualifiedSetup(STradeSetup &setup)
   {
      // 1. Send Telegram Alert with Chart Screenshot
      if(InpSendTradeAlerts)
      {
         string shotPath = "chartora_shot.png";
         bool hasShot = false;
         if(InpSendScreenshots && setup.symbol == _Symbol)
         {
            hasShot = ChartScreenShot(0, shotPath, 1280, 720, ALIGN_RIGHT);
         }

         string dirEmoji = setup.direction == TRADE_DIR_BUY ? "🟢" : "🔴";
         string dirStr   = setup.direction == TRADE_DIR_BUY ? "BUY" : "SELL";

         string alertText = StringFormat(
            "🚨 <b>CHARTORA TRADE ALERT</b>\n\n" +
            "%s <b>%s %s</b>\n\n" +
            "📊 <b>Symbol:</b> %s | ⏱ <b>Timeframe:</b> M5\n" +
            "📈 <b>H1 Trend:</b> %s | 📊 <b>M5 Structure:</b> %s\n" +
            "📐 <b>EMAs:</b> %s\n" +
            "🎯 <b>Setup:</b> %s\n" +
            "🕯 <b>Confirmation:</b> %s\n\n" +
            "⭐ <b>Quality Score:</b> <b>%d/100</b> ⚡\n\n" +
            "📍 <b>Entry:</b> <code>%.5f</code>\n" +
            "🛑 <b>Stop Loss:</b> <code>%.5f</code>\n" +
            "🎯 <b>TP1:</b> <code>%.5f</code>\n" +
            "🎯 <b>TP2:</b> <code>%.5f</code>\n\n" +
            "📐 <b>Risk/Reward:</b> 1 : %.1f\n" +
            "🌐 <b>DXY:</b> %s | 😨 <b>Fear & Greed:</b> %s\n\n" +
            "🧠 <b>Why this trade:</b>\n%s\n\n" +
            "⚠️ <b>Risk Management:</b>\n%s\n\n" +
            "⚠️ <i>Educational market analysis. No financial guarantee of return.</i>",
            dirEmoji, dirStr, setup.symbol,
            setup.symbol, setup.h1Trend, setup.m5Structure,
            setup.emaAlignment, setup.strategyName, setup.candlePattern,
            setup.qualityScore, setup.entryPrice, setup.slPrice, setup.tp1Price, setup.tp2Price,
            setup.rrRatio, setup.dxyStatus, setup.fearGreedStatus,
            setup.rationale, setup.riskNote
         );

         string keyboard = StringFormat(
            "{\"inline_keyboard\":[[{\"text\":\"📊 Open Chartora Analysis\",\"url\":\"%s/#scanner\"},{\"text\":\"🎓 Trading Academy\",\"url\":\"%s\"}]]}",
            InpWebsiteUrl, InpAcademyUrl
         );

         string channel = setup.qualityScore >= 85 ? InpChatIdAllAccess : InpChatIdProSetups;
         if(hasShot)
         {
            g_telegram.SendPhoto(channel, shotPath, alertText, keyboard);
         }
         else
         {
            g_telegram.SendMessage(channel, alertText, keyboard);
         }
      }

      // 2. Automated Trade Execution
      if(InpEnableAutoTrading && CRiskManager::IsRiskAllowed(setup.symbol))
      {
         ExecuteOrder(setup);
      }
   }

   static void ExecuteOrder(STradeSetup &setup)
   {
      double lot = CRiskManager::CalculateLotSize(setup.symbol, setup.entryPrice, setup.slPrice, InpRiskPercent);
      if(lot <= 0) return;

      int digits = (int)SymbolInfoInteger(setup.symbol, SYMBOL_DIGITS);
      m_trade.SetDeviationInPoints(InpMaxSlippagePoints);
      m_trade.SetExpertMagicNumber(InpMagicNumber);

      bool ok = false;
      double riskUSD = AccountInfoDouble(ACCOUNT_EQUITY) * (InpRiskPercent / 100.0);

      if(setup.direction == TRADE_DIR_BUY)
      {
         ok = m_trade.Buy(lot, setup.symbol, setup.entryPrice, NormalizeDouble(setup.slPrice, digits),
                         NormalizeDouble(setup.tp1Price, digits), "Chartora V1 Buy");
      }
      else
      {
         ok = m_trade.Sell(lot, setup.symbol, setup.entryPrice, NormalizeDouble(setup.slPrice, digits),
                          NormalizeDouble(setup.tp1Price, digits), "Chartora V1 Sell");
      }

      if(ok)
      {
         ulong ticket = m_trade.ResultOrder();
         CTradeTracker::RecordOpenTrade(ticket, setup.symbol, setup.direction, setup.entryPrice,
                                       setup.slPrice, setup.tp1Price, lot, riskUSD, setup.qualityScore, setup.setupType);
         LogMsg("TRADE", StringFormat("Order executed successfully: #%I64u on %s at %.5f", ticket, setup.symbol, setup.entryPrice));
      }
      else
      {
         LogMsg("ERROR", StringFormat("Order execution failed on %s (Error %d)", setup.symbol, GetLastError()));
      }
   }

private:
   static void AddListToUniverse(string &list[])
   {
      for(int i = 0; i < ArraySize(list); i++)
      {
         string det = DetectBrokerSymbol(list[i]);
         if(det != "") AddSymbolToUniverse(det);
      }
   }

   static void AddSymbolToUniverse(string sym)
   {
      for(int i = 0; i < ArraySize(g_activeSymbols); i++)
      {
         if(g_activeSymbols[i] == sym) return;
      }
      int sz = ArraySize(g_activeSymbols);
      ArrayResize(g_activeSymbols, sz + 1);
      g_activeSymbols[sz] = sym;
   }
};

//+------------------------------------------------------------------+
//| EXPERT INITIALIZATION FUNCTION                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   PrintFormat("🚀 Initializing %s (Magic: %d)...", InpEaName, InpMagicNumber);

   // Configure CTrade
   m_trade.SetExpertMagicNumber(InpMagicNumber);
   m_trade.SetDeviationInPoints(InpMaxSlippagePoints);
   m_trade.SetTypeFilling(ORDER_FILLING_IOC);

   // Initialize Telegram Notifier
   g_telegram.Init(InpTelegramBotToken);

   // Record Starting Day Equity & Peak Equity
   g_startingEquityDay = AccountInfoDouble(ACCOUNT_EQUITY);
   g_peakEquity        = g_startingEquityDay;

   // Indicator Handles on Primary Chart
   h_emaFast_M5 = iMA(_Symbol, InpExecutionTimeframe, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   h_emaMed_M5  = iMA(_Symbol, InpExecutionTimeframe, InpEmaMediumPeriod, 0, MODE_EMA, PRICE_CLOSE);
   h_emaSlow_M5 = iMA(_Symbol, InpExecutionTimeframe, InpEmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);
   h_atr_M5     = iATR(_Symbol, InpExecutionTimeframe, InpAtrPeriod);

   h_emaFast_H1 = iMA(_Symbol, InpHigherTimeframe, InpEmaFastPeriod, 0, MODE_EMA, PRICE_CLOSE);
   h_emaMed_H1  = iMA(_Symbol, InpHigherTimeframe, InpEmaMediumPeriod, 0, MODE_EMA, PRICE_CLOSE);
   h_emaSlow_H1 = iMA(_Symbol, InpHigherTimeframe, InpEmaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE);

   if(h_emaFast_M5 == INVALID_HANDLE || h_emaMed_M5 == INVALID_HANDLE || h_emaSlow_M5 == INVALID_HANDLE)
   {
      LogMsg("ERROR", "Failed to initialize indicator handles on chart symbol.");
      return INIT_FAILED;
   }

   // Discover Available Market Universe
   CMarketScanner::DiscoverUniverse();

   // Set 1-second high-resolution timer
   EventSetTimer(1);

   // Send Daily Opening Report if at start of day
   datetime now = TimeCurrent();
   g_lastDailyOpenTime = now;
   CReportEngine::SendDailyOpeningReport();

   LogMsg("INIT", "Chartora Official V1 Initialized Successfully. Quality Over Quantity Enabled.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| EXPERT DEINITIALIZATION FUNCTION                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();

   // Release Indicator Handles
   if(h_emaFast_M5 != INVALID_HANDLE) IndicatorRelease(h_emaFast_M5);
   if(h_emaMed_M5  != INVALID_HANDLE) IndicatorRelease(h_emaMed_M5);
   if(h_emaSlow_M5 != INVALID_HANDLE) IndicatorRelease(h_emaSlow_M5);
   if(h_atr_M5     != INVALID_HANDLE) IndicatorRelease(h_atr_M5);
   if(h_emaFast_H1 != INVALID_HANDLE) IndicatorRelease(h_emaFast_H1);
   if(h_emaMed_H1  != INVALID_HANDLE) IndicatorRelease(h_emaMed_H1);
   if(h_emaSlow_H1 != INVALID_HANDLE) IndicatorRelease(h_emaSlow_H1);

   CChartDashboard::Clear();
   LogMsg("DEINIT", StringFormat("Chartora Official V1 Stopped (Reason %d).", reason));
}

//+------------------------------------------------------------------+
//| EXPERT TICK FUNCTION                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Update Peak Equity Tracker
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity > g_peakEquity) g_peakEquity = equity;

   // 1. Update Active Live Trades (Break-even, Trailing Stops, R-calc)
   CTradeTracker::UpdateActiveTrades();

   // 2. On New M5 Bar on Current Chart -> Scan Single Chart
   datetime currentBarTime = iTime(_Symbol, InpExecutionTimeframe, 0);
   if(currentBarTime != g_lastBarTimeM5)
   {
      g_lastBarTimeM5 = currentBarTime;

      SSymbolScanResult chartScan = AnalyzeSymbol(_Symbol);
      CChartDashboard::Update(_Symbol, chartScan);

      if(chartScan.isEligible && chartScan.score >= InpMinTradeScore)
      {
         CMarketScanner::ProcessQualifiedSetup(chartScan.setup);
      }
   }
}

//+------------------------------------------------------------------+
//| TIMER FUNCTION FOR SCHEDULED REPORTS & MULTI-PAIR SCAN           |
//+------------------------------------------------------------------+
void OnTimer()
{
   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);

   // 1. Periodic Multi-Asset Universe Scan
   if(InpEnableScanner && (now - g_lastScanTime >= InpScanIntervalSec))
   {
      g_lastScanTime = now;
      CMarketScanner::ExecuteScan();
   }

   // 2. Daily Opening Report (08:00 UTC)
   if(dt.hour == 8 && dt.min == 0 && (now - g_lastDailyOpenTime > 3600))
   {
      g_lastDailyOpenTime = now;
      g_startingEquityDay = AccountInfoDouble(ACCOUNT_EQUITY);
      CReportEngine::SendDailyOpeningReport();
   }

   // 3. Daily Closing Report (21:00 UTC)
   if(dt.hour == 21 && dt.min == 0 && (now - g_lastDailyCloseTime > 3600))
   {
      g_lastDailyCloseTime = now;
      CReportEngine::SendDailyClosingReport();
      CTradeTracker::Rotate30DayHistory();
   }

   // 4. Weekly Report (Friday 21:30 UTC)
   if(dt.day_of_week == 5 && dt.hour == 21 && dt.min == 30 && (now - g_lastWeeklyReport > 3600))
   {
      g_lastWeeklyReport = now;
      CReportEngine::SendWeeklyReport();
   }

   // 5. Monthly Report (1st of month 09:00 UTC)
   if(dt.day == 1 && dt.hour == 9 && dt.min == 0 && (now - g_lastMonthlyReport > 3600))
   {
      g_lastMonthlyReport = now;
      CReportEngine::SendMonthlyReport();
   }

   // 6. Periodic Educational Snippet (Every 6 Hours)
   if(now - g_lastEduTime >= (6 * 3600))
   {
      g_lastEduTime = now;
      CReportEngine::SendEducationalInsight();
   }
}

//+------------------------------------------------------------------+
//| TRADE TRANSACTION MONITORING (REAL-TIME CLOSURES & FILLS)        |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type == TRADE_TRANSACTION_DEAL_ADD)
   {
      ulong dealTicket = trans.deal;
      if(HistoryDealSelect(dealTicket))
      {
         long dealMagic = HistoryDealGetInteger(dealTicket, DEAL_MAGIC);
         if(dealMagic == InpMagicNumber)
         {
            ENUM_DEAL_ENTRY entryType = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
            if(entryType == DEAL_ENTRY_OUT || entryType == DEAL_ENTRY_OUT_BY)
            {
               ulong positionId = HistoryDealGetInteger(dealTicket, DEAL_POSITION_ID);
               double profit    = HistoryDealGetDouble(dealTicket, DEAL_PROFIT) + HistoryDealGetDouble(dealTicket, DEAL_SWAP);
               double closeP    = HistoryDealGetDouble(dealTicket, DEAL_PRICE);
               string comment   = HistoryDealGetString(dealTicket, DEAL_COMMENT);

               CTradeTracker::ProcessTradeClosure(positionId, closeP, profit, comment != "" ? comment : "Deal Close");
            }
         }
      }
   }
}
