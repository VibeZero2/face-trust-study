from pathlib import Path
path = Path(r"dashboard/analysis/stats.py")
text = path.read_text()
old = "            included_pids = self.cleaned_data[self.cleaned_data['include_in_primary']]['pid'].astype(str).unique()\n            trust_df = trust_df[trust_df['pid'].isin(included_pids)]\n            if trust_df.empty:\n                return pd.DataFrame(columns(['face_id', 'mean_trust', 'half_face_avg'"
