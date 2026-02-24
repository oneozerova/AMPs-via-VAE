import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
data_path = project_root / "Data" / "processed" / "apd6_cVAE.csv"

df = pd.read_csv(data_path)
print(df.columns.tolist())

# for i in range(10):
#     print(df.iloc[i]["Activity"])
#
# for i in range(10):
#     print(df.iloc[i]["Additional info"])

text = (
    df["Activity"].fillna("").astype(str) + " " +
    df["Activity_seq"].fillna("").astype(str)
)

m_gram_pos = text.str.contains(r"gram\+", case=False, regex=True, na=False)
m_gram_neg = text.str.contains(r"gram-",  case=False, regex=True, na=False)

df["is_anti_gram_positive"] = m_gram_pos.astype(int)
df["is_anti_gram_negative"] = m_gram_neg.astype(int)
df["is_antibacterial"] = (m_gram_pos | m_gram_neg).astype(int)

df["is_antifungal"] = text.str.contains(r"\bantifungal\b",     case=False, regex=True, na=False).astype(int)
df["is_antiviral"] = text.str.contains(r"\bantiviral\b",      case=False, regex=True, na=False).astype(int)
df["is_antiparasitic"] = text.str.contains(r"\bantiparasitic\b",  case=False, regex=True, na=False).astype(int)
df["is_anticancer"] = text.str.contains(r"\banticancer\b",     case=False, regex=True, na=False).astype(int)

print(df.iloc[17])
for i in range(10):
    print(df.iloc[i]["Activity_seq"])

out_path = project_root / "Data" / "processed" / "data.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out_path, index=False)
print("Saved:", out_path)