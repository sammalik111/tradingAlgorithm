# infra/

Terraform. One environment (`environments/prod/`) wiring together the
modules in `modules/`. Nothing in this repo runs `terraform apply` —
that's a manual step (see "Applying" below).

## Modules

| Module             | Provisions                                                                                                                     |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `networking`       | VPC, 2 public + 2 private subnets, 1 NAT Gateway, security groups for Lambda/Aurora/Redis                                      |
| `aurora`           | Aurora Serverless v2 (PostgreSQL), 0.5–2 ACU, single instance, RDS-managed master password                                     |
| `bastion`          | Minimal EC2 instance for reaching Aurora from a local DB client via SSM, or optionally SSH (Aurora itself stays fully private) |
| `redis`            | ElastiCache Serverless (Redis) — pay-per-use, no always-on node                                                                |
| `sqs`              | `trade-ingest` queue + dead-letter queue                                                                                       |
| `ecr`              | Container image repositories for `backend` and `workers`                                                                       |
| `secrets`          | Empty Secrets Manager placeholders (Anthropic key, Quiver Quant key, Robinhood credentials)                                    |
| `lambda`           | Reusable module for one container-image Lambda function (IAM role, log group, optional VPC/SQS trigger)                        |
| `api_gateway`      | HTTP API in front of the backend-api Lambda                                                                                    |
| `frontend_hosting` | Private S3 bucket + CloudFront distribution (origin access control, SPA fallback routing)                                      |
| `eventbridge`      | Nightly schedules for `nightly-scrape` and `recommendation-engine`                                                             |
| `codepipeline`     | GitHub CodeStar connection, CodeBuild deploy project, CodePipeline, weekly EventBridge trigger                                 |

## Lambda functions

Four, all container-image, all built from `backend/Dockerfile` or
`workers/Dockerfile` with a different `image_command` override:

| Function                | Image   | Handler                                                        | Trigger               | VPC |
| ----------------------- | ------- | -------------------------------------------------------------- | --------------------- | --- |
| `backend-api`           | backend | `trading_backend.main.handler`                                 | API Gateway           | yes |
| `recommendation-engine` | backend | `trading_backend.recommendation_engine.lambda_handler.handler` | EventBridge (nightly) | yes |
| `nightly-scrape`        | workers | `trading_workers.jobs.nightly_scrape.handler`                  | EventBridge (nightly) | no  |
| `process-trade-message` | workers | `trading_workers.jobs.process_trade_message.handler`           | SQS                   | yes |

`nightly-scrape` is the only one outside the VPC: it only needs outbound
internet (to scrape) and the public SQS API, so it skips the NAT Gateway
hop the other three need to reach Aurora/Redis privately.

`networking` also creates a free S3 Gateway VPC Endpoint, attached to both
route tables. CodeBuild runs in the private subnets (see `codepipeline`
below) and needs it specifically to download its source/artifacts from
S3 — that download can time out through NAT alone even when NAT is
otherwise working fine for everything else.

## Networking cost note

`networking` uses a managed NAT Gateway (~$32/mo + data processing). A
cheaper self-managed NAT instance (`t4g.nano`, ~$3/mo) was tried first,
but produced a string of hard-to-diagnose partial-connectivity failures
(ECR auth succeeding intermittently, CloudWatch Logs delivery failing
outright) despite its MASQUERADE rule visibly forwarding some traffic —
inconsistent enough that the AWS-operated, self-healing managed service
was worth the extra cost here.

## Credentials

- **Database**: `aws_rds_cluster.manage_master_user_password = true`
  creates an AWS-managed Secrets Manager secret; Terraform passes its ARN
  plus the cluster host/db name to each Lambda as `DB_SECRET_ARN` /
  `DB_HOST` / `DB_NAME`. The app resolves the password at cold start (see
  `backend/db/secret_credentials.py`) — the password itself is never
  written into a Lambda environment variable.
- **Claude / Quiver Quant / Robinhood**: `secrets` module creates empty
  placeholders. Fill them after apply:
  ```
  aws secretsmanager put-secret-value \
    --secret-id trading-platform/prod/anthropic-api-key \
    --secret-string "sk-ant-..."
  ```

## Connecting to Aurora from a local DB client (Navicat, psql, TablePlus, ...)

Aurora has no path in from the internet at all — no public subnet, no
`publicly_accessible`, and its security group only allows the Lambda,
CodeBuild, and `bastion` module's security groups on 5432. The `bastion`
module (a small EC2 instance) exists specifically to make a local
connection possible without changing any of that. Two ways to reach it:

- **SSM** (default, always available): no open inbound ports, no SSH key
  to manage. You run a `aws ssm start-session` command that opens a local
  port forwarding to Aurora.
