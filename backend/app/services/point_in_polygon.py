from typing import List, Tuple, Dict, Any

def point_in_polygon(x: float, y: float, polygon: List) -> bool:
    """
    Determina se um ponto (x, y) está dentro de um polígono definido por uma lista de pontos.
    Usa o algoritmo "ray casting" (também conhecido como o algoritmo do ponto de cruzamento).
    
    Args:
        x: Coordenada X do ponto
        y: Coordenada Y do ponto
        polygon: Lista de pontos que formam o polígono, onde cada ponto é um dicionário
                 com as chaves 'x' e 'y' ou uma tupla [x, y] ou (x, y)
                 
    Returns:
        bool: True se o ponto está dentro do polígono, False caso contrário
    """
    # Garante que temos pelo menos 3 pontos para formar um polígono
    if len(polygon) < 3:
        return False
    
    # Inicializar a variável de resultado
    inside = False
    
    # Extrair valores de pontos conforme o formato
    # Manipulação flexível para suportar diferentes formatos de entrada
    def get_point_coords(point):
        if isinstance(point, dict):
            return point.get('x', 0), point.get('y', 0)
        elif isinstance(point, (list, tuple)) and len(point) >= 2:
            return point[0], point[1]
        return 0, 0
    
    # Processar o polígono
    n = len(polygon)
    j = n - 1  # Último ponto
    
    for i in range(n):
        # Extrair coordenadas dos pontos atuais e anteriores
        xi, yi = get_point_coords(polygon[i])
        xj, yj = get_point_coords(polygon[j])
        
        # Verificar se o raio cruza uma aresta
        if (
            ((yi > y) != (yj > y)) and  # Um ponto acima e outro abaixo do y
            (x < (xj - xi) * (y - yi) / (yj - yi) + xi)  # Ponto à esquerda da interseção
        ):
            inside = not inside  # Inverter a condição 'dentro/fora'
        
        j = i  # Armazenar o índice do ponto atual
    
    return inside 