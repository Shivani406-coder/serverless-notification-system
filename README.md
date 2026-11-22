# Serverless Notification System using AWS SNS and SQS

A student capstone starter project that demonstrates a notification workflow locally using LocalStack (an AWS cloud-service emulator), Docker, Python, Flask, Amazon SNS, and Amazon SQS.

> This project runs locally. It does not require an AWS account or create real AWS resources.

## Architecture

1. A user enters a recipient and notification message in the web page.
2. The Flask backend publishes the notification to an SNS topic.
3. An SQS queue subscribed to that SNS topic receives the notification.
4. The web page can read messages from the queue and delete them.

## Requirements

- Docker Desktop installed and running
- Docker Compose (included with current Docker Desktop)
- A web browser

You do not need to install Python, AWS CLI, or LocalStack separately because the application and LocalStack run in containers.

## Run the project

1. Extract the ZIP file.
2. Open the extracted `serverless-notification-system` folder in VS Code.
3. Open the VS Code terminal in that folder.
4. Start Docker Desktop and wait until it says Docker is running.
5. Run:

   ```bash
   docker compose up --build
   ```

6. Wait for LocalStack initialization and for the web service to start.
7. Open this address in your browser:

   http://localhost:5000

8. Enter a recipient and message, then select **Send notification**.
9. Select **Refresh messages** to see the SNS notification delivered to SQS.

## Useful commands

Stop containers:

```bash
docker compose down
```

Stop containers and delete LocalStack data:

```bash
docker compose down -v
```

View running containers:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f web
```

View LocalStack initialization logs:

```bash
docker compose logs -f localstack
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check service readiness |
| POST | `/api/notify` | Publish a notification to SNS |
| GET | `/api/messages` | Receive messages from SQS |
| DELETE | `/api/messages` | Delete a received message from SQS |

Example request to send a notification:

```json
{
  "recipient": "student@example.com",
  "message": "Your assignment deadline is tomorrow."
}
```

## Important notes

- LocalStack is an emulator; this is not a deployment to AWS.
- The recipient field is included in the message body. This starter project does not send real email or SMS.
- The SQS queue uses standard queue behavior. A message can reappear if it is not deleted before its visibility timeout expires.
- For a production version, add authentication, input validation, logging, monitoring, secrets management, and an actual delivery provider or AWS deployment.
- If Docker reports that it cannot connect to the daemon, start or restart Docker Desktop and retry `docker compose up --build`.

## Suggested capstone extensions

- Add user login and role-based access.
- Add notification history in a database.
- Add message status and timestamps.
- Add separate topics for announcements, reminders, and alerts.
- Add unit and integration tests.
- Prepare architecture, sequence, and use-case diagrams for the project report.
