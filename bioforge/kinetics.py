"""
kinetics.py - the maths engine behind the enzyme simulator.

These formulas are a line-by-line Python port of the original BioForge
TypeScript engine, so the biology behaves exactly like the website did:

    1. Michaelis-Menten rate      v = Vmax * [S] / (Km + [S])
    2. Temperature modifier       Gaussian bell around the optimum,
                                  sharp collapse above 55 C (denaturation)
    3. pH modifier                Gaussian bell around the optimum pH
    4. Stirring modifier          gentle 0.85x, medium 1.0x, vigorous 1.18x

The functions take plain numbers (or NumPy arrays) and return numbers,
so they are easy to test and reuse anywhere.
"""

import math

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Model constants
# ---------------------------------------------------------------------------
DENATURATION_TEMP_C = 55.0   # above this, protein folds are destroyed
PH_STRESS_LIMIT = 1.5        # |pH - optimum| above this = "pH stressed"
TEMP_SIGMA = 14.0            # width of the temperature bell curve (C)
PH_SIGMA = 1.6               # width of the pH bell curve (pH units)

STIR_FACTORS = {1: 0.85, 2: 1.0, 3: 1.18}
STIR_LABELS = {1: "Gentle (1x)", 2: "Medium (2x)", 3: "Vigorous (3x)"}

VESSEL_VOLUME_ML = 5.2       # product (umol) = concentration (mM) x volume (mL)
RUN_DURATION_S = 20.0        # one experiment lasts 20 simulated seconds
TIME_STEP_S = 0.1            # the engine updates every 0.1 s
RECORD_EVERY_STEPS = 5       # store a data point every 0.5 s
MAX_YIELD_PCT = 98.5         # equilibrium ceiling at ideal conditions
CONVERSION_GAIN = 0.045      # fraction of the remaining gap closed per step


# ---------------------------------------------------------------------------
# 1. Core rate laws
# ---------------------------------------------------------------------------
def michaelis_menten(substrate_mM, vmax, km):
    """Reaction velocity v (umol/s) at substrate concentration [S] (mM).

    Works for a single number or a whole NumPy array of concentrations.
    """
    return vmax * substrate_mM / (km + substrate_mM)


def lineweaver_burk(substrate_mM, vmax, km):
    """Double-reciprocal transform: returns (1/[S], 1/v).

    Plotting 1/v against 1/[S] gives a straight line:
        1/v = (Km/Vmax) * (1/[S]) + 1/Vmax
    slope = Km/Vmax, y-intercept = 1/Vmax, x-intercept = -1/Km
    """
    substrate_mM = np.asarray(substrate_mM, dtype=float)
    velocity = michaelis_menten(substrate_mM, vmax, km)
    return 1.0 / substrate_mM, 1.0 / velocity


# ---------------------------------------------------------------------------
# 2. Environmental modifiers (each returns a factor between 0 and 1)
# ---------------------------------------------------------------------------
def temperature_factor(temp_c, optimal_temp):
    """Activity multiplier from temperature."""
    if temp_c > DENATURATION_TEMP_C:
        # rapid thermal unfolding above 55 C
        return max(0.01, 0.06 * math.exp(-(temp_c - DENATURATION_TEMP_C) / 4))
    delta_t = temp_c - optimal_temp
    return math.exp(-(delta_t ** 2) / (2 * TEMP_SIGMA ** 2))


def ph_factor(ph, optimal_ph):
    """Activity multiplier from pH (bell curve)."""
    delta_ph = ph - optimal_ph
    return math.exp(-(delta_ph ** 2) / (2 * PH_SIGMA ** 2))


def stir_factor(stirring_rate):
    """Activity multiplier from stirring (1 = gentle, 2 = medium, 3 = vigorous)."""
    return STIR_FACTORS[stirring_rate]


def is_denatured(temp_c):
    return temp_c > DENATURATION_TEMP_C


def is_ph_stressed(ph, optimal_ph):
    return abs(ph - optimal_ph) > PH_STRESS_LIMIT


