"""
Unit tests for GCP Provider Authentication Module
"""

from unittest.mock import Mock, patch

import pytest

from app.models.auth import AuthMethod
from providers.gcp.auth import GCPAuth


class TestGCPAuth:
    """Test cases for GCPAuth class."""

    def setup_method(self):
        self.valid_service_account = {
            "type": "service_account",
            "project_id": "test-project-123",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
            "client_email": "test-service@test-project-123.iam.gserviceaccount.com",
            "client_id": "123456789012345678901",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs/test-service%40test-project-123.iam.gserviceaccount.com",
        }

        self.valid_auth_config = {
            "method": AuthMethod.SERVICE_ACCOUNT,
            "credentials": self.valid_service_account,
        }

    def test_init_with_valid_config(self):
        """Test GCPAuth initialization with valid configuration."""
        auth = GCPAuth(self.valid_auth_config)

        assert auth.auth_config == self.valid_auth_config
        assert auth.method == AuthMethod.SERVICE_ACCOUNT
        assert auth._credentials is None
        assert auth._project_id is None

    def test_init_with_default_method(self):
        """Test GCPAuth initialization with default method when not specified."""
        auth_config = {"credentials": self.valid_service_account}
        auth = GCPAuth(auth_config)

        assert auth.method == AuthMethod.SERVICE_ACCOUNT

    def test_init_with_empty_config(self):
        """Test GCPAuth initialization with empty configuration."""
        auth = GCPAuth({})

        assert auth.auth_config == {}
        assert auth.method == AuthMethod.SERVICE_ACCOUNT
        assert auth._credentials is None
        assert auth._project_id is None

    @patch("providers.gcp.auth.service_account.Credentials.from_service_account_info")
    def test_get_credentials_success(self, mock_from_service_account_info):
        """Test successful credentials retrieval."""
        mock_credentials = Mock()
        mock_from_service_account_info.return_value = mock_credentials

        auth = GCPAuth(self.valid_auth_config)
        credentials = auth.get_credentials()

        assert credentials == mock_credentials
        assert auth._credentials == mock_credentials
        assert auth._project_id == "test-project-123"

        mock_from_service_account_info.assert_called_once_with(
            self.valid_service_account,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

    @patch("providers.gcp.auth.service_account.Credentials.from_service_account_info")
    def test_get_credentials_cached(self, mock_from_service_account_info):
        """Test that credentials are cached after first retrieval."""
        mock_credentials = Mock()
        mock_from_service_account_info.return_value = mock_credentials

        auth = GCPAuth(self.valid_auth_config)

        credentials1 = auth.get_credentials()
        credentials2 = auth.get_credentials()

        assert credentials1 == credentials2
        mock_from_service_account_info.assert_called_once()

    def test_get_credentials_no_credentials(self):
        """Test get_credentials raises ValueError when no credentials provided."""
        auth_config = {"method": AuthMethod.SERVICE_ACCOUNT}
        auth = GCPAuth(auth_config)

        with pytest.raises(
            ValueError, match="Service account credentials not provided"
        ):
            auth.get_credentials()

    def test_get_project_id_from_cached(self):
        """Test get_project_id returns cached project_id."""
        auth = GCPAuth(self.valid_auth_config)
        auth._project_id = "cached-project-123"

        project_id = auth.get_project_id()

        assert project_id == "cached-project-123"

    def test_get_project_id_from_credentials(self):
        """Test get_project_id extracts project_id from credentials."""
        auth = GCPAuth(self.valid_auth_config)

        project_id = auth.get_project_id()

        assert project_id == "test-project-123"

    def test_get_project_id_no_credentials(self):
        """Test get_project_id returns None when no credentials."""
        auth_config = {"method": AuthMethod.SERVICE_ACCOUNT}
        auth = GCPAuth(auth_config)

        project_id = auth.get_project_id()

        assert project_id is None

    @patch("providers.gcp.auth.bigquery.Client")
    @patch("providers.gcp.auth.service_account.Credentials.from_service_account_info")
    def test_create_bigquery_client_success(
        self, mock_from_service_account_info, mock_bigquery_client
    ):
        """Test successful BigQuery client creation."""
        mock_credentials = Mock()
        mock_from_service_account_info.return_value = mock_credentials
        mock_client = Mock()
        mock_bigquery_client.return_value = mock_client

        auth = GCPAuth(self.valid_auth_config)
        client = auth.create_bigquery_client("test-project", "EU")

        assert client == mock_client
        mock_bigquery_client.assert_called_once_with(
            credentials=mock_credentials, project="test-project", location="EU"
        )

    @patch("providers.gcp.auth.bigquery.Client")
    @patch("providers.gcp.auth.service_account.Credentials.from_service_account_info")
    def test_create_bigquery_client_default_location(
        self, mock_from_service_account_info, mock_bigquery_client
    ):
        """Test BigQuery client creation with default location."""
        mock_credentials = Mock()
        mock_from_service_account_info.return_value = mock_credentials
        mock_client = Mock()
        mock_bigquery_client.return_value = mock_client

        auth = GCPAuth(self.valid_auth_config)
        client = auth.create_bigquery_client("test-project")

        assert client == mock_client
        mock_bigquery_client.assert_called_once_with(
            credentials=mock_credentials, project="test-project", location="US"
        )

    def test_validate_success(self):
        """Test successful validation with valid configuration."""
        auth = GCPAuth(self.valid_auth_config)

        auth.validate()

    def test_validate_no_auth_config(self):
        """Test validation fails with no authentication configuration."""
        auth = GCPAuth({})

        with pytest.raises(
            ValueError, match="Authentication configuration is required"
        ):
            auth.validate()

    def test_validate_unsupported_method(self):
        """Test validation fails with unsupported authentication method."""
        auth_config = {
            "method": "invalid_method",
            "credentials": self.valid_service_account,
        }
        auth = GCPAuth(auth_config)

        with pytest.raises(
            ValueError,
            match="GCP only supports AuthMethod.SERVICE_ACCOUNT authentication",
        ):
            auth.validate()

    def test_validate_no_credentials(self):
        """Test validation fails when no credentials provided."""
        auth_config = {"method": AuthMethod.SERVICE_ACCOUNT}
        auth = GCPAuth(auth_config)

        with pytest.raises(
            ValueError, match="Service account credentials are required"
        ):
            auth.validate()

    def test_validate_credentials_not_dict(self):
        """Test validation fails when credentials is not a dictionary."""
        auth_config = {
            "method": AuthMethod.SERVICE_ACCOUNT,
            "credentials": "not-a-dict",
        }
        auth = GCPAuth(auth_config)

        with pytest.raises(ValueError, match="Credentials must be a JSON object"):
            auth.validate()

    @pytest.mark.parametrize(
        "missing_field", ["type", "project_id", "private_key", "client_email"]
    )
    def test_validate_missing_required_fields(self, missing_field):
        """Test validation fails when required fields are missing."""
        credentials = self.valid_service_account.copy()
        del credentials[missing_field]

        auth_config = {"method": AuthMethod.SERVICE_ACCOUNT, "credentials": credentials}
        auth = GCPAuth(auth_config)

        with pytest.raises(
            ValueError,
            match=f"Missing required fields in service account: {missing_field}",
        ):
            auth.validate()

    def test_validate_invalid_type(self):
        """Test validation fails when credentials type is not service_account."""
        credentials = self.valid_service_account.copy()
        credentials["type"] = "user_account"

        auth_config = {"method": AuthMethod.SERVICE_ACCOUNT, "credentials": credentials}
        auth = GCPAuth(auth_config)

        with pytest.raises(
            ValueError, match="Credentials type must be 'service_account'"
        ):
            auth.validate()

    def test_validate_multiple_missing_fields(self):
        """Test validation error message includes all missing fields."""
        credentials = self.valid_service_account.copy()
        del credentials["project_id"]
        del credentials["private_key"]

        auth_config = {"method": AuthMethod.SERVICE_ACCOUNT, "credentials": credentials}
        auth = GCPAuth(auth_config)

        with pytest.raises(
            ValueError,
            match="Missing required fields in service account: project_id, private_key",
        ):
            auth.validate()

    def test_supported_methods_constant(self):
        """Test that SUPPORTED_METHODS contains expected methods."""
        assert GCPAuth.SUPPORTED_METHODS == [AuthMethod.SERVICE_ACCOUNT]

    def test_default_method_constant(self):
        """Test that DEFAULT_METHOD is SERVICE_ACCOUNT."""
        assert GCPAuth.DEFAULT_METHOD == AuthMethod.SERVICE_ACCOUNT

    def test_auth_fields_structure(self):
        """Test that AUTH_FIELDS has proper structure."""
        assert AuthMethod.SERVICE_ACCOUNT in GCPAuth.AUTH_FIELDS

        service_account_fields = GCPAuth.AUTH_FIELDS[AuthMethod.SERVICE_ACCOUNT]
        assert "credentials" in service_account_fields

        credentials_field = service_account_fields["credentials"]
        assert credentials_field["required"] is True
        assert credentials_field["type"] == "json_upload"
        assert "placeholder" in credentials_field
        assert "description" in credentials_field
