# GitHub Secrets Setup Guide

This guide walks you through setting up the required GitHub secrets for the Django Europe Production deployment workflow.

## Prerequisites

- Admin access to the GitHub repository
- SSH access to Django Europe production server (148.251.140.153)
- Terminal with SSH client

## Step-by-Step Setup

### Step 1: Generate SSH Key Pair

**On your local machine**, generate a dedicated SSH key pair for GitHub Actions:

```bash
# Generate ED25519 key (recommended)
ssh-keygen -t ed25519 -C "github-actions-beryl3-deploy" -f ~/.ssh/beryl3-github-actions

# When prompted:
# - Enter file location: (press Enter to accept default)
# - Enter passphrase: (leave empty - press Enter twice)
```

**Output**: Two files will be created:
- `~/.ssh/beryl3-github-actions` - Private key (goes in GitHub secret)
- `~/.ssh/beryl3-github-actions.pub` - Public key (goes on server)

---

### Step 2: Copy Public Key to Server

Copy the public key to the Django Europe production server:

```bash
# Method 1: Using ssh-copy-id (recommended)
ssh-copy-id -i ~/.ssh/beryl3-github-actions.pub mdubiel@148.251.140.153

# Method 2: Manual copy
cat ~/.ssh/beryl3-github-actions.pub
# Then SSH to server and paste into ~/.ssh/authorized_keys
```

**Verify access**:
```bash
ssh -i ~/.ssh/beryl3-github-actions mdubiel@148.251.140.153 "echo 'SSH access successful!'"
```

Expected output: `SSH access successful!`

---

### Step 3: Get Known Hosts Entry

Get the SSH fingerprint for the server:

```bash
ssh-keyscan -H 148.251.140.153
```

**Example output**:
```
|1|abc123...= ecdsa-sha2-nistp256 AAAAE2VjZHNh...
|1|def456...= ssh-ed25519 AAAAC3NzaC1lZDI1NTE5...
|1|ghi789...= ssh-rsa AAAAB3NzaC1yc2EAAAA...
```

**Copy all output lines** - you'll need them for the next step.

---

### Step 4: Add Secrets to GitHub

#### 4.1 Navigate to GitHub Secrets

1. Open your GitHub repository in a browser
2. Click **Settings** (top menu)
3. In left sidebar, click **Secrets and variables** → **Actions**
4. You should see the "Actions secrets" page

#### 4.2 Add DJE_SSH_PRIVATE_KEY

1. Click **"New repository secret"** button
2. Fill in the form:
   - **Name**: `DJE_SSH_PRIVATE_KEY`
   - **Secret**: Paste the **private key** content

**Get the private key content**:
```bash
cat ~/.ssh/beryl3-github-actions
```

**Copy everything**, including:
- `-----BEGIN OPENSSH PRIVATE KEY-----`
- All the encoded content
- `-----END OPENSSH PRIVATE KEY-----`

3. Click **"Add secret"**

#### 4.3 Add DJE_SSH_KNOWN_HOSTS

1. Click **"New repository secret"** button again
2. Fill in the form:
   - **Name**: `DJE_SSH_KNOWN_HOSTS`
   - **Secret**: Paste the **ssh-keyscan output** from Step 3

3. Click **"Add secret"**

---

### Step 5: Verify Secrets

After adding both secrets, you should see:

```
DJE_SSH_PRIVATE_KEY    Updated X minutes ago
DJE_SSH_KNOWN_HOSTS    Updated X minutes ago
```

✅ **Secrets are now configured!**

---

## Testing the Setup

### Test 1: Manual Workflow Run (Dry Run)

1. Go to **Actions** tab in GitHub
2. Select **"Deploy to Django Europe Production"** workflow
3. Click **"Run workflow"** dropdown
4. Enter a valid release tag (e.g., `v0.2.122`)
5. Click **"Run workflow"**

The workflow should:
- ✅ Connect to the server successfully
- ✅ Complete all 8 jobs
- ✅ Deploy the application

### Test 2: SSH Connection Test

Create a test workflow to verify SSH connection:

**.github/workflows/test-ssh.yml**:
```yaml
name: Test SSH Connection

on:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.DJE_SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          echo "${{ secrets.DJE_SSH_KNOWN_HOSTS }}" > ~/.ssh/known_hosts

      - name: Test SSH connection
        run: |
          ssh mdubiel@148.251.140.153 "hostname && whoami && pwd"
```

Expected output:
```
yourhostname
mdubiel
/home/mdubiel
```

---

## Troubleshooting

### Error: "Permission denied (publickey)"

**Problem**: GitHub Actions can't authenticate with the server

**Solutions**:

