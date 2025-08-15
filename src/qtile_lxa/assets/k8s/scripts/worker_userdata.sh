#!/bin/bash
set -e
# set -x

echo "=== Waiting for join script from master ==="
while [ ! -f /common/join.sh ]; do
	echo "waiting..."
    sleep 2
done

mkdir -p ~/.kube/
cp /common/kubeconfig ~/.kube/config
/common/join.sh

