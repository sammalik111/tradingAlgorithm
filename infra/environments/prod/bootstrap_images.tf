# A package_type = "Image" Lambda function must reference an image already
# sitting in a *private* ECR repo in this account/region — AWS does not
# accept images referenced directly from a public registry (public.ecr.aws
# included) as a Lambda source image. Since nothing has been deployed yet
# on a fresh apply, there's no real backend/workers image to point at, so
# this pulls AWS's own base Lambda Python image and re-pushes it into our
# private repos purely as a placeholder. The first successful CodePipeline
# run replaces it with the real image via `update-function-code`.
#
# Requires Docker and the AWS CLI to be available (and already
# authenticated) on the machine running `terraform apply`.

locals {
  bootstrap_source_image  = "public.ecr.aws/lambda/python:3.11"
  ecr_registry_host       = split("/", module.ecr.repository_urls["backend"])[0]
  backend_bootstrap_image = "${module.ecr.repository_urls["backend"]}:bootstrap"
  workers_bootstrap_image = "${module.ecr.repository_urls["workers"]}:bootstrap"
}

# Login + pull happen once, here. backend/workers push in parallel below —
# `docker login` writes to the local machine's credential store (macOS
# Keychain, etc.), and two concurrent logins to the same registry race and
# can corrupt that write, so every registry auth is centralized in this one
# resource instead of being duplicated per bootstrap push.
resource "null_resource" "ecr_login_and_pull" {
  triggers = {
    registry_host = local.ecr_registry_host
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${local.ecr_registry_host}
      docker pull ${local.bootstrap_source_image}
    EOT
  }
}

resource "null_resource" "bootstrap_backend_image" {
  depends_on = [null_resource.ecr_login_and_pull]

  triggers = {
    repo_url = module.ecr.repository_urls["backend"]
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      docker tag ${local.bootstrap_source_image} ${local.backend_bootstrap_image}
      docker push ${local.backend_bootstrap_image}
    EOT
  }
}

resource "null_resource" "bootstrap_workers_image" {
  depends_on = [null_resource.ecr_login_and_pull]

  triggers = {
    repo_url = module.ecr.repository_urls["workers"]
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      docker tag ${local.bootstrap_source_image} ${local.workers_bootstrap_image}
      docker push ${local.workers_bootstrap_image}
    EOT
  }
}
