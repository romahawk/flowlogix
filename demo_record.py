#!/usr/bin/env python3
"""
FlowLogix Demo Recorder
=======================
Records a concise 20-second dashboard-focused demo with on-screen captions:

0-3s   Show full dashboard   "Single source of truth"
3-8s   Click STATUS sort     "State-driven system"
8-14s  Hover actions + click Move to warehouse   "Real-time updates"
14-18s Show timeline + click Date   "Helicopter view"
18-20s Zoom out             "System overview"

Prerequisites
-------------
    pip install playwright
    playwright install chromium

Usage
-----
    # App must already be running before you start the recorder
    python demo_record.py
    python demo_record.py --url http://127.0.0.1:5000 --out my_demo
"""

import argparse
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Locator, Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    raise SystemExit(
        "\n[demo_record] 'playwright' is not installed.\n"
        "  Run:  pip install playwright && playwright install chromium\n"
    )

DEFAULT_URL = "http://127.0.0.1:5000"
USERNAME = "demo"
PASSWORD = "demo1234"
VIEWPORT = {"width": 1440, "height": 900}


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
    print(f"\n  ->  {msg}")


async def ensure_caption_overlay(page: Page) -> None:
    await page.evaluate(
        """
        () => {
          if (document.getElementById('demo-caption-overlay')) return;
          const el = document.createElement('div');
          el.id = 'demo-caption-overlay';
          Object.assign(el.style, {
            position: 'fixed',
            left: '50%',
            bottom: '28px',
            transform: 'translateX(-50%)',
            zIndex: '99999',
            padding: '12px 18px',
            borderRadius: '999px',
            background: 'rgba(15, 23, 42, 0.84)',
            color: '#f8fafc',
            fontFamily: 'Segoe UI, Arial, sans-serif',
            fontSize: '24px',
            fontWeight: '700',
            letterSpacing: '0.01em',
            boxShadow: '0 18px 48px rgba(15, 23, 42, 0.35)',
            backdropFilter: 'blur(8px)',
            pointerEvents: 'none',
            opacity: '0',
            transition: 'opacity 220ms ease'
          });
          document.body.appendChild(el);
        }
        """
    )


async def set_caption(page: Page, text: str) -> None:
    await ensure_caption_overlay(page)
    await page.evaluate(
        """([message]) => {
          const el = document.getElementById('demo-caption-overlay');
          if (!el) return;
          el.textContent = message;
          el.style.opacity = message ? '1' : '0';
        }""",
        [text],
    )


async def wait_for_dashboard(page: Page, base_url: str) -> None:
    await page.wait_for_url(f"{base_url}/dashboard**", timeout=12_000)
    await dismiss_tour_modal(page)
    await page.wait_for_selector("#orders-table-container tbody tr", timeout=15_000)
    await dismiss_tour_modal(page)
    await wait(700)


async def disable_warehouse_submit(page: Page) -> None:
    await page.evaluate(
        """
        () => {
          document.querySelectorAll('form[action^="/stock_order/"]').forEach((form) => {
            if (form.dataset.demoRecorderBound === '1') return;
            form.dataset.demoRecorderBound = '1';
            form.addEventListener('submit', (event) => {
              event.preventDefault();
              const btn = form.querySelector('button[title="Move to Warehouse"]');
              const kpi = document.getElementById('kpi-warehouse-count');
              if (btn) {
                btn.style.transform = 'scale(0.94)';
                setTimeout(() => { btn.style.transform = ''; }, 180);
              }
              if (kpi) {
                kpi.style.transition = 'transform 220ms ease, color 220ms ease';
                kpi.style.transform = 'scale(1.08)';
                kpi.style.color = '#a855f7';
                setTimeout(() => {
                  kpi.style.transform = '';
                  kpi.style.color = '';
                }, 700);
              }
            });
          });
        }
        """
    )


async def sort_by_status(page: Page) -> None:
    header = page.locator('th[data-sort="transit_status"]')
    await header.scroll_into_view_if_needed()
    await wait(300)
    await header.click(force=True)
    await page.wait_for_timeout(900)


async def find_warehouse_button(page: Page) -> Locator:
    next_btn = page.locator("#orders-next-page")
    warehouse_btn = page.locator('button[title="Move to Warehouse"]')

    for attempt in range(6):
        await disable_warehouse_submit(page)
        if await warehouse_btn.count() > 0:
            return warehouse_btn.first
        if attempt == 0:
            await sort_by_status(page)
            continue
        if await next_btn.count() > 0 and await next_btn.is_visible() and await next_btn.is_enabled():
            await next_btn.click(force=True)
            await page.wait_for_timeout(900)
            continue
        break

    raise PlaywrightTimeoutError("No visible 'Move to Warehouse' action found in paginated orders table.")


