"""
Some helpers and wrappers
"""
import polars as pl
import s3fs
import pyarrow.dataset as ds
from typing import Union, List
from functools import partial


def get_filesystem(uri):
    fs = None if uri[:5] != "s3://" else s3fs.S3FileSystem()
    return fs  # if none we could return something like an interface


def _get_writer(df, uri=None):
    """
    the writer is determined from the uri and defaults to parquet
    """
    # TODO generalize / assume parquet for now for our usecase
    return partial(df.write_parquet)


def read_dataset(uri) -> ds.Dataset:
    fs = None if uri[:5] != "s3://" else s3fs.S3FileSystem()
    # we choose to infer the format
    format = uri.split(".")[-1]
    return ds.dataset(uri, filesystem=fs, format=format)


def exists(uri):
    fs = None if uri[:5] != "s3://" else s3fs.S3FileSystem()
    if fs:
        return fs.exists(uri)
    raise Exception("Not implemented for scheme but easy to fix")


def ls(root, file_type="*", search=f"**/", **kwargs):
    """
    deep listing
    """
    file_type = f"*.{file_type}" if file_type else None
    search = f"{root}/{search}{file_type}"
    results = [f"s3://{f}" for f in s3fs.S3FileSystem().glob(search)]
    return results


def glob(pattern, **kwargs):
    return s3fs.S3FileSystem().glob(pattern, **kwargs)


def read(uri, lazy=False) -> pl.DataFrame:
    """
    read data to polar data
    """
    dataset = read_dataset(uri)
    if lazy:
        return pl.scan_pyarrow_dataset(dataset)

    return pl.from_arrow(dataset.to_table())


def get_query_context(uri, name):
    """
    get the polar query context from polars
    """
    ctx = pl.SQLContext()
    ctx.register(name, read(uri, lazy=True))
    return ctx


def read_if_exists(uri, **kwargs):
    # TODO: add some s3 clients stuff
    try:
        # fs = get_filesystem()
        # if fs and not fs.exists(uri):
        #     return None
        return read(uri=uri, **kwargs)
    except:
        return None


def write(uri, data: Union[pl.DataFrame, List[dict]]):
    """
    write data from polar data to format=parquet
    """
    if not isinstance(data, pl.DataFrame):
        # assume the data are dicts or pydantic objects
        data = pl.DataFrame([d.dict() if hasattr(d, "dict") else d for d in data])

    fs = None if uri[:5] != "s3://" else s3fs.S3FileSystem()

    fn = _get_writer(data, uri)
    if fs:
        with fs.open(uri, "wb") as f:
            fn(f)
    else:
        # we never really do this because we are always floating in the cloud
        fn(uri)

    return read_dataset(uri)


def merge(uri: str, data: Union[pl.DataFrame, List[dict]], key: str) -> ds.Dataset:
    """
    merge data from polar data using key

    """
    existing = read_if_exists(uri)

    if isinstance(data, list):
        # assume the data are dicts or pydantic objects
        data = pl.DataFrame([d.dict() if hasattr(d, "dict") else d for d in data])
    if not isinstance(data, pl.DataFrame):
        raise Exception(
            "Only list of dicts and polar dataframes are supported - what did you pass in?"
        )
    if existing is not None:
        data = pl.concat([existing, data])

    write(uri, data.unique(subset=[key], keep="last"))

    return read_dataset(uri)


def typed_record_iterator(uri, entity_type, lazy=False):
    """
    im not sure how to lazily do this but we will look into it or chunk perhaps
    """
    df = read(uri, lazy=lazy)
    for record in df.rows(named=True):
        yield (entity_type(**record))
