#!/usr/bin/env bash
# Підготовка середовища Codespaces / devcontainer (Ubuntu 24.04): інструменти для завдань і тестів.
set -e
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends python3-pip python3-venv acl openssh-client openssh-server ufw nftables nginx-light openssl \
  curl dnsutils jq shellcheck qemu-utils libvirt-clients virtinst postgresql postgresql-client
python3 -m pip install --user --break-system-packages -r requirements.txt
grep -q '.local/bin' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
