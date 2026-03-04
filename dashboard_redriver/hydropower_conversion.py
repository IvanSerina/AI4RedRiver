import pandas as pd
import numpy as np


def convert_hydropower_to_release(energy_demand):
    energy_demand = np.array(energy_demand)
    converted_energy = np.zeros(len(energy_demand))
    for i in range(len(energy_demand)):
        demand = energy_demand[i]
        for j in range(1, 17):
            release = 147.5 * j
            power = _evaluate_hydropower(release)
            if power >= demand:
                converted_energy[i] = release
                break
    return converted_energy

def _evaluate_hydropower(release):
    """
    Evaluate the hydropower generation based on the release.
    """
    # Constants
    
    # for h_downstream
    c_1 = 2.0877e-3
    c_2 = -1.3637e-7
    c_3 = 3.6636e-12
    c_0 = 11.660
    H_UP = 90
    
    # for efficiency
    a = -7.476e-4
    b = 0.137
    c = 3.029
    
    # for power
    phi = 2.27e-6
    g = 9.81
    gamma = 1000
    
    # Calculate h_downstream
    h_downstream = c_3 * release**3 + c_2 * release**2 + c_1 * release + c_0
    
    H = H_UP - h_downstream
    
    eta = a * H**2 + b * H + c
    
    power = phi * g * gamma * eta * release
    
    power = power * 100
    
    return power