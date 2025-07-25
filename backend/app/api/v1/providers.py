"""
NarevAI Billing Analyzer - Providers API v1
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.provider import (
    AuthFieldsResponse,
    HealthCheckResponse,
    MessageResponse,
    ProviderCreate,
    ProviderResponse,
    ProviderTestResult,
    ProviderTypesResponse,
    ProviderUpdate,
)
from app.services.provider_service import ProviderService

from .deps import get_provider_service

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/health")
def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for providers API.
    """
    return HealthCheckResponse(
        status="healthy", service="providers_api", version="1.0.0"
    )


@router.get("")
def list_providers(
    include_inactive: bool = Query(False, description="Include inactive providers"),
    provider_type: str | None = Query(None, description="Filter by provider type"),
    provider_service: ProviderService = Depends(get_provider_service),
) -> list[ProviderResponse]:
    """
    List all providers.

    - **include_inactive**: Include deactivated providers in results
    - **provider_type**: Filter by specific provider type (e.g., 'openai', 'aws')
    """
    try:
        providers = provider_service.get_all_providers(
            provider_type=provider_type, include_inactive=include_inactive
        )

        return [ProviderResponse.model_validate(provider) for provider in providers]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get("/{provider_id}")
def get_provider(
    provider_id: UUID, provider_service: ProviderService = Depends(get_provider_service)
) -> ProviderResponse:
    """
    Get a specific provider by ID.

    - **provider_id**: UUID of the provider to retrieve
    """
    try:
        provider = provider_service.get_provider(provider_id)

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
            )

        return ProviderResponse.model_validate(provider)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    provider_service: ProviderService = Depends(get_provider_service),
) -> ProviderResponse:
    """
    Create a new provider.

    - **name**: Unique name for the provider
    - **provider_type**: Type of provider (openai, aws, azure, etc.)
    - **display_name**: Human-readable name for UI
    - **auth_config**: Authentication configuration (required)
    - **api_endpoint**: Optional custom API endpoint
    - **additional_config**: Optional provider-specific configuration
    """
    try:
        # Extract fields from Pydantic model
        result = await provider_service.create_provider(
            name=provider_data.name,
            provider_type=provider_data.provider_type,
            display_name=provider_data.display_name,
            auth_config=provider_data.auth_config,
            api_endpoint=provider_data.api_endpoint,
            additional_config=provider_data.additional_config,
        )

        return ProviderResponse.model_validate(result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        import traceback

        traceback.print_exc()  # Log full traceback for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during provider creation: {str(e)}",
        ) from e


@router.put("/{provider_id}")
async def update_provider(
    provider_id: UUID,
    provider_data: ProviderUpdate,
    provider_service: ProviderService = Depends(get_provider_service),
) -> ProviderResponse:
    """
    Update an existing provider.

    - **provider_id**: UUID of the provider to update
    - **display_name**: Updated display name
    - **auth_config**: Updated authentication configuration
    - **api_endpoint**: Updated API endpoint
    - **additional_config**: Updated provider-specific configuration
    - **is_active**: Enable/disable the provider
    """
    try:
        # Convert Pydantic model to dict, excluding unset fields
        update_dict = provider_data.model_dump(exclude_unset=True)

        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided",
            )

        result = await provider_service.update_provider(
            provider_id=provider_id,
            display_name=update_dict.get("display_name"),
            auth_config=update_dict.get("auth_config"),
            api_endpoint=update_dict.get("api_endpoint"),
            additional_config=update_dict.get("additional_config"),
            is_active=update_dict.get("is_active"),
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
            )

        return ProviderResponse.model_validate(result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during provider update: {str(e)}",
        ) from e


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: UUID, provider_service: ProviderService = Depends(get_provider_service)
) -> MessageResponse:
    """
    Delete (deactivate) a provider.

    Note: This performs a soft delete - the provider is deactivated but data is preserved.

    - **provider_id**: UUID of the provider to delete
    """
    try:
        success = await provider_service.delete_provider(provider_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
            )

        return MessageResponse(message="Provider deactivated successfully")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/{provider_id}/test")
async def test_provider_connection(
    provider_id: UUID, provider_service: ProviderService = Depends(get_provider_service)
) -> ProviderTestResult:
    """
    Test connection to a provider's API.

    - **provider_id**: UUID of the provider to test
    """
    try:
        result = await provider_service.test_provider_connection(provider_id)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during connection test: {str(e)}",
        ) from e


@router.get("/types/info")
def get_provider_types_info(
    provider_service: ProviderService = Depends(get_provider_service),
) -> ProviderTypesResponse:
    """
    Get information about all supported provider types.

    Returns details about available provider types, their authentication methods,
    and configuration options.
    """
    try:
        types_info = provider_service.get_provider_types_info()
        return ProviderTypesResponse.model_validate(types_info)

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving provider types information: {str(e)}",
        ) from e


@router.get("/types/{provider_type}/auth-fields")
def get_auth_fields(
    provider_type: str,
    auth_method: str | None = Query(
        None, description="Specific auth method to get fields for"
    ),
    provider_service: ProviderService = Depends(get_provider_service),
) -> AuthFieldsResponse:
    """
    Get authentication field definitions for a provider type.

    Returns the fields required for each supported authentication method.

    - **provider_type**: Type of provider (openai, aws, etc.)
    - **auth_method**: Optional specific auth method to get fields for
    """
    try:
        return provider_service.get_auth_fields(provider_type, auth_method)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
