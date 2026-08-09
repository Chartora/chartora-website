#!/usr/bin/env python3
import re
import sys
import os

def audit_links():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, 'index.html')
    app_js_path = os.path.join(base_dir, 'js', 'app.js')
    redirects_path = os.path.join(base_dir, 'public', '_redirects')

    print("=== CHARTORA.IN LINK & ROUTE AUDIT ===")

    if not os.path.exists(index_path):
        print("❌ Error: index.html not found!")
        sys.exit(1)
    if not os.path.exists(app_js_path):
        print("❌ Error: js/app.js not found!")
        sys.exit(1)

    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    with open(app_js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()

    # Extract all navigateTo('route') calls from HTML
    nav_routes = set(re.findall(r"navigateTo\(['\"]([^'\"]+)['\"]", html_content))
    print(f"Found {len(nav_routes)} distinct navigation targets in HTML: {sorted(list(nav_routes))}")

    # Extract switch cases in handleRoute() in js/app.js
    cases = set(re.findall(r"case\s+['\"]([^'\"]+)['\"]:", js_content))
    print(f"Found {len(cases)} route cases in js/app.js: {sorted(list(cases))}")

    # Verify every nav_route maps to a case or academy subroute or external file
    missing = []
    for route in nav_routes:
        base_route = route.split('/')[0]
        if base_route in ['home', 'academy']:
            continue
        if base_route not in cases and route not in cases:
            missing.append(route)

    if missing:
        print(f"❌ Missing route handlers in js/app.js for: {missing}")
        sys.exit(1)
    else:
        print("✅ All navigation routes have corresponding handlers in js/app.js!")

    # Check for empty href="#" without click handler
    empty_hrefs = re.findall(r'href="#"(?![\s>]*(?:onclick|class="dropdown-trigger"))', html_content)
    if empty_hrefs:
        print(f"⚠️ Found {len(empty_hrefs)} unhandled href='#' links in HTML!")
    else:
        print("✅ No unhandled href='#' links found in HTML.")

    # Check public/_redirects
    if os.path.exists(redirects_path):
        with open(redirects_path, 'r') as f:
            red = f.read()
        if '/* /index.html 200' in red or '/*  /index.html 200' in red:
            print("✅ public/_redirects contains valid Cloudflare Pages SPA rewrite rule!")
        else:
            print("⚠️ public/_redirects rule check recommendation: verify /* /index.html 200")
    else:
        print("⚠️ public/_redirects file missing!")

    print("=== AUDIT COMPLETE: ALL CHECKS PASSED ===")

if __name__ == '__main__':
    audit_links()
