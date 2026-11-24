variable "ovh_endpoint" {
  description = "OVHcloud API endpoint."
  type        = string
  default     = "ovh-eu"
}

variable "service_name" {
  description = "ID of the team's OVHcloud Public Cloud project."
  type        = string
}

variable "team_name" {
  description = "Team identifier, used in tags and labels."
  type        = string
}

variable "name_prefix" {
  description = "Prefix used for all resource names."
  type        = string
  default     = "achrona"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,14}$", var.name_prefix))
    error_message = "name_prefix must be 2-15 chars, lowercase letters, digits and dashes, starting with a letter."
  }
}

variable "region" {
  description = "Public Cloud region for network, gateway and Kubernetes."
  type        = string
  default     = "GRA11"
}

variable "storage_region" {
  description = "Object Storage region (S3 region name)."
  type        = string
  default     = "GRA"
}

# --- Networking -------------------------------------------------------------

variable "vlan_id" {
  description = "vRack VLAN ID of the private network."
  type        = number
  default     = 10
}

variable "subnet_cidr" {
  description = "CIDR of the private subnet for the Kubernetes nodes."
  type        = string
  default     = "10.10.0.0/24"
}

variable "gateway_model" {
  description = "Size of the managed Public Cloud Gateway (s, m, l, xl). Case-insensitive."
  type        = string
  default     = "s"
}

# --- Kubernetes -------------------------------------------------------------

variable "kube_version" {
  description = "Kubernetes minor version (e.g. \"1.33\"). null = latest available at creation."
  type        = string
  default     = null
}

variable "kube_plan" {
  description = "MKS plan: free or standard."
  type        = string
  default     = "free"
}

variable "node_flavor" {
  description = "Instance flavor of the worker nodes."
  type        = string
  default     = "b3-8"
}

variable "node_min_count" {
  description = "Minimum number of nodes."
  type        = number
  # Was 1. Raised to 2 after the drift review (docs/bewijs/level-1): the pool
  # uses anti-affinity and the realm's services should survive losing one node,
  # so the manual change to 2 was a sensible one and is now part of the code.
  default = 2
}

variable "node_max_count" {
  description = "Maximum number of nodes."
  type        = number
  default     = 3
}

variable "node_desired_count" {
  description = "Initial number of nodes."
  type        = number
  default     = 2
}

variable "kube_api_allowed_cidrs" {
  description = "CIDRs that may reach the Kubernetes API server. Managed in code so any change in the console shows up as drift."
  type        = list(string)
  # Open on purpose: the API itself requires the cluster's client certificate,
  # and the GitHub Actions runners that apply workload/ have no fixed IP.
  # A list of addresses here would lock the pipeline out.
  default = ["0.0.0.0/0"]
}

variable "registry_region" {
  description = "Region of the Managed Private Registry."
  type        = string
  default     = "GRA"
}

variable "registry_plan" {
  description = "Plan of the Managed Private Registry (SMALL, MEDIUM or LARGE)."
  type        = string
  default     = "SMALL"
}

variable "scrolls_key_version" {
  description = "Bump this (any new string) to rotate the S3 key of scrolls_app. See iam.tf."
  type        = string
  default     = "2026-11-24-rotatie-1"
}
