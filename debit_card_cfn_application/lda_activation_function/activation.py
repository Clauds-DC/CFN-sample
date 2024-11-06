import json
import boto3
import random
import os

# manual string on yaml. not !Ref
CARD_HOLDER_TABLE = os.environ.get("CARD_HOLDER_TABLE")


def activate_card(new_card_details):
    dynamodb = boto3.client("dynamodb")

    response = dynamodb.update_item(
        TableName=CARD_HOLDER_TABLE,
        Key={
            # Replace 'hash_key' with your actual hash key field name
            'card_account_no': {'S': new_card_details["card_account_no"]}
        },
        UpdateExpression='SET card_status = :val',
        ExpressionAttributeValues={
            ':val': {"BOOL": new_card_details["card_status"]}
        }
    )

    print(f"activate response: {json.dumps(response, indent=2, default=str)}")


"""
    expected:
        {
            "card_account_no": "",
            "card_status": true|false
        }
"""


def lambda_handler(event, context):
    print("## Event Received ##")
    print(f"event: {json.dumps(event, indent=2, default=str)}")
    # query_params = event.get("queryStringParameters", None)
    query_params = event

    try:
        if not query_params:
            raise Exception("'card_account_no' and 'card_status' is required")

        card_account_no = query_params.get("card_account_no", None)
        if not card_account_no:
            raise Exception("'card_account_no' should not be null")

        card_status = query_params.get("card_status", None)
        if card_status == None:
            raise Exception("'card_status' should not be null")
        if not type(card_status) == bool:
            raise Exception(
                "'card_status' should be boolean type - true|false")

        activate_details = {
            "card_account_no": card_account_no,
            "card_status": card_status
        }

        # Call Function to generate card details
        activate_card(activate_details)

        return {
            'statusCode': 200,
            'body': {"message": f"card account '{card_account_no}' successfully set to '{card_status}' status!"}
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {"error": str(e)}
        }
