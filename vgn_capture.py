#!/usr/bin/env python3
"""
Playwright script to search a route on vgn.de and capture all network traffic.

Goes to vgn.de, accepts cookies, searches a route from
"Nürnberg, Am Schlag" to "Nürnberg, Hauptbahnhof", and writes all
captured network requests/responses (especially XHR/Fetch) to a JSON file.

Requirements:
    pip install playwright
    playwright install chromium
"""

import json
import os
import shutil
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, Response, Request

# Use CHROMIUM_PATH env var if set, otherwise default Playwright path.
CHROMIUM_PATH = os.environ.get("CHROMIUM_PATH", None)

ORIGIN = "Nürnberg, Am Schlag"
DESTINATION = "Nürnberg, Hauptbahnhof"
OUTPUT_FILE = "vgn_network_capture.json"


def make_serializable(obj):
    """Ensure an object is JSON-serializable."""
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8")
        except UnicodeDecodeError:
            return f"<binary {len(obj)} bytes>"
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def try_parse_json(text):
    """Try to parse a string as JSON; return parsed object or the raw string."""
    if not text:
        return text
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text


def read_body(response: Response):
    """Safely read the response body after the response has finished."""
    try:
        body_bytes = response.body()
        body_text = body_bytes.decode("utf-8", errors="replace")
        return try_parse_json(body_text)
    except Exception as exc:
        return f"<could not read body: {exc}>"


def accept_cookies(page):
    """Try to find and click the cookie-consent 'accept all' button."""
    selectors = [
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Alle Cookies akzeptieren')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Alles akzeptieren')",
        "a:has-text('Alle akzeptieren')",
        "[data-action='accept-all']",
        "#acceptAllCookies",
        ".cookie-accept-all",
    ]

    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  -> Clicked cookie button via: {selector}")
                return True
        except Exception:
            continue

    # Fallback: scan all visible buttons/links for text containing "akzeptieren"
    try:
        for btn in page.locator("button, a").all():
            try:
                text = btn.inner_text(timeout=1000).strip().lower()
                if "akzeptieren" in text and btn.is_visible():
                    btn.click()
                    print(f"  -> Clicked fallback cookie button: '{text}'")
                    return True
            except Exception:
                continue
    except Exception:
        pass

    print("  -> No cookie banner found (may already be accepted).")
    return False


def fill_field(page, selectors, value, label):
    """Try multiple selectors to fill a form field, then pick an autocomplete suggestion."""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                loc.click()
                loc.fill("")
                loc.type(value, delay=50)
                print(f"  -> Filled {label} via: {sel}")
                page.wait_for_timeout(2000)

                # Try to click the first autocomplete suggestion
                suggestion_selectors = [
                    ".suggestion-list li:first-child",
                    ".autocomplete-suggestion:first-child",
                    "[role='option']:first-child",
                    "[role='listbox'] [role='option']:first-child",
                    ".tt-suggestion:first-child",
                    "ul.suggestions li:first-child",
                    ".dropdown-menu li:first-child",
                    ".search-suggestions li:first-child",
                ]
                for sug_sel in suggestion_selectors:
                    try:
                        sug = page.locator(sug_sel).first
                        if sug.is_visible(timeout=1000):
                            sug.click()
                            print(f"  -> Selected suggestion via: {sug_sel}")
                            break
                    except Exception:
                        continue
                else:
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(500)
                    page.keyboard.press("Enter")
                return True
        except Exception:
            continue
    return False


def fill_by_position(page, index, value, label):
    """Fallback: fill the Nth visible text input on the page."""
    text_inputs = page.locator('input[type="text"], input:not([type])').all()
    visible = [inp for inp in text_inputs if inp.is_visible(timeout=500)]
    if index < len(visible):
        visible[index].click()
        visible[index].fill("")
        visible[index].type(value, delay=50)
        page.wait_for_timeout(2000)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(300)
        page.keyboard.press("Enter")
        print(f"  -> Filled {label} via positional input[{index}]")
        return True
    return False


def submit_search(page):
    """Find and click the search/submit button."""
    selectors = [
        "button[type='submit']",
        "button:has-text('Suchen')",
        "button:has-text('Verbindung suchen')",
        "button:has-text('Auskunft')",
        "input[type='submit']",
        "a:has-text('Suchen')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  -> Clicked submit via: {sel}")
                return
        except Exception:
            continue

    page.keyboard.press("Enter")
    print("  -> Submitted via Enter key")


