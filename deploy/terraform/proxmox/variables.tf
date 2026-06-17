variable "proxmox_endpoint" {
  description = "Proxmox API-URL, bv. https://proxmox.local:8006/"
  type        = string
}

variable "proxmox_api_token" {
  description = "API-token in de vorm 'user@realm!tokenid=uuid'"
  type        = string
  sensitive   = true
}

variable "proxmox_insecure" {
  description = "Self-signed certificaat toelaten"
  type        = bool
  default     = true
}

variable "proxmox_node" {
  description = "Naam van de Proxmox-node"
  type        = string
}

variable "template_vm_id" {
  description = "VMID van de Ubuntu cloud-init template om uit te klonen"
  type        = number
}

variable "vm_name" {
  description = "Naam van de nieuwe VM"
  type        = string
  default     = "ai-factory"
}

variable "vm_cores" {
  type    = number
  default = 2
}

variable "vm_memory_mb" {
  type    = number
  default = 4096
}

variable "vm_disk_gb" {
  type    = number
  default = 20
}

variable "vm_datastore" {
  description = "Storage voor disk + cloud-init, bv. 'local-lvm'"
  type        = string
  default     = "local-lvm"
}

variable "vm_bridge" {
  description = "Netwerk-bridge"
  type        = string
  default     = "vmbr0"
}

variable "vm_ipv4" {
  description = "'dhcp' of een statisch adres met masker, bv. '192.168.128.50/23'"
  type        = string
  default     = "dhcp"
}

variable "vm_gateway" {
  description = "Gateway bij statisch IP; leeg laten bij dhcp"
  type        = string
  default     = ""
}

variable "ci_user" {
  description = "Cloud-init gebruikersnaam (gebruik dezelfde als ansible_user)"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key" {
  description = "Publieke SSH-sleutel voor toegang tot de VM"
  type        = string
}
