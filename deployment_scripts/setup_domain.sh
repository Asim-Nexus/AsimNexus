
#!/bin/bash
echo "🌐 ASIMNEXUS Domain & SSL Setup"
echo "================================="

DOMAIN="asimnexus.ai"

# Install Certbot
apt-get install certbot python3-certbot-nginx -y

# Generate SSL certificate
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@asimnexus.ai

# Configure automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

echo "✅ SSL certificate installed for $DOMAIN"
echo "🔒 HTTPS enabled at: https://$DOMAIN"
