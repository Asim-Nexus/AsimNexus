
#!/bin/bash
echo "🚀 ASIMNEXUS AWS Deployment"
echo "============================="

# Create EC2 instance
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.medium \
    --key-name asimnexus-key \
    --security-group-ids sg-12345678 \
    --subnet-id subnet-12345678 \
    --user-data file://cloud-init.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ASIMNEXUS}]'

echo "✅ AWS instance created"
echo "🌐 Access at: $(aws ec2 describe-instances --filters 'Name=tag:Name,Values=ASIMNEXUS' --query 'Instances[0].PublicIpAddress' --output text)"
