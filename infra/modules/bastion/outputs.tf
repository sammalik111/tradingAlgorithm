output "instance_id" {
  value = aws_instance.bastion.id
}

output "security_group_id" {
  value = aws_security_group.bastion.id
}

output "ssh_public_ip" {
  description = "Set only when SSH access is enabled (ssh_public_key + allowed_ssh_cidr both set) -- the Elastic IP for SSH, not the SSM/private path."
  value       = local.ssh_enabled ? aws_eip.bastion[0].public_ip : null
}