def run():
    # Collect raw response objects; we read bodies *after* page interactions
    # to avoid re-entrancy issues inside the event handler.
    responses: list[Response] = []

    with sync_playwright() as pw:
        launch_opts = {"headless": True}
        chromium = (
            CHROMIUM_PATH
            or shutil.which("chromium")
            or shutil.which("chromium-browser")
        )
        if chromium:
            launch_opts["executable_path"] = chromium
        browser = pw.chromium.launch(**launch_opts)
        context = browser.new_context(
            locale="de-DE",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Collect response references (body is read later)
        page.on("response", lambda resp: responses.append(resp))

        # ---- 1. Navigate ----
        print("[1/4] Navigating to https://www.vgn.de ...")
        page.goto("https://www.vgn.de", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)

        # ---- 2. Cookies ----
        print("[2/4] Accepting cookies ...")
        accept_cookies(page)
        page.wait_for_timeout(2000)

        # ---- 3. Fill search form ----
        print("[3/4] Filling route search form ...")

        origin_selectors = [
            "input[placeholder*='Von']",
            "input[placeholder*='Start']",
            "input[placeholder*='Abfahrt']",
            "input[aria-label*='Von']",
            "input[aria-label*='Start']",
            "input[name*='origin']",
            "input[name*='from']",
            "input[name*='Von']",
            "#origin", "#from",
        ]
        dest_selectors = [
            "input[placeholder*='Nach']",
            "input[placeholder*='Ziel']",
            "input[placeholder*='Ankunft']",
            "input[aria-label*='Nach']",
            "input[aria-label*='Ziel']",
            "input[name*='destination']",
            "input[name*='to']",
            "input[name*='Nach']",
            "#destination", "#to",
        ]

        origin_ok = fill_field(page, origin_selectors, ORIGIN, "origin")
        page.wait_for_timeout(1000)
        dest_ok = fill_field(page, dest_selectors, DESTINATION, "destination")

        if not origin_ok or not dest_ok:
            print("  -> Trying positional input strategy ...")
            if not origin_ok:
                fill_by_position(page, 0, ORIGIN, "origin")
            page.wait_for_timeout(1000)
            if not dest_ok:
                fill_by_position(page, 1, DESTINATION, "destination")

        page.wait_for_timeout(1000)

        # ---- 4. Submit ----
        print("[4/4] Submitting search ...")
        submit_search(page)

        print("Waiting for responses ...")
        page.wait_for_timeout(8000)

        # Take a debug screenshot
        page.screenshot(path="vgn_result_screenshot.png", full_page=True)
        print("Screenshot saved to vgn_result_screenshot.png")

        # ---- Build captured data (read bodies now that page is idle) ----
        print("Reading response bodies ...")
        captured = []
        for resp in responses:
            req = resp.request
            captured.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request": {
                    "url": req.url,
                    "method": req.method,
                    "headers": req.headers,
                    "post_data": req.post_data,
                    "resource_type": req.resource_type,
                    "is_navigation_request": req.is_navigation_request(),
                },
                "response": {
                    "url": resp.url,
                    "status": resp.status,
                    "status_text": resp.status_text,
                    "headers": resp.headers,
                    "body": read_body(resp),
                },
            })

        browser.close()

    # ---- Write JSON output ----
    xhr_entries = [
        e for e in captured if e["request"]["resource_type"] in ("xhr", "fetch")
    ]
    other_entries = [
        e for e in captured if e["request"]["resource_type"] not in ("xhr", "fetch")
    ]

    output = {
        "metadata": {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "origin": ORIGIN,
            "destination": DESTINATION,
            "total_requests": len(captured),
            "xhr_fetch_requests": len(xhr_entries),
            "other_requests": len(other_entries),
        },
        "xhr_and_fetch": xhr_entries,
        "other_requests": other_entries,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=make_serializable)

    print(f"\nDone! Captured {len(captured)} total responses "
          f"({len(xhr_entries)} XHR/Fetch).")
    print(f"Results written to {OUTPUT_FILE}")


if __name__ == "__main__":
    run()
