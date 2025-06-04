import requests
import os
import time
import re

import automationassets

from azure.identity import DefaultAzureCredential
from azure.monitor.ingestion import LogsIngestionClient
from azure.core.exceptions import HttpResponseError

# Load environment variables

# Token cache
cached_token = None
token_expiry = None

# The code below is for local testing purposes
# from dotenv import load_dotenv
# load_dotenv()

# Azure Monitor configuration
ADME_INSTANCE = automationassets.get_automation_variable("ADME_INSTANCE")
ADME_DATA_PARTITION = automationassets.get_automation_variable("ADME_DATA_PARTITION")
ADME_SCOPE = automationassets.get_automation_variable("ADME_SCOPE")
AZURE_CLIENT_ID = automationassets.get_automation_variable("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET_OBJECT = automationassets.get_automation_credential(
    "AZURE_CLIENT_SECRET"
)
AZURE_CLIENT_SECRET = AZURE_CLIENT_SECRET_OBJECT["password"]
AZURE_TENANT_ID = automationassets.get_automation_variable("AZURE_TENANT_ID")
DATA_COLLECTION_ENDPOINT = automationassets.get_automation_variable(
    "DATA_COLLECTION_ENDPOINT"
)
DCR_RULE_ID = automationassets.get_automation_variable("DCR_RULE_ID")
DCR_STREAM_NAME = automationassets.get_automation_variable("DCR_STREAM_NAME")
TOKEN_ENDPOINT = (
    f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
)

# Set environment variables (required for EnvironmentCredential)
os.environ["AZURE_CLIENT_ID"] = AZURE_CLIENT_ID
os.environ["AZURE_CLIENT_SECRET"] = AZURE_CLIENT_SECRET
os.environ["AZURE_TENANT_ID"] = AZURE_TENANT_ID

# The code below is for local testing purposes
# AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
# AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
# AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
# DATA_COLLECTION_ENDPOINT = os.getenv("DATA_COLLECTION_ENDPOINT")
# DCR_RULE_ID = os.getenv("DCR_RULE_ID")
# DCR_STREAM_NAME = os.getenv("DCR_STREAM_NAME")


# Instance and service configurations
ENDPOINTS = [
    {
        "name": "CRS Catalog Service",
        "healthEndpoint": f"https://{ADME_INSTANCE}.energy.azure.com/api/crs/catalog/_ah/liveness_check",
    },
    {
        "name": "CRS Converter Service",
        "healthEndpoint": f"https://{ADME_INSTANCE}.energy.azure.com/api/crs/converter/_ah/liveness_check",
    },
    {
        "name": "Dataset Service",
        "healthEndpoint": f"https://{ADME_INSTANCE}.energy.azure.com/api/dataset/v1/liveness_check",
    },
    {
        "name": "EDS Service",
        "healthEndpoint": f"https://{ADME_INSTANCE}.energy.azure.com/api/eds/v1/health/liveness_check",
    },
    {
        "name": "Entitlements Service",
        "healthEndpoint": f"https://{ADME_INSTANCE}.energy.azure.com/api/entitlements/v2/_ah/readiness_check",
    },
    {
        "name": "File Service",
        "healthEndpoint": f"https://{ADME_INSTANCE}.energy.azure.com/api/file/v2/liveness_check",
    },
    {
        "name": "Indexer Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/indexer/v2/liveness_check",
    },
    {
        "name": "Legal Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/legal/v1/_ah/liveness_check",
    },
    {
        "name": "Notification Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/notification/v1/_ah/warmup",
    },
    {
        "name": "Register Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/register/v1/ah/liveness_check",
    },
    {
        "name": "Schema Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/schema-service/v1/liveness_check",
    },
    {
        "name": "Search Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/search/v2/liveness_check",
    },
    {
        "name": "Seismic DMS",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/seistore-svc/api/v3/svcstatus",
    },
    {
        "name": "Storage Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/storage/v2/liveness_check",
    },
    {
        "name": "Unit Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/unit/_ah/liveness_check",
    },
    {
        "name": "Well Delivery DMS",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/well-delivery/_ah/warmup",
    },
    {
        "name": "Wellbore DMS",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/os-wellbore-ddms/about",
    },
    {
        "name": "Workflow Service",
        "healthEndpoint": "https://{ADME_INSTANCE}.energy.azure.com/api/workflow/liveness_check",
    }
]

