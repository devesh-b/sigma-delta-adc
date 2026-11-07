#!/usr/bin/env python3
"""Single source of truth for v1 design numbers (SPEC.md §1, §3, §6).

Running `python3 design/params.py` writes design/spice/params.spice
(generated; not committed). Pattern: Paul Thomas params.py.
"""
import itertools
import os

# ---- SPEC §1: loop and clock ------------------------------------------------
ORDER = 2
FS_NOM = 2e6                       # Hz, nominal
FS_RANGE = (0.25e6, 4e6)           # Hz
FS_PRECISION = (0.25e6, 2e6)       # Hz, precision mode (SPEC §1)
FS_FAST = 4e6                      # Hz, fast / low-resolution mode (D13)
N_SET = (64, 256, 1024, 4096)      # cycles per conversion
N_PRECISION = 4096                 # precision modes, 3.75-60 SPS (D23)
N_FAST = (64, 256, 1024)           # fast / low-resolution modes
K = 0.5                            # stage-2 feedback coefficient (option B, D17)

# ---- SPEC §3.4 capacitors (F) ----------------------------------------------
CS1 = 0.5e-12                      # D22: shared Cs (input = DAC cap)
CINT1 = 4e-12                      # option B: c1 = 0.5p/4p = 0.125 (D17, D22)
CS2 = 0.5e-12                      # stage 2: see work/v1-design/results/s3_budget.md item 3
CINT2 = 1e-12                      # c2 = 0.5

# c1 = Cs1/Cint1 ; c2 = Cs2/Cint2
C1 = CS1 / CINT1
C2 = CS2 / CINT2

# ---- Reference (SPEC §1 VREF row) ------------------------------------------
VREF_OPTION = "B"                  # v1 nominal = option B (D17/D18); A/A2 kept for reference
VREF_NOM = 2.048                   # V (option B)
VREF_OPTIONS = {
    "A_1p2V": {"vref": 1.2, "c1": 0.25, "c2": 0.5, "k": 1.0},
    "A2_1p2V": {"vref": 1.2, "c1": 0.25, "c2": 0.25, "k": 1.0},
    "B_2p048V": {"vref": 2.048, "c1": 0.125, "c2": 0.5, "k": 0.5},  # swing halved via c1, k
}
# Pads (D24): ua0 VIN+, ua1 VIN-, ua2 VREF+, ua3 VREF- (Kelvin to sensor ground)
PINS = {"ua0": "VIN+", "ua1": "VIN-", "ua2": "VREF+", "ua3": "VREF-"}
PAD_R = 500.0                      # ohm, each pad path
PAD_C = 5e-12                      # F
OVERLOAD_RANGE = (1.0, 1.1)        # x VREF; must recover on the next conversion (D21)
# PGA: none in v1 (D14); any PGA gain is a stretch goal and has no entry here.

# ---- Chopping (D17/D18) ------------------------------------------------------
# OTA chop is a config bit valid only together with system chop; N must be even
# (chop phase restarts at every reset, so a conversion holds whole chop periods).
CHOP_SYSTEM = True
CHOP_OTA = True


def chop_config_valid(system, ota, n):
    return (not ota or system) and n % 2 == 0


# ---- Offsets (D21) -----------------------------------------------------------
VOS_3SIGMA = 9e-3                  # V, budgeting value for OTA1 and OTA2 input offset

# ---- Supplies ---------------------------------------------------------------
VAPWR = 3.3
VDPWR = 1.8
CM = VAPWR / 2                     # common mode

# ---- OTA targets (SPEC §3.1) ------------------------------------------------
OTA_A0_DB_MIN = 80.0               # SPEC §3.1 (user Q6)
OTA_GBW_MIN = 10e6                 # Hz required
OTA_GBW_TARGET = 20e6              # Hz design target
OTA_PM_MIN = 60.0                  # deg
OTA_SR_MIN = 10e6                  # V/s (10 V/us)

