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
  backend_bootstrap_image = "${module.ecr.repository_urls["backend"]}:bootstrap"
  workers_bootstrap_image = "${module.ecr.repository_urls["workers"]}:bootstrap"
}

resource "null_resource" "bootstrap_backend_image" {
  triggers = {
    repo_url = module.ecr.repository_urls["backend"]
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      registry_host="$(echo "${module.ecr.repository_urls["backend"]}" | cut -d/ -f1)"
      aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin "$registry_host"
      docker pull ${local.bootstrap_source_image}
      docker tag ${local.bootstrap_source_image} ${local.backend_bootstrap_image}
      docker push ${local.backend_bootstrap_image}
    EOT
  }
}

resource "null_resource" "bootstrap_workers_image" {
  triggers = {
    repo_url = module.ecr.repository_urls["workers"]
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      set -euo pipefail
      registry_host="$(echo "${module.ecr.repository_urls["workers"]}" | cut -d/ -f1)"
      aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin "$registry_host"
      docker pull ${local.bootstrap_source_image}
      docker tag ${local.bootstrap_source_image} ${local.workers_bootstrap_image}
      docker push ${local.workers_bootstrap_image}
    EOT
  }
}
