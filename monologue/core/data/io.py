"""
Some helpers and wrappers
"""
import polars as pl
import s3fs
import pyarrow.dataset as ds

def read_dataset(uri) -> ds.Dataset:
    fs = None if uri[:5] != 's3://' else s3fs.S3FileSystem()
    return ds.dataset(uri, filesystem=fs)

def read(uri, lazy=False):
    """
    read data to polar data
    """
    dataset = read_dataset(uri)
    if lazy:
        return pl.scan_pyarrow_dataset(dataset)
    
    return pl.from_arrow(dataset.to_table())

def write(uri,  data ):
    """
    write data from polar data
    """
    
    pass 


def merge(uri,  data, key ):
    """
    merge data from polar data using key
    """
    
    pass    
