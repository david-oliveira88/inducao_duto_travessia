import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

# Constantes físicas
MU_0 = 4 * np.pi * 1e-7      # Permeabilidade do vácuo (H/m)
EPSILON_0 = 8.854187817e-12  # Permissividade do vácuo (F/m)
OMEGA = 2 * np.pi * 60       # Frequência angular (rad/s)
GAMMA_EULER = 0.5772156649   # Constante de Euler

class TipoAcoplamento(Enum):
    INDUTIVO = "indutivo"
    CONDUTIVO = "condutivo"
    CAPACITIVO = "capacitivo"

@dataclass
class Coordenadas:
    """Classe para representar coordenadas 2D ou 3D"""
    x: float
    y: float
    z: float = 0.0  # Profundidade (negativa para subterrâneo)

@dataclass
class ParametrosSolo:
    """Parâmetros do solo estratificado"""
    resistividade_camada1: float  # Ω.m
    resistividade_camada2: float  # Ω.m  
    espessura_camada1: float      # m
    permissividade_relativa: float = 10.0

class Solo:
    def __init__(self, parametros: ParametrosSolo):
        self.parametros = parametros
        
    def resistividade_equivalente_uniforme(self, frequencia: float = 60.0) -> float:
        """
        Calcula resistividade equivalente uniforme usando fórmula de Tsiamitros
        Referência: Equação (3.6) da dissertação
        """
        rho1 = self.parametros.resistividade_camada1
        rho2 = self.parametros.resistividade_camada2
        h1 = self.parametros.espessura_camada1
        
        mu1 = MU_0  # Assumindo solo não-magnético
        f = frequencia
        
        sqrt_rho1_inv = np.sqrt(1/rho1)
        sqrt_rho2_inv = np.sqrt(1/rho2)
        
        exp_term = np.exp(-2 * h1 * np.sqrt(np.pi * f * mu1 / rho1))
        
        numerator = (sqrt_rho1_inv + sqrt_rho2_inv) + (sqrt_rho1_inv - sqrt_rho2_inv) * exp_term
        denominator = (sqrt_rho1_inv + sqrt_rho2_inv) - (sqrt_rho1_inv - sqrt_rho2_inv) * exp_term
        
        return rho1 * (numerator / denominator)**2

class Cabo:
    def __init__(self, coordenadas: Coordenadas, corrente: complex, 
                 raio: float, tipo: str = "fase"):
        self.coordenadas = coordenadas
        self.corrente = corrente
        self.raio = raio
        self.tipo = tipo  # "fase", "neutro", "guarda"

class LinhaTransmissao:
    def __init__(self, cabos: List[Cabo], solo: Solo):
        self.cabos = cabos
        self.solo = solo

    def calcular_distancia_cabo_duto(self, cabo: Cabo, duto: 'Duto') -> float:
        """Calcula distância entre cabo aéreo e duto subterrâneo"""
        dx = cabo.coordenadas.x - duto.coordenadas.x
        dy = cabo.coordenadas.y - duto.coordenadas.y
        return np.sqrt(dx**2 + dy**2)

    def calcular_impedancia_mutua_carson_fechada(self, cabo: Cabo, duto: 'Duto') -> complex:
        """
        Implementa solução analítica em forma fechada da integral de Carson
        Referência: Equação (4.20) da dissertação - Theodoulidis
        """
        # Parâmetros geométricos
        x_cabo, y_cabo, z_cabo = cabo.coordenadas.x, cabo.coordenadas.y, cabo.coordenadas.z
        x_duto, y_duto, z_duto = duto.coordenadas.x, duto.coordenadas.y, duto.coordenadas.z
        
        # Distâncias conforme equações (4.16)-(4.19)
        H = y_cabo + abs(z_duto)  # Altura cabo + profundidade duto
        D = x_duto - x_cabo       # Separação horizontal
        
        # Distância cabo-duto
        D_ij = np.sqrt((x_duto - x_cabo)**2 + (y_cabo - z_duto)**2)
        # Distância cabo-imagem do duto
        D_ij_prime = np.sqrt((x_duto - x_cabo)**2 + (y_cabo + abs(z_duto))**2)
        
        # Resistividade equivalente do solo
        rho = self.solo.resistividade_equivalente_uniforme()
        epsilon_r = self.solo.parametros.permissividade_relativa
        
        # Primeira parcela da impedância mútua (meio perfeitamente condutor)
        Z_primeira = (1j * OMEGA * MU_0) / (2 * np.pi) * np.log(D_ij_prime / D_ij)
        
        # Segunda parcela - integral de Carson em forma fechada
        # Mudança de variáveis conforme equações (4.21)-(4.22)
        gamma_propagacao = np.sqrt(1j * OMEGA * MU_0 / rho - OMEGA**2 * MU_0 * EPSILON_0 * epsilon_r)
        
        u1 = gamma_propagacao * (H - 1j * D)
        u2 = gamma_propagacao * (H + 1j * D)
        
        # Funções de Struve e Bessel (aproximação para casos práticos)
        def struve_bessel_approx(u):
            """Aproximação das funções de Struve e Bessel de primeira ordem"""
            if abs(u) < 0.1:
                return (2/np.pi) * (1 - u**2/8 + u**4/192)
            else:
                return (2/np.pi) * (1 - np.exp(-abs(u)) * np.cos(np.angle(u)))
        
        termo1 = (np.pi / (2 * u1)) * struve_bessel_approx(u1) - 1 / (u1**2)
        termo2 = (np.pi / (2 * u2)) * struve_bessel_approx(u2) - 1 / (u2**2)
        
        Z_segunda = (1j * OMEGA * MU_0) / (2 * np.pi) * (termo1 + termo2)
        
        return Z_primeira + Z_segunda

