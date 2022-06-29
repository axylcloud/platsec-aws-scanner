from dataclasses import dataclass
from typing import Any, Dict

from src.clients.composite.aws_route53_client import AwsRoute53Client
from src.data.aws_organizations_types import Account
from src.tasks.aws_task import AwsTask
import src.data.aws_route53_types as route53Type


@dataclass
class AwsAuditRoute53PublicZonesTask(AwsTask):
    def __init__(self, account: Account) -> None:
        super().__init__("audit Route53 public zones", account)

    def _run_task(self, client: AwsRoute53Client) -> Dict[Any, Any]:
        public_zones: Dict[Any, Any] = {}
        hostedzones = client.list_hosted_zones()["HostedZones"]
        for host in hostedzones:
            zone = route53Type.to_route53Zone(host)
            if not zone.privateZone:
                queryLogConfig = client.list_query_logging_configs(zone.id.replace("/hostedzone/", ""))
                if len(queryLogConfig) > 0 and len(queryLogConfig["QueryLoggingConfigs"]) > 0:
                    zone.queryLog = queryLogConfig["QueryLoggingConfigs"][0]["CloudWatchLogsLogGroupArn"]
                public_zones[zone.id] = zone

        return public_zones
