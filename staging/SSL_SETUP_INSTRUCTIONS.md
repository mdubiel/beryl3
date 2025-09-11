# SSL Certificate Setup Instructions

## Overview
Since the staging environment (192.168.1.14) is on a local network and cannot be reached from the internet, we need to use DNS challenges for Let's Encrypt certificate generation.

## Prerequisites
1. Access to DNS management for mdubiel.org domain
2. SSH access to staging server (192.168.1.14)

## Domains to Certificate
- beryl3.staging.mdubiel.org
- grafana.staging.mdubiel.org  
- prometheus.staging.mdubiel.org
- registry.staging.mdubiel.org

## Step 1: Run SSL Setup Playbook (Preparation)
```bash
cd /home/mdubiel/projects/beryl3/staging/ansible
ansible-playbook -i inventory/staging.yml playbooks/ssl-setup.yml --tags generate-certs
```

This will:
- Install certbot and required packages
- Create SSL directories
- Display instructions for manual certificate generation

## Step 2: Generate Certificates Manually

SSH to the staging server and run:
```bash
sudo certbot certonly --manual --preferred-challenges=dns \
  --email mdubiel@gmail.com --agree-tos --no-eff-email \
  --manual-public-ip-logging-ok \
  -d beryl3.staging.mdubiel.org \
  -d grafana.staging.mdubiel.org \
  -d prometheus.staging.mdubiel.org \
  -d registry.staging.mdubiel.org
```

## Step 3: Add DNS TXT Records

Certbot will provide TXT record values for each domain. Add these records to your DNS provider:

### Record Format:
```
Type: TXT
Name: _acme-challenge.[domain]
Value: [provided by certbot]
TTL: 300 (5 minutes)
```

### Example Records:
```
_acme-challenge.beryl3.staging.mdubiel.org      TXT  "abc123def456..."
_acme-challenge.grafana.staging.mdubiel.org     TXT  "def456ghi789..."
_acme-challenge.prometheus.staging.mdubiel.org  TXT  "ghi789jkl012..."
_acme-challenge.registry.staging.mdubiel.org    TXT  "jkl012mno345..."
```

## Step 4: Wait for DNS Propagation

Wait 5-10 minutes for DNS propagation, then verify:
```bash
# Check each domain's TXT record
nslookup -type=txt _acme-challenge.beryl3.staging.mdubiel.org
nslookup -type=txt _acme-challenge.grafana.staging.mdubiel.org
nslookup -type=txt _acme-challenge.prometheus.staging.mdubiel.org
nslookup -type=txt _acme-challenge.registry.staging.mdubiel.org
```

## Step 5: Complete Certificate Generation

Continue with the certbot process by pressing Enter when prompted after DNS records are added and propagated.

## Step 6: Copy Certificates to /opt/ssl

After successful generation, run:
```bash
cd /home/mdubiel/projects/beryl3/staging/ansible
ansible-playbook -i inventory/staging.yml playbooks/ssl-setup.yml --tags copy-certs
```

## Step 7: Update Container Configurations

Run:
```bash
ansible-playbook -i inventory/staging.yml playbooks/ssl-setup.yml --tags update-config
ansible-playbook -i inventory/staging.yml playbooks/infra.yml
```

## Step 8: Restart Services

Restart the nginx proxy and other services:
```bash
ssh ansible@192.168.1.14 "docker restart nginx-proxy grafana prometheus"
```

## Verification

Test SSL certificates:
```bash
curl -I https://beryl3.staging.mdubiel.org
curl -I https://grafana.staging.mdubiel.org
curl -I https://prometheus.staging.mdubiel.org
curl -I https://registry.staging.mdubiel.org
```

## Certificate Paths

After setup, certificates will be available at:
- `/opt/ssl/fullchain.pem` - Full certificate chain
- `/opt/ssl/privkey.pem` - Private key
- `/opt/ssl/cert.pem` - Certificate only
- `/opt/ssl/chain.pem` - Intermediate certificates

## Renewal

Automatic renewal is configured via cron to run weekly. Manual renewal:
```bash
sudo certbot renew --manual --preferred-challenges=dns
```

## Troubleshooting

### DNS Record Issues
- Ensure TXT records are added correctly
- Wait for full DNS propagation (up to 15 minutes)
- Use multiple DNS checkers to verify propagation

### Certificate Generation Fails
- Check DNS records are still present
- Verify domain ownership
- Try generating one domain at a time if issues persist

### Container Issues
- Ensure /opt/ssl directory has correct permissions
- Verify SSL files are mounted into containers
- Check nginx configuration syntax

## Next Steps After Manual Setup
1. Verify all services are accessible via HTTPS
2. Test certificate validity and expiration dates
3. Configure automatic renewal testing
4. Update firewall rules if needed for HTTPS traffic