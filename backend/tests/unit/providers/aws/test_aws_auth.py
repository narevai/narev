"""
Unit tests for AWS Provider Authentication Module
"""

from unittest.mock import Mock, patch

import pytest

from app.models.auth import AuthMethod
from providers.aws.auth import AWSAuth


class TestAWSAuth:
    """Test cases for AWSAuth class."""

    def setup_method(self):
        self.valid_primary_config = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "session_token": "FwoGZXIvYXdzEJr...",
        }

        self.valid_secondary_config = {
            "role_arn": "arn:aws:iam::123456789012:role/CURAccessRole",
            "external_id": "unique-external-id",
        }

        self.valid_auth_config = {
            "method": AuthMethod.MULTI_FACTOR,
            "primary": self.valid_primary_config,
            "secondary": self.valid_secondary_config,
        }

    def test_init_with_valid_config(self):
        """Test AWSAuth initialization with valid configuration."""
        auth = AWSAuth(self.valid_auth_config, region="us-west-2")

        assert auth.auth_config == self.valid_auth_config
        assert auth.method == AuthMethod.MULTI_FACTOR
        assert auth.region == "us-west-2"

    def test_init_with_default_method(self):
        """Test AWSAuth initialization with default method when not specified."""
        auth_config = {"primary": self.valid_primary_config}
        auth = AWSAuth(auth_config)

        assert auth.method == AuthMethod.MULTI_FACTOR

    def test_init_with_default_region(self):
        """Test AWSAuth initialization with default region."""
        auth = AWSAuth(self.valid_auth_config)

        assert auth.region == "us-east-1"

    def test_init_with_custom_region(self):
        """Test AWSAuth initialization with custom region."""
        auth = AWSAuth(self.valid_auth_config, region="eu-west-1")

        assert auth.region == "eu-west-1"

    def test_get_credentials_success(self):
        """Test successful credentials retrieval."""
        auth = AWSAuth(self.valid_auth_config)
        credentials = auth.get_credentials()

        expected_credentials = {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEJr...",
        }

        assert credentials == expected_credentials

    def test_get_credentials_without_session_token(self):
        """Test credentials retrieval without session token."""
        primary_config = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}

        auth = AWSAuth(auth_config)
        credentials = auth.get_credentials()

        expected_credentials = {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }

        assert credentials == expected_credentials
        assert "aws_session_token" not in credentials

    def test_get_credentials_unsupported_method(self):
        """Test get_credentials raises ValueError with unsupported method."""
        auth_config = {"method": "invalid_method", "primary": self.valid_primary_config}
        auth = AWSAuth(auth_config)

        with pytest.raises(ValueError, match="Unsupported auth method: invalid_method"):
            auth.get_credentials()

    def test_get_role_config_with_role_arn(self):
        """Test role configuration retrieval with role ARN."""
        auth = AWSAuth(self.valid_auth_config)
        role_config = auth.get_role_config()

        expected_config = {
            "role_arn": "arn:aws:iam::123456789012:role/CURAccessRole",
            "external_id": "unique-external-id",
        }

        assert role_config == expected_config

    def test_get_role_config_without_external_id(self):
        """Test role configuration retrieval without external ID."""
        secondary_config = {"role_arn": "arn:aws:iam::123456789012:role/CURAccessRole"}
        auth_config = {
            "method": AuthMethod.MULTI_FACTOR,
            "primary": self.valid_primary_config,
            "secondary": secondary_config,
        }

        auth = AWSAuth(auth_config)
        role_config = auth.get_role_config()

        expected_config = {"role_arn": "arn:aws:iam::123456789012:role/CURAccessRole"}

        assert role_config == expected_config
        assert "external_id" not in role_config

    def test_get_role_config_without_role_arn(self):
        """Test role configuration returns None when no role ARN."""
        auth_config = {
            "method": AuthMethod.MULTI_FACTOR,
            "primary": self.valid_primary_config,
            "secondary": {},
        }

        auth = AWSAuth(auth_config)
        role_config = auth.get_role_config()

        assert role_config is None

    def test_get_role_config_no_secondary(self):
        """Test role configuration returns None when no secondary config."""
        auth_config = {
            "method": AuthMethod.MULTI_FACTOR,
            "primary": self.valid_primary_config,
        }

        auth = AWSAuth(auth_config)
        role_config = auth.get_role_config()

        assert role_config is None

    def test_get_role_config_unsupported_method(self):
        """Test get_role_config returns None with unsupported method."""
        auth_config = {
            "method": "invalid_method",
            "primary": self.valid_primary_config,
            "secondary": self.valid_secondary_config,
        }
        auth = AWSAuth(auth_config)

        role_config = auth.get_role_config()

        assert role_config is None

    @patch("providers.aws.auth.boto3.Session")
    def test_get_boto3_session_success(self, mock_session_class):
        """Test successful boto3 session creation."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        auth = AWSAuth(self.valid_auth_config, region="eu-west-1")
        session = auth.get_boto3_session()

        assert session == mock_session
        mock_session_class.assert_called_once_with(
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            aws_session_token="FwoGZXIvYXdzEJr...",
            region_name="eu-west-1",
        )

    @patch("providers.aws.auth.boto3.Session")
    def test_get_boto3_session_without_session_token(self, mock_session_class):
        """Test boto3 session creation without session token."""
        primary_config = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        auth = AWSAuth(auth_config)
        session = auth.get_boto3_session()

        assert session == mock_session
        mock_session_class.assert_called_once_with(
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region_name="us-east-1",
        )

    @patch("providers.aws.auth.boto3.Session")
    def test_get_boto3_session_filters_none_values(self, mock_session_class):
        """Test boto3 session creation filters None values."""
        primary_config = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "session_token": None,  # Explicitly None
        }
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}

        mock_session = Mock()
        mock_session_class.return_value = mock_session

        auth = AWSAuth(auth_config)
        auth.get_boto3_session()

        mock_session_class.assert_called_once_with(
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region_name="us-east-1",
        )

    def test_validate_success(self):
        """Test successful validation with valid configuration."""
        auth = AWSAuth(self.valid_auth_config)

        auth.validate()

    def test_validate_no_auth_config(self):
        """Test validation fails with no authentication configuration."""
        auth = AWSAuth({})

        with pytest.raises(
            ValueError, match="Authentication configuration is required"
        ):
            auth.validate()

    def test_validate_unsupported_method(self):
        """Test validation fails with unsupported authentication method."""
        auth_config = {"method": "invalid_method", "primary": self.valid_primary_config}
        auth = AWSAuth(auth_config)

        with pytest.raises(
            ValueError, match="AWS only supports AuthMethod.MULTI_FACTOR authentication"
        ):
            auth.validate()

    def test_validate_missing_access_key_id(self):
        """Test validation fails when access key ID is missing."""
        primary_config = {
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        }
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}
        auth = AWSAuth(auth_config)

        with pytest.raises(ValueError, match="AWS Access Key ID is required"):
            auth.validate()

    def test_validate_missing_secret_access_key(self):
        """Test validation fails when secret access key is missing."""
        primary_config = {"access_key_id": "AKIAIOSFODNN7EXAMPLE"}
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}
        auth = AWSAuth(auth_config)

        with pytest.raises(ValueError, match="AWS Secret Access Key is required"):
            auth.validate()

    def test_validate_empty_access_key_id(self):
        """Test validation fails when access key ID is empty."""
        primary_config = {
            "access_key_id": "",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}
        auth = AWSAuth(auth_config)

        with pytest.raises(ValueError, match="AWS Access Key ID is required"):
            auth.validate()

    def test_validate_empty_secret_access_key(self):
        """Test validation fails when secret access key is empty."""
        primary_config = {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "",
        }
        auth_config = {"method": AuthMethod.MULTI_FACTOR, "primary": primary_config}
        auth = AWSAuth(auth_config)

        with pytest.raises(ValueError, match="AWS Secret Access Key is required"):
            auth.validate()

    def test_validate_no_primary_config(self):
        """Test validation fails when primary config is missing."""
        auth_config = {"method": AuthMethod.MULTI_FACTOR}
        auth = AWSAuth(auth_config)

        with pytest.raises(ValueError, match="AWS Access Key ID is required"):
            auth.validate()

    def test_supported_methods_constant(self):
        """Test that SUPPORTED_METHODS contains expected methods."""
        assert AWSAuth.SUPPORTED_METHODS == [AuthMethod.MULTI_FACTOR]

    def test_default_method_constant(self):
        """Test that DEFAULT_METHOD is MULTI_FACTOR."""
        assert AWSAuth.DEFAULT_METHOD == AuthMethod.MULTI_FACTOR

    def test_auth_fields_structure(self):
        """Test that AUTH_FIELDS has proper structure."""
        assert AuthMethod.MULTI_FACTOR in AWSAuth.AUTH_FIELDS

        multi_factor_fields = AWSAuth.AUTH_FIELDS[AuthMethod.MULTI_FACTOR]
        assert "primary" in multi_factor_fields
        assert "secondary" in multi_factor_fields

        # Test primary fields structure
        primary_fields = multi_factor_fields["primary"]
        assert primary_fields["required"] is True
        assert primary_fields["type"] == "group"
        assert "fields" in primary_fields

        primary_auth_fields = primary_fields["fields"]
        assert "access_key_id" in primary_auth_fields
        assert "secret_access_key" in primary_auth_fields
        assert "session_token" in primary_auth_fields

        # Test access_key_id field
        access_key_field = primary_auth_fields["access_key_id"]
        assert access_key_field["required"] is True
        assert access_key_field["type"] == "string"

        # Test secret_access_key field
        secret_key_field = primary_auth_fields["secret_access_key"]
        assert secret_key_field["required"] is True
        assert secret_key_field["type"] == "password"

        # Test session_token field
        session_token_field = primary_auth_fields["session_token"]
        assert session_token_field["required"] is False
        assert session_token_field["type"] == "password"

        # Test secondary fields structure
        secondary_fields = multi_factor_fields["secondary"]
        assert secondary_fields["required"] is False
        assert secondary_fields["type"] == "group"
        assert "fields" in secondary_fields

        secondary_auth_fields = secondary_fields["fields"]
        assert "role_arn" in secondary_auth_fields
        assert "external_id" in secondary_auth_fields

        # Test role_arn field
        role_arn_field = secondary_auth_fields["role_arn"]
        assert role_arn_field["required"] is False
        assert role_arn_field["type"] == "string"

        # Test external_id field
        external_id_field = secondary_auth_fields["external_id"]
        assert external_id_field["required"] is False
        assert external_id_field["type"] == "string"
