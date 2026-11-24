# The cluster's monitoring stack: a Helm chart in charts/kube-monitoring.
# Terraform installs it and upgrades it when the chart changes. Bump `version`
# in the chart's Chart.yaml whenever you change a template.
resource "helm_release" "monitoring" {
  name      = "kube-monitoring"
  chart     = "${path.module}/charts/kube-monitoring"
  namespace = "observability"

  create_namespace = true
  wait             = true
  timeout          = 600

  set = [
    {
      name  = "ingress.domain"
      value = var.ingress_domain
    },
    {
      name  = "scrolls.credentials.s3Bucket"
      value = try(data.terraform_remote_state.core.outputs.scrolls_bucket, local.core_pending)
    },
    {
      name  = "scrolls.credentials.s3Endpoint"
      value = try(data.terraform_remote_state.core.outputs.scrolls_s3_endpoint, local.core_pending)
    },
  ]

  # Secrets for the scrolls app (Level 2, #6): from Terraform, never from Git.
  set_sensitive = [
    {
      name  = "scrolls.credentials.s3AccessKey"
      value = try(data.terraform_remote_state.core.outputs.scrolls_s3_access_key, local.core_pending)
    },
    {
      name  = "scrolls.credentials.s3SecretKey"
      value = try(data.terraform_remote_state.core.outputs.scrolls_s3_secret_key, local.core_pending)
    },
    {
      name  = "scrolls.credentials.signingKey"
      value = random_password.scrolls_signing_key.result
    },
  ]
}

# Until core/ is applied (the pipeline does core before workload), its new outputs
# don't exist yet; a PR plan then shows this placeholder instead of failing.
locals {
  core_pending = "wacht-op-core-apply"
}

# Signing key of the scrolls app. Replaces the one that was hardcoded in the chart
# (and so leaked). To rotate: change `keepers`.
resource "random_password" "scrolls_signing_key" {
  length  = 48
  special = false
  keepers = {
    rotation = "2026-11-24-rotatie-1"
  }
}
