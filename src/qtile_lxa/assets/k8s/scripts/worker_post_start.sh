#!/bin/bash



mkdir -p ~/.kube
cp /common/kubeconfig ~/.kube/config

for i in {1..5}; do
    if kubectl label node "$HOSTNAME" node-role.kubernetes.io/worker=""; then
        echo "Node labeled successfully"
        break
    else
        echo "Labeling failed (attempt $i), retrying in 2 seconds..."
        sleep 2
    fi
done
