import json
import boto3
import random
import os
import time

CARD_HOLDER_TABLE = os.environ.get("CARD_HOLDER_TABLE")
CARD_TRANSACTION_TABLE = os.environ.get("CARD_TRANSACTION_TABLE")
dynamodb = boto3.client("dynamodb")


def lambda_handler(event, context):
    print("## Event Received ##")
    print(f"event: {json.dumps(event, indent=2, default=str)}")
    # query_params = event.get("queryStringParameters", None)
    query_params = event

    try:
        if not query_params:
            raise Exception("'parameters' is required")

        # Test parameters
        # "card_account_no": "xxxx",
        # "txn_type": "debit",
        # "txn_amount": 100.0,
        # "txn_description": "Initial Deposit"

        card_account_no = query_params.get("card_account_no", None)
        if not card_account_no:
            raise Exception("'card_account_no' should not be null")

        txn_type = query_params.get("txn_type", None)
        if not txn_type:
            raise Exception("'txn_type' should not be null")
        elif txn_type.lower() not in ['debit', 'credit']:
            raise Exception("'txn_type' should be 'credit' or 'debit' only")

        txn_description = query_params.get("txn_description", None)
        if not txn_description:
            raise Exception("'txn_description' should not be null")

        txn_amount = query_params.get("txn_amount", None)
        if not txn_amount:
            raise Exception("'txn_amount' should not be null")
        try:
            txn_amount = float(txn_amount)
        except:
            raise Exception("'txn_amount' should be number/float")

        # Call Process
        transaction_details = {
            "card_account_no": card_account_no,
            "txn_date": get_current_datetime(),
            "txn_type": txn_type.lower(),
            "txn_amount": float(txn_amount),
            "txn_description": txn_description
        }
        process_transaction(transaction_details)

        return {
            'statusCode': 200,
            'body': {"transaction_details": transaction_details,
                     "Transaction_status": "Success"
                     }
        }

    except Exception as e:
        return {
            'statusCode': 400,
            'body': {"error": str(e)}
        }


def get_current_datetime():
    # Get current time as a tuple: (year, month, day, hour, minute, second)
    current_time = time.localtime()

    # Format it into a string: YYYY-MM-DD HH:MM:SS
    formatted_time = f"{current_time.tm_year}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d} " \
        f"{current_time.tm_hour:02d}:{
            current_time.tm_min:02d}:{current_time.tm_sec:02d}"

    return formatted_time


def process_transaction(transaction_details: dict):

    # Test if card number exists
    card_holder_details = get_card_holder_record(
        transaction_details['card_account_no'])
    if not card_holder_details:
        raise Exception(f"'card_account_no' does not exists: {
                        transaction_details['card_account_no']}")

    # Check if activated
    if not card_holder_details['card_status']['BOOL']:
        raise Exception(f"'card_account_no' is not activated!")

    # Check if "amount" is valid
    txn_history = get_transaction_history(
        transaction_details['card_account_no'])
    balance = get_balance_amount(txn_history)
    if transaction_details['txn_type'] == 'debit':
        if transaction_details['txn_amount'] > balance:
            raise Exception(f'Remaining balance is lower than requested amount "{
                            transaction_details['txn_amount']}"')

    # insert transaction
    insert_transaction(transaction_details)

    return True


def get_balance_amount(transaction_history: list) -> float:
    balance = 0
    for transaction in transaction_history:

        if transaction['txn_type'] == 'debit':
            balance -= transaction['txn_amount']
        else:
            balance += transaction['txn_amount']

    return balance


def get_transaction_history(card_account_no: str) -> str:
    # Query DynamoDB table to get all records with the given hash key
    response = dynamodb.query(
        TableName=CARD_TRANSACTION_TABLE,
        KeyConditionExpression=f"card_account_no = :val",
        ExpressionAttributeValues={
            # 'S' for string type; change if necessary (e.g., 'N' for number)
            ':val': {'S': card_account_no}
        }
    )

    # Check if items exist and return them
    items = response.get('Items', [])
    consolidated_items = []
    if items:
        print(f"items history: {json.dumps(
            items, indent=2, default=str)}")
        for record in items:
            consolidated_items.append({
                "card_account_no": record['card_account_no']['S'],
                "txn_date": record['txn_date']['S'],
                "txn_type": record['txn_type']['S'],
                "txn_amount": float(record['txn_amount']['N']),
                "txn_description": record['txn_description']['S']
            })

        return consolidated_items
    else:
        print("No items found for the given hash key.")
        return []


def insert_transaction(transaction_details):
    item = {
        "card_account_no": {"S": transaction_details["card_account_no"]},
        "txn_date": {"S": transaction_details["txn_date"]},
        "txn_type": {"S": transaction_details["txn_type"]},
        "txn_amount": {"N": str(transaction_details["txn_amount"])},
        "txn_description": {"S": transaction_details["txn_description"]},
    }

    response = dynamodb.put_item(TableName=CARD_TRANSACTION_TABLE, Item=item)
    print(f"Transaction response: {
          json.dumps(response, indent=2, default=str)}")


def get_card_holder_record(card_account_no: str) -> dict:
    dynamodb_client = boto3.client('dynamodb')
    response = dynamodb_client.get_item(
        TableName=CARD_HOLDER_TABLE,
        Key={
            # Replace 'hash_key' with your actual hash key name
            'card_account_no': {'S': card_account_no}
        }
    )

    # Check if the item exists
    if 'Item' in response:
        item = response['Item']
        print(f"card_account_no details found: {
              json.dumps(item, indent=2, default=str)}", )
        return item
    else:
        print("card_account_no details not found:", card_account_no)
        return None
