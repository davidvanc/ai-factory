def get_advice(uv_index):
    if uv_index <= 2:
        level = "Laag"
        advice = "Minimale bescherming: geen speciale maatregelen nodig."
    elif uv_index <= 5:
        level = "Gemiddeld"
        advice = "Bescherming aanbevolen: gebruik zonnecrème, draag een hoed en zonnebril."
    elif uv_index <= 7:
        level = "Hoog"
        advice = "Extra bescherming: vermijd de zon tussen 12 en 15 uur, gebruik zonnecrème met hoge factor, draag beschermende kleding."
    elif uv_index <= 10:
        level = "Zeer hoog"
        advice = "Schaduw opzoeken: blijf uit de zon tussen 11 en 16 uur, draag beschermende kleding, hoed en zonnebril, gebruik zonnecrème met factor 30+."
    else:
        level = "Extreem"
        advice = "Maximale bescherming: blijf binnen tussen 10 en 17 uur, draag volledig beschermende kleding, gebruik zonnecrème met factor 50+."
    return f"UV-index {uv_index}: {level} - {advice}"