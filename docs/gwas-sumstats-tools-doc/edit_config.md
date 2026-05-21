# How to Edit the Configuration
----
## Configuration Overview
The configuration file serves as a blueprint for the formatting options. It includes options for output file settings and column-specific formatting operations. Users can customize field separators, column splitting, renaming, finding and replacing values, and more based on requirements.

While using the CLI, configurations are managed within the `filename.json` file. On the UI, however, configurations are accessible in a text box, allowing users to easily customize settings without the need to open and edit JSON files

<details>
<summary>Here is an example of the JSON configuration template</summary>

```json
{
    "fileConfig": {
        "outFileSuffix": null,
        "convertNegLog10Pvalue": false,
        "fieldSeparator": " ",
        "naValue": null,
        "removeComments": null,
    },
    "columnConfig": {
        "split": [
            {
                "field": "SNP",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "A1",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "A2",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "freq",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "b",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "se",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "p",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "N_cases",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            },
            {
                "field": "N_controls",
                "separator": null,
                "capture": null,
                "new_field": null,
                "include_original": null
            }
        ],
        "edit": [
            {
                "field": "SNP",
                "rename": "variant_id",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "",
                "rename": "",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "A1",
                "rename": "effect_allele",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "A2",
                "rename": "other_allele",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "freq",
                "rename": "effect_allele_frequency",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "b",
                "rename": "beta",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "se",
                "rename": "standard_error",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "p",
                "rename": "p_value",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "N_cases",
                "rename": "n_cas",
                "find": null,
                "replace": null,
                "extract": null
            },
            {
                "field": "N_controls",
                "rename": "n_con",
                "find": null,
                "replace": null,
                "extract": null
            }
        ]
    }
}
```
</details>

The configurations comprises two primary sections: `fileConfig` and `columnConfig`. The `columnConfig` section further encompasses two subsections: `split` and `edit`. 

The `fileConfig` settings are applied to the input file first, followed by modifications from the `split` and then the `edit` subsections.

### fileConfig Section:
  - `outFileSuffix`: Specifies the suffix for the output file. It is currently set to null. To name your formatted file as `filename_formatted.tsv`, specify the suffix in your configuration as shown below:
    ```json
     "outFileSuffix":"_formatted"
     ```
  - `convertNegLog10Pvalue`: Specifies whether to recognize and convert the column named `neg_log_10_p_value` into p-values. This field is set to false by default. To enable this conversion, adjust your settings as follows:
    ```json
     "convertNegLog10Pvalue":true
     ```

  If `convertNegLog10Pvalue` is set to `false`: The formatter will automatically create a `p_value` column with `NA` values if the `p_value` column is missing in the input data.

  If `convertNegLog10Pvalue` is set to `true`: The values in the `neg_log_10_p_value` column will be converted to p-values using the formula `10**(-float(x))`. The `neg_log_10_p_value` column will be renamed to `p_value`.

  - `fieldSeparator`: Defines the field separator for reading the input file. It is the same as the `--delimiter` option in the command line. If not specified, we can automatically detect the delimiter as whitespace for a *.txt file, comma for a *.csv file; or tab for a *.tsv file. Otherwise, please specify the delimiter to help the validator to recognise the column correctly.To specify a tab as the separator, use:
     ```json
     "fieldSeparator":"\t"
     ```
  - `removeComments`: The `removeComments` field acts like the `--remove_comments` command-line option. Setting this to a character or string, like "#", removes lines starting with that character or string from the input file. For example, to remove lines that begin with `#`, effectively eliminating comments or metadata for a cleaner output, use:
     ```json
     "removeComments":"#"
     ```
  - `naValue`: Different software may represent missing values in various ways. The `naValue` parameter allows you to convert your specified missing value representation into the GWAS-SSF standard `#NA`.
    ```json
     "naValue":"Nan"
     ```


### columnConfig Section:

#### `split` Subsection:

