#!/bin/bash
set -e
# set -x

echo "=== Installing K3s master ==="
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC='--write-kubeconfig-mode 644 --disable traefik --disable local-storage' sh -

echo "=== Getting token ==="
TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)

echo "=== Getting master ip ==="
MASTER_IP=$(hostname -I | awk '{print $1}')

echo "=== Preparing Join Command ==="
JOIN_CMD="curl -sfL https://get.k3s.io | K3S_URL=https://${MASTER_IP}:6443 K3S_TOKEN=${TOKEN} sh -"
echo $JOIN_CMD > /common/join.sh
chmod +x /common/join.sh
echo $JOIN_CMD

echo "=== Fetching Kube config ==="
sudo cat /etc/rancher/k3s/k3s.yaml > /common/kubeconfig
sed -i "s/127.0.0.1/$MASTER_IP/" /common/kubeconfig

echo "=== Setting up Kube config ==="
mkdir -p ~/.kube
cp /common/kubeconfig ~/.kube/config

