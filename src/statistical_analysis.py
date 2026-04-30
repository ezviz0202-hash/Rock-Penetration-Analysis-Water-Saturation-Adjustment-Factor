import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import f_oneway


def compute_summary_stats(df, group_cols, value_col):
    return (
        df.groupby(group_cols)[value_col]
        .agg(["mean", "std", "count"])
        .reset_index()
    )


def run_anova_by_saturation(df, value_col, rock_type=None):
    if rock_type:
        df = df[df["rock_type"] == rock_type]
    groups = [
        grp[value_col].values
        for _, grp in df.groupby("water_saturation")
    ]
    f_stat, p_val = f_oneway(*groups)
    return {"F_statistic": round(f_stat, 4), "p_value": round(p_val, 6)}


def compute_pearson_correlation(df, x_col, y_col):
    r, p = stats.pearsonr(df[x_col], df[y_col])
    return {"r": round(r, 4), "p_value": round(p, 6)}


def compute_spearman_correlation(df, x_col, y_col):
    r, p = stats.spearmanr(df[x_col], df[y_col])
    return {"rho": round(r, 4), "p_value": round(p, 6)}


def normality_test(series):
    stat, p = stats.shapiro(series[:50] if len(series) > 50 else series)
    return {"W_statistic": round(stat, 4), "p_value": round(p, 6)}


def build_correlation_matrix(df, cols):
    return df[cols].corr(method="pearson")


def group_means_by_saturation(df, value_col, rock_type=None, energy=None):
    mask = pd.Series([True] * len(df), index=df.index)
    if rock_type:
        mask &= df["rock_type"] == rock_type
    if energy:
        mask &= df["impact_energy_J"] == energy
    sub = df[mask]
    return sub.groupby("water_saturation")[value_col].agg(["mean", "std"]).reset_index()
