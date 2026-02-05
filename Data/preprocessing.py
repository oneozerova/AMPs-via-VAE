import pandas as pd
from pathlib import Path
import numpy as np
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class AddInfoConfig:
    text_col: str = "Additional info"
    top_k: int = 5
    min_header_len: int = 3

HDR_STANDALONE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /-]*?(?::[A-Za-z0-9_-]+)?)\s*$")
HDR_SAMELINE_RE  = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /-]*?(?::[A-Za-z0-9_-]+)?)\s*:\s*(.*)\s*$")

def data_loading(path)->pd.DataFrame:
    return pd.read_csv(path)

def norm_text(s: str) -> str:
    s = "" if pd.isna(s) else str(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s

def canon_header(h: str) -> str:
    h = str(h).strip().lower()
    h = re.sub(r"\s+", " ", h)
    return h

def to_col_name(canon_h: str) -> str:
    if canon_h == "activity":
        return "Activity_seq"
    x = re.sub(r"[^a-z0-9]+", "_", canon_h)
    x = re.sub(r"_+", "_", x).strip("_")
    return f"addinfo_{x}_seq"

def extract_headers(df: pd.DataFrame, cfg: AddInfoConfig) -> pd.Series:
    """
    Возвращает value_counts() заголовков, найденных в Additional info.
    Поддерживает:
      - 'Header: content' (в одной строке)
      - 'Header' (отдельной строкой) + следующая строка начинается с ':'
    """
    headers: list[str] = []
    col = cfg.text_col
    for txt in df[col].map(norm_text).fillna(""):
        if not txt.strip():
            continue
        lines = txt.split("\n")
        for i, line in enumerate(lines):
            s = line.strip()
            if not s:
                continue
            m = HDR_SAMELINE_RE.match(s)
            if m:
                headers.append(m.group(1).strip())
                continue
            m = HDR_STANDALONE_RE.match(s)
            if m:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and lines[j].lstrip().startswith(":"):
                    headers.append(m.group(1).strip())

    return pd.Series(headers).value_counts()

def pick_top_headers(header_counts: pd.Series, cfg: AddInfoConfig) -> list[str]:
    hdr_df = header_counts.rename_axis("header").reset_index(name="count")
    hdr_df["canon"] = hdr_df["header"].map(canon_header)

    # фильтр мусора типа 'K', 'R', ...
    hdr_df = hdr_df[hdr_df["canon"].str.len() >= cfg.min_header_len].copy()

    canon_counts = (
        hdr_df.groupby("canon", as_index=False)["count"]
        .sum()
        .sort_values("count", ascending=False)
    )
    return canon_counts.head(cfg.top_k)["canon"].tolist()

def extract_top_sections(add_info: str, top_headers_canon: list[str]) -> dict:
    """
    Достаёт из текста только секции из top_headers_canon.
    Возвращает dict: {new_col -> text_or_nan}
    """
    txt = norm_text(add_info)
    out = {to_col_name(h): np.nan for h in top_headers_canon}
    if not txt.strip():
        return out

    lines = txt.split("\n")
    cur = None
    buf = {h: [] for h in top_headers_canon}

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue

        # Case A: "Header: content"
        m = HDR_SAMELINE_RE.match(s)
        if m:
            hdr_raw = m.group(1).strip()
            rest = m.group(2).strip()
            ch = canon_header(hdr_raw)

            cur = ch if ch in top_headers_canon else None
            if cur is not None and rest:
                buf[cur].append(rest)

            i += 1
            continue

        # Case B: standalone "Header" + next line ": content"
        m = HDR_STANDALONE_RE.match(s)
        if m:
            hdr_raw = m.group(1).strip()
            ch = canon_header(hdr_raw)

            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1

            if j < len(lines) and lines[j].lstrip().startswith(":"):
                cur = ch if ch in top_headers_canon else None
                if cur is not None:
                    after = lines[j].split(":", 1)[1].strip()
                    if after:
                        buf[cur].append(after)
                i = j + 1
                continue

        # content line
        if cur is not None:
            buf[cur].append(s)
        i += 1

    for h in top_headers_canon:
        col = to_col_name(h)
        val = "\n".join(buf[h]).strip()
        out[col] = val if val else np.nan

    return out

def add_addinfo_topk_columns(df: pd.DataFrame, cfg: AddInfoConfig) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    header_counts = extract_headers(df, cfg)
    top_headers = pick_top_headers(header_counts, cfg)

    parsed = df[cfg.text_col].apply(lambda x: extract_top_sections(x, top_headers)).apply(pd.Series)
    df = df.drop(columns=parsed.columns, errors="ignore")
    df = pd.concat([df, parsed], axis=1)

    return df, header_counts, top_headers

def main():
    cfg = AddInfoConfig(text_col="Additional info", top_k=5, min_header_len=3)

    project_root = Path(__file__).resolve().parents[1]
    data_path = project_root / "Data" / "raw_data" / "apd6_peptides_raw_data.csv"

    df = data_loading(data_path)
    df = df.drop(columns=["Sequence analysis", "History and discovery"], errors="ignore")

    df, header_counts, top_headers = add_addinfo_topk_columns(df, cfg)

    print("TOP_HEADERS_CANON:", top_headers)
    new_cols = [to_col_name(h) for h in top_headers]
    print("Added columns:", new_cols)
    print("NaN fraction:\n", df[new_cols].isna().mean().sort_values(ascending=False))

    out_path = project_root / "Data" / "processed" / "apd6_with_addinfo_topk.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print("Saved:", out_path)

    print(df.shape)
    print(df.columns)
    print(df.isna().sum())

    for i in range(10, 15):
        print(f'Activity_seq {i}: {df.iloc[i + 1]["Activity_seq"]}')


if __name__ == "__main__":
    main()