from typing import Dict, Any, Optional
from app.config import settings
from app.connectors.base import CloudConnectorBase
from app.connectors.aws_connector import AWSConnector
from app.connectors.azure_connector import AzureConnector
from app.connectors.gcp_connector import GCPConnector
from app.connectors.mock_connector import MockMultiCloudConnector

def get_connector(
    provider: str,
    account_id: str,
    credentials_config: Optional[Dict[str, Any]] = None,
    force_mock: Optional[bool] = None
) -> CloudConnectorBase:
    """
    Connector Factory following the Adapter Pattern.
    Returns the appropriate cloud connector instance adhering to CloudConnectorBase.
    """
    is_mock = force_mock if force_mock is not None else settings.DEMO_MODE
    prov = provider.lower()

    if is_mock:
        return MockMultiCloudConnector(account_id=account_id, provider=prov, credentials_config=credentials_config)

    if prov == "aws":
        return AWSConnector(account_id=account_id, credentials_config=credentials_config)
    elif prov == "azure":
        return AzureConnector(account_id=account_id, credentials_config=credentials_config)
    elif prov == "gcp":
        return GCPConnector(account_id=account_id, credentials_config=credentials_config)
    else:
        # Default fallback to mock for custom or unregistered providers
        return MockMultiCloudConnector(account_id=account_id, provider=prov, credentials_config=credentials_config)

__all__ = [
    "CloudConnectorBase",
    "AWSConnector",
    "AzureConnector",
    "GCPConnector",
    "MockMultiCloudConnector",
    "get_connector"
]
