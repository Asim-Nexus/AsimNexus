# GitHub Secrets Setup Guide for ASIMNEXUS

## Overview

This guide shows you how to set up all required GitHub secrets for ASIMNEXUS CI/CD pipeline to deploy universally.

---

## Step-by-Step Setup

### 1. Go to GitHub Repository Settings

1. Navigate to your GitHub repository: `https://github.com/YOUR_USERNAME/AsimNexus`
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret**

---

## Required Secrets

### AWS Credentials (Required for deployment)

```
Name: AWS_ACCESS_KEY_ID
Value: your_aws_access_key_id_here
```

```
Name: AWS_SECRET_ACCESS_KEY
Value: your_aws_secret_access_key_here
```

**How to get AWS credentials:**
1. Go to AWS Console → IAM → Users
2. Create user or select existing user
3. Go to Security credentials tab
4. Click "Create access key"
5. Copy Access Key ID and Secret Access Key
6. **Important:** Save the secret - you won't see it again!

### LLM API Keys (Required for AI functionality)

```
Name: OPENAI_API_KEY
Value: sk-proj-...
```

**How to get OpenAI API key:**
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key

```
Name: ANTHROPIC_API_KEY
Value: sk-ant-...
```

**How to get Anthropic API key:**
1. Go to https://console.anthropic.com/
2. Go to API Keys section
3. Click "Create Key"
4. Copy the key

```
Name: GEMINI_API_KEY
Value: AIza...
```

**How to get Gemini API key:**
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API key"
3. Copy the key

```
Name: GROK_API_KEY
Value: xai-...
```

**How to get Grok API key:**
1. Go to https://x.ai/
2. Sign up for API access
3. Get API key from dashboard

### Database & Vector DB (Required for memory)

```
Name: PINECONE_API_KEY
Value: your_pinecone_api_key
```

**How to get Pinecone API key:**
1. Go to https://www.pinecone.io/
2. Sign up and login
3. Go to API Keys section
4. Copy the key

```
Name: PINECONE_ENVIRONMENT
Value: us-east-1-aws
```

```
Name: REDIS_URL
Value: redis://localhost:6379
```

### Security Keys (Required for encryption)

```
Name: SECRET_KEY
Value: generate_with_python_c_secrets
```

**How to generate SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

```
Name: ENCRYPTION_KEY
Value: generate_with_cryptography
```

**How to generate ENCRYPTION_KEY:**
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Google Ecosystem (Optional)

```
Name: GOOGLE_CLIENT_ID
Value: your_google_client_id
```

**How to get Google Client ID:**
1. Go to Google Cloud Console
2. Create OAuth 2.0 credentials
3. Copy Client ID

```
Name: GOOGLE_CLIENT_SECRET
Value: your_google_client_secret
```

### Monitoring & Observability (Optional but recommended)

```
Name: LANGFUSE_PUBLIC_KEY
Value: pk-...
```

**How to get Langfuse keys:**
1. Go to https://cloud.langfuse.com/
2. Sign up and create project
3. Copy Public Key and Secret Key

```
Name: LANGFUSE_SECRET_KEY
Value: sk-...
```

```
Name: LANGFUSE_HOST
Value: https://cloud.langfuse.com
```

### Cloud Provider Credentials (Optional for multi-cloud)

```
Name: GCP_PROJECT_ID
Value: your_gcp_project_id
```

```
Name: GCP_SERVICE_ACCOUNT_KEY
Value: base64_encoded_service_account_json
```

**How to get GCP credentials:**
1. Go to Google Cloud Console
2. Create service account
3. Download JSON key
4. Encode to base64: `base64 -i key.json`

```
Name: AZURE_SUBSCRIPTION_ID
Value: your_azure_subscription_id
```

```
Name: AZURE_CLIENT_ID
Value: your_azure_client_id
```

```
Name: AZURE_CLIENT_SECRET
Value: your_azure_client_secret
```

```
Name: AZURE_TENANT_ID
Value: your_azure_tenant_id
```

---

## Complete Secret List

### Required (Must have for deployment)

