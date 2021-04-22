from unittest import TestCase
from unittest.mock import mock_open, patch

test_config = """
[accounts]
auth = 111222333444
cloudtrail = 555666777888
root = 999888777666

[athena]
database_prefix = some_prefix

[buckets]
athena_query_results = query-results-bucket
cloudtrail_logs = cloudtrail-logs-bucket

[cloudtrail]
log_retention_days = 90

[organizational_unit]
include_root_accounts = true
parent = Parent OU

[roles]
cloudtrail = cloudtrail_role
organizations = orgs_role
s3 = s3_role
ssm = ssm_role
username = joe.bloggs

[session]
duration_seconds = 3600

[tasks]
executor = 10
"""


class AwsScannerTestCase(TestCase):
    patch("builtins.open", mock_open(read_data=test_config)).start()