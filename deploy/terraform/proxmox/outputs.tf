output "vm_name" {
  value = proxmox_virtual_environment_vm.ai_factory.name
}

output "vm_ipv4_address" {
  description = "IP voor in de Ansible inventory (vereist qemu-guest-agent in de template)"
  value       = try(proxmox_virtual_environment_vm.ai_factory.ipv4_addresses[1][0], "kijk in de Proxmox-console")
}
