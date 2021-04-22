from tests.aws_scanner_test_case import AwsScannerTestCase
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

from botocore.exceptions import NoCredentialsError

from src.clients.aws_client_factory import AwsClientFactory, AwsCredentials
from src.data.aws_organizations_types import Account
from src.data.aws_scanner_exceptions import ClientFactoryException

from tests.test_types_generator import account


class TestGetBotoClients(AwsScannerTestCase):
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
        mock_get_client.assert_called_once_with(service, target_account, role)

    def test_get_athena_boto_client(self) -> None:
        self.assert_get_client(
            method_under_test="get_athena_boto_client",
            service="athena",
            target_account=account(identifier="555666777888", name="cloudtrail"),
            role="cloudtrail_role",
        )

    def test_get_s3_boto_client(self) -> None:
        s3_account = account(identifier="122344566788", name="some_s3_account")
        self.assert_get_client(
            method_under_test="get_s3_boto_client",
            method_args={"account": s3_account},
            service="s3",
            target_account=s3_account,
            role="s3_role",
        )

    def test_get_organizations_boto_client(self) -> None:
        self.assert_get_client(
            method_under_test="get_organizations_boto_client",
            service="organizations",
            target_account=account(identifier="999888777666", name="root"),
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


@patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token")
class TestGetClients(AwsScannerTestCase):
    factory_path = "src.clients.aws_client_factory.AwsClientFactory"
    mfa, username = "123456", "joe.bloggs"

    def test_get_athena_client(self, _: Mock) -> None:
        with patch(f"{self.factory_path}.get_athena_boto_client") as boto_client:
            athena_client = AwsClientFactory(self.mfa, self.username).get_athena_client()
            self.assertEqual(athena_client._athena_async._boto_athena, boto_client.return_value)

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
            side_effect=lambda acc: s3_boto_client if acc == account() else None,
        ):
            s3_client = AwsClientFactory(self.mfa, self.username).get_s3_client(account())
            self.assertEqual(s3_client._s3, s3_boto_client)


class TestAwsClientFactory(AwsScannerTestCase):
    mfa, username = "123456", "joe.bloggs"
    service_name, role = "some_service", "some_role"

    def test_get_session_token(self) -> None:
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

    def test_assume_role(self) -> None:
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

    def test_to_credentials_failure(self) -> None:
        def trigger_error() -> None:
            raise NoCredentialsError

        with patch("src.clients.aws_client_factory.AwsClientFactory._get_session_token"):
            with self.assertRaisesRegex(ClientFactoryException, NoCredentialsError.fmt):
                AwsClientFactory("123456", "bob")._to_credentials(trigger_error)