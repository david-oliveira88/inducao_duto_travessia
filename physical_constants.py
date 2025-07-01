import numpy as np

# Constantes físicas
MU_0 = 4 * np.pi * 1e-7      # Permeabilidade do vácuo (H/m)
EPSILON_0 = 8.85e-12         # Permissividade do vácuo (F/m)
K_0 = 1 / (2 * np.pi * EPSILON_0)  # Fator para cálculos capacitivos (m/F)
w = 2*np.pi*60          # Frequência angular (rad/s)