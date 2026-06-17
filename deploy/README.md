# Deploy — VM aanmaken + provisionen

Van een lege VM naar een klaar-voor-gebruik AI Factory in twee stappen:

1. **Terraform** maakt één Ubuntu-VM (optioneel — je mag de VM ook zelf aanmaken).
2. **Ansible** installeert Docker + Python, kopieert deze repo naar de VM, maakt een venv en schrijft `.env`.

```
deploy/
├── ansible/
│   ├── playbook.yml              # installeert alles op de VM
│   ├── inventory.ini.example     # → kopieer naar inventory.ini, vul IP in
│   └── templates/env.j2          # genereert .env op de VM
└── terraform/
    ├── proxmox/                  # VM op je eigen Proxmox
    └── azure/                    # VM in Azure
```

> De code gaat als **lokale kopie** naar de VM (rsync vanuit deze repo). Je hoeft de
> repo dus niet op de VM te clonen. Voor het **pushen** van gegenereerde services naar
> GitHub heeft de VM wél git-credentials nodig — zie onderaan.

---

## Vereisten op je controle-machine

- `terraform` (alleen als je stap 1 gebruikt)
- `ansible` + de collectie: `ansible-galaxy collection install ansible.posix`
- Een SSH-sleutelpaar (`ssh-keygen -t ed25519`)

---

## Stap 1 — VM aanmaken (optioneel)

### Proxmox

Maak vooraf een Ubuntu **cloud-init template** (Ubuntu cloud image, met `qemu-guest-agent`),
noteer het VMID, en:

```bash
cd deploy/terraform/proxmox
cp terraform.tfvars.example terraform.tfvars   # invullen
terraform init
terraform apply
terraform output vm_ipv4_address
```

### Azure

```bash
az login
cd deploy/terraform/azure
cp terraform.tfvars.example terraform.tfvars    # invullen (zet allowed_ssh_cidr op je eigen IP)
terraform init
terraform apply
terraform output vm_public_ip
```

Geen Terraform? Maak gewoon zelf een Ubuntu 22.04-VM aan en onthoud het IP + de SSH-gebruiker.

---

## Stap 2 — Provisionen met Ansible

```bash
cd deploy/ansible
cp inventory.ini.example inventory.ini          # zet het IP uit stap 1 erin
ansible-playbook -i inventory.ini playbook.yml \
    -e "openrouter_api_key=sk-or-..." \
    -e "firecrawl_api_key=fc-..."               # optioneel
```

De key netjes uit je shell-history houden? Gebruik `ansible-vault`:

```bash
ansible-vault create vault.yml                  # zet hierin: openrouter_api_key: sk-or-...
ansible-playbook -i inventory.ini playbook.yml -e @vault.yml --ask-vault-pass
```

---

## Stap 3 — Gebruiken

```bash
ssh ubuntu@<ip>
cd ai-factory && source venv/bin/activate
python main.py "Maak een service met POST /reverse die een string omkeert"
```

---

## Git-push van gegenereerde services

De factory pusht goedgekeurde services naar GitHub. Op de VM moet `git push` daarom
kunnen authenticeren. Kies één van:

- **Deploy key (SSH):** maak op de VM een sleutel (`ssh-keygen`), voeg de public key toe
  als Deploy Key (met write access) op de GitHub-repo, en zet de remote op de SSH-URL:
  `git -C ~/ai-factory remote set-url origin git@github.com:davidvanc/ai-factory.git`
- **Personal Access Token (HTTPS):** `git -C ~/ai-factory remote set-url origin \
  https://<TOKEN>@github.com/davidvanc/ai-factory.git`

Wil je geen output pushen, dan kun je dit overslaan — de pipeline meldt dan enkel dat de
push faalde, de gegenereerde service staat sowieso lokaal in `~/ai-factory/output/`.

---

## Een paar keer per jaar

Klaar met een sessie? Stop of verwijder de VM gewoon:

- Proxmox/Azure: `terraform destroy` (of de VM pauzeren in de UI).
- De memory en gegenereerde output staan in de repo/`data/` — niets gaat verloren zolang
  je `output/` naar GitHub gepusht hebt.
