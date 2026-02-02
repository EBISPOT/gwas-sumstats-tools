# 1. pandera is used for sumstats validation
Date: 2026-01-02

## Status
Accepted

## Context
Summary statistics validation operates on large-scale GWAS summary statistic files, enforcing data type and order checks on 7 mandatory and 7 optional columns. These files are typically very large, often containing millions of rows:
- Average: ~11.5 million rows
- Median: ~10.0 million rows
- Minimum: 138,140 rows
- Maximum: 68,826,018 rows
(Data based on submissions prior to February 2024)

Given this scale, performance and memory efficiency are critical considerations.

Pandera V.S. pydantic:

reference: https://www.union.ai/blog-post/pandera-0-17-adds-support-for-pydantic-v2

Based on this benchmarking result, it shows that Pandera is approximately 100× faster than Pydantic (both v1 and v2) when validating datasets with more than 1 million rows.

In addition, petl is significantly more efficient than pandas for reading large TSV files in chunks and for fast row indexing, which further improves overall validation performance.

## Decision

We will use Pandera + petl as the core technologies for summary statistics validation to ensure fast, scalable, and memory-efficient processing of large GWAS datasets.

While metadata schema use pydantic (version:1.10.9). 

## Consequences
- These performance gains are essential for summary statistics validation, as the tool is used in multiple contexts:
   - local execution by users
   - server-side validation
   - user-side JS script.
- Integration with larger Pydantic-based systems is less straightforward and may require explicit schema translation or adapter layers.
   - Pandera is validate based on volumn (vector)
   - Pydantic is vlidate based on row