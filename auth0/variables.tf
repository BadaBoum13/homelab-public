variable "auth0_domain" {
  description = "Auth0 domain"
  type        = string
}

variable "auth0_client_id" {
  description = "Auth0 client ID"
  type        = string
}

variable "auth0_client_secret" {
  description = "Auth0 client secret"
  type        = string
  sensitive   = true
}

variable "vault_callback_urls" {
  description = "List of Vault callback URLs"
  type        = list(string)
}

variable "argocd_callback_urls" {
  description = "List of ArgoCD callback URLs"
  type        = list(string)
}

variable "allowed_origins" {
  description = "List of allowed origins for CORS"
  type        = list(string)
  default     = []
}
