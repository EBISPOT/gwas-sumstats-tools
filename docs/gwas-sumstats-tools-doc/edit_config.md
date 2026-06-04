# How to Edit the Configuration
----

## Configuration Overview

The configuration file is a blueprint for all formatting options. It has two top-level sections:

- **`fileConfig`** — applied first; controls file-level settings (separator, output prefix, missing values, etc.)
- **`columnConfig`** — applied after `fileConfig`; controls column-level operations via two subsections:
  - `split` — runs first; splits or extracts values from a column into new columns
  - `edit` — runs after `split`; renames, finds/replaces, or extracts values within a column

<details>
<summary>Full example of a JSON configuration template</summary>

```json
{
    "fileConfig": {
        "outFilePrefix": null,
        "convertNegLog10Pvalue": false,
        "fieldSeparator": "\t",
        "naValue": null,
        "removeComments": null
    },
    "columnConfig": {
        "split": [
            {
                "field": "SNP",
                "separator": ":",
                "capture": null,
                "new_field": ["chromosome", "base_pair_location"],
                "include_original": true
            }
        ],
        "edit": [
            {
                "field": "A1",
                "rename": "effect_allele",
                "find": null,
                "replace": null,
                "extract": null
            }
        ]
    }
}
```
</details>

---

## fileConfig Section

| Field | Description | Example value |
|---|---|---|
| `outFilePrefix` | Prefix prepended to the output filename | `"formatted_"` |
| `fieldSeparator` | Delimiter used in the input file | `"\t"` (tab), `","` (comma) |
| `naValue` | Missing value string to convert to `#NA` | `"NaN"` |
| `removeComments` | Strip lines beginning with this character | `"#"` |
| `convertNegLog10Pvalue` | Convert `-log₁₀(p)` column to p-values | `true` |

>[!WARNING|style:callout]
> `convertNegLog10Pvalue` applies `10^(-x)` to the column **already named `p_value`** — it does **not** find or rename your original column automatically.
> If your input column has a different name (e.g. `neg_p_value`, `LOG10P`), you **must** rename it to `p_value` in the **Column Config → Edit** section first, otherwise the conversion will silently have no effect.
>
> **Two-step checklist:**
> 1. Column Config → Edit: rename your `-log₁₀(p)` column to `p_value`
> 2. File Config: set `convertNegLog10Pvalue` to `true`


---

## columnConfig Section

### `split` Subsection

Use `split` to break one column into multiple new columns, either by a plain separator or a regex capture group.

| Field | Description |
|---|---|
| `field` | Name of the column to split |
| `separator` | Plain character or string to split on (e.g. `":"`) |
| `capture` | Regex pattern with capture groups; each group becomes a new column |
| `new_field` | List of names for the new columns produced by the split |
| `include_original` | `true` to keep the original column; `false` (default) to drop it |

>[!NOTE|style:callout]
> `new_field` names are assigned **first-comes-first-serve**: the first name is given to the first split part, the second name to the second part, and so on. If a column produces more parts than there are names in `new_field`, the extra parts are silently **dropped**.
>
> For example, if column `A1_A2_A3_A4` is split by `_` but `new_field` is `["B1", "B2", "B3"]`, then `B1 = A1`, `B2 = A2`, `B3 = A3`, and the fourth part `A4` is discarded.

