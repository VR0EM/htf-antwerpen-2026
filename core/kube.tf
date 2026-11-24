resource "ovh_cloud_project_kube" "this" {
  service_name = var.service_name
  name         = "${var.name_prefix}-kube"
  region       = var.region
  plan         = var.kube_plan
  version      = var.kube_version

  update_policy   = "MINIMAL_DOWNTIME"
  kube_proxy_mode = "iptables"

  private_network_id = ovh_cloud_network_private_vrack.this.id
  nodes_subnet_id    = ovh_cloud_network_private_vrack_subnet.nodes.id

  private_network_configuration {
    default_vrack_gateway              = ""
    private_network_routing_as_default = false
  }

  depends_on = [ovh_cloud_gateway.this]
}

resource "ovh_cloud_project_kube_nodepool" "default" {
  service_name = var.service_name
  kube_id      = ovh_cloud_project_kube.this.id
  name         = "${var.name_prefix}-pool"
  flavor_name  = var.node_flavor

  autoscale      = true
  min_nodes      = var.node_min_count
  max_nodes      = var.node_max_count
  desired_nodes  = var.node_desired_count
  anti_affinity  = true
  monthly_billed = false

  template {
    metadata {
      annotations = {}
      finalizers  = []
      labels      = local.tags
    }
    spec {
      unschedulable = false
      taints        = []
    }
  }

  lifecycle {
    # The autoscaler owns the actual node count.
    ignore_changes = [desired_nodes]
  }
}

# Who may reach the Kubernetes API. Not in the original code, so when someone
# set a restriction in the console (198.51.100.0/24, which locked everyone
# out), Terraform could not see it. Now it is code: any other value is drift.
resource "ovh_cloud_project_kube_iprestrictions" "this" {
  service_name = var.service_name
  kube_id      = ovh_cloud_project_kube.this.id
  ips          = var.kube_api_allowed_cidrs
}

# Adopt the restriction that already exists, then overwrite it with the list above.
import {
  to = ovh_cloud_project_kube_iprestrictions.this
  id = "${var.service_name}/${ovh_cloud_project_kube.this.id}"
}
