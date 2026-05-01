import numpy as np

def calculate_statistics(numbers):
    """
    Berekent gemiddelde, mediaan en standaarddeviatie van een lijst getallen.
    
    Args:
        numbers: Lijst met numerieke waarden (int of float).
    
    Returns:
        dict met keys 'mean', 'median', 'std'.
    
    Raises:
        ValueError: Als de lijst leeg is.
        TypeError: Als de lijst niet-numerieke elementen bevat.
    """
    if len(numbers) == 0:
        raise ValueError("Lijst mag niet leeg zijn.")
    
    # Controleer of alle elementen numeriek zijn
    for num in numbers:
        if not isinstance(num, (int, float)):
            raise TypeError("Alle elementen moeten numeriek zijn.")
    
    arr = np.array(numbers, dtype=float)
    mean = np.mean(arr)
    median = np.median(arr)
    # Gebruik steekproef standaarddeviatie (ddof=1)
    std = np.std(arr, ddof=1)
    
    return {
        'mean': mean,
        'median': median,
        'std': std
    }