# ---- Comparator / reference -------------------------------------------------
COMP_OFFSET_MAX = 20e-3            # V budget
TAU_REF_FRAC = 0.2                 # tau_ref <= 0.2 * t_half

# ---- SPEC §6 corner set -----------------------------------------------------
CORNERS_PROCESS = ("tt", "ss", "ff", "sf", "fs")
TEMPS = (-40, 27, 125)             # C
VAPWR_SET = (3.0, 3.3, 3.6)
VDPWR_SET = (1.62, 1.8, 1.98)
CORNERS_RC = ("ss_hh", "ff_ll")    # RC-only corners (R and C extremes, MOS typical)
# Monte Carlo: key = .lib section, value = runs. "<worst>_mm" is a PLACEHOLDER key: replace it with the actual
# worst-case MOS corner's mismatch section (e.g. "ss_mm") once S3/C10 identify it. The tests only
# accept it because the placeholder is listed in MC_PLACEHOLDERS.
MC_RUNS = {"tt_mm": 200, "<worst>_mm": 50}
MC_PLACEHOLDERS = ("<worst>_mm",)
FS_SET = (0.25e6, 2e6, 4e6)

# ---- Derived ----------------------------------------------------------------
T_HALF = 1.0 / (2.0 * FS_NOM)            # t_half = 1/(2 fs) = 250 ns at 2 MHz
TAU_REF_MAX = TAU_REF_FRAC * T_HALF
ZIN = 1.0 / (FS_NOM * CS1)               # Zin ~ 1/(fs*Cs) = 1 MOhm at 2 MHz
# Analog PVT list (SPEC §6): (5 MOS + 2 RC corners) x 3 temp x 3 VAPWR = 63 points
PVT_LIST_ANALOG = [
    {"proc": p, "temp": t, "vapwr": va}
    for p, t, va in itertools.product(
        CORNERS_PROCESS + CORNERS_RC, TEMPS, VAPWR_SET)
]
# Digital PVT list: 5 MOS x 3 temp x 3 VAPWR x 3 VDPWR (own axis) = 135 points
PVT_LIST_DIGITAL = [
    {"proc": p, "temp": t, "vapwr": va, "vdpwr": vd}
    for p, t, va, vd in itertools.product(
        CORNERS_PROCESS, TEMPS, VAPWR_SET, VDPWR_SET)
]


def scalars():
    """Name -> scalar value, written to params.spice."""
    return {
        "fs_nom": FS_NOM, "fs_min": FS_RANGE[0], "fs_max": FS_RANGE[1],
        "order": ORDER, "k": K, "n_precision": N_PRECISION, "vos_3sigma": VOS_3SIGMA,
        "overload_max": OVERLOAD_RANGE[1], "pad_r": PAD_R, "pad_c": PAD_C,
        "cs1": CS1, "cint1": CINT1, "cs2": CS2, "cint2": CINT2,
        "c1": C1, "c2": C2,
        "vref": VREF_NOM, "fs_fast": FS_FAST, "fs_prec_min": FS_PRECISION[0], "fs_prec_max": FS_PRECISION[1], "vapwr": VAPWR, "vdpwr": VDPWR, "cm": CM,
        "ota_a0_db_min": OTA_A0_DB_MIN, "ota_gbw_min": OTA_GBW_MIN,
        "ota_gbw_target": OTA_GBW_TARGET, "ota_pm_min": OTA_PM_MIN,
        "ota_sr_min": OTA_SR_MIN,
        "comp_offset_max": COMP_OFFSET_MAX, "tau_ref_frac": TAU_REF_FRAC,
        "t_half": T_HALF, "tau_ref_max": TAU_REF_MAX, "zin": ZIN,
    }


def write_spice(path=None):
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "spice", "params.spice")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("* generated by design/params.py - do not edit\n")
        for k, v in scalars().items():
            f.write(f".param {k} = {v!r}\n")
    return path


if __name__ == "__main__":
    print(write_spice())
