from unittest import TestCase
from typing import Any, Dict, Optional, Callable
from unittest.mock import Mock, patch

from botocore.exceptions import NoCredentialsError

from src.clients.aws_client_factory import AwsClientFactory, AwsCredentials
from src.clients.aws_iam_audit_client import AwsIamAuditClient
from src.data import SERVICE_ACCOUNT_TOKEN, SERVICE_ACCOUNT_USER
from src.data.aws_organizations_types import Account
from src.data.aws_scanner_exceptions import ClientFactoryException

from tests.test_types_generator import account


class TestGetBotoClients(TestCase):
    mfa, username = "123456", "joe.bloggs"

    def assert_get_client(
        self,
        method_under_test: str,
        service: str,
        target_account: Account,
        role: str,
        method_args: Optional[Dict[str, Any]] = None,
    ) -> None:
        mock_client = Mock()
        mock_get_client = Mock(return_value=mock_client)

        with patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token"):
            with patch("src.clients.aws_client_factory.AwsClientFactory._get_client", mock_get_client):
                factory = AwsClientFactory(self.mfa, self.username)
                client = (
                    getattr(factory, method_under_test)(**method_args)
                    if method_args
                    else getattr(factory, method_under_test)()
                )

            self.assertEqual(mock_client, client)

            if method_under_test == "get_logs_boto_client":
                mock_get_client.assert_called_once_with(service, target_account, role, "us-east-1")

            else:
                mock_get_client.assert_called_once_with(service, target_account, role)

    def test_get_athena_boto_client(self) -> None:
        self.assert_get_client(
            method_under_test="get_athena_boto_client",
            service="athena",
            target_account=account(identifier="555666777888", name="athena"),
            role="athena_role",
        )

    def test_get_cost_explorer_boto_client(self) -> None:
        cost_explorer_account = account(identifier="999888777666", name="some_account")
        self.assert_get_client(
            method_under_test="get_cost_explorer_boto_client",
            method_args={"account": cost_explorer_account},
            service="ce",
            target_account=cost_explorer_account,
            role="cost_explorer_role",
        )

    def test_get_ec2_boto_client(self) -> None:
        ec2_account = account(identifier="999888777666", name="some_ec2_account")
        self.assert_get_client(
            method_under_test="get_ec2_boto_client",
            method_args={"account": ec2_account, "role": "ec2_role"},
            service="ec2",
            target_account=ec2_account,
            role="ec2_role",
        )

    def test_get_route53_boto_client(self) -> None:
        route53_account = account(identifier="999888777666", name="some_route53_account")
        self.assert_get_client(
            method_under_test="get_route53_boto_client",
            method_args={"account": route53_account, "role": "route53_role"},
            service="route53",
            target_account=route53_account,
            role="route53_role",
        )

    def test_get_s3_boto_client(self) -> None:
        s3_account = account(identifier="122344566788", name="some_s3_account")
        self.assert_get_client(
            method_under_test="get_s3_boto_client",
            method_args={"account": s3_account, "role": "s3_role"},
            service="s3",
            target_account=s3_account,
            role="s3_role",
        )

    def test_get_organizations_boto_client(self) -> None:
        self.assert_get_client(
            method_under_test="get_organizations_boto_client",
            service="organizations",
            target_account=account(identifier="999888777666", name="organization"),
            role="orgs_role",
        )

    def test_get_ssm_boto_client(self) -> None:
        ssm_account = account(identifier="122344566788", name="some_ssm_account")
        self.assert_get_client(
            method_under_test="get_ssm_boto_client",
            method_args={"account": ssm_account},
            service="ssm",
            target_account=ssm_account,
            role="ssm_role",
        )

    def test_get_logs_boto_client(self) -> None:
        logs_account = account(identifier="654654654654", name="some_logs_account")
        self.assert_get_client(
            method_under_test="get_logs_boto_client",
            method_args={"account": logs_account, "region": "us-east-1"},
            service="logs",
            target_account=logs_account,
            role="logs_role",
        )

    def test_get_iam_boto_client(self) -> None:
        iam_account = account(identifier="977644311255", name="some_iam_account")
        self.assert_get_client(
            method_under_test="get_iam_boto_client",
            method_args={"account": iam_account, "role": "iam_role"},
            service="iam",
            target_account=iam_account,
            role="iam_role",
        )

    def test_get_kms_boto_client(self) -> None:
        kms_account = account(identifier="887331665442", name="some_kms_account")
        self.assert_get_client(
            method_under_test="get_kms_boto_client",
            method_args={"account": kms_account},
            service="kms",
            target_account=kms_account,
            role="kms_role",
        )

    def test_get_route53_resolver_boto_client(self) -> None:
        kms_account = account(identifier="887331665442", name="some_kms_account")
        self.assert_get_client(
            method_under_test="get_route53_resolver_boto_client",
            method_args={"account": kms_account},
            service="route53resolver",
            target_account=kms_account,
            role="route53resolver_role",
        )

    def test_get_cloudtrail_boto_client(self) -> None:
        cloudtrail_account = account(identifier="644355211788", name="some_cloudtrail_account")
        self.assert_get_client(
            method_under_test="get_cloudtrail_boto_client",
            method_args={"account": cloudtrail_account},
            service="cloudtrail",
            target_account=cloudtrail_account,
            role="cloudtrail_role",
        )


@patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token")
class TestGetClients(TestCase):
    factory_path = "src.clients.aws_client_factory.AwsClientFactory"
    mfa, username = "123456", "joe.bloggs"

    def test_get_athena_client(self, _: Mock) -> None:
        with patch(f"{self.factory_path}.get_athena_boto_client") as boto_client:
            athena_client = AwsClientFactory(self.mfa, self.username).get_athena_client()
            self.assertEqual(athena_client._athena_async._boto_athena, boto_client.return_value)

    def test_get_cost_explorer_client(self, _: Mock) -> None:
        cost_explorer_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_cost_explorer_boto_client",
            side_effect=lambda acc: cost_explorer_boto_client if acc == account() else None,
        ):
            cost_explorer_client = AwsClientFactory(self.mfa, self.username).get_cost_explorer_client(account())
            self.assertEqual(cost_explorer_client._cost_explorer, cost_explorer_boto_client)

    def test_get_ec2_client(self, _: Mock) -> None:
        ec2_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_ec2_boto_client",
            side_effect=lambda acc, role: ec2_boto_client if acc == account() and role == "ec2_role" else None,
        ):
            ec2_client = AwsClientFactory(self.mfa, self.username).get_ec2_client(account())
            self.assertEqual(ec2_client._ec2, ec2_boto_client)

    def test_get_hostedZones_client(self, _: Mock) -> None:
        route53_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_route53_boto_client",
            side_effect=lambda acc, role: route53_boto_client if acc == account() and role == "route53_role" else None,
        ):
            hosted_zones_client = AwsClientFactory(self.mfa, self.username).get_hosted_zones_client(
                account(), "route53_role"
            )
            self.assertEqual(hosted_zones_client._route53, route53_boto_client)

    def test_get_organizations_client(self, _: Mock) -> None:
        with patch(f"{self.factory_path}.get_organizations_boto_client") as boto_client:
            orgs_client = AwsClientFactory(self.mfa, self.username).get_organizations_client()
            self.assertEqual(orgs_client._orgs, boto_client.return_value)

    def test_get_ssm_client(self, _: Mock) -> None:
        ssm_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_ssm_boto_client",
            side_effect=lambda acc: ssm_boto_client if acc == account() else None,
        ):
            ssm_client = AwsClientFactory(self.mfa, self.username).get_ssm_client(account())
            self.assertEqual(ssm_client._ssm, ssm_boto_client)

    def test_get_s3_client(self, _: Mock) -> None:
        s3_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_s3_boto_client",
            side_effect=lambda acc, role: s3_boto_client if acc == account() and role == "s3_role" else None,
        ):
            s3_client = AwsClientFactory(self.mfa, self.username).get_s3_client(account())
            self.assertEqual(s3_client._s3, s3_boto_client)

    def test_get_custom_s3_client(self, _: Mock) -> None:
        s3_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_s3_boto_client",
            side_effect=lambda acc, role: s3_boto_client if acc == account("id") and role == "role" else None,
        ):
            s3_client = AwsClientFactory(self.mfa, self.username).get_s3_client(account("id"), "role")
            self.assertEqual(s3_client._s3, s3_boto_client)

    def test_get_logs_client(self, _: Mock) -> None:
        logs_boto_client = Mock()
        kms_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_logs_boto_client",
            side_effect=lambda acc, region: logs_boto_client if acc == account() else None,
        ):
            with patch(
                f"{self.factory_path}.get_kms_boto_client",
                side_effect=lambda acc: kms_boto_client if acc == account() else None,
            ):
                logs_client = AwsClientFactory(self.mfa, self.username).get_logs_client(account(), None)
                self.assertEqual(logs_client._logs, logs_boto_client)
                self.assertEqual(logs_client.kms, kms_boto_client)

    def test_get_log_group_client(self, _: Mock) -> None:
        logs_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_logs_client",
            side_effect=lambda acc, region: logs_boto_client if acc == account() else None,
        ):
            log_group_client = AwsClientFactory(self.mfa, self.username).get_log_group_client(account(), None)
            self.assertEqual(log_group_client.logs, logs_boto_client)

    def test_get_iam_client(self, _: Mock) -> None:
        iam_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_iam_boto_client",
            side_effect=lambda acc, role: iam_boto_client if acc == account() and role == "iam_role" else None,
        ):
            iam_client = AwsClientFactory(self.mfa, self.username).get_iam_client(account())
            self.assertEqual(iam_client._iam, iam_boto_client)

    def test_get_iam_client_for_audit(self, _: Mock) -> None:
        iam_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_iam_boto_client",
            side_effect=lambda acc, role: iam_boto_client if acc == account() and role == "iam_audit_role" else None,
        ):
            iam_client = AwsClientFactory(self.mfa, self.username).get_iam_client_for_audit(account())
            self.assertEqual(iam_client._iam, iam_boto_client)
            self.assertEqual(type(iam_client), AwsIamAuditClient)

    def test_get_kms_client(self, _: Mock) -> None:
        kms_boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_kms_boto_client",
            side_effect=lambda acc: kms_boto_client if acc == account() else None,
        ):
            kms_client = AwsClientFactory(self.mfa, self.username).get_kms_client(account())
            self.assertEqual(kms_client._kms, kms_boto_client)

    def test_getroute53_resolver_client(self, _: Mock) -> None:
        route53_resolver__boto_client = Mock()
        with patch(
            f"{self.factory_path}.get_route53_resolver_boto_client",
            side_effect=lambda acc: route53_resolver__boto_client if acc == account() else None,
        ):
            route53_resolver_client = AwsClientFactory(self.mfa, self.username).get_route53resolver_client(account())
            self.assertEqual(route53_resolver_client.resolver, route53_resolver__boto_client)

    def test_get_cloudtrail_client(self, _: Mock) -> None:
        cloudtrail_boto_client = Mock()
        logs_client = Mock()
        with patch(
            f"{self.factory_path}.get_cloudtrail_boto_client",
            side_effect=lambda acc: cloudtrail_boto_client if acc == account() else None,
        ):
            with patch(
                f"{self.factory_path}.get_logs_client",
                side_effect=lambda acc: logs_client if acc == account() else None,
            ):
                cloudtrail_client = AwsClientFactory(self.mfa, self.username).get_cloudtrail_client(account())

                self.assertEqual(cloudtrail_client._cloudtrail, cloudtrail_boto_client)
                self.assertEqual(cloudtrail_client._logs, logs_client)

    def test_get_central_logging_client(self, _: Mock) -> None:
        cloudtrail_acc = account("111344576685", "cloudtrail")
        s3_client = Mock()
        kms_client = Mock()
        org_client = Mock()
        with patch(
            f"{self.factory_path}.get_s3_client",
            side_effect=lambda acc: s3_client if acc == cloudtrail_acc else None,
        ):
            with patch(
                f"{self.factory_path}.get_kms_client",
                side_effect=lambda acc: kms_client if acc == cloudtrail_acc else None,
            ):
                with patch(f"{self.factory_path}.get_organizations_client", return_value=org_client):
                    central_logging_client = AwsClientFactory(self.mfa, self.username).get_central_logging_client()
                    self.assertEqual(central_logging_client._s3, s3_client)
                    self.assertEqual(central_logging_client._kms, kms_client)
                    self.assertEqual(central_logging_client._org, org_client)

    def test_get_s3_kms_client(self, _: Mock) -> None:
        s3_client = Mock()
        kms_client = Mock()
        with patch(
            f"{self.factory_path}.get_s3_client",
            side_effect=lambda acc, role: s3_client if acc == account() and role == "s3_role" else None,
        ):
            with patch(
                f"{self.factory_path}.get_kms_client",
                side_effect=lambda acc: kms_client if acc == account() else None,
            ):
                s3_kms_client = AwsClientFactory(self.mfa, self.username).get_s3_kms_client(account())
                self.assertEqual(s3_kms_client._s3, s3_client)
                self.assertEqual(s3_kms_client._kms, kms_client)


