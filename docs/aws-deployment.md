# AWS Deployment Guide

This guide covers deploying the Teams Agent Integration services to AWS using ECS Fargate.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                            VPC                                 │  │
│  │  ┌─────────────┐    ┌─────────────────────────────────────┐   │  │
│  │  │   Route 53  │    │      Application Load Balancer      │   │  │
│  │  │   (DNS)     │───▶│  - /webhook → Receiver (3001)       │   │  │
│  │  └─────────────┘    │  - /notify  → Notifier (8001)       │   │  │
│  │                     └─────────────────────────────────────┘   │  │
│  │                              │                                 │  │
│  │              ┌───────────────┴───────────────┐                │  │
│  │              ▼                               ▼                │  │
│  │  ┌─────────────────────┐      ┌─────────────────────┐        │  │
│  │  │   ECS Fargate       │      │   ECS Fargate       │        │  │
│  │  │   Receiver Service  │      │   Notifier Service  │        │  │
│  │  │   Port 3001         │      │   Port 8001         │        │  │
│  │  └─────────────────────┘      └─────────────────────┘        │  │
│  │              │                               │                │  │
│  │              └───────────────┬───────────────┘                │  │
│  │                              ▼                                 │  │
│  │                   ┌─────────────────────┐                     │  │
│  │                   │   Secrets Manager   │                     │  │
│  │                   │   (API Keys, HMAC)  │                     │  │
│  │                   └─────────────────────┘                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
          │                                           │
          ▼                                           ▼
   ┌─────────────┐                           ┌─────────────────┐
   │  MS Teams   │                           │  Power Automate │
   │  Webhooks   │                           │  Workflows      │
   └─────────────┘                           └─────────────────┘
```

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured locally
3. **Docker** installed for local testing
4. **GitHub repository** with Actions enabled

## 1. AWS Infrastructure Setup

### 1.1 Create ECR Repositories

```bash
# Create repositories for both services
aws ecr create-repository --repository-name teams-receiver --region us-east-1
aws ecr create-repository --repository-name teams-notifier --region us-east-1
```

### 1.2 Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name teams-integration --region us-east-1
```

### 1.3 Create Secrets in AWS Secrets Manager

```bash
# Create secret for Teams HMAC
aws secretsmanager create-secret \
    --name teams-integration/hmac-secret \
    --secret-string '{"TEAMS_HMAC_SECRET":"your-base64-secret"}'

# Create secret for API keys
aws secretsmanager create-secret \
    --name teams-integration/api-keys \
    --secret-string '{
        "AGENT_API_KEY":"your-agent-api-key",
        "NOTIFIER_API_KEY":"your-notifier-api-key"
    }'

# Create secret for Power Automate Workflows
aws secretsmanager create-secret \
    --name teams-integration/workflow-urls \
    --secret-string '{
        "TEAMS_WORKFLOW_ALERTS":"https://prod-XX.logic.azure.com/...",
        "TEAMS_WORKFLOW_REPORTS":"https://prod-XX.logic.azure.com/...",
        "TEAMS_WORKFLOW_GENERAL":"https://prod-XX.logic.azure.com/..."
    }'
```

### 1.4 Create IAM Role for GitHub Actions

Create `github-actions-role.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:OWNER/REPO:*"
                }
            }
        }
    ]
}
```

```bash
aws iam create-role \
    --role-name github-actions-teams-deploy \
    --assume-role-policy-document file://github-actions-role.json
```

Attach required policies:
```bash
aws iam attach-role-policy \
    --role-name github-actions-teams-deploy \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-role-policy \
    --role-name github-actions-teams-deploy \
    --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess
```

### 1.5 Create ECS Task Definitions

#### Receiver Task Definition (`receiver-task-def.json`)

```json
{
    "family": "teams-receiver-service",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
    "containerDefinitions": [
        {
            "name": "receiver",
            "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/teams-receiver:latest",
            "portMappings": [
                {
                    "containerPort": 3001,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "ENVIRONMENT", "value": "production"},
                {"name": "LOG_LEVEL", "value": "INFO"},
                {"name": "RECEIVER_PORT", "value": "3001"},
                {"name": "AGENT_BASE_URL", "value": "https://agent-api.example.com"},
                {"name": "AGENT_TIMEOUT", "value": "4.5"},
                {"name": "AGENT_MAX_RETRIES", "value": "1"}
            ],
            "secrets": [
                {
                    "name": "TEAMS_HMAC_SECRET",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:teams-integration/hmac-secret:TEAMS_HMAC_SECRET::"
                },
                {
                    "name": "AGENT_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:teams-integration/api-keys:AGENT_API_KEY::"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/teams-receiver",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:3001/health || exit 1"],
                "interval": 30,
                "timeout": 10,
                "retries": 3,
                "startPeriod": 10
            }
        }
    ]
}
```

#### Notifier Task Definition (`notifier-task-def.json`)

```json
{
    "family": "teams-notifier-service",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
    "containerDefinitions": [
        {
            "name": "notifier",
            "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/teams-notifier:latest",
            "portMappings": [
                {
                    "containerPort": 8001,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "ENVIRONMENT", "value": "production"},
                {"name": "LOG_LEVEL", "value": "INFO"},
                {"name": "NOTIFIER_PORT", "value": "8001"}
            ],
            "secrets": [
                {
                    "name": "NOTIFIER_API_KEY",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:teams-integration/api-keys:NOTIFIER_API_KEY::"
                },
                {
                    "name": "TEAMS_WORKFLOW_ALERTS",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:teams-integration/workflow-urls:TEAMS_WORKFLOW_ALERTS::"
                },
                {
                    "name": "TEAMS_WORKFLOW_REPORTS",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:teams-integration/workflow-urls:TEAMS_WORKFLOW_REPORTS::"
                },
                {
                    "name": "TEAMS_WORKFLOW_GENERAL",
                    "valueFrom": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:teams-integration/workflow-urls:TEAMS_WORKFLOW_GENERAL::"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/teams-notifier",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:8001/health || exit 1"],
                "interval": 30,
                "timeout": 10,
                "retries": 3,
                "startPeriod": 10
            }
        }
    ]
}
```

Register task definitions:
```bash
aws ecs register-task-definition --cli-input-json file://receiver-task-def.json
aws ecs register-task-definition --cli-input-json file://notifier-task-def.json
```

### 1.6 Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name teams-integration-alb \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-xxx \
    --scheme internet-facing \
    --type application

# Create target groups
aws elbv2 create-target-group \
    --name teams-receiver-tg \
    --protocol HTTP \
    --port 3001 \
    --vpc-id vpc-xxx \
    --target-type ip \
    --health-check-path /health

aws elbv2 create-target-group \
    --name teams-notifier-tg \
    --protocol HTTP \
    --port 8001 \
    --vpc-id vpc-xxx \
    --target-type ip \
    --health-check-path /health
```

### 1.7 Create ECS Services

```bash
# Create Receiver service
aws ecs create-service \
    --cluster teams-integration \
    --service-name teams-receiver-service \
    --task-definition teams-receiver-service \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=receiver,containerPort=3001"

# Create Notifier service
aws ecs create-service \
    --cluster teams-integration \
    --service-name teams-notifier-service \
    --task-definition teams-notifier-service \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=notifier,containerPort=8001"
```

## 2. GitHub Repository Configuration

### 2.1 Add GitHub Secrets

In your GitHub repository, go to Settings > Secrets and variables > Actions:

| Secret Name | Description |
|-------------|-------------|
| `AWS_ROLE_ARN` | ARN of the IAM role for GitHub Actions |

### 2.2 Enable GitHub OIDC Provider in AWS

```bash
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

## 3. Release Process

### Automatic Deployment

The release workflow triggers automatically when code is pushed to `main`:

1. **Tests Run** - All 173 tests must pass
2. **Docker Build** - Multi-stage build for both services
3. **ECR Push** - Images tagged with commit SHA
4. **ECS Deploy** - Rolling update with health checks

### Manual Deployment

```bash
# Build locally
docker build --target receiver -t teams-receiver:local .
docker build --target notifier -t teams-notifier:local .

# Test locally
docker-compose up -d

# Verify health
curl http://localhost:3001/health
curl http://localhost:8001/health
```

## 4. Monitoring & Troubleshooting

### CloudWatch Logs

```bash
# View Receiver logs
aws logs tail /ecs/teams-receiver --follow

# View Notifier logs
aws logs tail /ecs/teams-notifier --follow
```

### Health Checks

```bash
# Check ALB endpoint
curl https://teams-integration.example.com/health

# Check service health via AWS CLI
aws ecs describe-services \
    --cluster teams-integration \
    --services teams-receiver-service teams-notifier-service
```

### Common Issues

| Issue | Solution |
|-------|----------|
| 5xx errors | Check CloudWatch logs for exceptions |
| Timeout errors | Verify AGENT_TIMEOUT < 5 seconds |
| HMAC failures | Verify secret matches Teams webhook config |
| Container won't start | Check task definition and secrets |

## 5. Cost Estimation

| Resource | Monthly Cost (approx) |
|----------|----------------------|
| ECS Fargate (2 tasks x 0.5vCPU, 1GB) | ~$30 |
| Application Load Balancer | ~$20 |
| NAT Gateway | ~$35 |
| CloudWatch Logs (10GB) | ~$5 |
| Secrets Manager (4 secrets) | ~$2 |
| **Total** | **~$92/month** |

## 6. Security Considerations

- All secrets stored in AWS Secrets Manager
- HTTPS enforced at ALB level
- HMAC verification for Teams webhooks
- API key authentication for notifier
- VPC with private subnets for ECS tasks
- Security groups restrict inbound traffic