# ---------------------------------------------------------------------------
# 3. Everything the simulator needs, calculated in one go
# ---------------------------------------------------------------------------
def compute_kinetics(enzyme, temp_c, ph, stirring_rate, substrate_mM):
    """Return a dictionary with the velocity, modifiers and efficiency score."""
    mm_velocity = michaelis_menten(substrate_mM, enzyme["vmax"], enzyme["km"])
    t_factor = temperature_factor(temp_c, enzyme["optimal_temp"])
    p_factor = ph_factor(ph, enzyme["optimal_ph"])
    s_factor = stir_factor(stirring_rate)

    effective_rate = mm_velocity * t_factor * p_factor * s_factor
    if is_denatured(temp_c):
        # a denatured enzyme can only keep a tiny residual activity
        effective_rate = min(effective_rate, enzyme["vmax"] * 0.04)

    efficiency = round(t_factor * p_factor * (s_factor / 1.18) * 100)
    efficiency = max(1, min(99, efficiency))

    return {
        "michaelis_velocity": mm_velocity,
        "effective_rate": effective_rate,
        "efficiency": efficiency,
        "temp_factor": t_factor,
        "ph_factor": p_factor,
        "stir_factor": s_factor,
        "denatured": is_denatured(temp_c),
        "ph_stressed": is_ph_stressed(ph, enzyme["optimal_ph"]),
    }


def yield_ceiling(progress_pct, kinetics):
    """Maximum % conversion the reaction can reach under current conditions."""
    if kinetics["denatured"]:
        return min(progress_pct + 1, 40)
    if kinetics["ph_stressed"]:
        return 75 * kinetics["ph_factor"]
    return MAX_YIELD_PCT


def simulate_reaction(enzyme, temp_c, ph, stirring_rate, substrate_mM):
    """Run one 20-second virtual experiment and return it as a DataFrame.

    Every 0.1 s the reaction closes a fraction of the gap between the current
    progress and the yield ceiling. Faster enzymes (higher effective rate
    compared with Vmax) close the gap faster.
    """
    kinetics = compute_kinetics(enzyme, temp_c, ph, stirring_rate, substrate_mM)
    rate_multiplier = kinetics["effective_rate"] / max(enzyme["vmax"], 1)

    progress = 0.0
    records = [(0.0, 0.0)]
    total_steps = int(round(RUN_DURATION_S / TIME_STEP_S))

    for step in range(1, total_steps + 1):
        time_s = step * TIME_STEP_S
        ceiling = yield_ceiling(progress, kinetics)
        increment = (ceiling - progress) * (CONVERSION_GAIN * max(0.05, rate_multiplier))
        progress = min(ceiling, progress + max(0.005, increment))

        if step % RECORD_EVERY_STEPS == 0 or progress >= 99.9:
            records.append((time_s, progress))
        if progress >= 99.5:
            break

    df = pd.DataFrame(records, columns=["time_s", "progress_pct"])
    df["product_umol"] = substrate_mM * (df["progress_pct"] / 100) * VESSEL_VOLUME_ML
    df["substrate_remaining_mM"] = (substrate_mM * (1 - df["progress_pct"] / 100)).clip(lower=0)
    return df


def export_table(run_df, enzyme, temp_c, ph):
    """Format a finished run like the original 'Export Data (CSV)' button."""
    table = pd.DataFrame(
        {
            "Time (s)": run_df["time_s"].round(1),
            "Progress (%)": run_df["progress_pct"].round(1),
            "Product Formed (umol)": run_df["product_umol"].round(1),
            "Substrate Remaining (mM)": run_df["substrate_remaining_mM"].round(1),
        }
    )
    table["Temperature (C)"] = temp_c
    table["pH"] = round(ph, 1)
    table["Enzyme"] = enzyme["name"]
    return table


# ---------------------------------------------------------------------------
# 4. Quick "teaser" score used on the Overview page (same as the website)
# ---------------------------------------------------------------------------
def teaser_activity(temp_c, ph, optimal_temp, optimal_ph, vmax):
    """Return (activity score %, velocity in mmol/min) for the 3-step demo."""
    temp_eff = math.exp(-((temp_c - optimal_temp) ** 2) / 320)
    if temp_c > DENATURATION_TEMP_C:
        temp_eff = max(0.0, temp_eff * (1 - (temp_c - DENATURATION_TEMP_C) / 20))
    ph_eff = math.exp(-((ph - optimal_ph) ** 2) / 3.2)
    score = max(2, min(99, round(temp_eff * ph_eff * 100)))
    velocity = (score / 100) * vmax * 0.38
    return score, velocity


# ---------------------------------------------------------------------------
# 5. Small helpers used for the descriptive badges
# ---------------------------------------------------------------------------
def affinity_label(km):
    if km < 3:
        return "High Affinity"
    if km < 12:
        return "Moderate"
    return "Low Affinity"


def turnover_label(vmax):
    if vmax > 20:
        return "Ultra Fast"
    if vmax > 10:
        return "Efficient"
    return "Moderate"


def specificity_constant(vmax, km):
    """Vmax / Km - a simple 'grip + speed' score."""
    return vmax / km
