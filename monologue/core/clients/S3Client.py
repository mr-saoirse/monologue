import pandas as pd
from pathlib import Path
import urllib
import boto3
import yaml
import json
import os
import pickle
import numpy as np
from io import BytesIO
import tempfile
from datetime import datetime, date
from pandas.api.types import is_datetime64_any_dtype as is_datetime
import fastavro
from dateutil.parser import parse as date_parse
from typing import Union, List
import s3fs
try:
    #optional
    from PIL import Image
except:
    pass

class S3Client(object):
    def __init__(self, format="line_json"):
        self.format = format
        self._s3fs = s3fs.S3FileSystem(version_aware=True)

    def get_client(self, **kwargs):
        return boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )


    def exists(self, url):
        url = urllib.parse.urlparse(url)
        assert (
            url.scheme == "s3"
        ), "The url must be of the form s3://BUCKET/path/to/file/ext"
        bucket = url.netloc
        prefix = url.path.lstrip("/")
        client = self.get_client()
        result = client.list_objects(Bucket=bucket, Prefix=prefix)
        return "Contents" in result


    def read(self, path, version_id=None, before=None, after=None, at=None, **kwargs):
        """
       
        """
        P = Path(path)
        url = urllib.parse.urlparse(path)
        assert (
            url.scheme == "s3"
        ), "The url must be of the form s3://BUCKET/path/to/file/ext"
        bucket = url.netloc
        prefix = url.path.lstrip("/")

        def get_streaming_body():
            c = self.get_client()
            try:
                if version_id or before or after or at:
                    response = self.read_version(
                        path, version_id=version_id, before=before, after=after, at=at
                    )
                else:
                    response = c.get_object(Bucket=bucket, Key=prefix)["Body"]
                return response
            except Exception as ex:
                raise ex
        if P.suffix in [".yml", ".yaml"]:
            return yaml.safe_load(get_streaming_body())
        if P.suffix in [".json"]:
            return json.load(get_streaming_body())
        if P.suffix in [".svg"]:
            return get_streaming_body().read().decode()
        if P.suffix in [".csv"]:
            return pd.read_csv(path, **kwargs)
        if P.suffix in [".txt", ".log"]:
            return get_streaming_body().read()
        if P.suffix in [".parquet"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "rb") as f:
                return pd.read_parquet(f, **kwargs)
        if P.suffix in [".avro"]:
            encoding = kwargs.get("encoding", "rb")
            with self._s3fs.open(f"{bucket}/{prefix}", encoding) as f:
                if "ignore_root" in kwargs:
                    root = kwargs.get("ignore_root")
                    return pd.DataFrame.from_records(
                        [r[root] for r in fastavro.reader(f)]
                    )
                return pd.DataFrame.from_records([r for r in fastavro.reader(f)])
        if P.suffix in [".feather"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "rb") as f:
                return pd.read_feather(f, **kwargs)
        if P.suffix in [".png", ".jpg", ".jpeg", ".tiff", ".tif"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "rb") as s3f:
                with tempfile.NamedTemporaryFile(
                    suffix=".png", prefix="f", mode="wb"
                ) as f:
                    f.write(s3f.read())
                    f.flush()
                    return Image.open(f.name)
        if P.suffix in [".pickle"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "rb") as f:
                return pickle.load(f)

        raise Exception(f"TODO: handle case for file type {path}")


    def write(self, path, data, **kwargs):
        P = Path(path)
        url = urllib.parse.urlparse(path)
        assert (
            url.scheme == "s3"
        ), "The url must be of the form s3://BUCKET/path/to/file/ext"
        bucket = url.netloc
        prefix = url.path.lstrip("/")
        c = self.get_client()

        # TODO handle dataframe or special types
        if P.suffix in [".parquet"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "wb") as f:
                return data.to_parquet(f, **kwargs)
        if P.suffix in [".feather"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "wb") as f:
                return data.to_feather(f, **kwargs)
        if P.suffix in [".csv"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "wb") as f:
                return data.to_csv(f, **kwargs)
        if P.suffix in [".pickle"]:
            with self._s3fs.open(f"{bucket}/{prefix}", "wb") as f:
                return pickle.dump(data, f, **kwargs)
        if P.suffix in [".jpg", ".jpeg", ".tiff", "tif", ".png"]:
            format = P.suffix[1:] 
            _data = BytesIO()
            if not isinstance(data, Image.Image):
                data = Image.fromarray(data)
            data.save(_data)
            data = _data.getvalue()
            return c.put_object(Bucket=bucket, Key=prefix, Body=data)
        if P.suffix in [".pdf"]:
            return c.put_object(
                Bucket=bucket, Key=prefix, Body=data, ContentType="application/pdf"
            )
        if isinstance(data, dict):
            if P.suffix in [".yml", "yaml"]:
                data = yaml.safe_dump(data)
            if P.suffix in [".json"]:
                data = json.dumps(data)

        return c.put_object(Bucket=bucket, Key=prefix, Body=data)


    def merge_records(self, uri: str, data: pd.DataFrame , key: str)->pd.DataFrame:
        """
        this is a simple merge of parquet files. Assumes fairly small data and we do not partition or version
        
        Args:
            uri (str): _description_
            data (pd.DataFrame): _description_
            key (str): _description_

        Returns:
            _type_: pd.DataFrame
            combined what was there and what we added
        """
        if not isinstance(data,pd.DataFrame):
            if isinstance(data,list):
                data = pd.DataFrame([d.dict() if hasattr(d,'dict') else d for d in data])
        if self.exists(uri) and len(data):
            existing = self.read(uri)
            data = pd.concat([existing, data]).drop_duplicates(subset=[key], keep="last")
        self.write(uri, data)
        return data
    
    def upload(self, source, target):
        bucket, path = self.split_bucket_and_blob_from_path(target)
        client = self.get_client()
        client.upload_file(source, bucket, path)


    def _open_image(self, file_or_buffer, **kwargs):
        return np.array(Image.open(file_or_buffer), dtype=np.uint8)

    def get_files_sizes(self, paths, check_exists=False):
        c = boto3.resource("s3")
        for f in paths:
            if not check_exists or self.exists(f):
                bucket, key = self.split_bucket_and_blob_from_path(f)
                yield {"filename": f, "size": c.Object(bucket, key).content_length}

    def get_file_info(self, file_url):
        bucket, key = self.split_bucket_and_blob_from_path(file_url)
        return self.get_client().head_object(Bucket=bucket, Key=key)

    def split_bucket_and_blob_from_path(self, path):
        P = Path(path)
        url = urllib.parse.urlparse(path)
        assert (
            url.scheme == "s3"
        ), "The url must be of the form s3://BUCKET/path/to/file/ext"
        bucket = url.netloc
        prefix = url.path.lstrip("/")

        return bucket, prefix

    def generate_presigned_url(self, url, expiry=3600, for_upload=False):
        """
        usually for get objects or specify put_object
        https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html#generating-a-presigned-url-to-upload-a-file
        """
        bucket_name, object_key = self.split_bucket_and_blob_from_path(url)

        try:
            if for_upload:
                return self.get_client().generate_presigned_url(
                    "put_object",
                    Params={
                        "Bucket": bucket_name,
                        "Key": object_key,
                    },
                    ExpiresIn=expiry,
                    HttpMethod="PUT",
                )

            return self.get_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": object_key},
                ExpiresIn=expiry,
            )

        except Exception as ex:
            raise ex



    def copy(self, source, target):
        """
        Copy from one location to another
        """
        bucket_a, path_a = self.split_bucket_and_blob_from_path(source)
        bucket_b, path_b = self.split_bucket_and_blob_from_path(target)

        with self._s3fs.open(f"{bucket_a}/{path_a}", "rb") as s:
            with self._s3fs.open(f"{bucket_b}/{path_b}", "wb") as t:
                t.write(s.read())

    def ls(self, url, suffixes=None, modified_after=None, modified_before=None):
        for info in self.ls_info(
            url=url,
            suffixes=suffixes,
            modified_after=modified_after,
            modified_before=modified_before,
        ):
            yield info["path"]

    def get_files_with_versions(self, uri):
        """
        not tested for pagination
        """
        bucket, prefix = self.split_bucket_and_blob_from_path(uri)
        # paginator = client.get_paginator("list_objects")
        V = self.get_client().list_object_versions(Bucket=bucket, Prefix=prefix)
        files = []
        for v in V["Versions"]:
            files.append(
                {
                    "version_id": v["VersionId"],
                    "uri": f"s3://{bucket}/{v[f'Key']}",
                    "last_modified": v["LastModified"].isoformat(),
                }
            )

        return files

    def ls_info(self, url, suffixes=None, modified_after=None, modified_before=None):
        """
        Use the paginator to list any number of object names in the bucket
        A path prefix can be used to limit the search
        One or more suffixes e.g. .ext, .txt, .parquet, .csv can be used to filter
        A generator is returned providing only the file names fully qualified s3://BUCKET/file.ext
        Also the url passed in should be an s3://url or url expression with wild cards (not yet implemented)
        In future could optionally return metadata such as time stamps
        """
        url = urllib.parse.urlparse(url)
        assert (
            url.scheme == "s3"
        ), "The url must be of the form s3://BUCKET/path/to/file/ext"
        bucket = url.netloc
        prefix = url.path.lstrip("/")

        client = self.get_client()

        paginator = client.get_paginator("list_objects")
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

        def _match_suffixes(s):
            return Path(s).suffix in suffixes
        
        def coerce_to_full_datetime(d, tzinfo=None):
            if isinstance(d, str):
                d = date_parse(d)

            if isinstance(d, date):
                d = datetime.combine(d, datetime.min.time())

            return d.replace(tzinfo=tzinfo)

        for page in page_iterator:
            if "Contents" in page:
                for obj in page["Contents"]:
                    f = obj["Key"]
                    if not suffixes or _match_suffixes(f):
                        mod_date = obj["LastModified"]

                        if isinstance(mod_date, str):
                            mod_date = date_parse(mod_date)

                        mod_date = mod_date.replace(tzinfo=None)
                        # conditions
                        if modified_before and mod_date > coerce_to_full_datetime(
                            modified_before
                        ):
                            continue
                        if modified_after and mod_date < coerce_to_full_datetime(
                            modified_after
                        ):
                            continue

                        yield {
                            "path": f"s3://{bucket}/{f}",
                            "size": obj["Size"],
                            "last_modified": mod_date,
                        }


 