#!/usr/bin/env python3
"""
Teste básico do sistema sem dependências externas (matplotlib, seaborn)
"""

import math
import cmath

# Constantes físicas básicas
MU_0 = 4 * math.pi * 1e-7
EPSILON_0 = 8.854187817e-12
OMEGA = 2 * math.pi * 60

class Coordenadas:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class ParametrosSolo:
    def __init__(self, resistividade_camada1, resistividade_camada2, espessura_camada1, permissividade_relativa=10.0):
        self.resistividade_camada1 = resistividade_camada1
        self.resistividade_camada2 = resistividade_camada2
        self.espessura_camada1 = espessura_camada1
        self.permissividade_relativa = permissividade_relativa

class Solo:
    def __init__(self, parametros):
        self.parametros = parametros
        
    def resistividade_equivalente_uniforme(self, frequencia=60.0):
        rho1 = self.parametros.resistividade_camada1
        rho2 = self.parametros.resistividade_camada2
        h1 = self.parametros.espessura_camada1
        
        mu1 = MU_0
        f = frequencia
        
        sqrt_rho1_inv = math.sqrt(1/rho1)
        sqrt_rho2_inv = math.sqrt(1/rho2)
        
        exp_term = math.exp(-2 * h1 * math.sqrt(math.pi * f * mu1 / rho1))
        
        numerator = (sqrt_rho1_inv + sqrt_rho2_inv) + (sqrt_rho1_inv - sqrt_rho2_inv) * exp_term
        denominator = (sqrt_rho1_inv + sqrt_rho2_inv) - (sqrt_rho1_inv - sqrt_rho2_inv) * exp_term
        
        return rho1 * (numerator / denominator)**2

class Cabo:
    def __init__(self, coordenadas, corrente, raio, tipo="fase"):
        self.coordenadas = coordenadas
        self.corrente = corrente
        self.raio = raio
        self.tipo = tipo

class Duto:
    def __init__(self, coordenadas, diametro, espessura_parede, espessura_revestimento, material="aco"):
        self.coordenadas = coordenadas
        self.diametro = diametro
        self.raio_externo = diametro / 2
        self.raio_interno = self.raio_externo - espessura_parede
        self.espessura_revestimento = espessura_revestimento
        
        if material == "aco":
            self.resistividade = 1.72e-7
            self.permeabilidade_relativa = 300
        else:
            self.resistividade = 2.82e-8
            self.permeabilidade_relativa = 1
            
        self.resistividade_revestimento = 1e8
        self.permissividade_revestimento = 2.3

class LinhaTransmissao:
    def __init__(self, cabos, solo):
        self.cabos = cabos
        self.solo = solo

    def calcular_impedancia_mutua_simples(self, cabo, duto):
        """Versão simplificada da impedância mútua"""
        dx = cabo.coordenadas.x - duto.coordenadas.x
        dy = cabo.coordenadas.y - duto.coordenadas.y
        dz = cabo.coordenadas.z - duto.coordenadas.z
        
        D_ij = math.sqrt(dx**2 + dy**2 + dz**2)
        rho = self.solo.resistividade_equivalente_uniforme()
        
        # Aproximação simplificada
        real_part = (MU_0 * OMEGA / 8)
        imag_part = (MU_0 * OMEGA / (2 * math.pi)) * math.log(1 / (D_ij * math.sqrt(OMEGA * MU_0 / rho)))
        
        return complex(real_part, imag_part)

def teste_sistema():
    print("=== TESTE BÁSICO DO SISTEMA EMI ===\n")
    
    # Configuração do solo
    parametros_solo = ParametrosSolo(100.0, 1000.0, 2.0, 10.0)
    solo = Solo(parametros_solo)
    
    # Duto subterrâneo
    coord_duto = Coordenadas(x=0, y=0, z=-1.5)
    duto = Duto(coord_duto, 0.219, 0.0065, 0.003, "aco")
    
    # Cabos da linha de transmissão
    cabos = [
        Cabo(Coordenadas(-3.3, 15, 0), complex(529, 0), 0.01257, "fase"),
        Cabo(Coordenadas(0, 19, 0), complex(529 * math.cos(math.radians(-120)), 529 * math.sin(math.radians(-120))), 0.01257, "fase"),
        Cabo(Coordenadas(3.3, 23, 0), complex(529 * math.cos(math.radians(120)), 529 * math.sin(math.radians(120))), 0.01257, "fase"),
        Cabo(Coordenadas(0, 26.7, 0), complex(0, 0), 0.004572, "guarda")
    ]
    
    lt = LinhaTransmissao(cabos, solo)
    
    # Calcular tensão induzida
    tensao_total = complex(0, 0)
    print("IMPEDÂNCIAS MÚTUAS:")
    
    for i, cabo in enumerate(lt.cabos):
        Z_mutua = lt.calcular_impedancia_mutua_simples(cabo, duto)
        tensao_contrib = Z_mutua * cabo.corrente * 1000  # 1 km
        tensao_total += tensao_contrib
        
        print(f"Cabo {i+1} ({cabo.tipo}): Z_mutua = {Z_mutua:.4e} Ω/m")
        print(f"  Contribuição: {abs(tensao_contrib):.2e} V (fase: {math.degrees(cmath.phase(tensao_contrib)):.1f}°)")
    
    print(f"\nTENSÃO TOTAL INDUZIDA:")
    print(f"  Magnitude: {abs(tensao_total):.2e} V")
    print(f"  Fase: {math.degrees(cmath.phase(tensao_total)):.1f}°")
    
    print(f"\nSOLO:")
    print(f"  Resistividade equivalente: {solo.resistividade_equivalente_uniforme():.1f} Ω.m")
    
    # Avaliação de segurança básica
    magnitude_kv = abs(tensao_total) / 1000
    limite_kv = 5.0  # Para PE
    seguro = magnitude_kv <= limite_kv
    
    print(f"\nAVALIAÇÃO DE SEGURANÇA:")
    print(f"  Tensão no revestimento: {magnitude_kv:.2f} kV")
    print(f"  Limite: {limite_kv:.1f} kV")
    print(f"  Status: {'SEGURO' if seguro else 'CRÍTICO'}")
    
    if seguro:
        print(f"  Margem de segurança: {((limite_kv - magnitude_kv) / limite_kv * 100):.1f}%")
    else:
        print(f"  ATENÇÃO: Tensão excede limite em {((magnitude_kv - limite_kv) / limite_kv * 100):.1f}%!")

if __name__ == "__main__":
    teste_sistema()