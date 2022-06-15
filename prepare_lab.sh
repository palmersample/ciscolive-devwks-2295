#!/bin/sh

# docker exec containers_vault_1 vault secrets enable --path=network kv
# docker exec containers_vault_1 vault secrets enable --path=infra kv
docker exec containers_vault_1 vault kv put secret/infra/netbox netbox_url=http://localhost:8000 api_token=0123456789abcdef0123456789abcdef01234567
docker exec containers_vault_1 vault kv put secret/network/WLC-NA-MCO-1 username=developer password=1234QWer enable=C1sco12345
docker exec containers_vault_1 vault kv put secret/network/WLC-NA-MCO-2 username=developer password=1234QWer enable=C1sco12345