# Token cache per scope
token_cache = {}


# Function to obtain an access token
def get_access_token(scope):
    now = time.time()

    # Check if we have a cached token for this scope that hasn't expired yet
    if scope in token_cache:
        token, expiry = token_cache[scope]
        if now < expiry:
            return token

    token_request_body = {
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": scope,
    }

    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data=token_request_body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        response_data = response.json()
        token = response_data["access_token"]
        expiry = now + (response_data["expires_in"] - 300)

        # Cache the token for this scope
        token_cache[scope] = (token, expiry)
        return token
    except requests.exceptions.RequestException as error:
        error_description = (
            error.response.json().get("error_description")
            if error.response
            else str(error)
        )
        raise Exception(f"Error fetching access token: {error_description}")


# Perform health checks and include additional data in logs
def perform_health_checks(instances):
    results = {}

    # Define scopes per environment
    environment_scopes = {
        "{ADME_INSTANCE}": "7daee810-3f78-40c4-84c2-7a199428de18/.default",
        "equinortest": "7daee810-3f78-40c4-84c2-7a199428de18/.default",
        "equinor": "5a1178c2-5867-4a34-8fb8-216164e30b5f/.default",
    }

    for environment, services in instances.items():
        token = get_access_token(environment_scopes[environment])

        print(token)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        results[environment] = []

        for service in services:
            try:
                response = requests.get(service["healthEndpoint"], headers=headers)
                response.raise_for_status()
                results[environment].append(
                    {
                        "serviceName": service["name"],
                        "status": "Healthy",
                        "statusCode": response.status_code,
                        "healthEndpoint": service["healthEndpoint"],
                        "partition": service["partition"],
                        "environment": environment,
                    }
                )
            except requests.exceptions.RequestException as error:
                status_code = 500
                error_message = str(error)

                if (
                    isinstance(error, requests.exceptions.HTTPError)
                    and error.response is not None
                ):
                    status_code = error.response.status_code
                    error_message = error.response.text or error_message
                else:
                    match = re.search(r"(\d{3}) .*Error", error_message)
                    if match:
                        parsed_code = match.group(1)
                        if parsed_code.isdigit():
                            status_code = int(parsed_code)

                results[environment].append(
                    {
                        "serviceName": service["name"],
                        "status": "Unhealthy",
                        "statusCode": status_code,
                        "errorMessage": error_message,
                        "healthEndpoint": service["healthEndpoint"],
                        "partition": service["partition"],
                        "environment": environment,
                    }
                )
    return results


# Send logs to Azure Monitor
def send_logs_to_azure_monitor(logs):
    # Flatten the logs into a list of dictionaries
    flattened_logs = [log for instance_logs in logs.values() for log in instance_logs]

    # Log the data being ingested
    print("\nData being ingested to Azure Monitor:\n")
    for log in flattened_logs:
        print(log)

    credential = DefaultAzureCredential()
    client = LogsIngestionClient(
        endpoint=DATA_COLLECTION_ENDPOINT, credential=credential
    )

    try:
        client.upload(
            rule_id=DCR_RULE_ID, stream_name=DCR_STREAM_NAME, logs=flattened_logs
        )
        print("Logs ingested successfully.")
    except HttpResponseError as e:
        print(f"Failed to ingest logs: {e}")


# Example usage
if __name__ == "__main__":
    # Perform health checks for all instances and their services
    health_check_results = perform_health_checks(instances)

    print("\nHealth Check Results:\n")
    for environment, services in health_check_results.items():
        print(f"Environment: {environment}")
        for service in services:
            print(
                f"  Service: {service['serviceName']}, Status: {service['status']}, "
                f"StatusCode: {service['statusCode']}, Partition: {service['partition']}, "
                f"HealthEndpoint: {service['healthEndpoint']}, "
                f"ErrorMessage: {service.get('errorMessage', 'N/A')}"
            )

    # Send health check results to Azure Monitor
    send_logs_to_azure_monitor(health_check_results)
