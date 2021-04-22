from logging import getLogger
from typing import List

from botocore.client import BaseClient

from src.clients import boto_try
from src.data.aws_s3_types import (
    Bucket,
    BucketEncryption,
    BucketLogging,
    to_bucket,
    to_bucket_encryption,
    to_bucket_logging,
)


class AwsS3Client:
    def __init__(self, boto_s3: BaseClient):
        self._logger = getLogger(self.__class__.__name__)
        self._s3 = boto_s3

    def list_buckets(self) -> List[Bucket]:
        return [to_bucket(bucket) for bucket in self._s3.list_buckets()["Buckets"]]

    def get_bucket_encryption(self, bucket: str) -> BucketEncryption:
        self._logger.debug(f"fetching encryption config for bucket '{bucket}'")
        return boto_try(
            lambda: to_bucket_encryption(self._s3.get_bucket_encryption(Bucket=bucket)),
            BucketEncryption,
            f"unable to fetch encryption config for bucket '{bucket}'",
        )

    def get_bucket_logging(self, bucket: str) -> BucketLogging:
        self._logger.debug(f"fetching server access logging config for bucket '{bucket}'")
        return boto_try(
            lambda: to_bucket_logging(self._s3.get_bucket_logging(Bucket=bucket)),
            BucketLogging,
            f"unable to fetch server access logging config for bucket '{bucket}'",
        )