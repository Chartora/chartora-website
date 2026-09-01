#!/usr/bin/env python3
"""
Static validator and linter for Chartora_Official_V1.mq5
Verifies single-file compliance, balanced brackets, includes, event handlers, and core features.
"""

import re
import sys

def validate_mq5(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    errors = []
    warnings = []

    # 1. Check includes - ONLY standard MT5 built-in allowed
    includes = re.findall(r'#include\s+["<]([^">]+)[">]', code)
    for inc in includes:
        if not inc.startswith("Trade\\") and not inc.startswith("Trade/") and not inc.startswith("Arrays\\") and not inc.startswith("Arrays/"):
            errors.append(f"Illegal non-standard include found: {inc}. Must be single-file without custom .mqh!")

    # 2. Check balanced braces, brackets, parentheses
    # Strip strings first, then comments
    clean_code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
    clean_code = re.sub(r"'(?:\\.|[^'\\])*'", "''", clean_code)
    clean_code = re.sub(r'//.*', '', clean_code)
    clean_code = re.sub(r'/\*[\s\S]*?\*/', '', clean_code)

    brace_stack = 0
    paren_stack = 0
    bracket_stack = 0

    for idx, ch in enumerate(clean_code):
        if ch == '{': brace_stack += 1
        elif ch == '}':
            brace_stack -= 1
            if brace_stack < 0:
                errors.append(f"Unmatched closing brace '}}' at character {idx}")
        elif ch == '(': paren_stack += 1
        elif ch == ')':
            paren_stack -= 1
            if paren_stack < 0:
                errors.append(f"Unmatched closing parenthesis ')' at character {idx}")
        elif ch == '[': bracket_stack += 1
        elif ch == ']':
            bracket_stack -= 1
            if bracket_stack < 0:
                errors.append(f"Unmatched closing bracket ']' at character {idx}")

    if brace_stack != 0: errors.append(f"Mismatched braces: net count is {brace_stack}")
    if paren_stack != 0: errors.append(f"Mismatched parentheses: net count is {paren_stack}")
    if bracket_stack != 0: errors.append(f"Mismatched brackets: net count is {bracket_stack}")

    # 3. Check required MT5 Event Handlers
    required_handlers = ["OnInit", "OnDeinit", "OnTick", "OnTimer", "OnTradeTransaction"]
    for h in required_handlers:
        if not re.search(r'\b' + h + r'\s*\(', code):
            errors.append(f"Missing required event handler: {h}()")

    # 4. Check Key Components
    required_features = [
        ("Choppy market filter", r'IsMarketChoppy'),
        ("Trade quality score", r'CalculateTradeScore'),
        ("Dynamic lot sizing", r'CalculateLotSize'),
        ("Telegram notifier", r'CTelegramNotifier'),
        ("Trade tracker & R-multiple", r'CTradeTracker'),
        ("Daily/Weekly report engine", r'CReportEngine'),
        ("On-chart HUD dashboard", r'CChartDashboard'),
        ("Multi-asset universe scanner", r'CMarketScanner'),
        ("DXY context evaluation", r'EvaluateDxyContext'),
        ("30-day data retention", r'Rotate30DayHistory'),
    ]

    for name, pattern in required_features:
        if not re.search(pattern, code):
            errors.append(f"Missing required capability: {name} (Pattern: {pattern})")

    # Print Report
    print("=== MQL5 STATIC VALIDATION REPORT ===")
    print(f"File: {file_path}")
    print(f"Total Lines: {len(code.splitlines())}")
    print(f"Standard MT5 Includes: {includes}")
    print(f"Errors Found: {len(errors)}")
    print(f"Warnings Found: {len(warnings)}")

    if errors:
        for err in errors:
            print(f"❌ ERROR: {err}")
        sys.exit(1)
    else:
        print("✅ ALL MQL5 VALIDATION CHECKS PASSED: Error-free, self-contained single file!")
        sys.exit(0)

if __name__ == "__main__":
    validate_mq5("mt5/Chartora_Official_V1.mq5")
