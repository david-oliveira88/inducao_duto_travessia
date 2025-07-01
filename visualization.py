import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from typing import List, Tuple
import seaborn as sns

# Definir estilo dos gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class VisualizadorEMI:
    def __init__(self, analise_interferencia):
        self.analise = analise_interferencia
        self.lt = analise_interferencia.lt
        self.duto = analise_interferencia.duto
        
    def plotar_configuracao_geometrica(self, figsize=(12, 8)):
        """Plota configuração geométrica da LT e duto"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Vista lateral (X-Z)
        ax1.set_title('Vista Lateral (X-Z)', fontsize=14, fontweight='bold')
        
        # Plotar superfície do solo
        x_range = np.linspace(-20, 20, 100)
        ax1.plot(x_range, np.zeros_like(x_range), 'k-', linewidth=2, label='Superfície do Solo')
        ax1.fill_between(x_range, -10, 0, alpha=0.3, color='brown', label='Solo')
        
        # Plotar cabos da LT
        for i, cabo in enumerate(self.lt.cabos):
            cor = 'red' if cabo.tipo == 'fase' else 'blue'
            marker = 'o' if cabo.tipo == 'fase' else '^'
            ax1.plot(cabo.coordenadas.x, cabo.coordenadas.z, marker, 
                    markersize=8, color=cor, label=f'Cabo {cabo.tipo} {i+1}')
        
        # Plotar duto
        ax1.plot(self.duto.coordenadas.x, self.duto.coordenadas.z, 's', 
                markersize=10, color='green', label='Duto')
        
        ax1.set_xlabel('Distância X (m)')
        ax1.set_ylabel('Altura/Profundidade Z (m)')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_aspect('equal')
        
        # Vista superior (X-Y)
        ax2.set_title('Vista Superior (X-Y)', fontsize=14, fontweight='bold')
        
        # Plotar cabos
        for i, cabo in enumerate(self.lt.cabos):
            cor = 'red' if cabo.tipo == 'fase' else 'blue'
            marker = 'o' if cabo.tipo == 'fase' else '^'
            ax2.plot(cabo.coordenadas.x, cabo.coordenadas.y, marker, 
                    markersize=8, color=cor, label=f'Cabo {cabo.tipo} {i+1}')
        
        # Plotar duto
        ax2.plot(self.duto.coordenadas.x, self.duto.coordenadas.y, 's', 
                markersize=10, color='green', label='Duto')
        
        # Plotar linhas de distância
        for cabo in self.lt.cabos:
            ax2.plot([cabo.coordenadas.x, self.duto.coordenadas.x],
                    [cabo.coordenadas.y, self.duto.coordenadas.y],
                    '--', alpha=0.5, color='gray')
        
        ax2.set_xlabel('Distância X (m)')
        ax2.set_ylabel('Distância Y (m)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.set_aspect('equal')
        
        plt.tight_layout()
        return fig

    def plotar_perfil_tensao_vs_distancia(self, distancias_range=None, figsize=(10, 6)):
        """Plota perfil de tensão induzida vs distância entre LT e duto"""
        if distancias_range is None:
            distancias_range = np.linspace(5, 100, 50)
        
        tensoes = []
        coord_original = self.duto.coordenadas
        
        for dist in distancias_range:
            # Mover duto para nova posição
            self.duto.coordenadas = type(coord_original)(
                x=dist, y=coord_original.y, z=coord_original.z
            )
            
            # Calcular tensão induzida
            tensao = self.analise.calcular_tensao_induzida_total(1000.0)  # 1 km
            tensoes.append(abs(tensao))
        
        # Restaurar coordenadas originais
        self.duto.coordenadas = coord_original
        
        # Plotar
        fig, ax = plt.subplots(figsize=figsize)
        ax.loglog(distancias_range, tensoes, 'o-', linewidth=2, markersize=6)
        ax.set_xlabel('Distância LT-Duto (m)')
        ax.set_ylabel('Tensão Induzida (V)')
        ax.set_title('Tensão Induzida vs Distância\n(Comprimento de exposição: 1 km)', 
                    fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Adicionar linha de limite de segurança
        limite_seguranca = 5000  # 5 kV para PE
        ax.axhline(y=limite_seguranca, color='red', linestyle='--', 
                  label=f'Limite Revestimento ({limite_seguranca/1000:.0f} kV)')
        ax.legend()
        
        plt.tight_layout()
        return fig, (distancias_range, tensoes)

    def plotar_espectro_frequencia(self, frequencias=None, figsize=(10, 6)):
        """Analisa resposta em frequência do sistema"""
        if frequencias is None:
            frequencias = np.logspace(0, 3, 50)  # 1 Hz a 1 kHz
        
        tensoes_magnitude = []
        tensoes_fase = []
        
        # Salvar frequência original
        from emi_system import OMEGA
        omega_original = OMEGA
        
        for freq in frequencias:
            # Atualizar frequência global (simulação - em implementação real seria diferente)
            import emi_system
            emi_system.OMEGA = 2 * np.pi * freq
            
            # Recalcular tensão induzida
            tensao = self.analise.calcular_tensao_induzida_total(1000.0)
            tensoes_magnitude.append(abs(tensao))
            tensoes_fase.append(np.degrees(np.angle(tensao)))
        
        # Restaurar frequência original
        import emi_system
        emi_system.OMEGA = omega_original
        
        # Plotar
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        # Magnitude
        ax1.loglog(frequencias, tensoes_magnitude, 'b-', linewidth=2)
        ax1.set_ylabel('Magnitude (V)')
        ax1.set_title('Resposta em Frequência do Sistema', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=60, color='red', linestyle='--', label='60 Hz')
        ax1.legend()
        
        # Fase
        ax2.semilogx(frequencias, tensoes_fase, 'r-', linewidth=2)
        ax2.set_xlabel('Frequência (Hz)')
        ax2.set_ylabel('Fase (°)')
        ax2.grid(True, alpha=0.3)
        ax2.axvline(x=60, color='red', linestyle='--', label='60 Hz')
        ax2.legend()
        
        plt.tight_layout()
        return fig

    def plotar_analise_parametros_solo(self, rho1_range=None, rho2_range=None, figsize=(12, 8)):
        """Analisa sensibilidade aos parâmetros do solo"""
        if rho1_range is None:
            rho1_range = np.logspace(1, 3, 20)  # 10 a 1000 Ω.m
        if rho2_range is None:
            rho2_range = np.logspace(2, 4, 20)  # 100 a 10000 Ω.m
        
        # Criar malha de parâmetros
        RHO1, RHO2 = np.meshgrid(rho1_range, rho2_range)
        tensoes_malha = np.zeros_like(RHO1)
        
        # Salvar parâmetros originais do solo
        params_originais = self.lt.solo.parametros
        
        # Calcular tensões para cada combinação
        for i in range(len(rho1_range)):
            for j in range(len(rho2_range)):
                # Atualizar parâmetros do solo
                self.lt.solo.parametros.resistividade_camada1 = RHO1[j, i]
                self.lt.solo.parametros.resistividade_camada2 = RHO2[j, i]
                
                # Calcular tensão
                tensao = self.analise.calcular_tensao_induzida_total(1000.0)
                tensoes_malha[j, i] = abs(tensao)
        
        # Restaurar parâmetros originais
        self.lt.solo.parametros = params_originais
        
        # Plotar mapa de calor
        fig, ax = plt.subplots(figsize=figsize)
        
        # Converter para escala logarítmica para visualização
        im = ax.contourf(np.log10(RHO1), np.log10(RHO2), 
                        np.log10(tensoes_malha), levels=20, cmap='viridis')
        
        # Configurar eixos
        ax.set_xlabel('log₁₀(ρ₁) [Ω.m]')
        ax.set_ylabel('log₁₀(ρ₂) [Ω.m]')
        ax.set_title('Tensão Induzida vs Parâmetros do Solo\n(Comprimento: 1 km)', 
                    fontweight='bold')
        
        # Adicionar barra de cores
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('log₁₀(Tensão Induzida) [V]')
        
        # Adicionar linhas de contorno
        contours = ax.contour(np.log10(RHO1), np.log10(RHO2), 
                             np.log10(tensoes_malha), levels=10, colors='white', alpha=0.5)
        ax.clabel(contours, inline=True, fontsize=8, fmt='%.1f')
        
        plt.tight_layout()
        return fig

    def plotar_dashboard_completo(self, figsize=(16, 12)):
        """Cria dashboard completo com múltiplas análises"""
        fig = plt.figure(figsize=figsize)
        
        # Configuração geométrica (subplot 1)
        ax1 = plt.subplot(2, 3, 1)
        self._plot_configuracao_simples(ax1)
        
        # Tensão vs distância (subplot 2)
        ax2 = plt.subplot(2, 3, 2)
        self._plot_tensao_distancia_simples(ax2)
        
        # Parâmetros do duto (subplot 3)
        ax3 = plt.subplot(2, 3, 3)
        self._plot_parametros_duto(ax3)
        
        # Análise de segurança (subplot 4)
        ax4 = plt.subplot(2, 3, 4)
        self._plot_analise_seguranca(ax4)
        
        # Contribuições por cabo (subplot 5)
        ax5 = plt.subplot(2, 3, 5)
        self._plot_contribuicoes_cabos(ax5)
        
        # Resumo numérico (subplot 6)
        ax6 = plt.subplot(2, 3, 6)
        self._plot_resumo_numerico(ax6)
        
        plt.suptitle('Dashboard de Análise de Interferência Eletromagnética', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        return fig

    def _plot_configuracao_simples(self, ax):
        """Plot simplificado da configuração"""
        ax.set_title('Configuração', fontweight='bold')
        
        # Solo
        ax.axhline(y=0, color='brown', linewidth=3, label='Solo')
        
        # Cabos
        for i, cabo in enumerate(self.lt.cabos):
            cor = 'red' if cabo.tipo == 'fase' else 'blue'
            ax.plot(cabo.coordenadas.x, cabo.coordenadas.z, 'o', 
                   color=cor, markersize=8)
        
        # Duto
        ax.plot(self.duto.coordenadas.x, self.duto.coordenadas.z, 's', 
               color='green', markersize=10)
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Z (m)')
        ax.grid(True, alpha=0.3)

    def _plot_tensao_distancia_simples(self, ax):
        """Plot simplificado tensão vs distância"""
        distancias = np.linspace(10, 100, 20)
        tensoes = []
        
        coord_orig = self.duto.coordenadas
        for dist in distancias:
            self.duto.coordenadas = type(coord_orig)(
                x=dist, y=coord_orig.y, z=coord_orig.z
            )
            tensao = abs(self.analise.calcular_tensao_induzida_total(1000.0))
            tensoes.append(tensao)
        self.duto.coordenadas = coord_orig
        
        ax.loglog(distancias, tensoes, 'o-')
        ax.set_title('Tensão vs Distância', fontweight='bold')
        ax.set_xlabel('Distância (m)')
        ax.set_ylabel('Tensão (V)')
        ax.grid(True, alpha=0.3)

    def _plot_parametros_duto(self, ax):
        """Plot dos parâmetros principais do duto"""
        relatorio = self.analise.gerar_relatorio_analise(1000.0)
        params = relatorio['parametros_duto']
        
        # Dados para o gráfico de barras
        labels = ['|Z₀|', '|Y|×10⁶', '|Zc|/100', 'γᵣ×10³']
        values = [
            abs(params['impedancia_propria_ohm_m']),
            abs(params['admitancia_siemens_m']) * 1e6,
            abs(params['impedancia_caracteristica_ohm']) / 100,
            params['constante_propagacao_m_1'].real * 1000
        ]
        
        bars = ax.bar(labels, values, color=['blue', 'green', 'orange', 'red'])
        ax.set_title('Parâmetros do Duto', fontweight='bold')
        ax.set_ylabel('Magnitude (normalizadas)')
        
        # Adicionar valores nas barras
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.2f}', ha='center', va='bottom')

    def _plot_analise_seguranca(self, ax):
        """Plot da análise de segurança"""
        relatorio = self.analise.gerar_relatorio_analise(1000.0)
        
        tensao_kv = relatorio['avaliacao_seguranca']['revestimento']['tensao_kv']
        limite_kv = relatorio['avaliacao_seguranca']['revestimento']['limite_kv']
        densidade_ma = relatorio['avaliacao_seguranca']['densidade_corrente_ma_m2']
        
        # Gráfico de barras para indicadores de segurança
        categorias = ['Tensão\nRevestimento', 'Densidade\nCorrente AC']
        valores_atuais = [tensao_kv, densidade_ma / 20]  # Normalizar densidade
        limites = [limite_kv, 1.0]  # Limite de 20 mA/m² normalizado
        
        x = np.arange(len(categorias))
        width = 0.35
        
        ax.bar(x - width/2, valores_atuais, width, label='Atual', color='red')
        ax.bar(x + width/2, limites, width, label='Limite', color='green')
        
        ax.set_title('Análise de Segurança', fontweight='bold')
        ax.set_ylabel('Valores (normalizados)')
        ax.set_xticks(x)
        ax.set_xticklabels(categorias)
        ax.legend()

    def _plot_contribuicoes_cabos(self, ax):
        """Plot das contribuições individuais dos cabos"""
        contribuicoes = []
        labels = []
        
        for i, cabo in enumerate(self.lt.cabos):
            Z_mutua = self.lt.calcular_impedancia_mutua_carson_fechada(cabo, self.duto)
            tensao_contrib = abs(Z_mutua * cabo.corrente * 1000)  # 1 km
            contribuicoes.append(tensao_contrib)
            labels.append(f'{cabo.tipo.title()}\n{i+1}')
        
        wedges, texts, autotexts = ax.pie(contribuicoes, labels=labels, autopct='%1.1f%%')
        ax.set_title('Contribuições por Cabo', fontweight='bold')

    def _plot_resumo_numerico(self, ax):
        """Resumo numérico dos principais resultados"""
        relatorio = self.analise.gerar_relatorio_analise(1000.0)
        
        # Preparar texto do resumo
        texto_resumo = f"""RESUMO EXECUTIVO

