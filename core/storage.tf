# Private, versioned, encrypted bucket holding application data ("the scrolls").

resource "ovh_cloud_project_storage" "scrolls" {
  service_name = var.service_name
  region_name  = var.storage_region
  name         = local.bucket_name

  versioning = {
    status = "enabled"
  }

  encryption = {
    sse_algorithm = "AES256"
  }

  tags = local.tags

  # The realm's data: never destroyed by a plan.
  lifecycle {
    prevent_destroy = true
  }
}

# Migration (#47): the bucket used to be ovh_cloud_storage_object_bucket (v2 API).
# After every change in the console that API reports an empty object_lock block,
# which the provider then sends back and the API refuses ("mode does not match the
# enum"), so every apply failed on the bucket. The v1 resource above manages the same
# bucket without that bug. `removed` forgets the old resource WITHOUT deleting the
# bucket, `import` adopts it again under the new resource.
removed {
  from = ovh_cloud_storage_object_bucket.scrolls
  lifecycle {
    destroy = false
  }
}

import {
  to = ovh_cloud_project_storage.scrolls
  id = "${var.service_name}/${var.storage_region}/${local.bucket_name}"
}

resource "ovh_cloud_project_storage_object_bucket_lifecycle_configuration" "scrolls" {
  service_name   = var.service_name
  region_name    = var.storage_region
  container_name = ovh_cloud_project_storage.scrolls.name

  rules = [
    {
      id     = "expire-old-versions"
      status = "enabled"
      noncurrent_version_expiration = {
        noncurrent_days           = 30
        newer_noncurrent_versions = 5
      }
    },
    {
      id     = "abort-incomplete-uploads"
      status = "enabled"
      abort_incomplete_multipart_upload = {
        days_after_initiation = 7
      }
    },
  ]
}
