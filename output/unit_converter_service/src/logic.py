def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    length_to_meters = {
        "meters": 1.0,
        "feet": 0.3048,
        "miles": 1609.344,
        "kilometers": 1000.0
    }
    if from_unit not in length_to_meters or to_unit not in length_to_meters:
        raise ValueError("Invalid unit")
    
    value_in_meters = value * length_to_meters[from_unit]
    return value_in_meters / length_to_meters[to_unit]

def convert_weight(value: float, from_unit: str, to_unit: str) -> float:
    weight_to_grams = {
        "g": 1.0,
        "kg": 1000.0,
        "lb": 453.59237,
        "oz": 28.349523125
    }
    if from_unit not in weight_to_grams or to_unit not in weight_to_grams:
        raise ValueError("Invalid unit")
    
    value_in_grams = value * weight_to_grams[from_unit]
    return value_in_grams / weight_to_grams[to_unit]

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    valid_units = {"celsius", "fahrenheit", "kelvin"}
    if from_unit not in valid_units or to_unit not in valid_units:
        raise ValueError("Invalid unit")
    
    if from_unit == to_unit:
        return value
        
    if from_unit == "celsius":
        celsius = value
    elif from_unit == "fahrenheit":
        celsius = (value - 32) * 5.0 / 9.0
    elif from_unit == "kelvin":
        celsius = value - 273.15
        
    if to_unit == "celsius":
        return celsius
    elif to_unit == "fahrenheit":
        return (celsius * 9.0 / 5.0) + 32
    elif to_unit == "kelvin":
        return celsius + 273.15
