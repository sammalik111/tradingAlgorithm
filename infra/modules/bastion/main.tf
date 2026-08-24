# A minimal EC2 instance reached only via AWS Systems Manager Session
# Manager -- no open inbound ports, no SSH key to manage. Exists solely so
# a human can port-forward to Aurora from a local DB client (Navicat, psql,
# etc.) without ever making the database itself internet-reachable. See
# documentation/infra.md for the connection instructions.

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
  description = "DB access bastion -- reached only via SSM Session Manager, no inbound rules at all"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.environment}-db-bastion-sg" }
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
  ami                    = data.aws_ami.bastion.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.bastion.id]
  iam_instance_profile   = aws_iam_instance_profile.bastion.name

  tags = { Name = "${var.project}-${var.environment}-db-bastion" }
}
