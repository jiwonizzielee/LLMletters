"""
Reconstructed from the ad-hoc `python3 << EOF` commands run directly in the
shell during the analysis session on 2026-09-08 (never originally saved as a
file). Produces every file currently committed under analysis/:

  descriptive_by_race_per300.csv
  descriptive_by_gender_per300.csv
  descriptive_by_race_gender_per300.csv
  results_omnibus_race_effect.csv
  results_race_strength_interaction.csv
  results_variance_decomposition.csv
  fig1_category_by_race.png
  fig2_effect_size_ranking.png
  fig3_strength_interaction.png
  fig4_variance_decomposition.png

Inputs (expected in this directory): "strong full analysis.csv",
"moderate analysis.csv" (4800 rows each, one row per generated letter).

Run from inside analysis/:  python3 run_analysis.py
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

CATS = ["standout", "ability", "grindstone", "communal", "agentic", "competitive"]
RACE_ORDER = ["White", "Black", "Asian", "Hispanic/Latinx", "Hawaiian/Pacific Islander"]
PALETTE = dict(zip(RACE_ORDER, ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"]))


def load(fname, strength):
    df = pd.read_csv(fname)
    assert len(df) == 4800, f"{fname} has {len(df)} rows, expected 4800"
    df["strength"] = strength
    for c in CATS:
        assert df[c + " count"].isna().sum() == 0
        df[c + "_norm"] = df[c + " count"] / df["Total words"] * 300  # per-300-word rate
    return df


def summarize(sub, group_cols):
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    rows = []
    for keys, gsub in sub.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        for c in CATS:
            vals = gsub[c + "_norm"]
            n = len(vals)
            mean = vals.mean()
            sd = vals.std(ddof=1)
            se = sd / np.sqrt(n)
            ci_lo, ci_hi = stats.t.interval(0.95, n - 1, loc=mean, scale=se)
            row = dict(zip(group_cols, keys))
            row.update(
                {
                    "Category": c,
                    "Letters": n,
                    "Mean_per300": round(mean, 4),
                    "SD_per300": round(sd, 4),
                    "CI_lower": round(ci_lo, 4),
                    "CI_upper": round(ci_hi, 4),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def descriptive_tables(strong, moderate, df):
    # --- by racial group ---
    race_rows = []
    for strength_label, sub in [("Strong", strong), ("Moderate", moderate), ("Combined", df)]:
        t = summarize(sub, "racial_group")
        t.insert(0, "Strength", strength_label)
        race_rows.append(t)
    race_out = pd.concat(race_rows, ignore_index=True).rename(columns={"racial_group": "Racial_Group"})
    race_out.to_csv("descriptive_by_race_per300.csv", index=False)

    # --- by gender ---
    gender_rows = []
    for strength_label, sub in [("Strong", strong), ("Moderate", moderate), ("Combined", df)]:
        t = summarize(sub, "gender_identity")
        t.insert(0, "Strength", strength_label)
        gender_rows.append(t)
    gender_out = pd.concat(gender_rows, ignore_index=True).rename(columns={"gender_identity": "Gender"})
    gender_out.to_csv("descriptive_by_gender_per300.csv", index=False)

    # --- by racial group x gender ---
    rg_rows = []
    for strength_label, sub in [("Strong", strong), ("Moderate", moderate), ("Combined", df)]:
        t = summarize(sub, ["racial_group", "gender_identity"])
        t.insert(0, "Strength", strength_label)
        rg_rows.append(t)
    rg_out = pd.concat(rg_rows, ignore_index=True).rename(
        columns={"racial_group": "Racial_Group", "gender_identity": "Gender"}
    )
    col_order = ["Strength", "Racial_Group", "Gender", "Category", "Letters", "Mean_per300", "SD_per300", "CI_lower", "CI_upper"]
    rg_out[col_order].to_csv("descriptive_by_race_gender_per300.csv", index=False)

    print("Wrote descriptive_by_race_per300.csv, descriptive_by_gender_per300.csv, descriptive_by_race_gender_per300.csv")
    return race_out, gender_out, rg_out


def inferential_tables(df):
    # 1) Omnibus ANOVA of racial_group per category
    rows = []
    for c in CATS:
        m = smf.ols(f"{c}_norm ~ C(racial_group)", data=df).fit()
        aov = sm.stats.anova_lm(m, typ=2)
        ss_e, ss_r = aov.loc["C(racial_group)", "sum_sq"], aov.loc["Residual", "sum_sq"]
        eta2 = ss_e / (ss_e + ss_r)
        rows.append((c, aov.loc["C(racial_group)", "F"], aov.loc["C(racial_group)", "PR(>F)"], eta2))
    omni = pd.DataFrame(rows, columns=["category", "F", "p_raw", "eta2"])
    omni["p_fdr"] = multipletests(omni["p_raw"], method="fdr_bh")[1]
    omni = omni.sort_values("eta2", ascending=False)
    omni.to_csv("results_omnibus_race_effect.csv", index=False)
    print("=== Omnibus race effect per category (FDR-corrected) ===")
    print(omni.round(4).to_string(index=False))

    # 2) Race x strength interaction per category
    rows = []
    for c in CATS:
        formula = (
            f"{c}_norm ~ C(racial_group)*C(strength) + C(gender_identity)+C(major)"
            "+C(quant_level)+C(volunteer_level)+C(rigor_level)+C(ec_level)"
        )
        m = smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df["name_id"]})
        inter = [p for p in m.params.index if ":" in p and "strength" in p]
        test = m.f_test([f"{p} = 0" for p in inter])
        rows.append((c, float(test.fvalue), float(test.pvalue)))
    inter_df = pd.DataFrame(rows, columns=["category", "F", "p_raw"])
    inter_df["p_fdr"] = multipletests(inter_df["p_raw"], method="fdr_bh")[1]
    inter_df.to_csv("results_race_strength_interaction.csv", index=False)
    print("\n=== Race x Strength interaction per category (FDR-corrected) ===")
    print(inter_df.round(4).to_string(index=False))

    # 3) Variance decomposition (mixed model, crossed random effects for name_id / profile_id)
    vc = {"name_id": "0 + C(name_id)", "profile_id": "0 + C(profile_id)"}
    rows = []
    for c in CATS:
        formula = (
            f"{c}_norm ~ C(racial_group)*C(strength) + C(gender_identity)+C(major)"
            "+C(quant_level)+C(volunteer_level)+C(rigor_level)+C(ec_level)"
        )
        model = smf.mixedlm(formula, data=df, groups=df["grp"], vc_formula=vc)
        res = model.fit(reml=True, method="lbfgs")
        name_var, profile_var = res.vcomp[0], res.vcomp[1]
        resid_var = res.scale
        total = name_var + profile_var + resid_var
        rows.append((c, name_var / total, profile_var / total, resid_var / total))
        print(f"done: {c}")
    var_df = pd.DataFrame(
        rows,
        columns=["category", "pct_var_name(race signal)", "pct_var_profile(qualifications)", "pct_var_residual(replication noise)"],
    )
    var_df.to_csv("results_variance_decomposition.csv", index=False)
    print("\n=== Variance decomposition per category ===")
    print(var_df.round(4).to_string(index=False))

    return omni, inter_df, var_df


def figures(df, var_df):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 10, "font.family": "sans-serif"})

    # FIG 1: grouped bar chart, category x race, with 95% CI
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(CATS))
    width = 0.15
    for i, race in enumerate(RACE_ORDER):
        means, cis = [], []
        for c in CATS:
            vals = df.loc[df.racial_group == race, c + "_norm"]
            n = len(vals)
            m = vals.mean()
            se = vals.std(ddof=1) / np.sqrt(n)
            ci = stats.t.ppf(0.975, n - 1) * se
            means.append(m)
            cis.append(ci)
        ax.bar(x + (i - 2) * width, means, width, yerr=cis, capsize=2, label=race, color=PALETTE[race])
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CATS])
    ax.set_ylabel("Mean words per 300-word letter")
    ax.set_title("Linguistic category frequency by racial signal (± 95% CI)")
    ax.legend(fontsize=8, ncol=1, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig("fig1_category_by_race.png", dpi=300)
    plt.close()

    # FIG 2: effect size ranking (partial eta^2)
    omni = pd.read_csv("results_omnibus_race_effect.csv").sort_values("eta2")
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#4C72B0" if p < 0.05 else "#B0B0B0" for p in omni["p_fdr"]]
    ax.barh(omni["category"].str.capitalize(), omni["eta2"], color=colors)
    ax.set_xlabel("Partial η² (variance explained by racial signal)")
    ax.set_title("Effect size ranking of racial signal by category\n(blue = significant after FDR correction, q<.05)")
    plt.tight_layout()
    plt.savefig("fig2_effect_size_ranking.png", dpi=300)
    plt.close()

    # FIG 3: interaction plot, strength x race, faceted by category
    fig, axes = plt.subplots(2, 3, figsize=(12, 8))
    for ax, c in zip(axes.flat, CATS):
        for race in RACE_ORDER:
            means = []
            for s in ["Moderate", "Strong"]:
                vals = df.loc[(df.racial_group == race) & (df.strength == s), c + "_norm"]
                means.append(vals.mean())
            ax.plot(["Moderate", "Strong"], means, marker="o", color=PALETTE[race], label=race, linewidth=2)
        ax.set_title(c.capitalize())
        ax.set_ylabel("Mean per 300 words")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.suptitle("Racial signal × recommendation strength interaction, by category", y=0.99)
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=9, frameon=True, bbox_to_anchor=(0.5, 0.0))
    plt.tight_layout(rect=[0, 0.07, 1, 0.96])
    plt.savefig("fig3_strength_interaction.png", dpi=300)
    plt.close()

    # FIG 4: variance decomposition stacked bar
    fig, ax = plt.subplots(figsize=(7, 4))
    bottom = np.zeros(len(var_df))
    labels = ["Name (racial signal)", "Profile (qualifications)", "Residual (replication noise)"]
    colors4 = ["#C44E52", "#55A868", "#B0B0B0"]
    for col, lab, col_c in zip(var_df.columns[1:], labels, colors4):
        ax.bar(var_df["category"].str.capitalize(), var_df[col], bottom=bottom, label=lab, color=col_c)
        bottom += var_df[col].values
    ax.set_ylabel("Proportion of total variance")
    ax.set_title("Variance decomposition: racial signal vs. qualifications vs. replication noise")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3)
    plt.tight_layout()
    plt.savefig("fig4_variance_decomposition.png", dpi=300)
    plt.close()

    print("Saved: fig1_category_by_race.png, fig2_effect_size_ranking.png, fig3_strength_interaction.png, fig4_variance_decomposition.png")


def tukey_posthoc(df):
    # exploratory post-hoc, printed only (not written to a committed file)
    for c in ["communal", "competitive"]:
        print(f"\n=== Tukey HSD: {c} (per 300 words) ===")
        res = pairwise_tukeyhsd(endog=df[c + "_norm"], groups=df["racial_group"], alpha=0.05)
        print(res.summary())


def main():
    strong = load("strong full analysis.csv", "Strong")
    moderate = load("moderate analysis.csv", "Moderate")
    df = pd.concat([strong, moderate], ignore_index=True)
    df["name_id"] = df["name_id"].astype(str)
    profile_cols = ["major", "quant_level", "volunteer_level", "rigor_level", "ec_level"]
    df["profile_id"] = df[profile_cols].astype(str).agg("_".join, axis=1)
    df["grp"] = 1  # single group; crossed random effects come from vc_formula

    descriptive_tables(strong, moderate, df)
    omni, inter_df, var_df = inferential_tables(df)
    figures(df, var_df)
    tukey_posthoc(df)


if __name__ == "__main__":
    main()
