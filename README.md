# Rock Penetration Analysis — Water-Saturation Adjustment Factor

A preliminary synthetic-data-based analysis prototype to explore the possible influence of **water saturation** on rock drill bit penetration performance, and to derive an interpretable **adjustment factor** suitable for future field ROP (Rate of Penetration) prediction.

**Note:** This project currently uses synthetic demonstration data generated from physically motivated assumptions. The present results should not be interpreted as experimentally validated findings.

---

## Research Background

In real field operations, water saturation levels in rocks vary significantly due to groundwater or rainfall. This directly affects excavation efficiency, specific energy consumption, and bit wear. While the effects of water saturation on static mechanical properties (compression, tension) are well established, their application to **dynamic percussion drilling** remains limited.

This project builds a reproducible analysis pipeline that:
1. Processes force–time curves from percussion drilling data
2. Extracts key penetration indicators
3. Performs statistical significance testing
4. Fits a simple, physically interpretable water-saturation adjustment factor

---

## Prototype Demonstration Results

The following results are based on synthetic demonstration data. They are intended to show the structure of the analysis pipeline rather than to claim experimentally validated conclusions.

### Force–Time Curves

Filtered force–time responses under varying water saturation levels for both rock types and three impact energy levels.

![Force-Time Curves](figures/fig1_force_time_curves.png)

---

### Penetration Depth vs Water Saturation

In the synthetic demonstration dataset, penetration depth was modeled to increase with water saturation due to reduced rock resistance, with the effect more pronounced for tuff than andesite.

![Penetration Depth](figures/fig2_penetration_depth.png)

---

### Specific Energy vs Water Saturation

In the synthetic demonstration dataset, specific energy was modeled to decrease with saturation, indicating that less energy may be required to penetrate saturated rock.

![Specific Energy](figures/fig3_specific_energy.png)

---

### Correlation Analysis

Correlation matrices reveal the modeled relationships between water saturation, impact energy, and penetration performance indicators in the synthetic demonstration dataset.

![Correlation Heatmap](figures/fig4_correlation_heatmap.png)

---

### Adjustment Factor f(Sw) — Model Fitting

Four models are fitted to the synthetic demonstration data. The best-performing model (highest R²) is highlighted.

| Rock | Best Model | R² |
|---|---|---|
| Andesite | Power | 0.9746 |
| Tuff | Quadratic | 0.9978 |

The fitted adjustment factors are:

```
Andesite: f(Sw) = 1 + 0.2862 × Sw^1.3674
Tuff:     f(Sw) = 1 + 0.2636 × Sw + 0.3922 × Sw²
```

At full saturation (`Sw = 1.0`), the fitted adjustment factor in the synthetic demonstration dataset indicates an approximate ROP increase of 28.6% for andesite and 65.6% for tuff relative to dry conditions.

![Adjustment Factor](figures/fig5_adjustment_factor.png)

---

### ANOVA Results

One-way ANOVA on the synthetic demonstration dataset indicates statistically significant differences among modeled water-saturation groups for all penetration indicators for both rock types.

Significance levels shown in the figure are defined as: `*` p<0.05, `**` p<0.01, `***` p<0.001. Here, a larger F-statistic indicates a stronger difference among water-saturation groups for the corresponding penetration indicator.

![ANOVA Summary](figures/fig6_anova_summary.png)

---

## Project Structure

```
rock-penetration-analysis/
├── run_analysis.py           # Main entry point
├── requirements.txt
├── data/
│   └── experimental_data.csv # Generated synthetic demonstration dataset
├── src/
│   ├── data_generator.py     # Synthetic data with physical basis
│   ├── signal_processing.py  # Force-time curve processing
│   ├── statistical_analysis.py
│   └── adjustment_factor.py  # f(Sw) model fitting
└── figures/                  # All output plots
```

---

## Installation

```bash
git clone (https://github.com/ezviz0202-hash/Rock-Penetration-Analysis-Water-Saturation-Adjustment-Factor)
cd rock-penetration-analysis
pip install -r requirements.txt
python run_analysis.py
```

---

## Methodology

### 1. Force–Time Curve Processing

Synthetic percussion force signals are filtered using a 4th-order Butterworth low-pass filter (cutoff: 2 kHz) to remove high-frequency noise while preserving impact dynamics. Peak detection and impulse integration are then applied.

### 2. Indicator Extraction

| Indicator | Description |
|---|---|
| Penetration Depth (mm) | Depth per blow under given impact energy |
| Peak Impact Force (kN) | Maximum recorded impact force |
| Specific Energy (MJ/m³) | Energy per unit volume of rock removed |
| Impact Efficiency | Penetration per unit energy input |

### 3. Statistical Analysis

- **Pearson / Spearman Correlation** between Sw and each indicator
- **One-Way ANOVA** to test whether saturation levels produce statistically significant differences
- Significance levels: `*` p<0.05, `**` p<0.01, `***` p<0.001

### 4. Adjustment Factor Fitting

Four candidate functional forms for f(Sw) are evaluated:

| Model | Formula |
|---|---|
| Linear | 1 + a·Sw |
| Quadratic | 1 + a·Sw + b·Sw² |
| Exponential | exp(a·Sw) |
| Power | 1 + a·Sw^b |

The best model is selected based on R², RMSE, and physical plausibility.

The adjustment factor is incorporated into field ROP prediction as:

```
ROP = ROP₀ × f(Sw)
```

where ROP₀ is the baseline penetration rate under dry conditions.

---

## Reference

Hashiba, K. and Fukui, K. (2024). Penetration Characteristics of a Rock Drill Bit into Rock. *Journal of MMIJ*.

---

## License

MIT
