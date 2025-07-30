# Resource group for organizing applications
resource "auth0_resource_server" "homelab" {
  name        = "homelab"
  identifier  = "https://homelab.local"
  signing_alg = "RS256"

  allow_offline_access                            = true
  token_lifetime                                  = 86400
  skip_consent_for_verifiable_first_party_clients = true
}


# Vault Application
resource "auth0_client" "tailscale" {
  name                = "tailscale"
  description         = "tailscale OIDC client"
  app_type           = "regular_web"
  callbacks          = var.vault_callback_urls
  allowed_origins    = var.allowed_origins
  allowed_logout_urls = var.vault_callback_urls
  oidc_conformant    = true

  jwt_configuration {
    alg = "RS256"
  }

  refresh_token {
    rotation_type   = "rotating"
    expiration_type = "expiring"
    leeway          = 0
    token_lifetime  = 2592000
  }
}

# Vault Application
# resource "auth0_client" "vault" {
#   name                = "Vault"
#   description         = "HashiCorp Vault OIDC client"
#   app_type           = "regular_web"
#   callbacks          = var.vault_callback_urls
#   allowed_origins    = var.allowed_origins
#   allowed_logout_urls = var.vault_callback_urls
#   oidc_conformant    = true

#   jwt_configuration {
#     alg = "RS256"
#   }

#   refresh_token {
#     rotation_type   = "rotating"
#     expiration_type = "expiring"
#     leeway          = 0
#     token_lifetime  = 2592000
#   }
# }

# # ArgoCD Application
# resource "auth0_client" "argocd" {
#   name                = "ArgoCD"
#   description         = "ArgoCD OIDC client"
#   app_type           = "regular_web"
#   callbacks          = var.argocd_callback_urls
#   allowed_origins    = var.allowed_origins
#   allowed_logout_urls = var.argocd_callback_urls
#   oidc_conformant    = true

#   jwt_configuration {
#     alg = "RS256"
#   }

#   refresh_token {
#     rotation_type   = "rotating"
#     expiration_type = "expiring"
#     leeway          = 0
#     token_lifetime  = 2592000
#   }
# }

# Create default roles
resource "auth0_role" "admin" {
  name        = "admin"
  description = "Administrator role with full access"
}

resource "auth0_role" "reader" {
  name        = "reader"
  description = "Reader role with read-only access"
}
