# Least-privilege identity used by workloads on the cluster to access the
# scrolls bucket. It can read and write objects in that one bucket only.

resource "ovh_cloud_project_user" "scrolls_app" {
  service_name = var.service_name
  description  = "${var.name_prefix}-scrolls-app"
  role_names   = ["objectstore_operator"]

  # A rotation replaces the whole identity, not only its key (#63). At 15:22 OVH's S3
  # service still accepted two keys that the API had deleted 80 minutes earlier (a key
  # that was never used was refused at once). A new user takes the old keys' owner,
  # and with it their policy, away. New user first, then the old one is deleted
  # (create_before_destroy is inherited from the credential below).
  lifecycle {
    replace_triggered_by = [terraform_data.scrolls_key_rotation]
  }
}

# Rotating the S3 key is a commit: bump var.scrolls_key_version and the pipeline
# creates a new key first, then deletes the old one (Level 2, #6). The key reaches
# the cluster through Terraform only (output -> workload/monitoring.tf), never Git.
resource "terraform_data" "scrolls_key_rotation" {
  input = var.scrolls_key_version
}

resource "ovh_cloud_project_user_s3_credential" "scrolls_app" {
  service_name = var.service_name
  user_id      = ovh_cloud_project_user.scrolls_app.id

  lifecycle {
    create_before_destroy = true
    replace_triggered_by  = [terraform_data.scrolls_key_rotation]
  }
}

resource "ovh_cloud_project_user_s3_policy" "scrolls_app" {
  service_name = var.service_name
  user_id      = ovh_cloud_project_user.scrolls_app.id

  policy = jsonencode({
    Statement = [
      {
        Sid    = "ScrollsReadWrite"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:ListMultipartUploadParts",
          "s3:ListBucketMultipartUploads",
          "s3:AbortMultipartUpload",
        ]
        Resource = [
          "arn:aws:s3:::${ovh_cloud_project_storage.scrolls.name}",
          "arn:aws:s3:::${ovh_cloud_project_storage.scrolls.name}/*",
        ]
      },
    ]
  })
}
