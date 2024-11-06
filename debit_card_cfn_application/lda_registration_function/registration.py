import json
import boto3
import random
import os

CARD_HOLDER_TABLE = os.environ.get("CARD_HOLDER_TABLE")


def register_user(new_card_details):
    dynamodb = boto3.client("dynamodb")
    item = {
        "card_account_no": {"S": new_card_details["card_account_no"]},
        "card_name": {"S": new_card_details["card_name"]},
        "card_status": {"BOOL": new_card_details["card_status"]}
    }

    response = dynamodb.put_item(TableName=CARD_HOLDER_TABLE, Item=item)
    print(f"register response: {json.dumps(response, indent=2, default=str)}")


def generate_card_uuid() -> str:
    # Generate a random 12-digit number
    number = ''.join([str(random.randint(0, 9)) for _ in range(12)])

    # Format the number with hyphens every 4 digits
    formatted_number = f"{number[:4]}-{number[4:8]}-{number[8:]}"

    return formatted_number


def lambda_handler(event, context):
    print("## Event Received ##")
    print(f"event: {json.dumps(event, indent=2, default=str)}")
    # query_params = event.get("queryStringParameters", None)
    query_params = event

    try:
        if not query_params:
            raise Exception("'card_name' is required")

        card_name = query_params.get("card_name", None)
        if not card_name:
            raise Exception("'card_name' should not be null")

        new_card_details = {
            "card_account_no": generate_card_uuid(),
            "card_name": card_name,
            "card_status": True
        }

        # Call Function to generate card details
        register_user(new_card_details)

        return {
            'statusCode': 200,
            'body': {"new_card_details": new_card_details}
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {"error": str(e)}
        }