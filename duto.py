import numpy as np
import constants

class solo:
    def __init__(self,resistividade):
        self.resistividade = resistividade

class coordenadas:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class cabo:
    def __init__(self, coordenadas, corrente):
        self.coordenadas = coordenadas
        self.corrente = corrente

class linha_transmissao:
    def __init__(self, cabos, solo):
        self.cabos = cabos
        self.solo = solo

    def calcular_distancia_duto(self, duto):
        distancias = []
        for cabo in self.cabos:
            dist = np.sqrt((cabo.coordenadas.x - duto.coordenadas.x)**2 + (cabo.coordenadas.y - duto.coordenadas.y)**2)
            distancias.append(dist)
        return distancias

    def calcular_impedancia_mutua(self, duto):
        impedancias_mutuas = []
        for i, cabo in enumerate(self.cabos):
            dist = self.calcular_distancia_duto(duto)[i]
            # Carson-Clem formula
            real = (constants.MU_0 * constants.w / 8)
            imaginario = (constants.MU_0 * constants.w / (2 * np.pi)) * np.log(1 / (dist * np.sqrt(constants.w * constants.MU_0 / self.solo.resistividade)))
            impedancias_mutuas.append(real + 1j * imaginario)
        return impedancias_mutuas

class duto:

    def __init__(self,diametro,solo, espessura_cobertura, coordenadas):
        self.coordenadas = coordenadas
        self.resistividade = 0.17e-6 # ohm/m
        self.permeabilidade = 300 
        self.permeabilidade_cobertura = 1e7
        self.EPSILON = 5
        self.diametro = diametro
        self.espessura_cobertura = espessura_cobertura
        self.impedancia_propria = self.calcular_impdancia_propria()
        self.adimitancia  = self.calcular_adimetancia()
        self.resistencia_cobertura  = self.espessura_cobertura * self.espessura_cobertura
        self.impedancia_caracteristica = self.calcular_impedancia_caracteristica()
        self.constante_propagacao = self.calcular_constante_propagacao()
        self.comprimento_caracteristico = self.calcular_comprimento_caracteristico()

        
    def calcular_impdancia_propria(self):
        a = np.sqrt(self.resistividade * self.permeabilidade * constants.MU_0 * constants.w) / (np.pi * self.diametro * np.sqrt(2))
        r_duto = a + constants.MU_0 * constants.w/8
        imaginario_duto = a + (constants.MU_0 * constants.w / (2*np.pi)) * np.log(3.7 * np.sqrt(self.resistividade * (constants.w**-1)*(constants.MU_0**-1) )/ self.diametro)
        return r_duto + 1j * imaginario_duto
    
    def calcular_adimetancia(self):
        real = np.pi * self.diametro / (self.permeabilidade_cobertura * self.espessura_cobertura)
        imaginario = constants.w * constants.EPSILON_0 * self.EPSILON * np.pi * self.diametro / self.espessura_cobertura
        return real + 1j * imaginario
    
    def calcular_impedancia_caracteristica(self):
        return np.sqrt(self.impedancia_propria / self.adimitancia)
    
    def calcular_constante_propagacao(self):
        return np.sqrt(self.impedancia_propria * self.adimitancia)
    
    def calcular_comprimento_caracteristico(self):
        return 1/ self.constante_propagacao.real

    def calcular_tensao_induzida(self, lt):
        tensao_total_induzida = 0
        impedancias_mutuas = lt.calcular_impedancia_mutua(self)
        for i, cabo in enumerate(lt.cabos):
            tensao_total_induzida += impedancias_mutuas[i] * cabo.corrente
        return tensao_total_induzida
    
    def imprimir_caracteristicas(self, lt):
        print("\n--- Características do Duto ---")
        print(f"Diâmetro: {self.diametro:.4f} m")
        print(f"Espessura da Cobertura: {self.espessura_cobertura:.4f} m")
        print(f"Resistividade do Duto: {self.resistividade:.2e} Ohm/m")
        print(f"Permeabilidade do Duto: {self.permeabilidade}")
        print(f"Permeabilidade da Cobertura: {self.permeabilidade_cobertura:.2e}")
        print(f"Permissividade Relativa (EPSILON): {self.EPSILON}")
        print(f"Resistividade do Solo: {lt.solo.resistividade:.2e} Ohm.m")
        print(f"Resistência da Cobertura (verificar fórmula): {self.resistencia_cobertura:.4f} Ohm (possivelmente)")
        print(f"")
        print(f"Impedância Própria (Zp): {self.impedancia_propria:.4e} Ohm")
        print(f"  (Real: {self.impedancia_propria.real:.4e}, Imaginária: {self.impedancia_propria.imag:.4e})")
        print(f"Admitância (Y): {self.adimitancia:.4e} Siemens")
        print(f"  (Real: {self.adimitancia.real:.4e}, Imaginária: {self.adimitancia.imag:.4e})")
        print(f"")
        print(f"Impedância Característica (Zc): {self.impedancia_caracteristica:.4e} Ohm")
        print(f"  (Magnitude: {np.abs(self.impedancia_caracteristica):.4e}, Ângulo: {np.degrees(np.angle(self.impedancia_caracteristica)):.2f}°)")
        print(f"Constante de Propagação (gamma): {self.constante_propagacao:.4e} 1/m")
        print(f"  (Alpha (Atenuação): {self.constante_propagacao.real:.4e}, Beta (Fase): {self.constante_propagacao.imag:.4e})")
        print(f"Comprimento Característico (1/Alpha): {self.comprimento_caracteristico:.4f} m")
        print("-----------------------------\n")

        # Calcular e imprimir impedâncias mútuas
        impedancias_mutuas = lt.calcular_impedancia_mutua(self)
        print("\n--- Impedâncias Mútuas (Duto-Cabos) ---")
        for i, zm in enumerate(impedancias_mutuas):
            print(f"Impedância Mútua com Cabo {i+1}: {zm:.4e} Ohm/m")
            print(f"  (Real: {zm.real:.4e}, Imaginária: {zm.imag:.4e})")
        print("----------------------------------------\n")

        # Calcular e imprimir tensão induzida
        tensao_induzida = self.calcular_tensao_induzida(lt)
        print("\n--- Tensão Induzida no Duto ---")
        print(f"Tensão Induzida Total: {tensao_induzida:.4e} V/m")
        print(f"  (Magnitude: {np.abs(tensao_induzida):.4e}, Ângulo: {np.degrees(np.angle(tensao_induzida)):.2f}°)")
        print("---------------------------------\n")