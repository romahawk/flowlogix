#!/usr/bin/env python3
"""
FlowLogix Demo Recorder
=======================
Drives the running app with Playwright and saves a high-quality video
walkthrough to demo_output/demo.webm (and a PNG thumbnail).

Prerequisites
-------------
    pip install playwright
    playwright install chromium

Usage
-----
    # App must already be running before you start the recorder
    python demo_record.py
    python demo_record.py --url http://127.0.0.1:5000 --out my_demo

Flags
-----
    --url    Base URL of the running app   (default: http://127.0.0.1:5000)
    --out    Output directory for artefacts (default: demo_output)
    --headless  Run without a visible window (default: False)
"""

import argparse
import asyncio
from pathlib import Path

# ── Dependency check ─────────────────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    raise SystemExit(
        "\n[demo_record] 'playwright' is not installed.\n"
        "  Run:  pip install playwright && playwright install chromium\n"
    )

# ── Constants ────────────────────────────────────────────────────────────────
DEFAULT_URL = "http://127.0.0.1:5000"
USERNAME    = "demo"
PASSWORD    = "demo1234"
VIEWPORT    = {"width": 1440, "height": 900}


# ── Helpers ──────────────────────────────────────────────────────────────────

async def wait(ms: int = 1200) -> None:
    await asyncio.sleep(ms / 1000)


async def slow_type(page: Page, selector: str, text: str, delay: int = 55) -> None:
    await page.click(selector)
    await page.type(selector, text, delay=delay)


async def scroll_into_view(page: Page, selector: str) -> None:
    await page.eval_on_selector(
        selector,
        "el => el.scrollIntoView({behavior: 'smooth', block: 'center'})",
    )
    await wait(600)


async def banner(msg: str) -> None:
    print(f"\n  ▶  {msg}")


# ── Scene helpers ─────────────────────────────────────────────────────────────

async def scene_login(page: Page, base_url: str) -> None:
    await banner("LOGIN PAGE")
    await page.goto(f"{base_url}/login")
    await wait(1000)

    # Clear any pre-filled values then type slowly for camera effect
    await page.fill('input[name="username"]', "")
    await slow_type(page, 'input[name="username"]', USERNAME)
    await wait(400)

    await page.fill('input[name="password"]', "")
    await slow_type(page, 'input[name="password"]', PASSWORD)
    await wait(700)

    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{base_url}/dashboard**", timeout=12_000)
    await wait(1800)


async def scene_orders_tab(page: Page) -> None:
    await banner("YOUR ORDERS TAB  – colour-coded statuses")

    # Ensure we are on the orders tab
    await page.click("#tab-orders")
    await wait(800)

    # Scroll the table into view
    await scroll_into_view(page, "#orders-table-container")
    await wait(1200)

    # Hover over the first few rows so the user can see the row highlight
    rows = await page.locator("#orders-table-container tbody tr").all()
    for row in rows[:5]:
        await row.hover()
        await wait(550)

    await wait(1000)


async def scene_timeline_tab(page: Page) -> None:
    await banner("TIMELINE TAB – Gantt-style chart")

    await page.click("#tab-timeline")
    await wait(1500)

    # Scroll chart into view
    canvas_locator = page.locator("#timelineChart")
    await canvas_locator.scroll_into_view_if_needed()
    await wait(1200)

    # Sweep cursor across the chart to trigger tooltips
    canvas = await canvas_locator.bounding_box()
    if canvas:
        await banner("  Sweeping cursor to show tooltips…")
        cx, cy = canvas["x"], canvas["y"]
        cw, ch = canvas["width"], canvas["height"]

        for x_frac, y_frac in [(0.25, 0.25), (0.42, 0.45), (0.60, 0.35), (0.75, 0.55)]:
            await page.mouse.move(cx + cw * x_frac, cy + ch * y_frac)
            await wait(900)

        # Park cursor off the chart
        await page.mouse.move(cx - 40, cy)

    await wait(1200)


