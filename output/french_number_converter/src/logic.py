def number_to_french(n: int) -> str:
    if n == 0:
        return "zéro"
    
    units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", 
             "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
    tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingts", "quatre-vingt-dix"]

    def convert_less_than_100(num: int) -> str:
        if num < 20:
            return units[num]
        
        t, u = divmod(num, 10)
        
        if t in (7, 9):
            if t == 7:
                if u == 1:
                    return "soixante et onze"
                else:
                    return f"soixante-{units[10+u]}"
            elif t == 9:
                return f"quatre-vingt-{units[10+u]}"
        else:
            if u == 0:
                if t == 8:
                    return "quatre-vingts"
                return tens[t]
            elif u == 1:
                if t == 8:
                    return "quatre-vingt-un"
                return f"{tens[t]} et un"
            else:
                if t == 8:
                    return f"quatre-vingt-{units[u]}"
                return f"{tens[t]}-{units[u]}"
        return ""

    def convert_less_than_1000(num: int) -> str:
        c, rest = divmod(num, 100)
        if c == 0:
            return convert_less_than_100(rest)
        
        res = ""
        if c == 1:
            res = "cent"
        else:
            res = f"{units[c]} cents" if rest == 0 else f"{units[c]} cent"
            
        if rest > 0:
            res += " " + convert_less_than_100(rest)
            
        return res

    def convert_group(num: int, singular: str, plural: str, is_mille: bool = False) -> str:
        if num == 0:
            return ""
        if num == 1:
            if is_mille:
                return "mille"
            return f"un {singular}"
        
        res = convert_less_than_1000(num)
        if is_mille:
            if res.endswith("cents"):
                res = res[:-1]
            elif res.endswith("vingts"):
                res = res[:-1]
            return f"{res} mille"
        return f"{res} {plural}"

    groups = [
        (1000000000000000, "billiard", "billiards", False),
        (1000000000000, "billion", "billions", False),
        (1000000000, "milliard", "milliards", False),
        (1000000, "million", "millions", False),
        (1000, "mille", "mille", True),
        (1, "", "", False)
    ]
    
    parts = []
    for limit, singular, plural, is_mille in groups:
        if limit == 1:
            if n > 0:
                parts.append(convert_less_than_1000(n))
        else:
            q, n = divmod(n, limit)
            if q > 0:
                parts.append(convert_group(q, singular, plural, is_mille))
                
    return " ".join(parts).strip()
