import os
import boto3

from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError

# Load environment variables
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "static"))

app = Flask(__name__, static_folder=STATIC_DIR)

# AWS configuration
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
SNS_AWS_REGION = os.getenv("SNS_AWS_REGION", "ap-southeast-2")

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "").strip()

LOCALSTACK_ENDPOINT = os.getenv(
    "LOCALSTACK_ENDPOINT_URL",
    "http://localhost:4566"
)

TOPIC_NAME = "student-notifications"
QUEUE_NAME = "student-notification-queue"

# LocalStack credentials are for local testing only
local_session = boto3.session.Session(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name=AWS_REGION
)

local_sns = local_session.client(
    "sns",
    endpoint_url=LOCALSTACK_ENDPOINT
)

sqs = local_session.client(
    "sqs",
    endpoint_url=LOCALSTACK_ENDPOINT
)

# Real AWS SNS client
aws_sns = boto3.client(
    "sns",
    region_name=SNS_AWS_REGION
)


# Find LocalStack SNS topic
def get_local_topic_arn():
    response = local_sns.list_topics()

    for topic in response.get("Topics", []):
        arn = topic["TopicArn"]

        if arn.endswith(":" + TOPIC_NAME):
            return arn

    raise RuntimeError(
        "LocalStack SNS topic not found. "
        "Check Docker initialization."
    )


# Find LocalStack SQS queue
def get_queue_url():
    response = sqs.get_queue_url(
        QueueName=QUEUE_NAME
    )

    return response["QueueUrl"]


# Homepage
@app.get("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")


# Notifications page
@app.get("/notify")
def notification_page():
    return send_from_directory(STATIC_DIR, "notify.html")


# Health check
@app.get("/api/health")
def health():
    try:
        topic_arn = get_local_topic_arn()
        queue_url = get_queue_url()

        return jsonify({
            "success": True,
            "status": "healthy",
            "message": "CloudNotify backend is running",
            "localstack_topic": topic_arn,
            "localstack_queue": queue_url,
            "aws_sns_configured": bool(SNS_TOPIC_ARN)
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "status": "not-ready",
            "error": str(exc)
        }), 503


# Send notification
@app.post("/api/notify")
def send_notification():
    data = request.get_json(silent=True) or {}

    recipient = str(data.get("recipient", "")).strip()
    message = str(data.get("message", "")).strip()

    if not recipient or not message:
        return jsonify({
            "error": "Recipient and message are required."
        }), 400

    notification_text = f"To: {recipient}\n\n{message}"

    results = {}

    # Publish to LocalStack SNS
    try:
        topic_arn = get_local_topic_arn()

        local_response = local_sns.publish(
            TopicArn=topic_arn,
            Subject="Student Notification",
            Message=notification_text
        )

        results["localstack"] = {
            "status": "sent",
            "message_id": local_response["MessageId"]
        }

    except (BotoCoreError, ClientError, RuntimeError) as exc:
        results["localstack"] = {
            "status": "failed",
            "error": str(exc)
        }

    # Publish to real AWS SNS
    try:
        if not SNS_TOPIC_ARN:
            raise RuntimeError(
                "SNS_TOPIC_ARN is missing from .env"
            )

        aws_response = aws_sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Student Notification",
            Message=notification_text
        )

        results["aws_sns"] = {
            "status": "sent",
            "message_id": aws_response["MessageId"]
        }

    except (BotoCoreError, ClientError, RuntimeError) as exc:
        results["aws_sns"] = {
            "status": "failed",
            "error": str(exc)
        }

    local_sent = (
        results.get("localstack", {}).get("status") == "sent"
    )

    aws_sent = (
        results.get("aws_sns", {}).get("status") == "sent"
    )

    if local_sent and aws_sent:
        return jsonify({
            "status": "sent",
            "detail": "Notification published to LocalStack and AWS SNS.",
            "results": results
        }), 201

    if local_sent:
        return jsonify({
            "status": "partial",
            "detail": "LocalStack notification sent. Real AWS SNS failed.",
            "results": results
        }), 201

    return jsonify({
        "status": "failed",
        "detail": "LocalStack notification could not be sent.",
        "results": results
    }), 502


# Receive messages from SQS
@app.get("/api/messages")
def get_messages():
    try:
        queue_url = get_queue_url()

        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=2,
            AttributeNames=["All"],
            MessageAttributeNames=["All"]
        )

        messages = []

        for item in response.get("Messages", []):
            messages.append({
                "message_id": item["MessageId"],
                "receipt_handle": item["ReceiptHandle"],
                "body": item["Body"]
            })

        return jsonify({
            "success": True,
            "messages": messages
        })

    except (BotoCoreError, ClientError, RuntimeError) as exc:
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


# Delete SQS message
@app.delete("/api/messages")
def delete_message():
    data = request.get_json(silent=True) or {}

    receipt_handle = data.get("receipt_handle")

    if not receipt_handle:
        return jsonify({
            "error": "receipt_handle is required."
        }), 400

    try:
        sqs.delete_message(
            QueueUrl=get_queue_url(),
            ReceiptHandle=receipt_handle
        )

        return jsonify({
            "success": True,
            "status": "deleted",
            "message": "Message deleted successfully."
        })

    except (BotoCoreError, ClientError, RuntimeError) as exc:
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )