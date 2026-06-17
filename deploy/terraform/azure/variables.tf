variable "name_prefix" {
  description = "Prefix voor alle resourcenamen"
  type        = string
  default     = "ai-factory"
}

variable "location" {
  description = "Azure-regio"
  type        = string
  default     = "westeurope"
}

variable "vm_size" {
  description = "Azure VM-grootte"
  type        = string
  default     = "Standard_B2s"
}

variable "disk_size_gb" {
  type    = number
  default = 30
}

variable "admin_username" {
  description = "Login-gebruiker (gebruik dezelfde als ansible_user)"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key" {
  description = "Publieke SSH-sleutel voor toegang tot de VM"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "Vanaf welk IP-bereik SSH mag (zet op je eigen IP, niet 0.0.0.0/0)"
  type        = string
  default     = "0.0.0.0/0"
}
