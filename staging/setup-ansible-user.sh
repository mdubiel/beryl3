#!/bin/bash
# Setup script for creating ansible user on remote host
# Run this as root or with sudo privileges

set -e

echo "Creating ansible user..."
useradd -m -s /bin/bash ansible || echo "User already exists"

echo "Adding ansible to appropriate sudo group..."
# Detect OS and use correct group
if [ -f /etc/redhat-release ] || [ -f /etc/centos-release ] || [ -f /etc/rocky-release ]; then
    # CentOS/RHEL/Rocky Linux use wheel group
    usermod -aG wheel ansible
    echo "Added to wheel group (CentOS/RHEL/Rocky)"
elif [ -f /etc/debian_version ]; then
    # Ubuntu/Debian use sudo group
    usermod -aG sudo ansible
    echo "Added to sudo group (Ubuntu/Debian)"
else
    # Try both, one will work
    usermod -aG wheel ansible 2>/dev/null || usermod -aG sudo ansible
    echo "Added to available sudo group"
fi

echo "Creating .ssh directory..."
mkdir -p /home/ansible/.ssh
chmod 700 /home/ansible/.ssh
chown ansible:ansible /home/ansible/.ssh

echo "Configuring passwordless sudo..."
echo 'ansible ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ansible
chmod 440 /etc/sudoers.d/ansible

echo "Ansible user setup complete!"
echo "Now copy your public key to /home/ansible/.ssh/authorized_keys"
echo "Example: cat ~/.ssh/ansible_staging.pub | ssh root@this_host 'tee /home/ansible/.ssh/authorized_keys && chown ansible:ansible /home/ansible/.ssh/authorized_keys && chmod 600 /home/ansible/.ssh/authorized_keys'"