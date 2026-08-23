data "aws_region" "current" {}

locals {
  az_count = length(var.availability_zones)
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "${var.project}-igw" }
}

resource "aws_subnet" "public" {
  count                   = local.az_count
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "${var.project}-public-${var.availability_zones[count.index]}" }
}

resource "aws_subnet" "private" {
  count             = local.az_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + local.az_count)
  availability_zone = var.availability_zones[count.index]

  tags = { Name = "${var.project}-private-${var.availability_zones[count.index]}" }
}

# Self-managed NAT instance instead of a managed NAT Gateway: ~$3/mo on the
# smallest ARM instance size vs. ~$32/mo + data processing for a NAT
# Gateway. Same job (outbound internet for the private subnets, e.g. the
# recommendation-engine Lambda calling Claude, and every VPC Lambda calling
# Secrets Manager for DB credentials), single point of failure either way —
# just cheaper. Swap back to aws_nat_gateway once real uptime matters.
data "aws_ami" "nat_instance" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-arm64"]
  }
}

resource "aws_security_group" "nat_instance" {
  name        = "${var.project}-nat-instance-sg"
  description = "NAT instance: accepts traffic only from inside the VPC"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-nat-instance-sg" }
}

resource "aws_instance" "nat" {
  ami                    = data.aws_ami.nat_instance.id
  instance_type          = var.nat_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.nat_instance.id]

  # Required for a NAT instance: it must be allowed to forward traffic that
  # isn't addressed to itself.
  source_dest_check = false

  # Amazon Linux 2023 does not ship `iptables` by default — installing it
  # explicitly (rather than assuming it's present) is the fix for a real
  # failure mode: if the binary didn't exist, `set -e` would stop the
  # script right after enabling IP forwarding and before ever adding the
  # MASQUERADE rule, silently leaving packets forwarded but not
  # source-NAT'd — which forwards traffic without ever getting a usable
  # reply back, i.e. general internet egress hangs/times out while
  # anything with its own VPC endpoint (like S3) keeps working fine.
  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf install -y iptables-services
    sysctl -w net.ipv4.ip_forward=1
    echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-nat.conf
    IFACE=$(ip -o -4 route show to default | awk '{print $5}')
    iptables -t nat -A POSTROUTING -o "$IFACE" -j MASQUERADE
    iptables-save > /etc/sysconfig/iptables
    systemctl enable --now iptables
  EOF

  tags = { Name = "${var.project}-nat-instance" }
}

resource "aws_eip" "nat" {
  domain            = "vpc"
  network_interface = aws_instance.nat.primary_network_interface_id
  tags              = { Name = "${var.project}-nat-eip" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = local.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block           = "0.0.0.0/0"
    network_interface_id = aws_instance.nat.primary_network_interface_id
  }

  tags = { Name = "${var.project}-private-rt" }
}

resource "aws_route_table_association" "private" {
  count          = local.az_count
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Free (no hourly charge, unlike interface endpoints). Routes S3 traffic
# directly within AWS's network instead of out through the NAT instance.
# CodeBuild running in the private subnets needs this specifically to
# download its source/artifacts from S3 — without it, that download can
# time out even with working NAT/internet egress otherwise.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private.id, aws_route_table.public.id]

  tags = { Name = "${var.project}-s3-endpoint" }
}

resource "aws_security_group" "lambda" {
  name        = "${var.project}-lambda-sg"
  description = "Lambda functions that run inside the VPC"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-lambda-sg" }
}

resource "aws_security_group" "aurora" {
  name        = "${var.project}-aurora-sg"
  description = "Aurora Postgres cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-aurora-sg" }
}

resource "aws_security_group" "redis" {
  name        = "${var.project}-redis-sg"
  description = "ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-redis-sg" }
}
