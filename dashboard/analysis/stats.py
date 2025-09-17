import logging
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    from scipy import stats
    from scipy.stats import chisquare, pearsonr, spearmanr
    SCIPY_AVAILABLE = True
except ImportError:  # pragma: no cover - Render fallback
    SCIPY_AVAILABLE = False

    class _FallbackStats:
        @staticmethod
        def ttest_rel(values_a, values_b):
            values_a = np.asarray(values_a, dtype=float)
            values_b = np.asarray(values_b, dtype=float)
            if values_a.size != values_b.size or values_a.size < 2:
                return 0.0, 1.0
            diffs = values_a - values_b
            mean_diff = diffs.mean()
            sd_diff = diffs.std(ddof=1)
            if sd_diff == 0:
                return 0.0, 1.0
            t_stat = mean_diff / (sd_diff / np.sqrt(len(diffs)))
            return t_stat, 1.0  # p-value approximation unavailable

        @staticmethod
        def f_oneway(*groups):
            return 0.0, 1.0

        @staticmethod
        def chisquare(f_obs, f_exp):
            return 0.0, 1.0

        class f:  # noqa: N801 - mimic scipy.stats API
            @staticmethod
            def sf(f_stat, df_num, df_den):
                return 1.0

        class t:  # noqa: N801
            @staticmethod
            def ppf(_, __):
                return 0.0

    stats = _FallbackStats()
    chisquare = stats.chisquare

    def pearsonr(values_a, values_b):
        return 0.0, 1.0

    def spearmanr(values_a, values_b):
        return 0.0, 1.0


logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """Compute statistical results for the face perception dashboard."""

    def __init__(self, data_cleaner):
        self.data_cleaner = data_cleaner
        self.cleaned_data = data_cleaner.get_cleaned_data()
        self._long_format_cache: Optional[pd.DataFrame] = None

    @staticmethod
    def _normalize_face_id(face_id: str) -> str:
        if pd.isna(face_id):
            return ""
        match = re.search(r"(\d+)", str(face_id))
        return f"face_{int(match.group(1))}" if match else str(face_id)

    def _build_long_format_from_wide(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=["pid", "face_id", "version", "question", "response", "response_numeric"])

        rows: List[Dict[str, object]] = []
        numeric_questions = {"trust_rating", "emotion_rating", "masculinity_full", "femininity_full"}

        for _, row in df.iterrows():
            pid = str(row.get("pid", "")).strip()
            face_id = self._normalize_face_id(row.get("face_id", ""))

            def add_entry(question: str, version: str, value):
                if pd.isna(value) or str(value).strip() == "":
                    return
                rows.append(
                    {
                        "pid": pid,
                        "face_id": face_id,
                        "version": version,
                        "question": question,
                        "response": str(value),
                        "response_numeric": float(value) if question in numeric_questions else np.nan,
                    }
                )

            add_entry("trust_rating", "left", row.get("trust_left"))
            add_entry("trust_rating", "right", row.get("trust_right"))
            add_entry("trust_rating", "both", row.get("trust_rating"))
            add_entry("emotion_rating", "left", row.get("emotion_left"))
            add_entry("emotion_rating", "right", row.get("emotion_right"))
            add_entry("emotion_rating", "both", row.get("emotion_rating"))
            add_entry("masc_choice", "both", row.get("masc_choice"))
            add_entry("fem_choice", "both", row.get("fem_choice"))
            add_entry("masculinity_full", "both", row.get("masculinity_full"))
            add_entry("femininity_full", "both", row.get("femininity_full"))

        if not rows:
            return pd.DataFrame(columns=["pid", "face_id", "version", "question", "response", "response_numeric"])

        return pd.DataFrame(rows)

    def _get_long_format_data(self) -> pd.DataFrame:
        if self._long_format_cache is not None:
            return self._long_format_cache

        if self.cleaned_data is None or self.cleaned_data.empty:
            self._long_format_cache = pd.DataFrame(columns=["pid", "face_id", "version", "question", "response", "response_numeric"])
            return self._long_format_cache

        df = self.cleaned_data.copy()
        if "question" not in df.columns and "question_type" in df.columns:
            df["question"] = df["question_type"]

        if "question" in df.columns and "response" in df.columns:
            long_df = df[df["question"].notna() & df["response"].notna()].copy()
            question_map = {
                "trust_rating": "trust_rating",
                "emotion_rating": "emotion_rating",
                "masc_choice": "masc_choice",
                "fem_choice": "fem_choice",
                "masculinity_full": "masculinity_full",
                "femininity_full": "femininity_full",
                "masculinity": "masculinity_full",
                "femininity": "femininity_full",
            }
            long_df["question"] = long_df["question"].astype(str).str.strip().str.lower()
            long_df["question"] = long_df["question"].map(question_map).fillna(long_df["question"])

            version_map = {
                "left half": "left",
                "right half": "right",
                "full face": "both",
                "full": "both",
                "both": "both",
                "left": "left",
                "right": "right",
            }
            long_df["version"] = long_df["version"].astype(str).str.strip().str.lower()
            long_df["version"] = long_df["version"].map(version_map).fillna(long_df["version"])
            long_df = long_df[long_df["version"].isin({"left", "right", "both"})]

            long_df["pid"] = long_df["pid"].astype(str)
            long_df["face_id"] = long_df.get("face_id", "").apply(self._normalize_face_id)
            long_df["response"] = long_df["response"].astype(str).str.strip()

            numeric_questions = {"trust_rating", "emotion_rating", "masculinity_full", "femininity_full"}
            long_df["response_numeric"] = np.where(
                long_df["question"].isin(numeric_questions),
                pd.to_numeric(long_df["response"], errors="coerce"),
                np.nan,
            )

            long_df = long_df.drop_duplicates(subset=["pid", "face_id", "version", "question", "response"])
            self._long_format_cache = long_df[["pid", "face_id", "version", "question", "response", "response_numeric"]]
            return self._long_format_cache

        self._long_format_cache = self._build_long_format_from_wide(df)
        return self._long_format_cache

    def _get_numeric_dataframe(self, question: str) -> pd.DataFrame:
        long_df = self._get_long_format_data()
        if long_df.empty:
            return pd.DataFrame(columns=["pid", "face_id", "version", "value"])

        numeric_df = long_df[(long_df["question"] == question) & long_df["response_numeric"].notna()].copy()
        if numeric_df.empty:
            return pd.DataFrame(columns=["pid", "face_id", "version", "value"])

        numeric_df = numeric_df.rename(columns={"response_numeric": "value"})
        return numeric_df[["pid", "face_id", "version", "value"]]

    def _get_choice_dataframe(self, question: str) -> pd.DataFrame:
        long_df = self._get_long_format_data()
        if long_df.empty:
            return pd.DataFrame(columns=["pid", "face_id", "version", "response"])

        choice_df = long_df[long_df["question"] == question].copy()
        if choice_df.empty:
            return pd.DataFrame(columns=["pid", "face_id", "version", "response"])

        return choice_df[["pid", "face_id", "version", "response"]]

    def get_image_summary(self) -> pd.DataFrame:
        """Summarize trust ratings per face for the images dashboard."""
        columns = ['face_id', 'mean_trust', 'half_face_avg', 'full_minus_half_diff', 'rating_count', 'std_trust', 'left_mean', 'right_mean', 'full_mean', 'unique_participants']

        long_df = self._get_long_format_data()
        if long_df.empty:
            return pd.DataFrame(columns=columns)

        working = long_df.copy()
        working['question'] = working['question'].astype(str).str.strip().str.lower()

        trust_df = working[working['question'].str.contains('trust', na=False)].copy()
        if trust_df.empty:
            return pd.DataFrame(columns=columns)

        if 'response_numeric' in trust_df.columns and trust_df['response_numeric'].notna().any():
            trust_df['value'] = trust_df['response_numeric']
        else:
            trust_df['value'] = pd.to_numeric(trust_df['response'], errors='coerce')

        trust_df = trust_df[trust_df['value'].notna()]
        if trust_df.empty:
            return pd.DataFrame(columns=columns)

        trust_df['face_id'] = trust_df['face_id'].astype(str)
        trust_df['version'] = trust_df['version'].astype(str)
        trust_df['pid'] = trust_df['pid'].astype(str)

        if self.cleaned_data is not None and 'include_in_primary' in self.cleaned_data.columns:
            included_pids = self.cleaned_data[self.cleaned_data['include_in_primary']]['pid'].astype(str).unique()
            if len(included_pids) > 0:
                trust_df = trust_df[trust_df['pid'].isin(included_pids)]
                if trust_df.empty:
                    return pd.DataFrame(columns=columns)

        def _clean_numeric(value):
            if value is None or pd.isna(value):
                return None
            return float(value)

        summaries = []
        for face_id, face_data in trust_df.groupby('face_id'):
            version_stats = face_data.groupby('version')['value'].agg(['mean', 'std', 'count'])

            def _extract(version_name: str):
                if version_name in version_stats.index:
                    row = version_stats.loc[version_name]
                    mean_val = _clean_numeric(row['mean'])
                    std_val = _clean_numeric(row['std'])
                    count_val = int(row['count'])
                    if std_val is None and count_val > 0:
                        std_val = 0.0 if count_val == 1 else 0.0
                    if std_val is not None and np.isnan(std_val):
                        std_val = 0.0
                    return mean_val, std_val, count_val
                return None, None, 0

            left_mean, left_std, left_count = _extract('left')
            right_mean, right_std, right_count = _extract('right')
            full_mean, full_std, full_count = _extract('both')
            if full_mean is None:
                full_mean_alt, full_std_alt, full_count_alt = _extract('full')
                if full_mean_alt is not None:
                    full_mean, full_std, full_count = full_mean_alt, full_std_alt, full_count_alt

            half_values = [val for val in (left_mean, right_mean) if val is not None]
            half_face_avg = float(np.mean(half_values)) if half_values else None

            overall_values = face_data['value'].dropna()
            overall_count = int(overall_values.count())
            overall_mean = _clean_numeric(overall_values.mean())
            overall_std = _clean_numeric(overall_values.std(ddof=0))
            if overall_std is not None and np.isnan(overall_std):
                overall_std = 0.0

            mean_trust = full_mean if full_mean is not None else overall_mean
            std_trust = full_std if full_std is not None else overall_std

            diff = None
            if mean_trust is not None and half_face_avg is not None:
                diff = float(mean_trust - half_face_avg)

            summaries.append({
                'face_id': face_id,
                'mean_trust': mean_trust,
                'half_face_avg': half_face_avg,
                'full_minus_half_diff': diff,
                'rating_count': overall_count,
                'std_trust': std_trust,
                'left_mean': left_mean,
                'right_mean': right_mean,
                'full_mean': full_mean if full_mean is not None else overall_mean,
                'unique_participants': int(face_data['pid'].nunique()),
            })

        if not summaries:
            return pd.DataFrame(columns=columns)

        summary_df = pd.DataFrame(summaries)
        return summary_df.sort_values('face_id').reset_index(drop=True)

    def _build_histogram(self, data: pd.DataFrame) -> Optional[Dict[str, List[int]]]:
        if data.empty:
            return None

        values = data["value"].dropna()
        if values.empty:
            return None

        discrete_values = sorted({int(round(v)) for v in values if np.isfinite(v)})
        if not discrete_values:
            return None

        min_rating, max_rating = discrete_values[0], discrete_values[-1]
        labels = list(range(min_rating, max_rating + 1))
        histogram = {"labels": labels}

        for version in ["left", "right", "both"]:
            version_values = data[data["version"] == version]["value"].dropna()
            histogram[version] = [int((version_values == label).sum()) for label in labels]

        return histogram

    def get_trust_histogram(self) -> Optional[Dict[str, List[int]]]:
        return self._build_histogram(self._get_numeric_dataframe("trust_rating"))

    def get_emotion_histogram(self) -> Optional[Dict[str, List[int]]]:
        return self._build_histogram(self._get_numeric_dataframe("emotion_rating"))

    def get_boxplot_data(self, question: str) -> Optional[Dict[str, List[float]]]:
        data = self._get_numeric_dataframe(question)
        if data.empty:
            return None

        result: Dict[str, List[float]] = {}
        for version in ["left", "right", "both"]:
            version_values = data[data["version"] == version]["value"].dropna()
            result[version] = [float(v) for v in version_values.tolist()]

        if all(len(values) == 0 for values in result.values()):
            return None
        return result

    def get_descriptive_stats(self) -> Dict[str, Dict[str, float]]:
        stats_dict: Dict[str, Dict[str, float]] = {}
        data = self._get_numeric_dataframe("trust_rating")
        for version in ["left", "right", "both"]:
            version_values = data[data["version"] == version]["value"].dropna()
            if version_values.empty:
                stats_dict[version] = {
                    "n": 0,
                    "mean": np.nan,
                    "std": np.nan,
                    "median": np.nan,
                    "min": np.nan,
                    "max": np.nan,
                    "q25": np.nan,
                    "q75": np.nan,
                }
            else:
                stats_dict[version] = {
                    "n": int(len(version_values)),
                    "mean": float(version_values.mean()),
                    "std": float(version_values.std(ddof=1)) if len(version_values) > 1 else 0.0,
                    "median": float(version_values.median()),
                    "min": float(version_values.min()),
                    "max": float(version_values.max()),
                    "q25": float(version_values.quantile(0.25)),
                    "q75": float(version_values.quantile(0.75)),
                }
        return stats_dict

    def get_all_question_stats(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        results: Dict[str, Dict[str, Dict[str, float]]] = {}
        numeric_questions = ["trust_rating", "emotion_rating", "masculinity_full", "femininity_full"]
        for question in numeric_questions:
            data = self._get_numeric_dataframe(question)
            if data.empty:
                continue

            question_stats: Dict[str, Dict[str, float]] = {}
            for version in ["left", "right", "both"]:
                version_values = data[data["version"] == version]["value"].dropna()
                if version_values.empty:
                    question_stats[version] = {
                        "n": 0,
                        "mean": np.nan,
                        "std": np.nan,
                        "median": np.nan,
                        "min": np.nan,
                        "max": np.nan,
                        "q25": np.nan,
                        "q75": np.nan,
                    }
                else:
                    question_stats[version] = {
                        "n": int(len(version_values)),
                        "mean": float(version_values.mean()),
                        "std": float(version_values.std(ddof=1)) if len(version_values) > 1 else 0.0,
                        "median": float(version_values.median()),
                        "min": float(version_values.min()),
                        "max": float(version_values.max()),
                        "q25": float(version_values.quantile(0.25)),
                        "q75": float(version_values.quantile(0.75)),
                    }
            if any(stats["n"] > 0 for stats in question_stats.values()):
                results[question] = question_stats
        return results

    def paired_t_test_half_vs_full(self) -> Dict[str, object]:
        data = self._get_numeric_dataframe("trust_rating")
        left_means = data[data["version"] == "left"].groupby("pid")["value"].mean()
        right_means = data[data["version"] == "right"].groupby("pid")["value"].mean()
        full_means = data[data["version"] == "both"].groupby("pid")["value"].mean()

        half_df = pd.concat({"left": left_means, "right": right_means}, axis=1).dropna()
        full_means = full_means.dropna()
        common_participants = half_df.index.intersection(full_means.index)
        n = len(common_participants)
        if n < 2:
            return {
                "statistic": np.nan,
                "pvalue": np.nan,
                "effect_size": np.nan,
                "df": n - 1 if n > 0 else np.nan,
                "n_participants": n,
                "half_face_mean": np.nan,
                "full_face_mean": np.nan,
                "difference": np.nan,
                "ci_lower": np.nan,
                "ci_upper": np.nan,
                "included_participants": list(map(str, common_participants)),
                "error": "Insufficient data for paired t-test",
            }

        half_values = half_df.loc[common_participants].mean(axis=1)
        full_values = full_means.loc[common_participants]
        try:
            t_stat, p_value = stats.ttest_rel(half_values, full_values)
        except Exception:
            t_stat, p_value = (0.0, 1.0)

        diffs = (half_values - full_values).astype(float)
        mean_diff = float(diffs.mean())
        sd_diff = float(diffs.std(ddof=1))
        df_val = n - 1
        se_diff = sd_diff / np.sqrt(n) if n > 0 else np.nan
        try:
            t_crit = stats.t.ppf(0.975, df_val) if df_val > 0 else np.nan
        except Exception:
            t_crit = np.nan
        effect_size = mean_diff / sd_diff if sd_diff > 0 else 0.0
        ci_lower = mean_diff - t_crit * se_diff if np.isfinite(se_diff) and np.isfinite(t_crit) else np.nan
        ci_upper = mean_diff + t_crit * se_diff if np.isfinite(se_diff) and np.isfinite(t_crit) else np.nan

        return {
            "statistic": float(t_stat),
            "pvalue": float(p_value),
            "effect_size": float(effect_size) if np.isfinite(effect_size) else np.nan,
            "df": int(df_val),
            "n_participants": int(n),
            "half_face_mean": float(half_values.mean()),
            "full_face_mean": float(full_values.mean()),
            "difference": mean_diff,
            "ci_lower": float(ci_lower) if np.isfinite(ci_lower) else np.nan,
            "ci_upper": float(ci_upper) if np.isfinite(ci_upper) else np.nan,
            "included_participants": list(map(str, common_participants)),
        }

    def repeated_measures_anova(self) -> Dict[str, object]:
        data = self._get_numeric_dataframe("trust_rating")
        pivot = data.pivot_table(index="pid", columns="version", values="value", aggfunc="mean")
        for version in ["left", "right", "both"]:
            if version not in pivot:
                pivot[version] = np.nan
        pivot = pivot[["left", "right", "both"]].dropna()

        n = pivot.shape[0]
        k = 3
        if n < 2:
            return {
                "f_statistic": np.nan,
                "pvalue": np.nan,
                "effect_size": np.nan,
                "df_num": k - 1,
                "df_den": (k - 1) * (n - 1),
                "n_participants": int(n),
                "means": {},
                "stds": {},
                "included_participants": list(map(str, pivot.index)),
                "error": "Insufficient data for repeated measures ANOVA",
            }

        grand_mean = pivot.values.mean()
        condition_means = pivot.mean(axis=0)
        subject_means = pivot.mean(axis=1)

        ss_conditions = n * ((condition_means - grand_mean) ** 2).sum()
        ss_subjects = k * ((subject_means - grand_mean) ** 2).sum()
        ss_total = ((pivot - grand_mean) ** 2).values.sum()
        ss_error = ss_total - ss_conditions - ss_subjects

        df_num = k - 1
        df_den = (k - 1) * (n - 1)
        if df_den <= 0 or ss_error <= 0:
            return {
                "f_statistic": np.nan,
                "pvalue": np.nan,
                "effect_size": np.nan,
                "df_num": int(df_num),
                "df_den": int(df_den),
                "n_participants": int(n),
                "means": {col: float(condition_means[col]) for col in ["left", "right", "both"]},
                "stds": {},
                "included_participants": list(map(str, pivot.index)),
                "error": "Insufficient variance for ANOVA",
            }

        ms_conditions = ss_conditions / df_num
        ms_error = ss_error / df_den
        f_stat = ms_conditions / ms_error if ms_error > 0 else np.nan
        try:
            p_value = stats.f.sf(f_stat, df_num, df_den) if np.isfinite(f_stat) else np.nan
        except Exception:
            p_value = 1.0

        partial_eta_sq = ss_conditions / (ss_conditions + ss_error) if (ss_conditions + ss_error) > 0 else np.nan

        return {
            "f_statistic": float(f_stat) if np.isfinite(f_stat) else np.nan,
            "pvalue": float(p_value) if np.isfinite(p_value) else np.nan,
            "effect_size": float(partial_eta_sq) if np.isfinite(partial_eta_sq) else np.nan,
            "df_num": int(df_num),
            "df_den": int(df_den),
            "n_participants": int(n),
            "means": {col: float(condition_means[col]) for col in ["left", "right", "both"]},
            "stds": {col: float(pivot[col].std(ddof=1)) for col in ["left", "right", "both"]},
            "included_participants": list(map(str, pivot.index)),
        }

    def emotion_paired_t_test_half_vs_full(self) -> Dict[str, object]:
        data = self._get_numeric_dataframe("emotion_rating")
        left_means = data[data["version"] == "left"].groupby("pid")["value"].mean()
        right_means = data[data["version"] == "right"].groupby("pid")["value"].mean()
        full_means = data[data["version"] == "both"].groupby("pid")["value"].mean()

        half_df = pd.concat({"left": left_means, "right": right_means}, axis=1).dropna()
        full_means = full_means.dropna()
        common_participants = half_df.index.intersection(full_means.index)
        if len(common_participants) < 3:
            return {"error": "Insufficient participants for emotion paired t-test"}

        half_values = half_df.loc[common_participants].mean(axis=1)
        full_values = full_means.loc[common_participants]
        try:
            t_stat, p_value = stats.ttest_rel(half_values, full_values)
        except Exception:
            t_stat, p_value = (0.0, 1.0)

        diffs = (half_values - full_values).astype(float)
        mean_diff = float(diffs.mean())
        sd_diff = float(diffs.std(ddof=1))
        n = len(diffs)
        df_val = n - 1
        se_diff = sd_diff / np.sqrt(n) if n > 0 else np.nan
        try:
            t_crit = stats.t.ppf(0.975, df_val) if df_val > 0 else np.nan
        except Exception:
            t_crit = np.nan
        effect_size = mean_diff / sd_diff if sd_diff > 0 else 0.0
        ci_lower = mean_diff - t_crit * se_diff if np.isfinite(se_diff) and np.isfinite(t_crit) else np.nan
        ci_upper = mean_diff + t_crit * se_diff if np.isfinite(se_diff) and np.isfinite(t_crit) else np.nan

        return {
            "statistic": float(t_stat),
            "pvalue": float(p_value),
            "df": int(df_val),
            "effect_size": float(effect_size) if np.isfinite(effect_size) else np.nan,
            "half_face_mean": float(half_values.mean()),
            "full_face_mean": float(full_values.mean()),
            "difference": mean_diff,
            "ci_lower": float(ci_lower) if np.isfinite(ci_lower) else np.nan,
            "ci_upper": float(ci_upper) if np.isfinite(ci_upper) else np.nan,
            "n_participants": int(n),
            "included_participants": list(map(str, common_participants)),
        }

    def emotion_repeated_measures_anova(self) -> Dict[str, object]:
        data = self._get_numeric_dataframe("emotion_rating")
        pivot = data.pivot_table(index="pid", columns="version", values="value", aggfunc="mean")
        for version in ["left", "right", "both"]:
            if version not in pivot:
                pivot[version] = np.nan
        pivot = pivot[["left", "right", "both"]].dropna()
        n = pivot.shape[0]
        if n < 2:
            return {"error": "Insufficient participants for emotion repeated measures ANOVA"}

        grand_mean = pivot.values.mean()
        condition_means = pivot.mean(axis=0)
        subject_means = pivot.mean(axis=1)
        k = 3
        ss_conditions = n * ((condition_means - grand_mean) ** 2).sum()
        ss_subjects = k * ((subject_means - grand_mean) ** 2).sum()
        ss_total = ((pivot - grand_mean) ** 2).values.sum()
        ss_error = ss_total - ss_conditions - ss_subjects
        df_between = k - 1
        df_within = (k - 1) * (n - 1)
        if df_within <= 0 or ss_error <= 0:
            return {
                "error": "Insufficient variance for ANOVA",
                "df_between": int(df_between),
                "df_within": int(df_within),
                "means": {col: float(condition_means[col]) for col in ["left", "right", "both"]},
            }
        ms_conditions = ss_conditions / df_between
        ms_error = ss_error / df_within
        f_stat = ms_conditions / ms_error if ms_error > 0 else np.nan
        try:
            p_value = stats.f.sf(f_stat, df_between, df_within) if np.isfinite(f_stat) else np.nan
        except Exception:
            p_value = 1.0
        partial_eta_sq = ss_conditions / (ss_conditions + ss_error) if (ss_conditions + ss_error) > 0 else np.nan
        return {
            "f_statistic": float(f_stat) if np.isfinite(f_stat) else np.nan,
            "pvalue": float(p_value) if np.isfinite(p_value) else np.nan,
            "df_between": int(df_between),
            "df_within": int(df_within),
            "partial_eta_squared": float(partial_eta_sq) if np.isfinite(partial_eta_sq) else np.nan,
            "means": {col: float(condition_means[col]) for col in ["left", "right", "both"]},
            "n_participants": int(n),
            "included_participants": list(map(str, pivot.index)),
        }

    def choice_preference_analysis(self) -> Dict[str, object]:
        masc_df = self._get_choice_dataframe("masc_choice")
        fem_df = self._get_choice_dataframe("fem_choice")
        if masc_df.empty and fem_df.empty:
            return {"error": "Insufficient data for choice preference analysis"}

        def prepare_counts(df: pd.DataFrame) -> Dict[str, int]:
            if df.empty:
                return {"left": 0, "right": 0, "neither": 0, "total": 0}
            responses = df[df["version"].astype(str).str.lower() == "both"]["response"].str.lower()
            left = int((responses == "left").sum())
            right = int((responses == "right").sum())
            neither = int((responses == "neither").sum())
            return {"left": left, "right": right, "neither": neither, "total": left + right + neither}

        def proportions(counts: Dict[str, int]) -> Dict[str, float]:
            total = counts.get("total", 0)
            if total == 0:
                return {"left": 0.0, "right": 0.0, "neither": 0.0}
            return {
                "left": counts["left"] / total,
                "right": counts["right"] / total,
                "neither": counts["neither"] / total,
            }

        def side_test(counts: Dict[str, int]) -> Dict[str, float]:
            left = counts.get("left", 0)
            right = counts.get("right", 0)
            side_total = left + right
            if side_total == 0:
                return {"chi2": np.nan, "p_value": np.nan}
            expected = [side_total / 2, side_total / 2]
            try:
                chi2, p_value = chisquare([left, right], expected)
            except Exception:
                chi2, p_value = (0.0, 1.0)
            return {"chi2": float(chi2), "p_value": float(p_value)}

        masc_counts = prepare_counts(masc_df)
        fem_counts = prepare_counts(fem_df)
        overall_left = masc_counts["left"] + fem_counts["left"]
        overall_right = masc_counts["right"] + fem_counts["right"]
        overall_result = {"left": overall_left, "right": overall_right, "neither": 0, "total": overall_left + overall_right}

        return {
            "masc_choice": {
                "counts": masc_counts,
                "proportions": proportions(masc_counts),
                "side_preference_test": side_test(masc_counts),
            },
            "fem_choice": {
                "counts": fem_counts,
                "proportions": proportions(fem_counts),
                "side_preference_test": side_test(fem_counts),
            },
            "overall_side_preference": {
                "counts": overall_result,
                "test": side_test({"left": overall_left, "right": overall_right}),
            },
        }

    def split_half_reliability(self) -> Dict[str, object]:
        data = self._get_numeric_dataframe("trust_rating")
        full_face = data[data["version"] == "both"]
        if full_face.empty:
            return {
                "split_half_correlation": np.nan,
                "spearman_brown": np.nan,
                "n_participants": 0,
                "n_faces_per_half": 0,
                "error": "No full face data available",
            }

        pivot = full_face.pivot_table(index="pid", columns="face_id", values="value", aggfunc="mean")
        pivot = pivot.dropna(how="all", axis=1)
        if pivot.shape[1] < 2:
            return {
                "split_half_correlation": np.nan,
                "spearman_brown": np.nan,
                "n_participants": 0,
                "n_faces_per_half": pivot.shape[1] // 2,
                "error": "Insufficient data for split-half reliability",
            }
        min_faces = max(int(pivot.shape[1] * 0.5), 1)
        pivot = pivot.dropna(thresh=min_faces)
        if pivot.shape[0] < 2 or pivot.shape[1] < 2:
            return {
                "split_half_correlation": np.nan,
                "spearman_brown": np.nan,
                "n_participants": 0,
                "n_faces_per_half": pivot.shape[1] // 2,
                "error": "Insufficient data for split-half reliability",
            }
        np.random.seed(42)
        face_indices = np.random.permutation(pivot.columns)
        half_size = len(face_indices) // 2
        if half_size == 0:
            return {
                "split_half_correlation": np.nan,
                "spearman_brown": np.nan,
                "n_participants": int(pivot.shape[0]),
                "n_faces_per_half": half_size,
                "error": "Insufficient faces for split-half reliability",
            }
        half1_cols = face_indices[:half_size]
        half2_cols = face_indices[half_size:]
        half1_scores = pivot[half1_cols].mean(axis=1)
        half2_scores = pivot[half2_cols].mean(axis=1)
        valid_mask = ~(half1_scores.isna() | half2_scores.isna())
        if valid_mask.sum() < 2:
            return {
                "split_half_correlation": np.nan,
                "spearman_brown": np.nan,
                "n_participants": 0,
                "n_faces_per_half": int(half_size),
                "error": "Insufficient valid data for correlation",
            }
        try:
            correlation, _ = pearsonr(half1_scores[valid_mask], half2_scores[valid_mask])
        except Exception:
            correlation = 0.0
        spearman_brown = (2 * correlation) / (1 + correlation) if correlation != 1 else 1
        return {
            "split_half_correlation": float(correlation) if np.isfinite(correlation) else np.nan,
            "spearman_brown": float(spearman_brown) if np.isfinite(spearman_brown) else np.nan,
            "n_participants": int(valid_mask.sum()),
            "n_faces_per_half": int(half_size),
        }

    def inter_rater_reliability(self) -> Dict[str, object]:
        data = self._get_numeric_dataframe("trust_rating")
        full_face = data[data["version"] == "both"]
        if full_face.empty:
            return {
                "icc": np.nan,
                "n_raters": 0,
                "n_stimuli": 0,
                "error": "No trust rating data available",
            }
        pivot = full_face.pivot_table(index="face_id", columns="pid", values="value", aggfunc="mean")
        pivot = pivot.dropna(how="all")
        pivot = pivot.dropna(how="all", axis=1)
        if pivot.shape[0] < 2 or pivot.shape[1] < 2:
            return {
                "icc": np.nan,
                "n_raters": int(pivot.shape[1]),
                "n_stimuli": int(pivot.shape[0]),
                "error": "Insufficient data for ICC calculation",
            }
        rating_matrix = pivot.values.astype(float)
        try:
            icc = self._calculate_icc(rating_matrix)
        except Exception as exc:
            logger.error("Error calculating ICC: %s", exc)
            icc = np.nan
        counts_per_stimulus = np.count_nonzero(~np.isnan(rating_matrix), axis=1)
        return {
            "icc": float(icc) if np.isfinite(icc) else np.nan,
            "n_raters": int(pivot.shape[1]),
            "n_stimuli": int(pivot.shape[0]),
            "mean_ratings_per_stimulus": float(counts_per_stimulus.mean()) if counts_per_stimulus.size else 0.0,
        }

    def _calculate_icc(self, data_matrix: np.ndarray) -> float:
        data_matrix = data_matrix[~np.all(np.isnan(data_matrix), axis=1)]
        if data_matrix.shape[0] < 2 or data_matrix.shape[1] < 2:
            return np.nan
        grand_mean = np.nanmean(data_matrix)
        row_means = np.nanmean(data_matrix, axis=1)
        col_means = np.nanmean(data_matrix, axis=0)
        n_rows, n_cols = data_matrix.shape
        ss_total = np.nansum((data_matrix - grand_mean) ** 2)
        ss_between = n_cols * np.nansum((row_means - grand_mean) ** 2)
        ss_raters = n_rows * np.nansum((col_means - grand_mean) ** 2)
        ss_error = ss_total - ss_between - ss_raters
        ms_between = ss_between / (n_rows - 1) if n_rows > 1 else np.nan
        ms_error = ss_error / ((n_rows - 1) * (n_cols - 1)) if n_rows > 1 and n_cols > 1 else np.nan
        if not np.isfinite(ms_between) or not np.isfinite(ms_error) or ms_between + ms_error == 0:
            return np.nan
        return (ms_between - ms_error) / (ms_between + (n_cols - 1) * ms_error)