@patch.object(AwsClientFactory, "_get_session_token")
class TestGetCompositeClients(TestCase):
    @staticmethod
    def mock_client(client: Mock, expected_account: Account) -> Callable[[Account], Optional[Mock]]:
        return lambda acc: client if acc == expected_account else None

    @staticmethod
    def mock_client_region(
        client: Mock, expected_account: Account, expected_region: str
    ) -> Callable[[Account, str], Optional[Mock]]:
        return lambda account, region: client if account == expected_account and region == expected_region else None

    @staticmethod
    def mock_client_role(
        client: Mock, expected_account: Account, expected_role: str
    ) -> Callable[[Account, str], Optional[Mock]]:
        return lambda acc, role: client if acc == expected_account and role == expected_role else None

    def test_get_vpc_client(self, _: Mock) -> None:
        acc = account(identifier="1234", name="some_account")
        ec2, iam, logs, log_group, resolver = (
            Mock(name="ec2"),
            Mock(name="iam"),
            Mock(name="logs"),
            Mock(name="log_group"),
            Mock(name="resolver"),
        )
        with patch.object(AwsClientFactory, "get_ec2_client", side_effect=self.mock_client(ec2, acc)):
            with patch.object(AwsClientFactory, "get_logs_client", side_effect=self.mock_client(logs, acc)):
                with patch.object(AwsClientFactory, "get_iam_client", side_effect=self.mock_client(iam, acc)):
                    with patch.object(
                        AwsClientFactory, "get_log_group_client", side_effect=self.mock_client(log_group, acc)
                    ):
                        with patch.object(
                            AwsClientFactory, "get_route53resolver_client", side_effect=self.mock_client(resolver, acc)
                        ):
                            vpc_client = AwsClientFactory("123456", "joe.bloggs").get_vpc_client(acc)
        self.assertEqual(
            [ec2, iam, logs, log_group], [vpc_client.ec2, vpc_client.iam, vpc_client.logs, vpc_client.log_group]
        )

    def test_get_route53_client(self, _: Mock) -> None:
        acc = account(identifier="1234", name="some_account")
        boto_route53, iam, log_group = (
            Mock(name="boto_route53"),
            Mock(name="iam"),
            Mock(name="log_group"),
        )
        with patch.object(AwsClientFactory, "get_hosted_zones_client", side_effect=self.mock_client(boto_route53, acc)):
            with patch.object(
                AwsClientFactory,
                "get_log_group_client",
                side_effect=self.mock_client_region(
                    client=log_group, expected_account=acc, expected_region="us-east-1"
                ),
            ):
                with patch.object(AwsClientFactory, "get_iam_client", side_effect=self.mock_client(iam, acc)):
                    route53_client = AwsClientFactory("123456", "joe.bloggs").get_route53_client(acc)
        self.assertEqual(
            [boto_route53, iam, log_group],
            [route53_client._route53, route53_client._iam, route53_client.log_group],
        )

    def test_get_vpc_peering_client(self, _: Mock) -> None:
        acc = account(identifier="1234", name="some_account")
        ec2, org = Mock(name="ec2"), Mock(name="org")
        with patch.object(AwsClientFactory, "get_ec2_client", side_effect=self.mock_client_role(ec2, acc, "pcx_role")):
            with patch.object(AwsClientFactory, "get_organizations_client", return_value=org):
                client = AwsClientFactory("123456", "joe.bloggs").get_vpc_peering_client(acc)
        self.assertEqual([ec2, org], [client.ec2, client.org])


