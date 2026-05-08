import re

def validate_email(email: str) -> tuple[bool, str]:
    if not email:
        return False, "Email cannot be empty"
    
    if email.count('@') != 1:
        return False, "Email must contain exactly one @ symbol"
        
    local_part, domain_part = email.split('@')
    
    if not local_part:
        return False, "Local part cannot be empty"
        
    if not domain_part:
        return False, "Domain part cannot be empty"
        
    if len(local_part) > 64:
        return False, "Local part exceeds 64 characters"
        
    if len(domain_part) > 255:
        return False, "Domain part exceeds 255 characters"
        
    if '..' in email:
        return False, "Email cannot contain consecutive dots"
        
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "Local part cannot start or end with a dot"
        
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False, "Domain part cannot start or end with a dot"
        
    if '.' not in domain_part:
        return False, "Domain must contain a TLD"
        
    tld = domain_part.split('.')[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False, "Invalid TLD"
        
    local_regex = re.compile(r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.\-]+$")
    if not local_regex.match(local_part):
        return False, "Local part contains invalid characters"
        
    domain_regex = re.compile(r"^[a-zA-Z0-9.\-]+$")
    if not domain_regex.match(domain_part):
        return False, "Domain part contains invalid characters"
        
    return True, "valid email address"