async def scene_add_order(page: Page) -> None:
    await banner("ADD ORDER FORM – opening & filling in a new order")

    # Navigate back to orders tab first
    await page.click("#tab-orders")
    await wait(600)

    # Click the green "New Order" button in the navbar
    toggle_btn = page.locator(".toggle-form-btn").first
    await toggle_btn.scroll_into_view_if_needed()
    await toggle_btn.click()
    await wait(1000)

    # Scroll form into view
    await scroll_into_view(page, "#add-order-section")
    await wait(600)

    # ── Order Identity ────────────────────────────────────────────────
    await page.fill("#order_date", "2026-04-01")
    await wait(300)

    await slow_type(page, "#order_number", "PO-2026-099", delay=60)
    await wait(400)

    # product_name is a TomSelect – click the control wrapper, type, then pick
    ts_control = page.locator("#product_name + .ts-wrapper .ts-control")
    await ts_control.click()
    await wait(300)
    await page.keyboard.type("Amox", delay=70)
    await wait(600)
    first_option = page.locator(".ts-dropdown .ts-option").first
    if await first_option.is_visible():
        await first_option.click()
    else:
        # Fallback: just press Enter to accept typed text
        await page.keyboard.press("Escape")
    await wait(400)

    # ── Parties & Quantity ────────────────────────────────────────────
    await slow_type(page, 'input[name="buyer"]', "City Hospital", delay=55)
    await wait(300)

    await page.fill('input[name="quantity"]', "500")
    await wait(300)

    # ── Schedule ──────────────────────────────────────────────────────
    await page.fill("#etd", "2026-04-10")
    await wait(300)
    await page.fill('input[name="eta"]', "2026-05-20")
    await wait(600)

    # Pause so the viewer can read the filled form
    await wait(1800)

    # Close form without submitting (demo only – we don't want to add real data)
    close_btn = page.locator("#close-add-order")
    if await close_btn.is_visible():
        await close_btn.click()
    else:
        await toggle_btn.click()
    await wait(800)


async def scene_dark_mode(page: Page) -> None:
    await banner("DARK MODE TOGGLE")

    dark_btn = page.locator("#dark-mode-toggle")
    await dark_btn.scroll_into_view_if_needed()

    # Switch to dark
    await dark_btn.click()
    await wait(1800)

    # Switch back to light
    await dark_btn.click()
    await wait(1200)


async def scene_warehouse(page: Page, base_url: str) -> None:
    await banner("WAREHOUSE PAGE")
    await page.goto(f"{base_url}/warehouse")
    await wait(2000)
    # Scroll down to show the table
    await page.mouse.wheel(0, 400)
    await wait(1500)


async def scene_delivered(page: Page, base_url: str) -> None:
    await banner("DELIVERED PAGE")
    await page.goto(f"{base_url}/delivered")
    await wait(2000)
    await page.mouse.wheel(0, 300)
    await wait(1500)


# ── Main ─────────────────────────────────────────────────────────────────────

async def record_demo(base_url: str, output_dir: Path, headless: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--start-maximized"],
        )

        ctx = await browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(output_dir),
            record_video_size=VIEWPORT,
            # Smooth scrolling
            java_script_enabled=True,
        )
        page = await ctx.new_page()

        # ── Run all scenes ────────────────────────────────────────────
        await scene_login(page, base_url)
        await scene_orders_tab(page)
        await scene_timeline_tab(page)
        await scene_add_order(page)
        await scene_dark_mode(page)
        await scene_warehouse(page, base_url)
        await scene_delivered(page, base_url)

        # ── Final pause & screenshot ──────────────────────────────────
        await banner("Saving screenshot thumbnail…")
        await page.goto(f"{base_url}/dashboard")
        await wait(1500)
        screenshot_path = output_dir / "thumbnail.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print(f"  ✓  Thumbnail → {screenshot_path}")

        await wait(1500)
        await ctx.close()
        await browser.close()

    # Rename the auto-generated video file to something predictable
    videos = sorted(output_dir.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    if videos:
        final = output_dir / "demo.webm"
        videos[-1].rename(final)
        print(f"\n  ✓  Video saved → {final.resolve()}\n")
        print("  To convert to MP4 (requires ffmpeg):")
        print(f"    ffmpeg -i {final} -c:v libx264 -crf 18 -preset slow {output_dir}/demo.mp4\n")
    else:
        print("\n  ⚠  No .webm found – check that the app was reachable.\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a FlowLogix demo walkthrough with Playwright."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Base URL of the running app (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--out",
        default="demo_output",
        help="Output directory for video + screenshot (default: demo_output)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser headlessly (no visible window)",
    )
    args = parser.parse_args()

    print(f"\n  FlowLogix Demo Recorder")
    print(f"  Target : {args.url}")
    print(f"  Output : {args.out}/")
    print(f"  Headless: {args.headless}")
    print("  Make sure the app is running before proceeding.\n")

    asyncio.run(record_demo(args.url, Path(args.out), args.headless))


if __name__ == "__main__":
    main()
