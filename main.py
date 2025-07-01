from emi_system import *
from visualization import VisualizadorEMI
import matplotlib.pyplot as plt

def main():
    print("=== SISTEMA AVANÇADO DE ANÁLISE EMI ===\n")
    
    # Configuração do sistema
    parametros_solo = ParametrosSolo(
        resistividade_camada1=100.0,
        resistividade_camada2=1000.0,
        espessura_camada1=2.0,
        permissividade_relativa=10.0
    )
    solo = Solo(parametros_solo)
    
    # Duto subterrâneo
    coord_duto = Coordenadas(x=0, y=0, z=-1.5)
    duto = Duto(
        coordenadas=coord_duto,
        diametro=0.219,
        espessura_parede=0.0065,
        espessura_revestimento=0.003,
        material="aco"
    )
    
    # Linha de transmissão 138kV
    cabos = [
        Cabo(Coordenadas(-3.3, 15, 0), 529+0j, 0.01257, "fase"),
        Cabo(Coordenadas(0, 19, 0), 529*np.exp(1j*np.radians(-120)), 0.01257, "fase"),
        Cabo(Coordenadas(3.3, 23, 0), 529*np.exp(1j*np.radians(120)), 0.01257, "fase"),
        Cabo(Coordenadas(0, 26.7, 0), 0+0j, 0.004572, "guarda")
    ]
    lt = LinhaTransmissao(cabos, solo)
    
    # Análise de interferência
    analise = AnaliseInterferencia(lt, duto)
    
    # Gerar relatório
    relatorio = analise.gerar_relatorio_analise(1000.0)
    
    # Imprimir resultados
    print("1. TENSÃO INDUZIDA:")
    tensao = relatorio["tensao_induzida"]
    print(f"   Magnitude: {tensao['magnitude_v']:.2e} V")
    print(f"   Fase: {tensao['fase_graus']:.1f}°")
    
    print("\n2. PARÂMETROS DO DUTO:")
    params = relatorio["parametros_duto"]
    print(f"   Impedância Própria: {abs(params['impedancia_propria_ohm_m']):.2e} Ω/m")
    print(f"   Impedância Característica: {abs(params['impedancia_caracteristica_ohm']):.2e} Ω")
    print(f"   Comprimento Característico: {params['comprimento_caracteristico_m']:.1f} m")
    
    print("\n3. AVALIAÇÃO DE SEGURANÇA:")
    seguranca = relatorio["avaliacao_seguranca"]
    print(f"   Tensão no Revestimento: {seguranca['revestimento']['tensao_kv']:.2f} kV")
    print(f"   Status: {'SEGURO' if seguranca['revestimento']['seguro'] else 'CRÍTICO'}")
    print(f"   Densidade de Corrente AC: {seguranca['densidade_corrente_ma_m2']:.1f} mA/m²")
    print(f"   Risco de Corrosão: {seguranca['risco_corrosao']}")
    
    # Visualizações
    vis = VisualizadorEMI(analise)
    
    # Dashboard completo
    fig_dashboard = vis.plotar_dashboard_completo()
    plt.savefig('dashboard_emi.png', dpi=300, bbox_inches='tight')
    
    # Configuração geométrica
    fig_config = vis.plotar_configuracao_geometrica()
    plt.savefig('configuracao_geometrica.png', dpi=300, bbox_inches='tight')
    
    # Perfil tensão vs distância
    fig_perfil, dados = vis.plotar_perfil_tensao_vs_distancia()
    plt.savefig('perfil_tensao_distancia.png', dpi=300, bbox_inches='tight')
    
    print(f"\n4. ARQUIVOS GERADOS:")
    print("   - dashboard_emi.png")
    print("   - configuracao_geometrica.png") 
    print("   - perfil_tensao_distancia.png")
    
    plt.show()

if __name__ == "__main__":
    main()