1. **Verify public key on server**:
   ```bash
   ssh mdubiel@148.251.140.153
   cat ~/.ssh/authorized_keys
   # Should contain the public key from beryl3-github-actions.pub
   ```

2. **Check file permissions on server**:
   ```bash
   ssh mdubiel@148.251.140.153
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **Verify private key in GitHub secret**:
   - Go to GitHub repository → Settings → Secrets
   - Click on `DJE_SSH_PRIVATE_KEY`
   - Click "Update"
   - Re-paste the private key from `cat ~/.ssh/beryl3-github-actions`

---

### Error: "Host key verification failed"

**Problem**: SSH can't verify server identity

**Solutions**:

1. **Regenerate known hosts entry**:
   ```bash
   ssh-keyscan -H 148.251.140.153
   ```

2. **Update GitHub secret**:
   - Go to GitHub repository → Settings → Secrets
   - Click on `DJE_SSH_KNOWN_HOSTS`
   - Click "Update"
   - Paste the new ssh-keyscan output

---

### Error: "Could not resolve hostname"

**Problem**: Server hostname is incorrect

**Solution**:
- Verify the IP address is correct: `148.251.140.153`
- Check if server is accessible: `ping 148.251.140.153`
- Verify firewall allows SSH (port 22)

---

## Security Best Practices

### ✅ DO:

- ✅ Use dedicated SSH keys for GitHub Actions (don't reuse personal keys)
- ✅ Use ED25519 keys (more secure than RSA)
- ✅ Keep private keys as GitHub secrets (never commit to repo)
- ✅ Rotate SSH keys periodically (every 6-12 months)
- ✅ Audit GitHub Actions usage regularly

### ❌ DON'T:

- ❌ Don't add passphrase to GitHub Actions SSH keys (automation needs passwordless access)
- ❌ Don't commit private keys to git repository
- ❌ Don't share GitHub secrets with unauthorized users
- ❌ Don't use the same SSH key across multiple environments

---

## Key Rotation

To rotate the SSH keys (recommended every 6-12 months):

1. **Generate new key pair**:
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-beryl3-deploy-2024" -f ~/.ssh/beryl3-github-actions-new
   ```

2. **Add new public key to server** (don't remove old one yet):
   ```bash
   ssh-copy-id -i ~/.ssh/beryl3-github-actions-new.pub mdubiel@148.251.140.153
   ```

3. **Update GitHub secret** `DJE_SSH_PRIVATE_KEY` with new private key

4. **Test deployment** with new key

5. **Remove old public key from server**:
   ```bash
   ssh mdubiel@148.251.140.153
   nano ~/.ssh/authorized_keys
   # Remove the old key line
   ```

---

## Appendix: Manual Secret Format Examples

### DJE_SSH_PRIVATE_KEY Format

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDl2q1V3X5xQ9g8F8P6K2L3M9R0Nn5D7W8YC4E3J1F6TwAAAJh8R9xKfEfc
SgAAAAtzc2gtZWQyNTUxOQAAACDl2q1V3X5xQ9g8F8P6K2L3M9R0Nn5D7W8YC4E3J1F6Tw
AAAEBGl9c8V5Q3N8F7L2K9R0M6W8D5P3Y4C1E6J8H9F2X7TOXarVXdfnFD2DwXw/orYvc
z1HQ2fkPtbxgLgTcnUXpPAAAAGGdpdGh1Yi1hY3Rpb25zLWRlcGxveS1rZXkBAgMEBQYH
-----END OPENSSH PRIVATE KEY-----
```

**Important**:
- Include `-----BEGIN OPENSSH PRIVATE KEY-----` header
- Include `-----END OPENSSH PRIVATE KEY-----` footer
- Preserve all line breaks
- Don't add extra spaces or characters

### DJE_SSH_KNOWN_HOSTS Format

```
|1|abc123def456...= ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTY...
|1|ghi789jkl012...= ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK8P...
|1|mno345pqr678...= ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB...
```

**Important**:
- Multiple lines (one per key type)
- Each line starts with `|1|` (hashed hostname format)
- Preserve exact format from `ssh-keyscan` output

---

## Summary Checklist

Before deploying, verify:

- [ ] SSH key pair generated
- [ ] Public key added to server (`~/.ssh/authorized_keys`)
- [ ] SSH connection tested successfully
- [ ] `DJE_SSH_PRIVATE_KEY` secret added to GitHub
- [ ] `DJE_SSH_KNOWN_HOSTS` secret added to GitHub
- [ ] Both secrets visible in GitHub Settings → Secrets and variables → Actions
- [ ] Test workflow run completed successfully

✅ **You're ready to deploy!**

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [SSH Key Generation Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
- [Deployment Workflow Documentation](github-actions-deployment.md)