This subsection specifies how to split certain columns in the input file. For each column, it contains:

  - `field`: Specifies the name of the column to be split.
  - `separator`: Defines the delimiter used to split the column. New columns created from the split will be name  as specified in the `new_field`.
     * <details>
        <summary>Separator example</summary>

        **Input**:
        | <span style="color:red">SNP</span> | rsid | EA |
        |-----|-------|---------|
        | <span style="color:red">chr11:88249377</span>| rs11020170_T_C  | T   |
        | <span style="color:red">chr1:60320992</span> | rs116406626_A_G  | A   |
        | <span style="color:red">chr2:18069070</span> | rs763680312_T_C  | T   |
        | <span style="color:red">chr8:135908647</span> | rs11992603_A_G  | A   |

        **JSON configuration**:
        ```json
        "field": "SNP",
        "separator": ":",
        "capture": null,
        "new_field": ["chromosome","base_pair_location"],
        "include_original": true
        ```
        **Output**:
        | SNP | rsid | EA |<span style="color:red">chromosome</span>|<span style="color:red">base_pair_location</span>|
        |-----|-------|---------|----|------------------|
        | <span style="color:red">chr11:88249377</span> | rs11020170_T_C  | T   |<span style="color:red">chr11</span> |<span style="color:red">88249377</span> |
        | <span style="color:red">chr1:60320992</span> | rs116406626_A_G  | A   |<span style="color:red">chr1</span>| <span style="color:red">60320992</span> |
        | <span style="color:red">chr2:18069070</span> | rs763680312_T_C  | T   |<span style="color:red">chr2</span> |<span style="color:red">18069070</span> |
        | <span style="color:red">chr8:135908647</span> | rs11992603_A_G  | A   |<span style="color:red">chr8</span>| <span style="color:red">135908647</span> |
        </details>
  - `capture`: Utilizes a regular expression to extract  specific patterns from the field into multiple new columns. These resulting columns are named according to the values specified in `new_field`.
      * <details>
        <summary>Capture example</summary>

        **Input**:
        | SNP | <span style="color:red">rsid</span> | EA |chromosome|base_pair_location|
        |-----|-------|---------|----|------------------|
        | chr11:88249377 | <span style="color:red">rs11020170_T_C</span> | T   |chr11 |88249377 |
        | chr1:60320992 | <span style="color:red">rs116406626_A_G</span>  | A   |chr1| 60320992 |
        | chr2:18069070 | <span style="color:red">rs763680312_T_C</span>  | T   |chr2 |18069070 |
        | chr8:135908647 | <span style="color:red">rs11992603_A_G</span>  | A   |chr8| 135908647 |

        **JSON configuration**:
        ```json
        "field": "rsid",
        "separator": null,
        "capture": "(rs[0-9]+)_([A,T,C,G])_([A,T,C,G])",
        "new_field": ["rsid","effect_allele","other_allele"],
        "include_original": false
        ```
        **Output**:
        | SNP | EA |chromosome|base_pair_location| <span style="color:red">rsid</span> | <span style="color:red">effect_allele</span>| <span style="color:red">other_allele</span> |
        |-----|---------|----|------------------|-----|-----|----|
        | chr11:88249377 |T   |chr11 |88249377 |<span style="color:red">rs11020170</span> | <span style="color:red">T</span> | <span style="color:red">C</span>  |
        | chr1:60320992 |A   |chr1| 60320992 |<span style="color:red">rs116406626</span> |<span style="color:red">A</span> | <span style="color:red">G</span>|
        | chr2:18069070 |T   |chr2 |18069070 |<span style="color:red">rs763680312</span>| <span style="color:red">T</span> |<span style="color:red">C</span> |
        | chr8:135908647 |A   |chr8| 135908647 |<span style="color:red">rs11992603</span> |<span style="color:red">A</span> |<span style="color:red">G</span> |
        </details>
  - `new_field`: Names the new fields created after splitting.
  - `include_original`: Determines whether to retain the original column after the splitting. By default, the  original field is omitted after the operation.
    

   >[!TIP|style:callout]
   > If you're new to regex, [Regex101](https://regex101.com/) is a highly recommended online tool for testing and debugging regular expressions. It offers detailed explanations of each component of your regex and tests your patterns against sample texts for easy understanding. Additionally, there are numerous [regex cheat sheet](https://cheatography.com/davechild/cheat-sheets/regular-expressions/) available online that provide a handy quick-start guide to familiarize yourself with the basics.