1. ✅ `AWS_ACCESS_KEY_ID`
2. ✅ `AWS_SECRET_ACCESS_KEY`
3. ✅ `OPENAI_API_KEY` (or at least one LLM provider)
4. ✅ `SECRET_KEY`
5. ✅ `ENCRYPTION_KEY`

### Recommended (For full functionality)

6. `ANTHROPIC_API_KEY`
7. `GEMINI_API_KEY`
8. `PINECONE_API_KEY`
9. `PINECONE_ENVIRONMENT`

### Optional (For additional features)

10. `GROK_API_KEY`
11. `REDIS_URL`
12. `GOOGLE_CLIENT_ID`
13. `GOOGLE_CLIENT_SECRET`
14. `LANGFUSE_PUBLIC_KEY`
15. `LANGFUSE_SECRET_KEY`
16. `GCP_PROJECT_ID`
17. `GCP_SERVICE_ACCOUNT_KEY`
18. `AZURE_SUBSCRIPTION_ID`
19. `AZURE_CLIENT_ID`
20. `AZURE_CLIENT_SECRET`
21. `AZURE_TENANT_ID`

---

## Verification

After adding secrets, verify:

1. Go to Actions tab in GitHub
2. Click on "ASIMNEXUS CI/CD Pipeline" workflow
3. Click "Run workflow" → "Run workflow"
4. Monitor the workflow to ensure secrets are working

If workflow fails, check:
- Secret names match exactly (case-sensitive)
- Secret values are correct
- AWS credentials have proper permissions

---

## AWS IAM Permissions Required

Your AWS user/role must have these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:CreateCluster",
        "ecs:DeleteCluster",
        "ecs:DescribeClusters",
        "ecs:RegisterTaskDefinition",
        "ecs:CreateService",
        "ecs:UpdateService",
        "ecs:DeleteService",
        "ecs:DescribeServices",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "elasticloadbalancing:CreateLoadBalancer",
        "elasticloadbalancing:DeleteLoadBalancer",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:CreateTargetGroup",
        "elasticloadbalancing:CreateListener",
        "iam:PassRole",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Security Best Practices

1. **Never commit secrets to repository** - Always use GitHub Secrets
2. **Rotate secrets regularly** - Update secrets every 90 days
3. **Use least privilege** - Give AWS credentials only needed permissions
4. **Monitor access** - Check AWS CloudTrail for suspicious activity
5. **Use separate keys for dev/prod** - Don't share keys across environments

---

## Troubleshooting

### Issue: Workflow fails with "AWS credentials not found"

**Solution:**
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set
- Check credentials are valid in AWS Console
- Ensure IAM user has ECS permissions

### Issue: Workflow fails with "LLM API key not found"

**Solution:**
- Verify at least one LLM API key is set (OpenAI, Anthropic, or Gemini)
- Check API key format is correct
- Verify API key is active in provider console

### Issue: Workflow fails with "Invalid secret format"

**Solution:**
- Ensure secret values don't have extra spaces or newlines
- Copy-paste directly from provider console
- Don't include quotes around values

---

## Quick Reference

| Secret | Required | Provider |
|--------|----------|----------|
| AWS_ACCESS_KEY_ID | ✅ Yes | AWS |
| AWS_SECRET_ACCESS_KEY | ✅ Yes | AWS |
| OPENAI_API_KEY | ⚠️ At least one LLM | OpenAI |
| ANTHROPIC_API_KEY | ⚠️ At least one LLM | Anthropic |
| GEMINI_API_KEY | ⚠️ At least one LLM | Google |
| GROK_API_KEY | Optional | xAI |
| PINECONE_API_KEY | Recommended | Pinecone |
| SECRET_KEY | ✅ Yes | Generated |
| ENCRYPTION_KEY | ✅ Yes | Generated |

---

## Next Steps

After setting up secrets:

1. ✅ Push code to GitHub main branch
2. ✅ GitHub Actions will automatically deploy
3. ✅ Monitor deployment in Actions tab
4. ✅ Verify deployment at https://api.asim-nexus.ai/health

---

**Status: Ready for GitHub Secrets Setup** ✅
