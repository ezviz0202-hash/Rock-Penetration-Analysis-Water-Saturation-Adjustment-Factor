import numpy as np
from scipy.optimize import curve_fit


def model_linear(sw, a):
    return 1.0 + a * sw


def model_quadratic(sw, a, b):
    return 1.0 + a * sw + b * sw**2


def model_exponential(sw, a):
    return np.exp(a * sw)


def model_power(sw, a, b):
    """
    Power-type water saturation adjustment factor.

    For the current physical assumption:
    - Water saturation weakens the rock.
    - Penetration / ROP increases with Sw.
    - Therefore f(Sw) should generally be >= 1.

    Formula:
        f(Sw) = 1 + a * Sw^b

    Parameter bounds in fit_all_models keep a and b positive.
    """
    return 1.0 + a * (sw**b)


MODELS = {
    "linear": (model_linear, ["a"]),
    "quadratic": (model_quadratic, ["a", "b"]),
    "exponential": (model_exponential, ["a"]),
    "power": (model_power, ["a", "b"]),
}


def compute_adjustment_factors(summary_df, value_col):
    """
    Compute f(Sw) from grouped mean values.

    f(Sw) = value(Sw) / value(Sw=0)

    For penetration or ROP:
        f(Sw) > 1 means water saturation increases penetration performance.
    """
    sw = summary_df["water_saturation"].values
    mean_vals = summary_df["mean"].values

    rop0 = mean_vals[0] if mean_vals[0] != 0 else 1.0
    f_sw = mean_vals / rop0

    return sw, f_sw, rop0


def fit_all_models(sw, f_sw):
    """
    Fit all candidate adjustment factor models.

    Bounds are used to avoid non-physical parameter values and numerical warnings.
    """
    results = {}

    p0_map = {
        "linear": [0.3],
        "quadratic": [0.3, 0.05],
        "exponential": [0.3],
        "power": [0.3, 1.0],
    }

    bounds_map = {
        "linear": ([0.0], [3.0]),
        "quadratic": ([0.0, -3.0], [3.0, 3.0]),
        "exponential": ([0.0], [3.0]),
        "power": ([0.0, 0.05], [3.0, 5.0]),
    }

    for name, (func, param_names) in MODELS.items():
        try:
            popt, pcov = curve_fit(
                func,
                sw,
                f_sw,
                p0=p0_map[name],
                bounds=bounds_map[name],
                maxfev=10000,
            )

            f_pred = func(sw, *popt)

            ss_res = np.sum((f_sw - f_pred) ** 2)
            ss_tot = np.sum((f_sw - np.mean(f_sw)) ** 2)

            r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
            rmse = np.sqrt(np.mean((f_sw - f_pred) ** 2))

            params = dict(zip(param_names, popt))

            results[name] = {
                "params": params,
                "R2": round(r2, 5),
                "RMSE": round(rmse, 6),
                "f_pred": f_pred,
            }

        except Exception as e:
            results[name] = None
            print(f"[warning] Model fitting failed for {name}: {e}")

    return results


def select_best_model(fit_results):
    """
    Select the best model by highest R2.
    """
    valid = {k: v for k, v in fit_results.items() if v is not None}

    if not valid:
        return None

    return max(valid, key=lambda k: valid[k]["R2"])


def predict_rop(rop0, sw_new, model_name, params):
    """
    Predict ROP under a given water saturation level.

    ROP = ROP0 * f(Sw)
    """
    func = MODELS[model_name][0]
    param_vals = list(params.values())

    f = func(sw_new, *param_vals)

    return rop0 * f