async def dismiss_tour_modal(page: Page) -> None:
    """Suppress the guided tour and remove any active blocker overlay."""
    await page.evaluate(
        """
        () => {
          localStorage.setItem('tourCompleted', 'true');
          localStorage.setItem('flx_tour_done', '1');
          ['flx-tour-tooltip', 'flx-tour-spotlight', 'flx-tour-blocker'].forEach((id) => {
            document.getElementById(id)?.remove();
          });
        }
        """
    )
    close_btn = page.locator("#closeTourBtn, #flx-tour-skip")
    if await close_btn.count() > 0:
        try:
            await close_btn.first.click(timeout=1000)
            await wait(200)
        except Exception:
            pass


async def scene_login(page: Page, base_url: str) -> None:
    await banner("OPEN DASHBOARD")
    await page.goto(f"{base_url}/dashboard")
    try:
        await wait_for_dashboard(page, base_url)
    except PlaywrightTimeoutError:
        await banner("Falling back to explicit login flow")
        await page.goto(f"{base_url}/login")
        await page.wait_for_selector('input[name="username"]', timeout=5000)
        await page.fill('input[name="username"]', "")
        await slow_type(page, 'input[name="username"]', USERNAME)
        await wait(300)
        await page.fill('input[name="password"]', "")
        await slow_type(page, 'input[name="password"]', PASSWORD)
        await wait(500)
        await page.click('button[type="submit"]')
        await wait_for_dashboard(page, base_url)


async def scene_dashboard_story(page: Page, base_url: str) -> None:
    await banner("20-SECOND DASHBOARD STORY")
    await dismiss_tour_modal(page)
    await scroll_into_view(page, "#kpi-cards")
    await page.evaluate("document.body.style.zoom = '1'")
    await set_caption(page, "Single source of truth")
    await wait(3000)

    await banner("Sorting by status")
    await set_caption(page, "State-driven system")
    await dismiss_tour_modal(page)
    await sort_by_status(page)
    await wait(4100)

    await banner("Hovering actions and clicking warehouse move")
    await set_caption(page, "Real-time updates")
    warehouse_btn = await find_warehouse_button(page)
    await warehouse_btn.scroll_into_view_if_needed()
    await wait(300)
    await warehouse_btn.hover()
    await wait(1400)
    await warehouse_btn.click(force=True)
    await wait(4300)

    await banner("Returning to timeline")
    await page.goto(f"{base_url}/dashboard")
    await wait_for_dashboard(page, base_url)
    await set_caption(page, "Helicopter view")
    await dismiss_tour_modal(page)
    await page.click("#tab-timeline", force=True)
    await page.wait_for_selector("#timelineChart", timeout=12_000)
    await wait(900)
    await page.click("#tl-sort-date", force=True)
    await wait(900)

    canvas_locator = page.locator("#timelineChart")
    canvas = await canvas_locator.bounding_box()
    if canvas:
        cx, cy = canvas["x"], canvas["y"]
        cw, ch = canvas["width"], canvas["height"]
        for x_frac, y_frac in [(0.22, 0.24), (0.46, 0.44), (0.72, 0.66)]:
            await page.mouse.move(cx + cw * x_frac, cy + ch * y_frac)
            await wait(550)
    await wait(250)

    await banner("Zooming out for final frame")
    await set_caption(page, "System overview")
    await page.evaluate("document.body.style.zoom = '0.88'")
    await wait(2000)
    await set_caption(page, "")


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
            java_script_enabled=True,
        )
        await ctx.add_init_script(
            """
            () => {
              localStorage.setItem('flx_tour_done', '1');
              localStorage.setItem('tourCompleted', 'true');
            }
            """
        )
        page = await ctx.new_page()

        await scene_login(page, base_url)
        await scene_dashboard_story(page, base_url)

        await banner("Saving screenshot thumbnail...")
        await page.goto(f"{base_url}/dashboard")
        await wait_for_dashboard(page, base_url)
        await set_caption(page, "")
        await page.evaluate("document.body.style.zoom = '1'")
        await wait(500)
        screenshot_path = output_dir / "thumbnail.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print(f"  OK  Thumbnail -> {screenshot_path}")

        await wait(1500)
        await ctx.close()
        await browser.close()

    videos = sorted(output_dir.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    if videos:
        final = output_dir / "demo.webm"
        if final.exists():
            final.unlink()
        videos[-1].rename(final)
        print(f"\n  OK  Video saved -> {final.resolve()}\n")
        print("  To convert to MP4 (requires ffmpeg):")
        print(f"    ffmpeg -i {final} -c:v libx264 -crf 18 -preset slow {output_dir}/demo.mp4\n")
    else:
        print("\n  WARN  No .webm found - check that the app was reachable.\n")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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

    print("\n  FlowLogix Demo Recorder")
    print(f"  Target : {args.url}")
    print(f"  Output : {args.out}/")
    print(f"  Headless: {args.headless}")
    print("  Make sure the app is running before proceeding.\n")

    asyncio.run(record_demo(args.url, Path(args.out), args.headless))


if __name__ == "__main__":
    main()
