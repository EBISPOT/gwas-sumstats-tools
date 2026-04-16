# 1. pandera is used for sumstats validation
Decision made date: 2023-02-23
Documentation creation date: 2026-01-02

## Status
Accepted

## Context

### Analysis data characteristics
1. Summary statistics
Summary statistics validation operates on large-scale GWAS summary statistic files, enforcing data type and order checks on 7 mandatory and 7 optional columns. These files are typically very large, often containing millions of rows:
- Average: ~11.5 million rows
- Median: ~10.0 million rows
- Minimum: 138,140 rows
- Maximum: 68,826,018 rows
(Data based on submissions prior to February 2024)

Given this scale, performance and memory efficiency are critical considerations.

2. Metadata YAML file
The metadata YAML is a lightweight file containing the metadata describing the GWAS study design and a few SumStats file features (file type, genome build, md5sum). It includes 5 mandatory fields and 25 optional fields. Each file is less than 50 KB.

### Options
1. Pandera = 0.13.4
2. pydantic = 1.10.9

### Benchmarking Result
1. James conducted internal benchmarking in 2023 and found that Pydantic v1 is slower than Pandera for large-scale tabular validation.

2. Pydantic v2 was released in 2023 with improved performance. Without conducting independent benchmarking, we relied on the benchmarking results published by the Pandera team. Reference: https://www.union.ai/blog-post/pandera-0-17-adds-support-for-pydantic-v2

## Discussion
1. Based on this online benchmarking result, it shows that Pandera is approximately 100× faster than Pydantic (both v1 and v2) when validating datasets with more than 1 million rows.
2. In addition, petl is significantly more efficient than pandas for reading large TSV files in chunks and for fast row indexing, which further improves overall validation performance.
3. Pandera is natively designed for DataFrame-based schema validation, which aligns naturally with the columnar structure of GWAS summary statistics files. Pydantic, by contrast, is primarily designed for validating individual Python objects (e.g., dicts, dataclasses), requiring row-by-row iteration over tabular data. The pydantic approach that does not scale well to millions of rows.

## Decision

1. We will use Pandera + petl as the core technologies for summary statistics validation to ensure fast, scalable, and memory-efficient processing of large GWAS datasets.
2. Pydantic (version:1.10.9)will continue to be used for lightweight YAML metadata validation, where its object-oriented
model is well-suited to small, structured files.

Sumstats validation is validating items and dataframes with the same logic

## Consequences

Positive

  - Significantly improved validation performance for large-scale GWAS summary statistics
    files (up to 100x faster than Pydantic for datasets >1 million rows).
  - Memory-efficient processing of large TSV files via petl chunked reading.
  - Schema definitions are expressive and closely aligned with the tabular/columnar data
    model of summary statistics files.
  - Pandera integrates well with pandas DataFrames.

Trade-offs

  - Two separate validation libraries (Pandera for tabular data, Pydantic for YAML metadata)
    must be maintained, increasing dependency surface area.
  - Benchmarking for Pydantic v2 was not conducted internally; the decision relies on
    third-party benchmarks published by the Pandera project. If the performance gap narrows
    in future releases, the decision should be revisited.

Future Considerations

  - Upgrade Pandera from v0.13.4 as new stable releases are made available, particularly
    to benefit from any Pydantic v2 interoperability improvements.
  - Consider consolidating to a single validation library if one framework becomes capable
    of efficiently handling both tabular and metadata validation at scale.
