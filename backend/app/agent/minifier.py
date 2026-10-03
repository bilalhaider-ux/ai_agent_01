"""Stage 1: Context Minification Engine.

Reads raw dataset using Polars and extracts a compressed, high-density
profile (schema, data types, sample rows, null distributions, summary statistics)
to minimize LLM token consumption while providing 100% analytical context.
"""

from pathlib import Path
from typing import Union
import polars as pl
from .contracts import DatasetMinifiedContext


def minify_dataset(file_path: Union[str, Path], sample_size: int = 5) -> DatasetMinifiedContext:
    """Read a dataset with Polars and produce a compact statistical schema.
    
    Args:
        file_path: Absolute or relative path to CSV, XLSX, Parquet, TSV, JSON, or JSONL file.
        sample_size: Number of head rows to sample.
        
    Returns:
        DatasetMinifiedContext schema model.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")
    
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pl.read_csv(str(path))
    elif suffix == ".xlsx":
        df = pl.read_excel(str(path))
    elif suffix in (".parquet", ".pq"):
        df = pl.read_parquet(str(path))
    elif suffix == ".tsv":
        df = pl.read_csv(str(path), separator="\t")
    elif suffix == ".json":
        df = pl.read_json(str(path))
    elif suffix == ".jsonl":
        df = pl.read_ndjson(str(path))
    else:
        raise ValueError(f"Unsupported dataset format: {suffix}")
        
    row_count = df.height
    col_count = df.width
    columns = df.columns
    dtypes = {col: str(df.schema[col]) for col in columns}
    
    # Calculate null counts per column
    null_counts = {}
    for col in columns:
        null_counts[col] = int(df[col].null_count())
        
    # Sample markdown table
    sample_df = df.head(sample_size)
    sample_markdown = str(sample_df)
    
    # Statistical summary for numeric / date columns
    try:
        describe_df = df.describe()
        summary_stats_markdown = str(describe_df)
    except Exception:
        summary_stats_markdown = "Summary statistics could not be computed automatically."
        
    return DatasetMinifiedContext(
        row_count=row_count,
        column_count=col_count,
        columns=columns,
        dtypes=dtypes,
        null_counts=null_counts,
        sample_markdown=sample_markdown,
        summary_stats_markdown=summary_stats_markdown
    )

