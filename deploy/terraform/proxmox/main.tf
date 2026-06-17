terraform {
  required_version = ">= 1.3"
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.66"
    }
  }
}

provider "proxmox" {
  endpoint  = var.proxmox_endpoint
  api_token = var.proxmox_api_token
  insecure  = var.proxmox_insecure
}

# Eén Ubuntu-VM, gekloond uit een bestaande cloud-init template.
# Maak vooraf een template (bv. via de Ubuntu cloud image) en geef het vmid op.
resource "proxmox_virtual_environment_vm" "ai_factory" {
  name      = var.vm_name
  node_name = var.proxmox_node
  tags      = ["ai-factory"]

  clone {
    vm_id = var.template_vm_id
    full  = true
  }

  cpu {
    cores = var.vm_cores
    type  = "host"
  }

  memory {
    dedicated = var.vm_memory_mb
  }

  disk {
    datastore_id = var.vm_datastore
    interface    = "scsi0"
    size         = var.vm_disk_gb
  }

  # qemu-guest-agent moet in de template aanstaan om het IP terug te lezen.
  agent {
    enabled = true
  }

  network_device {
    bridge = var.vm_bridge
  }

  initialization {
    datastore_id = var.vm_datastore

    ip_config {
      ipv4 {
        address = var.vm_ipv4
        gateway = var.vm_gateway != "" ? var.vm_gateway : null
      }
    }

    user_account {
      username = var.ci_user
      keys     = [trimspace(var.ssh_public_key)]
    }
  }
}
