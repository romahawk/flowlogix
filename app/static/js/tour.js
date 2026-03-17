/**
 * FlowLogics Spotlight Tour
 * Zero-dependency guided walkthrough for the dashboard.
 * Auto-starts on first visit; re-triggered via window.startTour() or ?tour=1.
 */
(function () {
  'use strict';

  const TOUR_KEY = 'flx_tour_done';

  const STEPS = [
    {
      target: null,
      title: 'Welcome to FlowLogics',
      body: 'A pharma supply chain dashboard for tracking orders from origin to delivery. This 60-second tour walks you through the key features.',
      position: 'center',
    },
    {
      target: '#kpi-cards',
      title: 'Live KPI Summary',
      body: 'Four real-time counters: <strong>In Transit</strong> (active shipments), <strong>In Warehouse</strong> (stocked goods), <strong>Delivered</strong> (completed), and <strong>Delayed</strong> (overdue). Each card shows month-over-month trend.',
      position: 'bottom',
    },
    {
      target: '#orders-table-container',
      title: 'Active Orders Table',
      body: 'All open orders in one view. Click any column header to sort. Use the search box above to filter by product, order number, or status. Row actions let you edit, deliver, or move to warehouse.',
      position: 'top',
    },
    {
      target: '#tab-timeline',
      title: 'Delivery Timeline',
      body: 'Switch to the <strong>Timeline</strong> tab for a Gantt-style chart of all orders by ETD/ETA. Color-coded status: <span style="color:#f97316">■</span> In Process &nbsp;<span style="color:#3b82f6">■</span> En Route &nbsp;<span style="color:#22c55e">■</span> Arrived.',
      position: 'bottom',
    },
    {
      target: '[data-tour="nav-warehouse"]',
      title: 'Warehouse Module',
      body: 'When goods arrive, move them here. Track stock per batch, add customs notes, and generate detailed <strong>Stock Reports</strong> with weights, packing, and sender details — downloadable as PDF.',
      position: 'bottom',
    },
    {
      target: '[data-tour="nav-delivered"]',
      title: 'Delivered Tracking',
      body: 'Finalize shipments, upload <strong>Proof of Delivery</strong> (PDF or image), and keep a full audit trail with transport method and client info. Partial deliveries are supported.',
      position: 'bottom',
    },
    {
      target: '[data-tour="nav-logs"]',
      title: 'Activity Logs',
      body: 'Every action taken in the system is logged here — who did what and when. Useful for ops audits and handover reports.',
      position: 'bottom',
    },
    {
      target: null,
      title: "You're all set!",
      body: "You're browsing in <strong>demo mode</strong> (read-only). All data resets to this state automatically. Click <strong>Tour</strong> in the navbar anytime to replay this walkthrough.",
      position: 'center',
    },
  ];

  // ── DOM helpers ──────────────────────────────────────────────────────────────

  function el(id) { return document.getElementById(id); }

  function buildUI() {
    // Spotlight frame (creates the dark backdrop via box-shadow)
    const spotlight = document.createElement('div');
    spotlight.id = 'flx-tour-spotlight';
    spotlight.style.cssText = [
      'position:fixed',
      'border-radius:6px',
      'box-shadow:0 0 0 max(100vw,100vh) rgba(0,0,0,0.68)',
      'z-index:9998',
      'pointer-events:none',
      'transition:top 0.28s ease,left 0.28s ease,width 0.28s ease,height 0.28s ease',
      'outline:3px solid rgba(99,179,237,0.8)',
    ].join(';');

    // Tooltip bubble
    const tooltip = document.createElement('div');
    tooltip.id = 'flx-tour-tooltip';
    tooltip.style.cssText = [
      'position:fixed',
      'z-index:9999',
      'max-width:360px',
      'width:calc(100vw - 32px)',
      'background:#1e293b',
      'color:#f1f5f9',
      'border-radius:10px',
      'box-shadow:0 8px 32px rgba(0,0,0,0.5)',
      'padding:20px 22px 16px',
      'font-family:inherit',
      'font-size:14px',
      'line-height:1.55',
      'transition:top 0.28s ease,left 0.28s ease',
    ].join(';');

    tooltip.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
        <strong id="flx-tour-title" style="font-size:15px;color:#93c5fd"></strong>
        <button id="flx-tour-skip" title="Close tour"
          style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:18px;line-height:1;padding:0 0 0 12px">✕</button>
      </div>
      <div id="flx-tour-body" style="color:#cbd5e1;margin-bottom:16px"></div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <span id="flx-tour-counter" style="font-size:12px;color:#64748b"></span>
        <div style="display:flex;gap:8px">
          <button id="flx-tour-prev"
            style="padding:6px 14px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#94a3b8;cursor:pointer;font-size:13px">
            ← Back
          </button>
          <button id="flx-tour-next"
            style="padding:6px 16px;border-radius:6px;border:none;background:#3b82f6;color:#fff;cursor:pointer;font-size:13px;font-weight:600">
            Next →
          </button>
        </div>
      </div>`;

    // Click blocker overlay (sits below spotlight, blocks page interaction)
    const blocker = document.createElement('div');
    blocker.id = 'flx-tour-blocker';
    blocker.style.cssText = 'position:fixed;inset:0;z-index:9997;cursor:default';

    document.body.appendChild(blocker);
    document.body.appendChild(spotlight);
    document.body.appendChild(tooltip);

    return { spotlight, tooltip, blocker };
  }

  // ── Positioning ──────────────────────────────────────────────────────────────

  const PAD = 10; // px padding around spotlight target

  function positionSpotlight(spotlight, rect) {
    spotlight.style.top    = (rect.top    - PAD) + 'px';
    spotlight.style.left   = (rect.left   - PAD) + 'px';
    spotlight.style.width  = (rect.width  + PAD * 2) + 'px';
    spotlight.style.height = (rect.height + PAD * 2) + 'px';
  }

  function positionTooltip(tooltip, rect, position) {
    const tw = tooltip.offsetWidth  || 360;
    const th = tooltip.offsetHeight || 160;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let top, left;

    if (position === 'center' || !rect) {
      top  = Math.max(16, (vh - th) / 2);
      left = Math.max(16, (vw - tw) / 2);
    } else if (position === 'bottom') {
      top  = rect.bottom + PAD + 14;
      left = Math.max(16, Math.min(rect.left, vw - tw - 16));
    } else { // top
      top  = rect.top - PAD - th - 14;
      left = Math.max(16, Math.min(rect.left, vw - tw - 16));
    }

    // Clamp to viewport
    top  = Math.max(16, Math.min(top,  vh - th - 16));
    left = Math.max(16, Math.min(left, vw - tw - 16));

    tooltip.style.top  = top  + 'px';
    tooltip.style.left = left + 'px';
  }

  // ── Tour controller ──────────────────────────────────────────────────────────

  function startTour() {
    if (el('flx-tour-tooltip')) return; // already running

    let step = 0;
    const { spotlight, tooltip, blocker } = buildUI();

    function scrollToTarget(target) {
      if (!target) return Promise.resolve();
      return new Promise(resolve => {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(resolve, 320);
      });
    }

    async function render(index) {
      const s = STEPS[index];
      const target = s.target ? document.querySelector(s.target) : null;

      el('flx-tour-title').textContent   = s.title;
      el('flx-tour-body').innerHTML      = s.body;
      el('flx-tour-counter').textContent = `${index + 1} / ${STEPS.length}`;
      el('flx-tour-prev').disabled       = index === 0;
      el('flx-tour-prev').style.opacity  = index === 0 ? '0.4' : '1';
      el('flx-tour-next').textContent    = index === STEPS.length - 1 ? 'Finish ✓' : 'Next →';

      if (target) {
        await scrollToTarget(target);
        const rect = target.getBoundingClientRect();
        spotlight.style.display = 'block';
        positionSpotlight(spotlight, rect);
        positionTooltip(tooltip, rect, s.position);
      } else {
        spotlight.style.display = 'none';
        positionTooltip(tooltip, null, 'center');
      }
    }

    function closeTour() {
      [spotlight, tooltip, blocker].forEach(n => n.remove());
      localStorage.setItem(TOUR_KEY, '1');
      // Remove ?tour=1 from URL without reload
      const url = new URL(window.location);
      url.searchParams.delete('tour');
      window.history.replaceState({}, '', url);
    }

    el('flx-tour-skip').addEventListener('click', closeTour);
    el('flx-tour-prev').addEventListener('click', () => {
      if (step > 0) { step--; render(step); }
    });
    el('flx-tour-next').addEventListener('click', () => {
      if (step < STEPS.length - 1) { step++; render(step); }
      else closeTour();
    });

    // Keyboard nav
    function onKey(e) {
      if (!el('flx-tour-tooltip')) { document.removeEventListener('keydown', onKey); return; }
      if (e.key === 'Escape')    { closeTour(); document.removeEventListener('keydown', onKey); }
      if (e.key === 'ArrowRight' && step < STEPS.length - 1) { step++; render(step); }
      if (e.key === 'ArrowLeft'  && step > 0)                { step--; render(step); }
    }
    document.addEventListener('keydown', onKey);

    render(0);
  }

  // ── Auto-start logic ──────────────────────────────────────────────────────────

  window.startTour = startTour;

  document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const forced = params.get('tour') === '1';
    const fresh  = !localStorage.getItem(TOUR_KEY);
    if (forced || fresh) {
      // Small delay so the page finishes painting
      setTimeout(startTour, 500);
    }
  });
})();