class Duto:
    def __init__(self, coordenadas: Coordenadas, diametro: float, 
                 espessura_parede: float, espessura_revestimento: float,
                 material: str = "aco"):
        self.coordenadas = coordenadas
        self.diametro = diametro
        self.raio_externo = diametro / 2
        self.raio_interno = self.raio_externo - espessura_parede
        self.espessura_revestimento = espessura_revestimento
        
        # Propriedades do material
        self.propriedades = self._obter_propriedades_material(material)
        
        # Propriedades do revestimento (polietileno extrudado típico)
        self.resistividade_revestimento = 1e8  # Ω.m
        self.permissividade_revestimento = 2.3
        
    def _obter_propriedades_material(self, material: str) -> dict:
        """Propriedades típicas de materiais de dutos"""
        propriedades_materiais = {
            "aco": {
                "resistividade": 1.72e-7,      # Ω.m
                "permeabilidade_relativa": 300, # μr
            },
            "aluminio": {
                "resistividade": 2.82e-8,      # Ω.m  
                "permeabilidade_relativa": 1,   # μr
            }
        }
        return propriedades_materiais.get(material, propriedades_materiais["aco"])

    def calcular_impedancia_propria(self, solo: Solo) -> complex:
        """
        Calcula impedância própria do duto conforme equação (4.23)
        """
        # Componente interna (equação 4.24)
        rho_d = self.propriedades["resistividade"]
        mu_d = self.propriedades["permeabilidade_relativa"] * MU_0
        
        Z_interno = (np.sqrt(rho_d * mu_d * OMEGA) / (np.pi * 2 * self.raio_externo * np.sqrt(2))) * (1 + 1j)
        
        # Componente externa (impedância própria com retorno pela terra)
        rho_solo = solo.resistividade_equivalente_uniforme()
        
        # Raio médio geométrico para condutor tubular (equação 4.26)
        RMG_tu = self._calcular_rmg_tubular()
        
        # Primeira parcela
        Z_ext_1 = (1j * OMEGA * MU_0) / (2 * np.pi) * np.log(2 * abs(self.coordenadas.z) / RMG_tu)
        
        # Segunda parcela - integral de Carson para impedância própria
        gamma = np.sqrt(1j * OMEGA * MU_0 / rho_solo)
        u = gamma * 2 * abs(self.coordenadas.z)
        
        # Aproximação para função de Struve-Bessel
        if abs(u) < 0.1:
            termo_integral = (2/np.pi) * (1 - u**2/8)
        else:
            termo_integral = (2/np.pi) * (1 - np.exp(-abs(u.real)) * np.cos(u.imag))
        
        Z_ext_2 = (1j * OMEGA * MU_0) / (2 * np.pi) * termo_integral
        
        return Z_interno + Z_ext_1 + Z_ext_2

    def _calcular_rmg_tubular(self) -> float:
        """Calcula raio médio geométrico para condutor tubular"""
        r_ext = self.raio_externo
        r_int = self.raio_interno
        
        ln_rmg = np.log(r_ext) - (r_ext**4 - r_int**2 * r_ext**2 + r_int**4 * (3/4 + np.log(r_int/r_ext))) / (r_ext**2 - r_int**2)**2
        
        return np.exp(ln_rmg)

    def calcular_admitancia_shunt(self) -> complex:
        """Calcula admitância shunt conforme equação (4.27)"""
        # Componente resistiva (fuga através do revestimento)
        G = (np.pi * 2 * self.raio_externo) / (self.resistividade_revestimento * self.espessura_revestimento)
        
        # Componente capacitiva
        C = (EPSILON_0 * self.permissividade_revestimento * np.pi * 2 * self.raio_externo) / self.espessura_revestimento
        
        return G + 1j * OMEGA * C

    def calcular_impedancia_caracteristica(self, solo: Solo) -> complex:
        """Calcula impedância característica"""
        Z_d = self.calcular_impedancia_propria(solo)
        Y_d = self.calcular_admitancia_shunt()
        return np.sqrt(Z_d / Y_d)

    def calcular_constante_propagacao(self, solo: Solo) -> complex:
        """Calcula constante de propagação"""
        Z_d = self.calcular_impedancia_propria(solo)
        Y_d = self.calcular_admitancia_shunt()
        return np.sqrt(Z_d * Y_d)

