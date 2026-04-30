def calculate_sum(numbers):
    if not numbers:
        raise ValueError("Lijst is leeg")
    return sum(numbers)

def calculate_average(numbers):
    if not numbers:
        raise ValueError("Lijst is leeg")
    return sum(numbers) / len(numbers)

def calculate_max(numbers):
    if not numbers:
        raise ValueError("Lijst is leeg")
    return max(numbers)
