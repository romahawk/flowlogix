/**
 * FlowLogics Spotlight Tour
 * Zero-dependency guided walkthrough for the dashboard.
 * Auto-starts on first visit; re-triggered via window.startTour() or ?tour=1.
 */
(function () {
  'use strict';

  const TOUR_KEY = 'flx_tour_done';
  const MOBILE_TOUR_QUERY = '(max-width: 768px)';
  const PAD = 10;

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
      body: 'Switch to the <strong>Timeline</strong> tab for a Gantt-style chart of all orders by ETD and ETA. Color-coded status: <span style="color:#f97316">■</span> In Process, <span style="color:#3b82f6">■</span> En Route, <span style="color:#22c55e">■</span> Arrived.',
      position: 'bottom',
    },
    {
      target: '[data-tour="nav-warehouse"]',
      title: 'Warehouse Module',
      body: 'When goods arrive, move them here. Track stock per batch, add customs notes, and generate detailed <strong>Stock Reports</strong> with weights, packing, and sender details.',
      position: 'bottom',
    },
    {
      target: '[data-tour="nav-delivered"]',
      title: 'Delivered Tracking',
      body: 'Finalize shipments, upload <strong>Proof of Delivery</strong>, and keep a full audit trail with transport method and client info. Partial deliveries are supported.',
      position: 'bottom',
    },
    {
      target: '[data-tour="nav-logs"]',
      title: 'Activity Logs',
      body: 'Every action taken in the system is logged here: who did what and when. Useful for ops audits and handover reports.',
      position: 'bottom',
    },
    {
      target: null,
      title: "You're all set",
      body: 'You are browsing in <strong>demo mode</strong> (read-only). All data resets to this state automatically. Click <strong>Tour</strong> in the navigation anytime to replay this walkthrough.',
      position: 'center',
    },
  ];

  function el(id) {
    return document.getElementById(id);
  }

  function isMobileTourLayout() {
    return window.matchMedia(MOBILE_TOUR_QUERY).matches;
  }

  function applyTooltipLayout(tooltip) {
    const mobile = isMobileTourLayout();
    tooltip.style.cssText = [
      'position:fixed',
      'z-index:9999',
      mobile ? 'inset:auto 0 0 0' : '',
      mobile ? 'max-width:none' : 'max-width:360px',
      mobile ? 'width:auto' : 'width:calc(100vw - 32px)',
      'background:#0f172a',
      'color:#f1f5f9',
      mobile ? 'border-radius:18px 18px 0 0' : 'border-radius:12px',
      'box-shadow:0 18px 48px rgba(0,0,0,0.45)',
      mobile ? 'padding:18px 18px calc(18px + env(safe-area-inset-bottom, 0px))' : 'padding:20px 22px 16px',
      'font-family:inherit',
      mobile ? 'font-size:13px' : 'font-size:14px',
      'line-height:1.55',
      mobile ? 'max-height:min(72vh, 620px)' : '',
      mobile ? 'overflow:auto' : '',
      'transition:top 0.28s ease,left 0.28s ease,width 0.28s ease',
    ].filter(Boolean).join(';');
  }

  function buildUI() {
    const spotlight = document.createElement('div');
    spotlight.id = 'flx-tour-spotlight';
    spotlight.setAttribute('aria-hidden', 'true');
    spotlight.style.cssText = [
      'position:fixed',
      'border-radius:8px',
      'box-shadow:0 0 0 max(100vw,100vh) rgba(2,6,23,0.72)',
      'z-index:9998',
      'pointer-events:none',
      'transition:top 0.28s ease,left 0.28s ease,width 0.28s ease,height 0.28s ease',
      'outline:3px solid rgba(96,165,250,0.78)',
    ].join(';');

    const tooltip = document.createElement('div');
    tooltip.id = 'flx-tour-tooltip';
    tooltip.setAttribute('role', 'dialog');
    tooltip.setAttribute('aria-modal', 'true');
    tooltip.setAttribute('aria-live', 'polite');
    applyTooltipLayout(tooltip);

    tooltip.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:10px">
        <strong id="flx-tour-title" style="font-size:15px;color:#93c5fd"></strong>
        <button id="flx-tour-skip" title="Close tour"
          style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:18px;line-height:1;padding:0">×</button>
      </div>
      <div id="flx-tour-body" style="color:#cbd5e1;margin-bottom:16px"></div>
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
        <span id="flx-tour-counter" style="font-size:12px;color:#64748b"></span>
        <div style="display:flex;gap:8px;margin-left:auto">
          <button id="flx-tour-prev"
            style="padding:8px 14px;border-radius:8px;border:1px solid #334155;background:#020617;color:#94a3b8;cursor:pointer;font-size:13px">
            Back
          </button>
          <button id="flx-tour-next"
            style="padding:8px 16px;border-radius:8px;border:none;background:#2563eb;color:#fff;cursor:pointer;font-size:13px;font-weight:600">
            Next
          </button>
        </div>
      </div>`;

    const blocker = document.createElement('div');
    blocker.id = 'flx-tour-blocker';
    blocker.style.cssText = 'position:fixed;inset:0;z-index:9997;cursor:default';

    document.body.appendChild(blocker);
    document.body.appendChild(spotlight);
    document.body.appendChild(tooltip);

    return { spotlight, tooltip, blocker };
  }

  function positionSpotlight(spotlight, rect) {
    spotlight.style.top = (rect.top - PAD) + 'px';
    spotlight.style.left = (rect.left - PAD) + 'px';
    spotlight.style.width = (rect.width + PAD * 2) + 'px';
    spotlight.style.height = (rect.height + PAD * 2) + 'px';
  }

  function positionTooltip(tooltip, rect, position) {
    if (isMobileTourLayout()) {
      tooltip.style.top = 'auto';
      tooltip.style.left = '0';
      tooltip.style.right = '0';
      tooltip.style.bottom = '0';
      return;
    }

    const tw = tooltip.offsetWidth || 360;
    const th = tooltip.offsetHeight || 160;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    let top;
    let left;

    if (position === 'center' || !rect) {
      top = Math.max(16, (vh - th) / 2);
      left = Math.max(16, (vw - tw) / 2);
    } else if (position === 'bottom') {
      top = rect.bottom + PAD + 14;
      left = Math.max(16, Math.min(rect.left, vw - tw - 16));
    } else {
      top = rect.top - PAD - th - 14;
      left = Math.max(16, Math.min(rect.left, vw - tw - 16));
    }

    top = Math.max(16, Math.min(top, vh - th - 16));
    left = Math.max(16, Math.min(left, vw - tw - 16));

    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
  }

  function startTour() {
    if (el('flx-tour-tooltip')) return;

    let step = 0;
    const { spotlight, tooltip, blocker } = buildUI();

    function syncLayout() {
      applyTooltipLayout(tooltip);
      render(step);
    }

    function getTarget(selector) {
      if (!selector) return null;
      const matches = Array.from(document.querySelectorAll(selector));
      return matches.find((node) => {
        const rect = node.getBoundingClientRect();
        const styles = window.getComputedStyle(node);
        return styles.display !== 'none' && styles.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
      }) || matches[0] || null;
    }

    function ensureStepContext(targetSelector) {
      if (targetSelector === '#tab-timeline') {
        document.getElementById('tab-timeline')?.click();
      }
      if (targetSelector === '#orders-table-container') {
        document.getElementById('tab-orders')?.click();
      }
    }

    function scrollToTarget(target) {
      if (!target) return Promise.resolve();
      return new Promise((resolve) => {
        target.style.scrollMarginTop = isMobileTourLayout() ? '92px' : '120px';
        target.scrollIntoView({ behavior: 'smooth', block: isMobileTourLayout() ? 'start' : 'center' });
        setTimeout(resolve, isMobileTourLayout() ? 420 : 320);
      });
    }

    function updateSpotlight(rect) {
      if (!rect || isMobileTourLayout()) {
        spotlight.style.display = 'none';
        return;
      }

      spotlight.style.display = 'block';
      positionSpotlight(spotlight, rect);
    }

    async function render(index) {
      const current = STEPS[index];
      ensureStepContext(current.target);
      const target = getTarget(current.target);

      el('flx-tour-title').textContent = current.title;
      el('flx-tour-body').innerHTML = current.body;
      el('flx-tour-counter').textContent = `${index + 1} / ${STEPS.length}`;
      el('flx-tour-prev').disabled = index === 0;
      el('flx-tour-prev').style.opacity = index === 0 ? '0.4' : '1';
      el('flx-tour-next').textContent = index === STEPS.length - 1 ? 'Finish' : 'Next';

      if (target) {
        await scrollToTarget(target);
        const rect = target.getBoundingClientRect();
        updateSpotlight(rect);
        positionTooltip(tooltip, rect, current.position);
      } else {
        updateSpotlight(null);
        positionTooltip(tooltip, null, 'center');
      }
    }

    function closeTour() {
      [spotlight, tooltip, blocker].forEach((node) => node.remove());
      localStorage.setItem(TOUR_KEY, '1');
      const url = new URL(window.location);
      url.searchParams.delete('tour');
      window.history.replaceState({}, '', url);
      window.removeEventListener('resize', syncLayout);
    }

    el('flx-tour-skip').addEventListener('click', closeTour);
    el('flx-tour-prev').addEventListener('click', () => {
      if (step > 0) {
        step -= 1;
        render(step);
      }
    });
    el('flx-tour-next').addEventListener('click', () => {
      if (step < STEPS.length - 1) {
        step += 1;
        render(step);
      } else {
        closeTour();
      }
    });

    function onKey(event) {
      if (!el('flx-tour-tooltip')) {
        document.removeEventListener('keydown', onKey);
        return;
      }
      if (event.key === 'Escape') {
        closeTour();
        document.removeEventListener('keydown', onKey);
      }
      if (event.key === 'ArrowRight' && step < STEPS.length - 1) {
        step += 1;
        render(step);
      }
      if (event.key === 'ArrowLeft' && step > 0) {
        step -= 1;
        render(step);
      }
    }

    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', syncLayout);

    render(0);
  }

  window.startTour = startTour;

  document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const forced = params.get('tour') === '1';
    const fresh = !localStorage.getItem(TOUR_KEY);
    if (forced || fresh) {
      setTimeout(startTour, 500);
    }
  });
})();
