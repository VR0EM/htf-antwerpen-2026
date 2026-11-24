# Private, versioned, encrypted bucket holding application data ("the scrolls").

resource "ovh_cloud_storage_object_bucket" "scrolls" {
  service_name = var.service_name
  region       = var.storage_region
  name         = local.bucket_name

  versioning = {
    status = "ENABLED"
  }

  encryption = {
    algorithm = "AES256"
  }

  tags = local.tags

  lifecycle {
    # Object lock is not used (it can only be set at creation). After the bucket
    # was changed in the console, the API reports an empty object_lock block,
    # which the provider sees as a change that forces a new bucket. Ignoring it
    # lets Terraform repair versioning and encryption in place instead of
    # destroying the scrolls.
    ignore_changes = [object_lock]
    # Never let a plan destroy the realm's data by accident.
    prevent_destroy = true
  }
}

resource "ovh_cloud_project_storage_object_bucket_lifecycle_configuration" "scrolls" {
  service_name   = var.service_name
  region_name    = var.storage_region
  container_name = ovh_cloud_storage_object_bucket.scrolls.name

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
