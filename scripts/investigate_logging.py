import boto3
import sys
import json
import time

TRAIL_NAME = 'confidential-workflow-trail'
REGION = 'ap-southeast-1'
# Fetch key ID from environment or hardcode for investigation
KEY_ARN = "arn:aws:kms:ap-southeast-1:345594574230:key/e67fcd71-77e8-441d-8092-fa9c6359771d"

def try_config(client, name, advanced_selectors=None, basic_selectors=None):
    print(f"\n--- Testing Configuration: {name} ---")
    try:
        if advanced_selectors:
            # Always include Management events to avoid breaking existing logging
            if not any(s['Name'] == 'Management Events' for s in advanced_selectors):
                 advanced_selectors.insert(0, {
                    "Name": "Management Events",
                    "FieldSelectors": [
                        { "Field": "eventCategory", "Equals": ["Management"] }
                    ]
                })
            
            print(f"Applying Advanced Selectors:\n{json.dumps(advanced_selectors, indent=2)}")
            client.put_event_selectors(
                TrailName=TRAIL_NAME,
                AdvancedEventSelectors=advanced_selectors
            )
        elif basic_selectors:
             print(f"Applying Basic Selectors:\n{json.dumps(basic_selectors, indent=2)}")
             client.put_event_selectors(
                TrailName=TRAIL_NAME,
                EventSelectors=basic_selectors
            )
            
        print("✅ SUCCESS: Configuration accepted by API.")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    print(f"Investigating CloudTrail logging for Key: {KEY_ARN}")
    try:
        client = boto3.client('cloudtrail', region_name=REGION)
    except Exception as e:
        print(f"Failed to create boto3 client: {e}")
        return

    # Attempt 1: Advanced Selector - Filter by ARN ONLY (No resources.type)
    # Rationale: The previous error was "resources.type value invalid". Maybe valid types are restricted.
    config1 = [
        {
            "Name": "Enclave KMS Data Events (ARN Only)",
            "FieldSelectors": [
                { "Field": "eventCategory", "Equals": ["Data"] },
                { "Field": "resources.ARN", "Equals": [KEY_ARN] }
            ]
        }
    ]
    if try_config(client, "Advanced Selector - ARN Only", advanced_selectors=config1):
        return

    # Attempt 2: Advanced Selector - resources.type = AWS::KMS::Key (Retrying to confirm exact error)
    config2 = [
        {
            "Name": "Enclave KMS Data Events (Type + ARN)",
            "FieldSelectors": [
                { "Field": "eventCategory", "Equals": ["Data"] },
                { "Field": "resources.type", "Equals": ["AWS::KMS::Key"] },
                { "Field": "resources.ARN", "Equals": [KEY_ARN] }
            ]
        }
    ]
    if try_config(client, "Advanced Selector - Type + ARN", advanced_selectors=config2):
        return

    # Attempt 3: Basic Selectors (Via Boto3 directly, bypassing CLI validation)
    # AWS Doc says: "To log data events for a KMS key, verify that you are using basic event selectors."
    # Some older docs suggest KMS is ONLY supported in Basic Selectors.
    config3 = [
        {
            "ReadWriteType": "All",
            "IncludeManagementEvents": True,
            "DataResources": [
                {
                    "Type": "AWS::KMS::Key",
                    "Values": [KEY_ARN]
                }
            ]
        }
    ]
    if try_config(client, "Basic Selector - AWS::KMS::Key", basic_selectors=config3):
        return

    print("\n⚠️  All configuration attempts failed.")

if __name__ == "__main__":
    main()
