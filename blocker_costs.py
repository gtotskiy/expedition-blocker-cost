import pandas as pd
import re

# Пути к CSV
raw_csv   = "raw.csv"
types_csv = "blocker_types.csv"

# 1) Считаем «сырую» таблицу без заголовков
df_raw = pd.read_csv(raw_csv, header=None, dtype=str)

# 2) Собираем пары (ID, type)
pattern = re.compile(r"EXP-N-_[A-Za-z]+(?:Small|Medium|Big)\d+")
records = []
for _, row in df_raw.iterrows():
    for col in df_raw.columns[:-1]:
        cell = row[col]
        if isinstance(cell, str) and pattern.fullmatch(cell.strip()):
            blocker_id = cell.strip()
            blocker_type = row[col+1].strip() if isinstance(row[col+1], str) else None
            if blocker_type:
                records.append((blocker_id, blocker_type))

df_ids = pd.DataFrame(records, columns=["blocker_id", "type"]).drop_duplicates()

# 3) Загрузка таблицы с ценами
df_cost = pd.read_csv(types_csv, usecols=["Type", "Cost"])
df_cost.columns = ["type", "cost"]

# 4) Мержим
df = df_ids.merge(df_cost, on="type", how="left")

# 5) Разбираем material, size и num
def parse_all(bid):
    m = re.match(r"EXP-N-_(?P<mat>[A-Za-z]+)(?P<size>Small|Medium|Big)(?P<num>\d+)", bid)
    if m:
        return m.group("mat"), m.group("size"), int(m.group("num"))
    return "", "", 0

parsed = df["blocker_id"].apply(parse_all)
df["material"] = parsed.str[0]
df["size"]     = parsed.str[1]
df["num"]      = parsed.str[2]

# 6) Размеру даём явный порядок
size_order = {"Small": 0, "Medium": 1, "Big": 2}
df["size_rank"] = df["size"].map(size_order)

# 7) Финальная сортировка
df_sorted = (
    df
    .sort_values(["material", "size_rank", "num"])
    [["blocker_id", "cost", "type"]]
)

# 8) Печать
print(df_sorted.to_string(index=False))
