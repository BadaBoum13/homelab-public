# Output the client IDs and secrets for use in Vault and ArgoCD configuration
output "vault_client_id" {
  value = auth0_client.vault.client_id
}

output "vault_client_secret" {
  value     = auth0_client.vault.client_secret
  sensitive = true
}

output "argocd_client_id" {
  value = auth0_client.argocd.client_id
}

output "argocd_client_secret" {
  value     = auth0_client.argocd.client_secret
  sensitive = true
}
