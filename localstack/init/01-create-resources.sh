#!/bin/bash
set -e

echo "Creating SNS topic and SQS queue..."

TOPIC_ARN=$(awslocal sns create-topic \
  --name student-notifications \
  --query 'TopicArn' --output text)

QUEUE_URL=$(awslocal sqs create-queue \
  --queue-name student-notification-queue \
  --query 'QueueUrl' --output text)

QUEUE_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' --output text)

echo "Adding permission for SNS to send messages to SQS..."

python - "$TOPIC_ARN" "$QUEUE_ARN" "$QUEUE_URL" <<'PY'
import json
import sys
import subprocess

topic_arn, queue_arn, queue_url = sys.argv[1:]

policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowSNS",
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": queue_arn,
        "Condition": {
            "ArnEquals": {"aws:SourceArn": topic_arn}
        }
    }]
}

attributes = {"Policy": json.dumps(policy)}

subprocess.run([
    "awslocal", "sqs", "set-queue-attributes",
    "--queue-url", queue_url,
    "--attributes", json.dumps(attributes)
], check=True)
PY

echo "Connecting SNS to SQS..."

awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$QUEUE_ARN"

echo "SNS and SQS configured successfully!"