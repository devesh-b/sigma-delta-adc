# design/

- `params.py`: single source of truth for SPEC §1/§3/§6 numbers. `python3 design/params.py` writes `design/spice/params.spice` (generated, not committed).
- `tests/test_params.py`: `python3 -m pytest design/tests -q`.
- Known model differences (recorded, not fixed): model default fs 1 MHz vs SPEC 2 MHz; vref 2.048 V vs SPEC 1.2 V provisional.
