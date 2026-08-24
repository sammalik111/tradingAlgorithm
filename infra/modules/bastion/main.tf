# A minimal EC2 instance for reaching Aurora from a local DB client
# (Navicat, psql, etc.) without ever making the database itself
# internet-reachable. Two access modes, both optional:
#   - SSM Session Manager: always available, no open inbound ports, no SSH
#     key to manage.
#   - SSH: opt-in (set var.ssh_public_key and var.allowed_ssh_cidr both),
#     for clients like Navicat that want a native SSH-tunnel connection
#     instead of a manually-run `aws ssm start-session` port-forward. Moves
#     the instance to the public subnet with a public IP and opens 22 to
#     allowed_ssh_cidr -- real internet exposure, scope allowed_ssh_cidr to
#     your own IP/32, never 0.0.0.0/0.
# See documentation/infra.md for connection instructions for both.
locals {
  ssh_enabled = var.ssh_public_key != null && var.allowed_ssh_cidr != null
  subnet_id   = local.ssh_enabled ? var.public_subnet_id : var.private_subnet_id
}

# Amazon Linux 2023 ships the SSM Agent preinstalled, so no user_data is
# needed to bootstrap it -- just the instance profile below.
data "aws_ami" "bastion" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-arm64"]
  }
}

resource "aws_security_group" "bastion" {
  name        = "${var.project}-${var.environment}-db-bastion-sg"
  description = "DB access bastion -- SSM always available; SSH ingress only when ssh_enabled"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.environment}-db-bastion-sg" }
}

resource "aws_security_group_rule" "bastion_ssh_ingress" {
  count             = local.ssh_enabled ? 1 : 0
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  security_group_id = aws_security_group.bastion.id
  cidr_blocks       = [var.allowed_ssh_cidr]
  description       = "SSH for local DB-client tunneling (e.g. Navicat built-in SSH tunnel)"
}

resource "aws_key_pair" "bastion" {
  count      = local.ssh_enabled ? 1 : 0
  key_name   = "${var.project}-${var.environment}-db-bastion"
  public_key = var.ssh_public_key
}

resource "aws_security_group_rule" "bastion_to_aurora" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = var.aurora_security_group_id
  source_security_group_id = aws_security_group.bastion.id
  description              = "Allow the DB bastion to reach Aurora"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "bastion" {
  name               = "${var.project}-${var.environment}-db-bastion-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "bastion_ssm" {
  role       = aws_iam_role.bastion.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "bastion" {
  name = "${var.project}-${var.environment}-db-bastion-profile"
  role = aws_iam_role.bastion.name
}

resource "aws_instance" "bastion" {
  ami                         = data.aws_ami.bastion.id
  instance_type               = var.instance_type
  subnet_id                   = local.subnet_id
  vpc_security_group_ids      = [aws_security_group.bastion.id]
  iam_instance_profile        = aws_iam_instance_profile.bastion.name
  key_name                    = local.ssh_enabled ? aws_key_pair.bastion[0].key_name : null
  associate_public_ip_address = local.ssh_enabled

  tags = { Name = "${var.project}-${var.environment}-db-bastion" }
}

# Static address so it doesn't change across stop/start or instance
# replacement -- the public subnet's map_public_ip_on_launch would
# otherwise give the instance a new ephemeral IP each time. Free while
# attached to a running instance (AWS only charges for an unattached EIP
# or one on a stopped instance).
resource "aws_eip" "bastion" {
  count  = local.ssh_enabled ? 1 : 0
  domain = "vpc"

  tags = { Name = "${var.project}-${var.environment}-db-bastion-eip" }
}

resource "aws_eip_association" "bastion" {
  count         = local.ssh_enabled ? 1 : 0
  instance_id   = aws_instance.bastion.id
  allocation_id = aws_eip.bastion[0].id
}
