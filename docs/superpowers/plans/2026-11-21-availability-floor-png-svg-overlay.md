# Availability PNG-in-SVG Overlay Plan

> **For agentic workers:** Use executing-plans or inline implementation.

**Goal:** Replace failed full-vector `floor_plan.svg` with raster `floor_plan.png` inside SVG plus hotspot overlays.

**Spec:** [`docs/superpowers/specs/2026-11-21-availability-floor-png-svg-overlay-design.md`](../specs/2026-11-21-availability-floor-png-svg-overlay-design.md)

**Tasks:** `floor_plan_hotspots.py` → `public.py` context → rewrite `floor_plan.svg` → update tests → visual calibration in browser.