- **SSH** (opt-in, set `bastion_ssh_public_key` + `bastion_allowed_ssh_cidr`
  in `terraform.tfvars`): for a DB client's native SSH-tunnel connection
  mode (e.g. Navicat's built-in "SSH Tunnel" tab) instead of a
  manually-run SSM command. This moves the bastion to the public subnet
  with a stable Elastic IP and opens port 22 to the CIDR you configured —
  real internet exposure, gated by your SSH key and (if you scoped it to
  your own IP/32, as you should) by source IP too.

Either way, get the master password first (rotated/managed by RDS, never
in Terraform state or a Lambda env var):

```
aws secretsmanager get-secret-value \
  --secret-id $(terraform output -raw aurora_master_secret_arn) \
  --query SecretString --output text | jq -r .password
```

### Via SSM

1. Requires the Session Manager plugin locally once:
   `brew install --cask session-manager-plugin` (macOS) — see AWS's docs
   for other platforms.
2. Open the tunnel (leave this running in a terminal):
   ```
   aws ssm start-session \
     --target $(terraform output -raw db_bastion_instance_id) \
     --document-name AWS-StartPortForwardingSessionToRemoteHost \
     --parameters '{"host":["'"$(terraform output -raw aurora_cluster_endpoint)"'"],"portNumber":["5432"],"localPortNumber":["5433"]}'
   ```
3. In Navicat, create a PostgreSQL connection to `localhost:5433`,
   database `trading`, user `trading_admin`, password from above. Leave
   it as a plain (non-SSH-tunnel) connection in Navicat — the SSM tunnel
   from step 2 already terminates locally on 5433, so nothing further to
   configure on Navicat's end.

Close the terminal from step 2 (or Ctrl+C) to end the tunnel; nothing
about the bastion needs to keep running between sessions.

### Via SSH (once `bastion_ssh_public_key`/`bastion_allowed_ssh_cidr` are set and applied)

1. `terraform output -raw db_bastion_ssh_public_ip` — the bastion's stable
   Elastic IP. If this comes back empty/null, the SSH vars aren't set/applied
   yet.
2. In Navicat, create a PostgreSQL connection with the **SSH Tunnel** tab
   enabled:
   - SSH Host: the IP from step 1, Port `22`
   - SSH User Name: `ec2-user`
   - SSH Authentication: Public Key, pointed at the private key matching
     the public key you put in `bastion_ssh_public_key` (never committed
     anywhere — it should only ever exist on your machine)
   - Then the normal PostgreSQL tab: host `<aurora_cluster_endpoint output>`,
     port `5432`, database `trading`, user `trading_admin`, password from
     above

No separate tunnel command to run or leave open here — Navicat manages
the SSH connection itself for the lifetime of the DB connection.

## Weekly deploy pipeline (`codepipeline` module)

- Source stage reads from GitHub via a CodeStar connection
  (`DetectChanges = false`, so a normal `git push` never triggers it).
- Build stage runs `infra/codebuild/buildspec.yml`: builds + pushes both
  container images, runs `alembic upgrade head` against Aurora, builds
  the frontend and syncs it to S3, invalidates CloudFront, and calls
  `aws lambda update-function-code` for all four functions.
- An EventBridge schedule (`deploy_schedule_expression`, default Monday
  09:00 UTC) calls `codepipeline:StartPipelineExecution` once a week.
  Triggering a deploy outside that schedule means clicking "Release
  change" in the CodePipeline console, or:
  ```
  aws codepipeline start-pipeline-execution --name trading-platform-prod-deploy
  ```

## Bootstrapping a container-image Lambda before any image exists

A `package_type = "Image"` Lambda must reference an image already in a
_private_ ECR repo in this account/region — AWS does not accept an image
referenced directly from a public registry (public.ecr.aws included) as a
Lambda source image, and on a fresh account there's no real
backend/workers image yet either.

`infra/environments/prod/bootstrap_images.tf` handles this: two
`null_resource`s with a `local-exec` provisioner pull AWS's own
`public.ecr.aws/lambda/python:3.11` base image and re-push it into our
private `backend`/`workers` ECR repos as a `:bootstrap` tag, which the
four Lambda modules then reference (with an explicit `depends_on` so
Terraform pushes the image before creating the function). Requires Docker
and the AWS CLI on the machine running `terraform apply`. The first
successful CodePipeline run replaces this placeholder with the real image
via `update-function-code`.

## Applying

1. `terraform init` (from `infra/environments/prod/`).
2. `terraform apply`.
3. In the AWS Console → Developer Tools → Settings → Connections, find
   the `trading-platform-prod-github` connection and complete the GitHub
   OAuth handshake (can't be scripted).
4. Populate the Secrets Manager placeholders above.
5. Either wait for the weekly schedule or manually start the pipeline to
   get real application code onto the bootstrap Lambdas.

Remote state is local by default (`versions.tf`). To use an S3 backend
instead, create the bucket + DynamoDB lock table once by hand, uncomment
the `backend "s3"` block in `versions.tf`, and run
`terraform init -migrate-state`.