class AnaliseInterferencia:
    def __init__(self, linha_transmissao: LinhaTransmissao, duto: Duto):
        self.lt = linha_transmissao
        self.duto = duto
        
    def calcular_tensao_induzida_total(self, comprimento_exposicao: float = 1.0) -> complex:
        """
        Calcula tensão total induzida no duto por todos os cabos da LT
        """
        tensao_total = 0j
        
        for cabo in self.lt.cabos:
            # Impedância mútua entre cabo e duto
            Z_mutua = self.lt.calcular_impedancia_mutua_carson_fechada(cabo, self.duto)
            
            # Contribuição para a tensão induzida
            tensao_total += Z_mutua * cabo.corrente * comprimento_exposicao
            
        return tensao_total

    def avaliar_seguranca_revestimento(self, tensao_induzida: complex) -> dict:
        """Avalia segurança do revestimento conforme critérios da NACE"""
        magnitude_tensao = abs(tensao_induzida)
        
        # Limites típicos para diferentes tipos de revestimento (kV)
        limites_revestimento = {
            "polietileno_extrudado": 5.0,  # kV
            "fbe": 3.0,                    # kV  
            "fitas_plasticas": 2.0         # kV
        }
        
        tipo_revestimento = "polietileno_extrudado"  # Assumindo PE
        limite = limites_revestimento[tipo_revestimento]
        
        return {
            "tensao_kv": magnitude_tensao / 1000,
            "limite_kv": limite,
            "seguro": magnitude_tensao / 1000 <= limite,
            "fator_seguranca": limite / (magnitude_tensao / 1000)
        }

    def calcular_densidade_corrente_ac(self, tensao_induzida: complex, 
                                     raio_defeito: float = 0.001) -> float:
        """
        Calcula densidade de corrente AC para análise de corrosão
        Equação (2.7) da dissertação
        """
        magnitude_tensao = abs(tensao_induzida)
        rho_solo = self.lt.solo.resistividade_equivalente_uniforme()
        
        # Densidade de corrente através de defeito cilíndrico
        J = magnitude_tensao / (rho_solo * (0.3927 * raio_defeito + self.duto.espessura_revestimento))
        
        return J  # A/m²

    def avaliar_risco_corrosao_ac(self, densidade_corrente: float) -> str:
        """Classifica risco de corrosão AC conforme NACE TG-327"""
        if densidade_corrente < 20e-3:  # < 20 mA/m²
            return "Baixo"
        elif densidade_corrente < 100e-3:  # < 100 mA/m²
            return "Moderado"
        else:
            return "Muito Alto"

    def gerar_relatorio_analise(self, comprimento_exposicao: float = 1.0) -> dict:
        """Gera relatório completo da análise de interferência"""
        # Cálculos principais
        tensao_induzida = self.calcular_tensao_induzida_total(comprimento_exposicao)
        seguranca_revestimento = self.avaliar_seguranca_revestimento(tensao_induzida)
        densidade_corrente = self.calcular_densidade_corrente_ac(tensao_induzida)
        risco_corrosao = self.avaliar_risco_corrosao_ac(densidade_corrente)
        
        # Características do duto
        Z_proprio = self.duto.calcular_impedancia_propria(self.lt.solo)
        Y_shunt = self.duto.calcular_admitancia_shunt()
        Z_carac = self.duto.calcular_impedancia_caracteristica(self.lt.solo)
        gamma = self.duto.calcular_constante_propagacao(self.lt.solo)
        
        return {
            "tensao_induzida": {
                "magnitude_v": abs(tensao_induzida),
                "fase_graus": np.degrees(np.angle(tensao_induzida)),
                "complexo": tensao_induzida
            },
            "parametros_duto": {
                "impedancia_propria_ohm_m": Z_proprio,
                "admitancia_siemens_m": Y_shunt,
                "impedancia_caracteristica_ohm": Z_carac,
                "constante_propagacao_m_1": gamma,
                "comprimento_caracteristico_m": 1 / gamma.real if gamma.real > 0 else np.inf
            },
            "avaliacao_seguranca": {
                "revestimento": seguranca_revestimento,
                "densidade_corrente_ma_m2": densidade_corrente * 1000,  # mA/m²
                "risco_corrosao": risco_corrosao
            },
            "solo": {
                "resistividade_equivalente_ohm_m": self.lt.solo.resistividade_equivalente_uniforme()
            }
        }

