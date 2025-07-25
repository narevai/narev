"""
Unit tests for AWS Provider Implementation
"""

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from app.models.auth import AuthMethod
from providers.aws.provider import AWSProvider
from providers.aws.sources import AWSSource


class TestAWSProvider:
    """Test cases for AWSProvider class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.valid_auth_config = {
            "method": AuthMethod.MULTI_FACTOR,
            "primary": {
                "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "session_token": "FwoGZXIvYXdzEJr...",
            },
            "secondary": {
                "role_arn": "arn:aws:iam::123456789012:role/CURAccessRole",
                "external_id": "unique-external-id",
            },
        }

        self.valid_config = {
            "auth_config": self.valid_auth_config,
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        # Alternative config format (flat structure)
        self.alternative_config = {
            "auth_config": self.valid_auth_config,
            "bucket_name": "my-cur-bucket",
            "report_name": "my-cost-report",
            "region": "eu-west-1",
        }

    @patch("providers.aws.provider.AWSAuth")
    @patch("providers.aws.provider.boto3.Session")
    def test_init_with_valid_config(self, mock_session_class, mock_auth_class):
        """Test AWSProvider initialization with valid configuration."""
        # Setup mocks
        mock_auth = Mock()
        mock_initial_session = Mock()
        mock_sts_client = Mock()
        mock_s3_client = Mock()
        mock_assumed_session = Mock()
        mock_assumed_s3_client = Mock()

        # Setup assume role response
        assume_role_response = {
            "Credentials": {
                "AccessKeyId": "ASSUMED_ACCESS_KEY",
                "SecretAccessKey": "ASSUMED_SECRET_KEY",
                "SessionToken": "ASSUMED_SESSION_TOKEN",
            }
        }

        mock_auth.get_boto3_session.return_value = mock_initial_session
        mock_initial_session.client.side_effect = lambda service, **kwargs: {
            "s3": mock_s3_client,
            "sts": mock_sts_client,
        }[service]

        mock_sts_client.assume_role.return_value = assume_role_response
        mock_session_class.return_value = mock_assumed_session
        mock_assumed_session.client.return_value = mock_assumed_s3_client
        mock_auth_class.return_value = mock_auth

        provider = AWSProvider(self.valid_config)

        assert provider.bucket_name == "my-cur-bucket"
        assert provider.report_name == "my-cost-report"
        assert provider.report_prefix == "cur/"
        assert provider.region == "us-west-2"
        assert provider.role_arn == "arn:aws:iam::123456789012:role/CURAccessRole"
        assert provider.external_id == "unique-external-id"
        assert provider.source_class == AWSSource
        assert (
            provider.session == mock_assumed_session
        )  # Should have assumed role session
        assert provider.s3_client == mock_assumed_s3_client

        mock_auth_class.assert_called_once_with(
            self.valid_auth_config, region="us-west-2"
        )
        mock_sts_client.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/CURAccessRole",
            RoleSessionName="billing-analyzer-session",
            ExternalId="unique-external-id",
        )

    @patch("providers.aws.provider.AWSAuth")
    @patch("providers.aws.provider.boto3.Session")
    def test_init_with_alternative_config_format(
        self, mock_session_class, mock_auth_class
    ):
        """Test AWSProvider initialization with alternative config format."""
        mock_auth = Mock()
        mock_initial_session = Mock()
        mock_sts_client = Mock()
        mock_s3_client = Mock()
        mock_assumed_session = Mock()
        mock_assumed_s3_client = Mock()

        # Setup assume role response
        assume_role_response = {
            "Credentials": {
                "AccessKeyId": "ASSUMED_ACCESS_KEY",
                "SecretAccessKey": "ASSUMED_SECRET_KEY",
                "SessionToken": "ASSUMED_SESSION_TOKEN",
            }
        }

        mock_auth.get_boto3_session.return_value = mock_initial_session
        mock_initial_session.client.side_effect = lambda service, **kwargs: {
            "s3": mock_s3_client,
            "sts": mock_sts_client,
        }[service]

        mock_sts_client.assume_role.return_value = assume_role_response
        mock_session_class.return_value = mock_assumed_session
        mock_assumed_session.client.return_value = mock_assumed_s3_client
        mock_auth_class.return_value = mock_auth

        provider = AWSProvider(self.alternative_config)

        assert provider.bucket_name == "my-cur-bucket"
        assert provider.report_name == "my-cost-report"
        assert provider.region == "eu-west-1"
        assert provider.session == mock_assumed_session
        assert provider.s3_client == mock_assumed_s3_client

    @patch("providers.aws.provider.AWSAuth")
    @patch("providers.aws.provider.boto3.Session")
    def test_init_with_defaults(self, mock_session_class, mock_auth_class):
        """Test AWSProvider initialization with default values."""
        # Config without role to avoid role assumption
        simple_auth_config = {
            "method": AuthMethod.MULTI_FACTOR,
            "primary": {
                "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            },
            # No secondary config with roles
        }
        config = {
            "auth_config": simple_auth_config,
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
            },
        }

        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        provider = AWSProvider(config)

        assert provider.report_prefix == ""  # Default empty string
        assert provider.region == "us-east-1"  # Default region
        assert provider.role_arn is None  # No role config
        assert provider.external_id is None  # No external ID

    @patch("providers.aws.provider.AWSAuth")
    def test_init_client_error(self, mock_auth_class):
        """Test AWSProvider initialization handles client errors."""
        mock_auth = Mock()
        mock_auth.get_boto3_session.side_effect = Exception("AWS connection failed")
        mock_auth_class.return_value = mock_auth

        with pytest.raises(Exception, match="AWS connection failed"):
            AWSProvider(self.valid_config)

    def test_get_config_value_from_root(self):
        """Test _get_config_value retrieves from root config."""
        config = {"bucket_name": "root-bucket"}

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider({"auth_config": self.valid_auth_config, **config})
            value = provider._get_config_value("bucket_name")

            assert value == "root-bucket"

    def test_get_config_value_from_additional_config(self):
        """Test _get_config_value retrieves from additional_config."""
        config = {"additional_config": {"bucket_name": "additional-bucket"}}

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider({"auth_config": self.valid_auth_config, **config})
            value = provider._get_config_value("bucket_name")

            assert value == "additional-bucket"

    def test_get_config_value_with_default(self):
        """Test _get_config_value returns default when key not found."""
        config = {}

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider({"auth_config": self.valid_auth_config, **config})
            value = provider._get_config_value("nonexistent", "default-value")

            assert value == "default-value"

    def test_get_role_arn_from_auth_config_secondary(self):
        """Test _get_role_arn retrieves from auth_config secondary."""
        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider(self.valid_config)

            assert (
                provider._get_role_arn()
                == "arn:aws:iam::123456789012:role/CURAccessRole"
            )

    def test_get_role_arn_from_additional_config(self):
        """Test _get_role_arn falls back to additional_config."""
        config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {"access_key_id": "test", "secret_access_key": "test"},
            },
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
                "role_arn": "arn:aws:iam::999:role/TestRole",
            },
        }

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider(config)

            assert provider._get_role_arn() == "arn:aws:iam::999:role/TestRole"

    def test_get_role_arn_not_found(self):
        """Test _get_role_arn returns None when not found."""
        config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {"access_key_id": "test", "secret_access_key": "test"},
            },
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
            },
        }

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider(config)

            assert provider._get_role_arn() is None

    def test_get_external_id_from_auth_config_secondary(self):
        """Test _get_external_id retrieves from auth_config secondary."""
        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider(self.valid_config)

            assert provider._get_external_id() == "unique-external-id"

    def test_get_external_id_from_additional_config(self):
        """Test _get_external_id falls back to additional_config."""
        config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {"access_key_id": "test", "secret_access_key": "test"},
            },
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
                "external_id": "fallback-external-id",
            },
        }

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider(config)

            assert provider._get_external_id() == "fallback-external-id"

    def test_get_external_id_not_found(self):
        """Test _get_external_id returns None when not found."""
        config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {"access_key_id": "test", "secret_access_key": "test"},
            },
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
            },
        }

        with (
            patch("providers.aws.provider.AWSAuth"),
            patch("providers.aws.provider.boto3.Session"),
        ):
            provider = AWSProvider(config)

            assert provider._get_external_id() is None

    @patch("providers.aws.provider.AWSAuth")
    @patch("providers.aws.provider.boto3.Session")
    def test_init_aws_clients_without_role(self, mock_session_class, mock_auth_class):
        """Test AWS clients initialization without role assumption."""
        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {"access_key_id": "test", "secret_access_key": "test"},
            },
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
            },
        }

        provider = AWSProvider(config)

        assert provider.session == mock_session
        assert provider.s3_client == mock_s3_client
        mock_session.client.assert_called_once_with("s3", region_name="us-east-1")

    @patch("providers.aws.provider.AWSAuth")
    @patch("providers.aws.provider.boto3.Session")
    def test_init_aws_clients_with_role_assumption(
        self, mock_session_class, mock_auth_class
    ):
        """Test AWS clients initialization with role assumption."""
        mock_auth = Mock()
        mock_initial_session = Mock()
        mock_sts_client = Mock()
        mock_assumed_session = Mock()
        mock_s3_client = Mock()

        # Setup assume role response
        assume_role_response = {
            "Credentials": {
                "AccessKeyId": "ASSUMED_ACCESS_KEY",
                "SecretAccessKey": "ASSUMED_SECRET_KEY",
                "SessionToken": "ASSUMED_SESSION_TOKEN",
            }
        }

        mock_auth.get_boto3_session.return_value = mock_initial_session
        mock_initial_session.client.side_effect = lambda service, **kwargs: {
            "s3": Mock(),
            "sts": mock_sts_client,
        }[service]

        mock_sts_client.assume_role.return_value = assume_role_response
        mock_session_class.return_value = mock_assumed_session
        mock_assumed_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        provider = AWSProvider(self.valid_config)

        # Verify role assumption was called
        mock_sts_client.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/CURAccessRole",
            RoleSessionName="billing-analyzer-session",
            ExternalId="unique-external-id",
        )

        # Verify new session was created with assumed credentials
        mock_session_class.assert_called_once_with(
            aws_access_key_id="ASSUMED_ACCESS_KEY",
            aws_secret_access_key="ASSUMED_SECRET_KEY",
            aws_session_token="ASSUMED_SESSION_TOKEN",
            region_name="us-west-2",
        )

        assert provider.session == mock_assumed_session
        assert provider.s3_client == mock_s3_client

    @patch("providers.aws.provider.AWSAuth")
    @patch("providers.aws.provider.boto3.Session")
    def test_init_aws_clients_role_assumption_without_external_id(
        self, mock_session_class, mock_auth_class
    ):
        """Test AWS clients initialization with role assumption but no external ID."""
        config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {"access_key_id": "test", "secret_access_key": "test"},
                "secondary": {"role_arn": "arn:aws:iam::123456789012:role/TestRole"},
            },
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
            },
        }

        mock_auth = Mock()
        mock_initial_session = Mock()
        mock_sts_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_initial_session
        mock_initial_session.client.side_effect = lambda service, **kwargs: {
            "s3": Mock(),
            "sts": mock_sts_client,
        }[service]

        assume_role_response = {
            "Credentials": {
                "AccessKeyId": "ASSUMED_ACCESS_KEY",
                "SecretAccessKey": "ASSUMED_SECRET_KEY",
                "SessionToken": "ASSUMED_SESSION_TOKEN",
            }
        }
        mock_sts_client.assume_role.return_value = assume_role_response
        mock_auth_class.return_value = mock_auth

        AWSProvider(config)

        # Verify role assumption was called without ExternalId
        mock_sts_client.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            RoleSessionName="billing-analyzer-session",
        )

    @patch("providers.aws.provider.AWSAuth")
    def test_get_sources(self, mock_auth_class):
        """Test sources retrieval."""
        # Setup provider
        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)

        start_date = datetime(2024, 1, 1, tzinfo=UTC)
        end_date = datetime(2024, 1, 31, tzinfo=UTC)

        sources = provider.get_sources(start_date, end_date)

        # Should return sources from AWSSource class
        assert len(sources) > 0
        assert isinstance(sources, list)
        assert "name" in sources[0]
        assert "source_type" in sources[0]
        assert "config" in sources[0]

    @patch("providers.aws.provider.AWSAuth")
    def test_test_connection_success(self, mock_auth_class):
        """Test successful connection test."""
        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        # Setup successful S3 operations
        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_s3_client.head_bucket.return_value = {}
        mock_s3_client.list_objects_v2.return_value = {
            "KeyCount": 2,
            "Contents": [
                {
                    "Key": "cur/my-cost-report/year=2024/month=01/file1.csv.gz",
                    "Size": 1024,
                },
                {
                    "Key": "cur/my-cost-report/year=2024/month=01/file2.csv.gz",
                    "Size": 2048,
                },
            ],
        }
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)
            result = provider.test_connection()

        assert result["success"] is True
        # Check that message contains the key information (format changed to include export type)
        assert "Successfully connected to AWS S3" in result["message"]
        assert result["details"]["bucket"] == "my-cur-bucket"
        assert result["details"]["report_name"] == "my-cost-report"
        assert result["details"]["region"] == "us-west-2"
        assert result["details"]["objects_found"] == 2
        assert result["details"]["role_assumed"] is False  # No role in simple config
        assert result["details"]["export_type"] == "focus"  # Default export type
        assert (
            "file_types_found" in result["details"]
        )  # New field for file type detection

    @patch("providers.aws.provider.AWSAuth")
    def test_test_connection_bucket_not_found(self, mock_auth_class):
        """Test connection test with bucket not found."""
        from botocore.exceptions import ClientError

        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client

        # Simulate bucket not found
        error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        mock_s3_client.head_bucket.side_effect = ClientError(
            error_response, "HeadBucket"
        )
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)
            result = provider.test_connection()

        assert result["success"] is False
        assert "AWS connection failed: 404" in result["message"]
        assert result["details"]["error_code"] == "404"
        assert result["details"]["bucket"] == "my-cur-bucket"

    @patch("providers.aws.provider.AWSAuth")
    def test_test_connection_permission_denied(self, mock_auth_class):
        """Test connection test with permission denied."""
        from botocore.exceptions import ClientError

        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client

        # Simulate permission denied
        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        mock_s3_client.head_bucket.side_effect = ClientError(
            error_response, "HeadBucket"
        )
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)
            result = provider.test_connection()

        assert result["success"] is False
        assert "AWS connection failed: 403" in result["message"]
        assert result["details"]["error_code"] == "403"
        assert result["details"]["bucket"] == "my-cur-bucket"

    @patch("providers.aws.provider.AWSAuth")
    def test_test_connection_generic_error(self, mock_auth_class):
        """Test connection test with generic error."""
        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_s3_client.head_bucket.side_effect = Exception("Network error")
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)
            result = provider.test_connection()

        assert result["success"] is False
        assert "Connection test failed: Network error" in result["message"]

    @patch("providers.aws.provider.AWSAuth")
    def test_get_filesystem_config(self, mock_auth_class):
        """Test filesystem configuration retrieval."""
        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)
            fs_config = provider.get_filesystem_config()

        assert "bucket_url" in fs_config
        assert "s3://my-cur-bucket/cur/my-cost-report" in fs_config["bucket_url"]
        assert "aws_access_key_id" in fs_config
        assert "aws_secret_access_key" in fs_config
        # No role_arn expected in simple config without roles
        assert "role_arn" not in fs_config

    @patch("providers.aws.provider.AWSAuth")
    def test_get_auth_method(self, mock_auth_class):
        """Test getting authentication method."""
        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        # Use config without role to avoid role assumption in test_connection tests
        simple_config = {
            "auth_config": {
                "method": AuthMethod.MULTI_FACTOR,
                "primary": {
                    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                },
            },
            "additional_config": {
                "bucket_name": "my-cur-bucket",
                "report_name": "my-cost-report",
                "report_prefix": "cur/",
                "region": "us-west-2",
            },
        }

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(simple_config)
            auth_method = provider.get_auth_method()

        assert auth_method == AuthMethod.MULTI_FACTOR

    @patch("providers.aws.provider.AWSAuth")
    def test_get_auth_method_no_config(self, mock_auth_class):
        """Test getting authentication method when no auth config."""
        config = {
            "additional_config": {
                "bucket_name": "test-bucket",
                "report_name": "test-report",
            }
        }

        mock_auth = Mock()
        mock_session = Mock()
        mock_s3_client = Mock()

        mock_auth.get_boto3_session.return_value = mock_session
        mock_session.client.return_value = mock_s3_client
        mock_auth_class.return_value = mock_auth

        with patch("providers.aws.provider.boto3.Session"):
            provider = AWSProvider(config)
            auth_method = provider.get_auth_method()

        assert auth_method == "default"