Tensão Induzida:
• Magnitude: {relatorio['tensao_induzida']['magnitude_v']/1000:.1f} kV
• Fase: {relatorio['tensao_induzida']['fase_graus']:.0f}°

Segurança:
• Revestimento: {'OK' if relatorio['avaliacao_seguranca']['revestimento']['seguro'] else 'CRÍTICO'}
• Corrosão AC: {relatorio['avaliacao_seguranca']['risco_corrosao']}
• Densidade J: {relatorio['avaliacao_seguranca']['densidade_corrente_ma_m2']:.1f} mA/m²

Solo:
• ρ equiv: {relatorio['solo']['resistividade_equivalente_ohm_m']:.0f} Ω.m

Duto:
• Lc: {relatorio['parametros_duto']['comprimento_caracteristico_m']:.0f} m
"""
        
        ax.text(0.05, 0.95, texto_resumo, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

def exemplo_visualizacao():
    """Exemplo de uso do sistema de visualização"""
    from emi_system import *
    
    # Configurar sistema
    parametros_solo = ParametrosSolo(100.0, 1000.0, 2.0, 10.0)
    solo = Solo(parametros_solo)
    
    coord_duto = Coordenadas(x=0, y=0, z=-1.5)
    duto = Duto(coord_duto, 0.219, 0.0065, 0.003, "aco")
    
    cabos = [
        Cabo(Coordenadas(-3.3, 15, 0), 529+0j, 0.01257, "fase"),
        Cabo(Coordenadas(0, 19, 0), 529*np.exp(1j*np.radians(-120)), 0.01257, "fase"),
        Cabo(Coordenadas(3.3, 23, 0), 529*np.exp(1j*np.radians(120)), 0.01257, "fase"),
        Cabo(Coordenadas(0, 26.7, 0), 0+0j, 0.004572, "guarda")
    ]
    lt = LinhaTransmissao(cabos, solo)
    
    # Criar análise e visualizador
    analise = AnaliseInterferencia(lt, duto)
    vis = VisualizadorEMI(analise)
    
    # Gerar gráficos
    fig1 = vis.plotar_configuracao_geometrica()
    fig2 = vis.plotar_dashboard_completo()
    
    plt.show()
    
    return vis

if __name__ == "__main__":
    exemplo_visualizacao()