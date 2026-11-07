---
name: reference-tt-workspace
description: Where the TT survey data, cloned reference repos, PCB repos, and shuttle index live in ~/projects/tt
metadata:
  type: reference
---

- `~/projects/tt/NOTES.md`: prior-work survey, ΣΔ applications, TT analog constraints, PCB info
- `~/projects/tt/data/idx_<shuttle>.json`: project lists for each shuttle. Refetch from `https://index.tinytapeout.com/<id>.json`; `https://index.tinytapeout.com/` lists all shuttles.
- `~/projects/tt/repos/{sd-analog,sd-digital,decimation,adc-ref,sd-ihp}`: shallow clones of reference designs. Best analog ΣΔ reference: `sd-analog/pthomas-sigma-delta-design` (gitlab.com/pthomas1/sigma-delta). Best decimator: `decimation/tt09-decimation_filter` (bmurmann).
- `~/projects/tt/pcb/`: tt-demo-pcb (current ETR dbv3 with RP2350; analog on a 100-mil header), breakout-pcb, tt-micropython-firmware
- `~/projects/tt/WORKFLOW.md`: working rules adapted from the AlphaOneSoC export; the original is in `process/export-2026-11-07/` (templates, sandbox scripts, `home/` bridge files)
- `~/projects/tt/.claude/agents/`: sd-adc-design-reviewer, rtl-verification-engineer, pd-expert; `work/<campaign>/` for ledgers and work orders
- The `gh` CLI is not installed. Use the GitHub REST API through curl.

Related: [[project-sigma-delta-tt]]
