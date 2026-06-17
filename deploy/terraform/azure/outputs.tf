output "vm_public_ip" {
  description = "IP voor in de Ansible inventory"
  value       = azurerm_public_ip.pip.ip_address
}

output "ssh_command" {
  value = "ssh ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}