def exemplo_uso():
    """Exemplo de uso do sistema aprimorado"""
    
    # Configuração do solo (duas camadas)
    parametros_solo = ParametrosSolo(
        resistividade_camada1=100.0,    # Ω.m
        resistividade_camada2=1000.0,   # Ω.m
        espessura_camada1=2.0,          # m
        permissividade_relativa=10.0
    )
    solo = Solo(parametros_solo)
    
    # Configuração do duto (subterrâneo a 1.5m)
    coord_duto = Coordenadas(x=0, y=0, z=-1.5)
    duto = Duto(
        coordenadas=coord_duto,
        diametro=0.219,                 # 8" em metros
        espessura_parede=0.0065,        # m
        espessura_revestimento=0.003,   # 3mm
        material="aco"
    )
    
    # Configuração da linha de transmissão (configuração típica 138kV)
    cabos = [
        Cabo(Coordenadas(-3.3, 15, 0), 529+0j, 0.01257, "fase"),  # Fase A
        Cabo(Coordenadas(0, 19, 0), 529*np.exp(1j*np.radians(-120)), 0.01257, "fase"),  # Fase B  
        Cabo(Coordenadas(3.3, 23, 0), 529*np.exp(1j*np.radians(120)), 0.01257, "fase"),  # Fase C
        Cabo(Coordenadas(0, 26.7, 0), 0+0j, 0.004572, "guarda")   # Cabo guarda
    ]
    lt = LinhaTransmissao(cabos, solo)
    
    # Análise de interferência
    analise = AnaliseInterferencia(lt, duto)
    relatorio = analise.gerar_relatorio_analise(comprimento_exposicao=1000.0)  # 1 km
    
    return relatorio

if __name__ == "__main__":
    # Executar exemplo
    resultado = exemplo_uso()
    
    print("=== RELATÓRIO DE ANÁLISE DE INTERFERÊNCIA ELETROMAGNÉTICA ===\n")
    
    print("1. TENSÃO INDUZIDA:")
    tensao = resultado["tensao_induzida"]
    print(f"   Magnitude: {tensao['magnitude_v']:.2e} V")
    print(f"   Fase: {tensao['fase_graus']:.1f}°")
    
    print("\n2. PARÂMETROS DO DUTO:")
    params = resultado["parametros_duto"]
    print(f"   Impedância Própria: {abs(params['impedancia_propria_ohm_m']):.2e} Ω/m")
    print(f"   Impedância Característica: {abs(params['impedancia_caracteristica_ohm']):.2e} Ω")
    print(f"   Comprimento Característico: {params['comprimento_caracteristico_m']:.1f} m")
    
    print("\n3. AVALIAÇÃO DE SEGURANÇA:")
    seguranca = resultado["avaliacao_seguranca"]
    print(f"   Tensão no Revestimento: {seguranca['revestimento']['tensao_kv']:.2f} kV")
    print(f"   Limite Permitido: {seguranca['revestimento']['limite_kv']:.1f} kV")
    print(f"   Status: {'SEGURO' if seguranca['revestimento']['seguro'] else 'CRÍTICO'}")
    print(f"   Densidade de Corrente AC: {seguranca['densidade_corrente_ma_m2']:.1f} mA/m²")
    print(f"   Risco de Corrosão: {seguranca['risco_corrosao']}")
    
    print(f"\n4. SOLO:")
    print(f"   Resistividade Equivalente: {resultado['solo']['resistividade_equivalente_ohm_m']:.1f} Ω.m")