>[!TIP|style:callout]
> Use either `separator` **or** `capture` — not both at the same time. If your pattern is complex, [Regex101](https://regex101.com/) is a great tool for testing and debugging regular expressions.

---

#### Example 1 — Split by separator

Split a combined `SNP` column (`chr11:88249377`) into separate `chromosome` and `base_pair_location` columns using `:` as the separator.

**Before:**

| **SNP** | rsid | EA |
|---|---|---|
| **chr11:88249377** | rs11020170_T_C | T |
| **chr1:60320992** | rs116406626_A_G | A |
| **chr2:18069070** | rs763680312_T_C | T |
| **chr8:135908647** | rs11992603_A_G | A |

**Configuration:**

```json
{
    "field": "SNP",
    "separator": ":",
    "capture": null,
    "new_field": ["chromosome", "base_pair_location"],
    "include_original": true
}
```

**After:**

| SNP | rsid | EA | **chromosome** | **base_pair_location** |
|---|---|---|---|---|
| chr11:88249377 | rs11020170_T_C | T | **chr11** | **88249377** |
| chr1:60320992 | rs116406626_A_G | A | **chr1** | **60320992** |
| chr2:18069070 | rs763680312_T_C | T | **chr2** | **18069070** |
| chr8:135908647 | rs11992603_A_G | A | **chr8** | **135908647** |

---

#### Example 2 — Split by regex capture group

Extract the rsID and both alleles from a combined `rsid` column (`rs11020170_T_C`) into three separate columns using a capture group.

**Before:**

| SNP | **rsid** | EA |
|---|---|---|
| chr11:88249377 | **rs11020170_T_C** | T |
| chr1:60320992 | **rs116406626_A_G** | A |
| chr2:18069070 | **rs763680312_T_C** | T |
| chr8:135908647 | **rs11992603_A_G** | A |

**Configuration:**

```json
{
    "field": "rsid",
    "separator": null,
    "capture": "(rs[0-9]+)_([A,T,C,G])_([A,T,C,G])",
    "new_field": ["rsid", "effect_allele", "other_allele"],
    "include_original": false
}
```

**After** (original `rsid` column is replaced by three new columns):

| SNP | EA | **rsid** | **effect_allele** | **other_allele** |
|---|---|---|---|---|
| chr11:88249377 | T | **rs11020170** | **T** | **C** |
| chr1:60320992 | A | **rs116406626** | **A** | **G** |
| chr2:18069070 | T | **rs763680312** | **T** | **C** |
| chr8:135908647 | A | **rs11992603** | **A** | **G** |

---

### `edit` Subsection

Use `edit` to rename columns or modify values within a column. Each entry operates on one column.

| Field | Description |
|---|---|
| `field` | Name of the column to edit |
| `rename` | New name for the column header |
| `find` | Regex pattern to find within cell values |
| `replace` | Replacement string (use `""` to delete the matched text) |
| `extract` | Regex pattern; only the matched portion is kept as the new cell value |

>[!NOTE|style:callout]
> `find` and `replace` must be used **together**. To delete a substring, set `replace` to `""` — do not leave it as `null`.
> `rename` only changes the column header, not the values. Use `find`/`replace` for value changes.

---

#### Example 3 — Rename and find/replace

Rename the `chr` column to `chromosome` and strip the `chr`/`CHR` prefix from its values to produce numeric chromosome codes.

**Before:**

| SNP | EA | **chr** | base_pair_location |
|---|---|---|---|
| chr11:88249377 | T | **chr11** | 88249377 |
| chr1:60320992 | A | **CHR1** | 60320992 |
| chr2:18069070 | T | **chr2** | 18069070 |
| chr8:135908647 | A | **CHR8** | 135908647 |

**Configuration:**

```json
{
    "field": "chr",
    "rename": "chromosome",
    "find": "chr|CHR",
    "replace": "",
    "extract": null
}
```

**After:**

| SNP | EA | **chromosome** | base_pair_location |
|---|---|---|---|
| chr11:88249377 | T | **11** | 88249377 |
| chr1:60320992 | A | **1** | 60320992 |
| chr2:18069070 | T | **2** | 18069070 |
| chr8:135908647 | A | **8** | 135908647 |

---

#### Example 4 — Extract with regex

Extract only the rsID portion from a combined `rsid` column and rename the column to `variant_id`.

**Before:**

| chromosome | base_pair_location | **rsid** | effect_allele | other_allele |
|---|---|---|---|---|
| 11 | 88249377 | **rs11020170_T_C** | T | C |
| 1 | 60320992 | **rs116406626_A_G** | A | G |
| 2 | 18069070 | **rs763680312_T_C** | T | C |
| 8 | 135908647 | **rs11992603_A_G** | A | G |

**Configuration:**

```json
{
    "field": "rsid",
    "rename": "variant_id",
    "find": null,
    "replace": null,
    "extract": "rs[0-9]+"
}
```

**After:**

| chromosome | base_pair_location | **variant_id** | effect_allele | other_allele |
|---|---|---|---|---|
| 11 | 88249377 | **rs11020170** | T | C |
| 1 | 60320992 | **rs116406626** | A | G |
| 2 | 18069070 | **rs763680312** | T | C |
| 8 | 135908647 | **rs11992603** | A | G |

---

## Additional Functions

Beyond the configuration file, the formatter automatically applies these steps to every file:

1. **Reorder mandatory columns** to match the GWAS-SSF sequence:
   `chromosome` → `base_pair_location` → `effect_allele` → `other_allele` → `effect` (beta / odds ratio / hazard ratio / `z-score`) → `standard_error` → `effect_allele_frequency` → `p_value` (or `neg_log_10_p_value`). For `z-score` files, omit `standard_error`.
   Any extra columns follow in their original order.

2. **Fill missing mandatory columns** — if a required column is absent, it is added and filled with `#NA`.

3. **Normalise NA values** — any `NA` or `None` values are converted to `#NA` for consistency.

----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
