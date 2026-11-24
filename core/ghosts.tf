# Ghost resources: created outside Git ("night-shift", via the console) and not
# part of the realm as it should be. See docs/bewijs/level-1/.
#
# Terraform can only remove what it manages, so this is done in two steps:
#   1. this file: adopt the ghosts into the state with import blocks (no changes)
#   2. the next PR deletes this file, and the pipeline's apply destroys them
#
# The attributes below mirror what exists, so step 1 imports without changing anything.

# Extra node pool, 1 extra b3-8 VM, created 2026-11-24 10:57.
resource "ovh_cloud_project_kube_nodepool" "ghost_hotfix" {
  service_name   = var.service_name
  kube_id        = ovh_cloud_project_kube.this.id
  name           = "hotfix-pool"
  flavor_name    = "b3-8"
  autoscale      = false
  min_nodes      = 1
  max_nodes      = 1
  desired_nodes  = 1
  anti_affinity  = false
  monthly_billed = false
}

import {
  to = ovh_cloud_project_kube_nodepool.ghost_hotfix
  id = "${var.service_name}/${ovh_cloud_project_kube.this.id}/ef0f8e2f-8343-4b18-bcad-9f369857c004"
}

# OpenStack user with the administrator role on the whole project, created 2026-11-24 11:02.
resource "ovh_cloud_project_user" "ghost_debug_admin" {
  service_name = var.service_name
  description  = "debug-admin"
  role_names   = ["administrator"]
}

import {
  to = ovh_cloud_project_user.ghost_debug_admin
  id = "${var.service_name}/1014203"
}

# Second S3 key on the scrolls_app user, next to the one Terraform made.
resource "ovh_cloud_project_user_s3_credential" "ghost_scrolls_app_extra" {
  service_name = var.service_name
  user_id      = ovh_cloud_project_user.scrolls_app.id
}

import {
  to = ovh_cloud_project_user_s3_credential.ghost_scrolls_app_extra
  id = "${var.service_name}/1013904/915a9a74d85e42959734fff64ddb2c4e"
}
