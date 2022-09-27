from src.data.aws_task_report import AwsTaskReport
from unittest import TestCase
from unittest.mock import Mock, patch

from typing import Sequence

from src.clients.composite.aws_vpc_client import AwsVpcClient
from src.data.aws_compliance_actions import ComplianceAction, ComplianceActionReport
from src.data.aws_ec2_types import Vpc

from tests.test_types_generator import (
    compliance_action_report,
    create_flow_log_action,
    delete_flow_log_action,
    task_report,
    vpc,
    aws_audit_vpc_dns_logs_task,
)

vpc_client = AwsVpcClient(ec2=Mock(), iam=Mock(), logs=Mock(), config=Mock(), log_group=Mock(), resolver=Mock())
vpcs = [vpc(id="vpc-1"), vpc(id="vpc-2")]


def enforcement_actions(v: Sequence[Vpc], with_sub_filter: bool) -> Sequence[ComplianceAction]:
    return (
        [delete_flow_log_action(flow_log_id="fl-4"), create_flow_log_action(vpc_id="vpc-7")]
        if v == vpcs and with_sub_filter
        else []
    )


@patch.object(AwsVpcClient, "enforcement_dns_log_actions", side_effect=enforcement_actions)
@patch.object(AwsVpcClient, "list_vpcs", return_value=vpcs)
class TestAwsAuditVPCDNSLogsTask(TestCase):
    def test_run_plan_task(self, _: Mock, __: Mock) -> None:
        action_reports = [
            compliance_action_report(description="Delete VPC flow log", details=dict(flow_log_id="fl-4")),
            compliance_action_report(
                description="Create VPC flow log",
                details=dict(vpc_id="vpc-7", log_group_name="/vpc/flow_log"),
            ),
        ]
        report = self.expected_report(action_reports)
        self.assertEqual(
            report, aws_audit_vpc_dns_logs_task(enforce=False, with_subscription_filter=True).run(vpc_client)
        )

    @staticmethod
    def expected_report(action_reports: Sequence[ComplianceActionReport]) -> AwsTaskReport:
        results = {"vpcs": vpcs, "enforcement_actions": action_reports}
        report = task_report(description="audit VPC dns logs compliance", partition=None, results=results)
        return report

    def test_run_apply_task(self, _: Mock, __: Mock) -> None:
        reports = [
            compliance_action_report(
                status="applied", description="Delete VPC flow log", details=dict(flow_log_id="fl-4")
            ),
            compliance_action_report(
                status="applied",
                description="Create VPC flow log",
                details=dict(vpc_id="vpc-7", log_group_name="/vpc/flow_log"),
            ),
        ]
        self.assertEqual(
            self.expected_report(reports),
            aws_audit_vpc_dns_logs_task(enforce=True, with_subscription_filter=True).run(vpc_client),
        )
