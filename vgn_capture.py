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
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright, Response, Request


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


def capture_response_safely(response: Response):
    """Safely extract response body, handling failures gracefully."""
    try:
        body_bytes = response.body()
        body_text = body_bytes.decode("utf-8", errors="replace")
        return try_parse_json(body_text)
    except Exception as exc:
        return f"<could not read body: {exc}>"


def build_request_record(request: Request):
    """Build a dict with all relevant request information."""
    return {
        "url": request.url,
        "method": request.method,
        "headers": request.headers,
        "post_data": request.post_data,
        "resource_type": request.resource_type,
        "is_navigation_request": request.is_navigation_request(),
    }


def build_response_record(response: Response):
    """Build a dict with all relevant response information."""
    return {
        "url": response.url,
        "status": response.status,
        "status_text": response.status_text,
        "headers": response.headers,
        "body": capture_response_safely(response),
    }


def run():
    captured = []
    output_file = "vgn_network_capture.json"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            locale="de-DE",
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # -----------------------------------------------------------------
        # Set up network listener – capture every response
        # -----------------------------------------------------------------
        def on_response(response: Response):
            request = response.request
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request": build_request_record(request),
                "response": build_response_record(response),
            }
            captured.append(entry)

        page.on("response", on_response)

        # -----------------------------------------------------------------
        # 1. Navigate to vgn.de
        # -----------------------------------------------------------------
        print("[1/4] Navigating to https://www.vgn.de ...")
        page.goto("https://www.vgn.de", wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3000)

        # -----------------------------------------------------------------
        # 2. Accept cookies
        # -----------------------------------------------------------------
        print("[2/4] Accepting cookies ...")
        cookie_accepted = False

        # Common cookie-consent button selectors for German sites
        cookie_selectors = [
            "button:has-text('Alle akzeptieren')",
            "button:has-text('Alle Cookies akzeptieren')",
            "button:has-text('Akzeptieren')",
            "button:has-text('Alles akzeptieren')",
            "a:has-text('Alle akzeptieren')",
            "[data-action='accept-all']",
            "#acceptAllCookies",
            ".cookie-accept-all",
        ]

        for selector in cookie_selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    cookie_accepted = True
                    print(f"  -> Clicked cookie button via: {selector}")
                    break
            except Exception:
                continue

        if not cookie_accepted:
            # Fallback: try to find any visible button whose text contains
            # "akzeptieren" (case-insensitive).
            try:
                buttons = page.locator("button, a").all()
                for btn in buttons:
                    try:
                        text = btn.inner_text(timeout=1000).strip().lower()
                        if "akzeptieren" in text and btn.is_visible():
                            btn.click()
                            cookie_accepted = True
                            print(f"  -> Clicked fallback cookie button: '{text}'")
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if not cookie_accepted:
            print("  -> No cookie banner found (may already be accepted).")

        page.wait_for_timeout(2000)

        # -----------------------------------------------------------------
        # 3. Fill in the route search form
        # -----------------------------------------------------------------
        print("[3/4] Filling route search form ...")

        origin = "Nürnberg, Am Schlag"
        destination = "Nürnberg, Hauptbahnhof"

        # The VGN homepage / /verbindungen page has origin/destination fields.
        # Try multiple strategies to find the input fields.

        # Strategy A: Look for labeled inputs or placeholders
        origin_selectors = [
            "input[placeholder*='Von']",
            "input[placeholder*='Start']",
            "input[placeholder*='Abfahrt']",
            "input[aria-label*='Von']",
            "input[aria-label*='Start']",
            "input[name*='origin']",
            "input[name*='from']",
            "input[name*='Von']",
            "#origin",
            "#from",
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
            "#destination",
            "#to",
        ]

        def fill_field(selectors, value, label):
            """Try multiple selectors to fill a form field."""
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.is_visible(timeout=2000):
                        loc.click()
                        loc.fill("")
                        loc.type(value, delay=50)
                        print(f"  -> Filled {label} via: {sel}")
                        # Wait for autocomplete suggestions and pick the first
                        page.wait_for_timeout(2000)
                        # Try to click the first suggestion from any dropdown
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
                            # If no dropdown found, press Enter or Tab
                            page.keyboard.press("ArrowDown")
                            page.wait_for_timeout(500)
                            page.keyboard.press("Enter")
                        return True
                except Exception:
                    continue

            # Strategy B: Fall back to finding text inputs by position
            # (first visible text input = origin, second = destination)
            return False

        origin_filled = fill_field(origin_selectors, origin, "origin")
        page.wait_for_timeout(1000)
        dest_filled = fill_field(dest_selectors, destination, "destination")

        # Strategy B: If specific selectors didn't work, try by input position
        if not origin_filled or not dest_filled:
            print("  -> Trying positional input strategy ...")
            text_inputs = page.locator(
                'input[type="text"], input:not([type])'
            ).all()
            visible_inputs = []
            for inp in text_inputs:
                try:
                    if inp.is_visible(timeout=500):
                        visible_inputs.append(inp)
                except Exception:
                    continue

            if len(visible_inputs) >= 2:
                if not origin_filled:
                    visible_inputs[0].click()
                    visible_inputs[0].fill("")
                    visible_inputs[0].type(origin, delay=50)
                    page.wait_for_timeout(2000)
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(300)
                    page.keyboard.press("Enter")
                    print(f"  -> Filled origin via positional input[0]")

                page.wait_for_timeout(1000)

                if not dest_filled:
                    visible_inputs[1].click()
                    visible_inputs[1].fill("")
                    visible_inputs[1].type(destination, delay=50)
                    page.wait_for_timeout(2000)
                    page.keyboard.press("ArrowDown")
                    page.wait_for_timeout(300)
                    page.keyboard.press("Enter")
                    print(f"  -> Filled destination via positional input[1]")
            else:
                print(f"  -> WARNING: Found only {len(visible_inputs)} visible inputs")

        page.wait_for_timeout(1000)

        # -----------------------------------------------------------------
        # 4. Submit the search
        # -----------------------------------------------------------------
        print("[4/4] Submitting search ...")

        submit_selectors = [
            "button[type='submit']",
            "button:has-text('Suchen')",
            "button:has-text('Verbindung suchen')",
            "button:has-text('Auskunft')",
            "input[type='submit']",
            "a:has-text('Suchen')",
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    submitted = True
                    print(f"  -> Clicked submit via: {sel}")
                    break
            except Exception:
                continue

        if not submitted:
            # Fallback: press Enter
            page.keyboard.press("Enter")
            print("  -> Submitted via Enter key")

        # Wait for results / XHR responses
        print("Waiting for responses ...")
        page.wait_for_timeout(8000)

        # Take a screenshot for debugging
        page.screenshot(path="vgn_result_screenshot.png", full_page=True)
        print("Screenshot saved to vgn_result_screenshot.png")

        browser.close()

    # -----------------------------------------------------------------
    # Write captured data to JSON
    # -----------------------------------------------------------------
    # Separate XHR/Fetch from other resource types for clarity
    xhr_entries = [
        e for e in captured
        if e["request"]["resource_type"] in ("xhr", "fetch")
    ]
    other_entries = [
        e for e in captured
        if e["request"]["resource_type"] not in ("xhr", "fetch")
    ]

    output = {
        "metadata": {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "origin": origin,
            "destination": destination,
            "total_requests": len(captured),
            "xhr_fetch_requests": len(xhr_entries),
            "other_requests": len(other_entries),
        },
        "xhr_and_fetch": xhr_entries,
        "other_requests": other_entries,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=make_serializable)

    print(f"\nDone! Captured {len(captured)} total responses "
          f"({len(xhr_entries)} XHR/Fetch).")
    print(f"Results written to {output_file}")


if __name__ == "__main__":
    run()