#### `edit` Subsection:
This subsection specifies editing operations to be performed on certain columns.Each entry contains:
- `field`: The name of the column to edit.
- `rename`: Specifies the new name for the column.
- `find`: Specifies a pattern to find within the column.
- `replace`: Specifies a pattern to replace within the  column.
- `extract`: Specifies a pattern to extract from the column.
    * <details>
      <summary>Find and replace example</summary>

      **Input**:
      | SNP | EA |<span style="color:red">chr</span>|base_pair_locatiorsid |rsid| effect_allele|other_allele |
      |-----|----|---------|-----------------------|----|-------------|------------|
      | chr11:88249377 |T   |<span style="color:red">chr11</span> |88249377    |rs11020170 |     T | C  |
      | chr1:60320992 |A   |<span style="color:red">CHR1</span>| 60320992  |   rs116406626 |    A | G|
      | chr2:18069070 |T   |<span style="color:red">chr2</span> |18069070  |  rs763680312|     T |C |
      | chr8:135908647 |A   |<span style="color:red">CHR8</span>| 135908647 |rs11992603 |    A |G |
      
      **JSON configuration**:
       ```json
      "field": "chr",
      "rename": "chromosome",
      "find": "chr|CHR",
      "replace": "",
      "extract": null
       ```
      
      **Output**:
      | SNP | EA |<span style="color:red">chromosome</span>|base_pair_location| rsid  |effect_allele| other_allele |
      |-----|----|----------|------------------|-------|--------------|-------------|
      | chr11:88249377 |T   |<span style="color:red">11</span> |88249377| rs11020170 |     T | C  |
      | chr1:60320992 |A   |<span style="color:red">1</span>| 60320992 |rs116406626|A |     G|
      | chr2:18069070 |T   |<span style="color:red">2</span> |18069070 |rs763680312 |T |    C |
      | chr8:135908647 |A   |<span style="color:red">8</span>| 135908647 |rs11992603 | A |    G |
      
      
      When utilizing the find and replace function, please note that it will modify values within the columns but  not within the headers. For instance, if you try to replace `chr` in the column headers, the header `chromosome` will remain unchanged. Please use the `rename` function to change the header.

      >[!NOTE|style:callout]
      > Please use "find and replace" together. To remove      any character, enter `""` (an empty string) in the      replace field, rather than leaving it as `null`.      
      </details>

    
    * <details>
      <summary>Extract example</summary>
      
      **Input**:
      | chromosome| base_pair_location | <span style="color:red">rsid</span> |effect_allele| other_allele |
      |-----------|--------------------|------|-------------|-------------|
      | 11| 88249377 | <span style="color:red">rs11020170_T_C</span>  | T   | C|
      | 1 | 60320992 | <span style="color:red">rs116406626_A_G</span>  | A   | G|
      | 2 | 18069070 | <span style="color:red">rs763680312_T_C </span> | T   | C|
      | 8 |135908647 | <span style="color:red">rs11992603_A_G</span>  | A   | G|
      
      **JSON configuration**:
       ```json
      "field": "rsid",
      "rename": "variant_id",
      "find": null,
      "replace": null,
      "extract": "rs[0-9]+"
       ```
      
      **Output**:
       | chromosome| base_pair_location | <span style="color:red">variant_id |effect_allele|other_allele |
      |-----|-------|-------------|-------------|------|
      | 11| 88249377 | <span style="color:red">rs11020170</span> | T   | C|
      | 1| 60320992 | <span style="color:red">rs116406626</span>  | A   | G|
      | 2| 18069070 | <span style="color:red">rs763680312</span> | T   | C|
      | 8|135908647 | <span style="color:red">rs11992603</span>  | A   | G|
      
      </details>

## Additional Functions
Beyond formatting the input file according to the configuration file, the format tool also applies several default settings to every summary statistics file:

1. Reorder the mandatory columns in your dataset to match the GWAS-SSF specified sequence: 
```text
chromosome, base_pair_location, effect_allele, other_allele, effect (beta/odds ratio/hazard ratio), standard_error, effect_allele_frequency, pval (or negativelog10Pvalue). 
```
Arrange any additional columns in their original input order.
2. Fill missing fields: If any mandatory column is missing from the input file, the format tool will automatically add this column and populate all its values with `#NA`.
3. Convert NA values: The tool converts any 'NA' or 'None' values to `#NA`, ensuring data consistency.

----
Copyright © EMBL-EBI 2024 | EMBL-EBI is an Outstation of the [European Molecular Biology Laboratory](https://www.embl.org/) | [Terms of use](https://www.ebi.ac.uk/about/terms-of-use) | [Data Preservation Statement](https://www.ebi.ac.uk/long-term-data-preservation)