class TestAwsClientFactory(TestCase):
    mfa, username = "123456", "joe.bloggs"
    service_name, role = "some_service", "some_role"

    def test_get_session_token_user_account(self) -> None:
        boto_credentials = {
            "Credentials": {
                "AccessKeyId": "some_access_key",
                "SecretAccessKey": "some_secret_access_key",
                "SessionToken": "some_session_token",
            }
        }
        mock_sts_client = Mock(get_session_token=Mock(return_value=boto_credentials))
        mock_boto3 = Mock(client=Mock(return_value=mock_sts_client))

        with patch("src.clients.aws_client_factory.boto3", mock_boto3):
            client_factory = AwsClientFactory(self.mfa, self.username)
        self.assertEqual(
            client_factory._session_token,
            AwsCredentials("some_access_key", "some_secret_access_key", "some_session_token"),
        )
        mock_boto3.client.assert_called_once_with(service_name="sts")
        mock_sts_client.get_session_token.assert_called_once_with(
            DurationSeconds=3600, SerialNumber="arn:aws:iam::111222333444:mfa/joe.bloggs", TokenCode="123456"
        )

    def test_get_session_token_service_account(self) -> None:
        with patch("src.clients.aws_client_factory.boto3") as mock_boto3:
            self.assertIsNone(AwsClientFactory(SERVICE_ACCOUNT_TOKEN, SERVICE_ACCOUNT_USER)._session_token)
        mock_boto3.client.assert_not_called()

    def test_get_client(self) -> None:
        mock_client = Mock()
        mock_boto = Mock(client=Mock(return_value=mock_client))
        mock_assume_role = Mock(return_value=AwsCredentials("access", "secret", "session"))

        with patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token"):
            with patch("src.clients.aws_client_factory.AwsClientFactory._assume_role", mock_assume_role):
                with patch("src.clients.aws_client_factory.boto3", mock_boto):
                    client = AwsClientFactory(self.mfa, self.username)._get_client(
                        self.service_name, account(), self.role
                    )
        self.assertEqual(mock_client, client)
        mock_assume_role.assert_called_once_with(account(), self.role)
        mock_boto.client.assert_called_once_with(
            service_name="some_service",
            aws_access_key_id="access",
            aws_secret_access_key="secret",
            aws_session_token="session",
        )

    def test_get_client_with_region(self) -> None:
        mock_client = Mock()
        mock_boto = Mock(client=Mock(return_value=mock_client))
        mock_assume_role = Mock(return_value=AwsCredentials("access", "secret", "session"))

        with patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token"):
            with patch("src.clients.aws_client_factory.AwsClientFactory._assume_role", mock_assume_role):
                with patch("src.clients.aws_client_factory.boto3", mock_boto):
                    client = AwsClientFactory(self.mfa, self.username)._get_client(
                        self.service_name, account(), self.role, "us-east-1"
                    )
        self.assertEqual(mock_client, client)
        mock_assume_role.assert_called_once_with(account(), self.role)
        mock_boto.client.assert_called_once_with(
            service_name="some_service",
            aws_access_key_id="access",
            aws_secret_access_key="secret",
            aws_session_token="session",
            region_name="us-east-1",
        )

    def test_assume_role_user_account(self) -> None:
        assumed_role_creds = {
            "Credentials": {
                "AccessKeyId": "some_access_key",
                "SecretAccessKey": "some_secret_access_key",
                "SessionToken": "some_session_token",
            }
        }
        mock_sts_client = Mock(assume_role=Mock(return_value=assumed_role_creds))
        mock_boto = Mock(client=Mock(return_value=mock_sts_client))
        session_token = AwsCredentials("session_access_key", "session_secret_key", "session_token")

        with patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token", return_value=session_token):
            with patch("src.clients.aws_client_factory.boto3", mock_boto):
                creds = AwsClientFactory(self.mfa, self.username)._assume_role(account(), self.role)
        self.assertEqual(creds, AwsCredentials("some_access_key", "some_secret_access_key", "some_session_token"))
        mock_boto.client.assert_called_once_with(
            service_name="sts",
            aws_access_key_id="session_access_key",
            aws_secret_access_key="session_secret_key",
            aws_session_token="session_token",
        )
        mock_sts_client.assume_role.assert_called_once_with(
            DurationSeconds=3600,
            RoleArn="arn:aws:iam::account_id:role/some_role",
            RoleSessionName="boto3_assuming_some_role",
        )

    def test_assume_role_service_account(self) -> None:
        assumed_role_creds = {
            "Credentials": {
                "AccessKeyId": "some_access_key",
                "SecretAccessKey": "some_secret_access_key",
                "SessionToken": "some_session_token",
            }
        }
        mock_sts_client = Mock(assume_role=Mock(return_value=assumed_role_creds))
        mock_boto = Mock(client=Mock(return_value=mock_sts_client))

        with patch("src.clients.aws_client_factory.boto3", mock_boto):
            creds = AwsClientFactory(SERVICE_ACCOUNT_TOKEN, SERVICE_ACCOUNT_USER)._assume_role(account(), self.role)
        self.assertEqual(creds, AwsCredentials("some_access_key", "some_secret_access_key", "some_session_token"))
        mock_boto.client.assert_called_once_with(service_name="sts")
        mock_sts_client.assume_role.assert_called_once_with(
            DurationSeconds=3600,
            RoleArn="arn:aws:iam::account_id:role/some_role",
            RoleSessionName="boto3_assuming_some_role",
        )

    def test_to_credentials_failure(self) -> None:
        def trigger_error() -> None:
            raise NoCredentialsError

        with patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token"):
            with self.assertRaisesRegex(ClientFactoryException, NoCredentialsError.fmt):
                AwsClientFactory("123456", "bob")._to_credentials(trigger_error)
