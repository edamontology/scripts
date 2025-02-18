import pandas as pan
import numpy as np

# This script uses a tsv file generated using OpenRefine from EDAM version 1.25.

df = pan.read_csv("../data/edam_openrefine_20241218_v1/EDAM-owl(2).tsv", sep="\t")

df = df.rename(columns={"copy of exactMatch": "copy exactMatch"})
print(df.columns)


def same_as_upper(col: pan.Series) -> pan.Series:
    """
    Recursively fill NaN rows with the previous value
    from: https://stackoverflow.com/questions/41212273/pandaspython-fill-empty-cells-with-with-previous-row-value
    """
    if any(pan.Series(col).isna()):
        col = pan.Series(np.where(col.isna(), col.shift(1), col))
        return same_as_upper(col)
    else:
        return col


def same_as_upper_if_a_match(df, col, i_row, column_to_match) -> pan.Series:
    """
    Recursively fill NaN rows with the previous value
    from: https://stackoverflow.com/questions/41212273/pandaspython-fill-empty-cells-with-with-previous-row-value
    """
    if any(df[col].isna()):
        col = pan.Series(np.where(col.isna(), col.shift(1), col))
        return same_as_upper_if_a_match(col, column_to_match)
    else:
        return col


def my_column_format(row, a_column_name="Match"):
    x = ""
    x0 = row[a_column_name]
    if not (pan.isnull(x0)):
        x = str(x0)
    y = row["copy " + a_column_name]
    if not (pan.isnull(y)) and not (y[:4] == "http"):
        x = str(y) + "  " + x
    if not (x == ""):
        x = a_column_name + ": " + x
    return x


df["exact Matches"] = df.apply(my_column_format, axis=1, a_column_name="exactMatch")
df["broad Matches"] = df.apply(my_column_format, axis=1, a_column_name="broadMatch")
df["narrow Matches"] = df.apply(my_column_format, axis=1, a_column_name="narrowMatch")
df["close Matches"] = df.apply(my_column_format, axis=1, a_column_name="closeMatch")
df["related Matches"] = df.apply(my_column_format, axis=1, a_column_name="relatedMatch")

for match_type in "exact broad narrow close related".split():
    df.drop(
        columns=[match_type + "Match", "copy " + match_type + "Match"], inplace=True
    )

print(df.head())

df.to_csv("../data/reformatted_matches_07.csv")

df["ID_filled"] = same_as_upper(df["ID"])
df["label_filled"] = same_as_upper(df["label"])

cname_mcl = "Match type, Concept and Link"
df = df.melt(
    id_vars="ID_filled label_filled inSubset".split(),
    value_vars=[
        "exact Matches",
        "broad Matches",
        "narrow Matches",
        "close Matches",
        "related Matches",
    ],
    value_name=cname_mcl,
)

print("empty rows:", df[cname_mcl] == "")
dg = df[df[cname_mcl] != ""]
print("dg", dg)
print("dg size", dg.shape)
dg.dropna(subset=[cname_mcl], inplace=True)
dg = dg.sort_values(by="ID_filled")
print(dg)
dg["inSubset_sorted"] = dg["inSubset"]
dg = dg.replace(to_replace="http://edamontology.org/bio", value="")
dg = dg.sort_values(by=["ID_filled", "inSubset_sorted"], ascending=[True, False])

dg["inSubset_filled"] = dg["inSubset_sorted"]
print(dg.columns)
print(len(dg))
dg.reset_index(inplace=True)
for i in range(1, len(dg)):
    x = dg.loc[i, "inSubset_sorted"]
    if x != x or x == "" or x == None or x == "http://edamontology.org/bio":
        dg.loc[i, "inSubset_filled"] = dg.loc[i - 1, "inSubset_filled"]

dg["inSubset_name"] = dg["inSubset_filled"].apply(lambda x: str(x).split("/")[-1])
dg["ID_short"] = dg["ID_filled"].apply(lambda x: str(x).split("/")[-1])
dg["ID_link_md"] = dg.apply(
    lambda x: "[`{}`]({})".format(x.ID_short, x.ID_filled), axis=1
)
dg = dg.sort_values(by=["ID_filled", cname_mcl], ascending=[True, True])
dg.to_csv("../data/reformatted_matches_filled_12.csv")

dg = dg.dropna(subset=["Match type, Concept and Link"])
indices_empty_rows = dg[dg["Match type, Concept and Link"] == ""].index
print("  indices_empty_rows", indices_empty_rows)
dg = dg.drop(index=indices_empty_rows)

dg.to_csv("../data/reformatted_matches_filled_cleaned_12.csv")

print(dg.columns)
dg["a"] = "|"
dg["b"] = "|"
dh = dg["a label_filled ID_link_md b ".split() + [cname_mcl] + ["b"]]
dh.to_csv("../data/reformatted_matches_selected_columns_12.csv", index=False, sep=" ")

print("done.")
