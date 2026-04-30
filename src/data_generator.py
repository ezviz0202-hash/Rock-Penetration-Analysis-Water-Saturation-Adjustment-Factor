import numpy as np
import pandas as pd

ROCK_PARAMS = {
    "andesite": {
        "base_strength": 180,
        "sw_sensitivity": 0.28,
        "peak_force_base": 12.5,
        "penetration_base": 2.1,
        "noise_scale": 0.08,
    },
    "tuff": {
        "base_strength": 95,
        "sw_sensitivity": 0.42,
        "peak_force_base": 7.8,
        "penetration_base": 3.6,
        "noise_scale": 0.10,
    },
}

IMPACT_ENERGIES = [80, 120, 160]
SATURATION_LEVELS = [0.0, 0.25, 0.50, 0.75, 1.00]
N_REPLICATES = 6
DT = 1e-5
T_TOTAL = 0.012


def _softening_factor(sw, sensitivity):
    """
    Rock softening factor.

    A smaller value means the rock is weaker under higher water saturation.
    For example:
        Sw = 0.0  -> sf close to 1.0
        Sw = 1.0  -> sf lower than 1.0
    """
    return 1.0 - sensitivity * sw + 0.04 * sw**2


def compute_trapezoid(y, x):
    """
    Compatible trapezoidal integration.

    np.trapezoid is available in newer NumPy versions.
    np.trapz works in older NumPy versions.
    """
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)


def generate_force_time(rock, sw, energy, rng):
    """
    Generate synthetic percussion force-time curve.

    Higher water saturation weakens the rock, so the peak resisting force
    decreases as saturation increases.
    """
    p = ROCK_PARAMS[rock]
    sf = _softening_factor(sw, p["sw_sensitivity"])

    t = np.arange(0, T_TOTAL, DT)

    t_rise = 0.0015
    t_peak = 0.0025
    t_fall = 0.0055

    envelope = np.zeros_like(t)

    mask1 = t < t_rise
    mask2 = (t >= t_rise) & (t < t_peak)
    mask3 = (t >= t_peak) & (t < t_fall)

    envelope[mask1] = (t[mask1] / t_rise) ** 2
    envelope[mask2] = 1.0
    envelope[mask3] = np.exp(-5.0 * (t[mask3] - t_peak))

    scale = p["peak_force_base"] * sf * (energy / 120) ** 0.6

    noise = rng.normal(0, p["noise_scale"] * scale, size=len(t))
    high_freq = 0.05 * scale * np.sin(2 * np.pi * 800 * t) * np.exp(-t / 0.003)

    force = scale * envelope + noise + high_freq
    force = np.maximum(force, 0)

    return t, force


def extract_indicators(t, force, rock, sw, energy, rng):
    """
    Extract penetration indicators from force-time response.

    Physical logic:
    - Water saturation weakens the rock.
    - Weaker rock gives lower peak force.
    - Weaker rock allows greater penetration depth.
    - Greater penetration depth reduces specific energy.
    """
    p = ROCK_PARAMS[rock]
    sf = _softening_factor(sw, p["sw_sensitivity"])

    peak_force = np.max(force)
    impulse = compute_trapezoid(force, t)

    # Since sf decreases with water saturation, 1/sf increases with saturation.
    # This makes penetration depth increase when the rock becomes weaker.
    penetration_factor = 1.0 / sf

    pen_base = (
        p["penetration_base"]
        * penetration_factor
        * (energy / 120) ** 0.75
    )

    penetration = pen_base * (1 + rng.normal(0, 0.05))

    # Specific energy = input energy / removed volume.
    # A larger penetration depth gives a larger removed volume,
    # therefore lower specific energy.
    bit_radius_m = 6e-3
    removed_volume = pen_base * 1e-3 * np.pi * bit_radius_m**2
    specific_energy = energy / removed_volume

    specific_energy = specific_energy * (1 + rng.normal(0, 0.06))

    efficiency = penetration / (energy / 1000) * (1 + rng.normal(0, 0.04))

    return {
        "peak_force_kN": round(peak_force, 4),
        "impulse_kNs": round(impulse, 6),
        "penetration_mm": round(penetration, 4),
        "specific_energy_MJm3": round(specific_energy / 1e6, 4),
        "impact_efficiency": round(efficiency, 4),
    }


def generate_dataset(seed=42):
    rng = np.random.default_rng(seed)

    records = []
    ft_curves = {}

    for rock in ["andesite", "tuff"]:
        for sw in SATURATION_LEVELS:
            for energy in IMPACT_ENERGIES:
                for rep in range(N_REPLICATES):
                    t, force = generate_force_time(rock, sw, energy, rng)
                    ind = extract_indicators(t, force, rock, sw, energy, rng)

                    row = {
                        "rock_type": rock,
                        "water_saturation": sw,
                        "impact_energy_J": energy,
                        "replicate": rep + 1,
                        **ind,
                    }

                    records.append(row)

                    key = (rock, sw, energy)
                    if rep == 0:
                        ft_curves[key] = (t, force)

    df = pd.DataFrame(records)

    return df, ft_curves


if __name__ == "__main__":
    df, _ = generate_dataset()
    df.to_csv("data/experimental_data.csv", index=False)
    print(df.head())