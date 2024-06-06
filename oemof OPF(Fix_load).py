
### relevant imports
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# oemof-solph needs to be installed (in respective py-venv)
import oemof.solph as solph
from oemof.tools import economics
from oemof.solph import *
from oemof.solph.buses.experimental import ElectricalBus
from oemof.solph.components import *
from oemof.solph.flows import Flow


### setup energysystem
"""
Example hyBit-EnergySystem

Pv (Source)                     ->  |                      |                          
wind (Source)                   ->  |->  (Transformer)  -> |  --> Load_A, fix (Sink)
Hydro (source)                  ->  |                      | <--> (Storage)                         


"""

###############################################################

print("-- Setup EnergySystem --")

### EnergySystem
my_index = pd.date_range('1/1/2023', periods=8760, freq='H')
energysystem = solph.EnergySystem(timeindex = my_index)

### Create and add buses to the energysystem
        
bus = solph.buses.Bus(label="electricity",)
bus2 = solph.buses.Bus(label="electricity_l")

energysystem.add( bus,bus2)
#investment of storage
invst= economics.annuity(500, 20, 0.05)

### Add Sources

energysystem.add(
    solph.components.Source(
        label="Wind",
        outputs={
            bus: solph.flows.Flow(
                nominal_value = 550,
                min=0.182,                            #Minimum power flow in MW
                max=1,                                #Maximum power flow in MW
                variable_costs= 568.921562,           # Per unit cost
            )
         },
    )
)
        
energysystem.add(
    solph.components.Source(
        label="PV",
        outputs={
            bus: solph.flows.Flow(
                    nominal_value= 470,
                    min=0.171,
                    max=1,
                    variable_costs=317.85194,
                                        
            )  
        },
    )
)
        
energysystem.add(
    solph.components.Source(
        label="Hydro", 
        outputs={ 
            bus: solph.flows.Flow(
                nominal_value = 200,
                min=0.25,
                max=1,
                variable_costs=85.97482,
            )},
     )
)
        
    

### Sinks
# Load | fixed
energysystem.add(
    solph.components.Sink(
        label="Load",
        inputs={
            bus2: solph.flows.Flow(   
                nominal_value= 1200,
                        
                        
            )
        },
    )
)
energysystem.add(
    solph.components.GenericStorage(
            label='storage',
            inputs={bus2: solph.flows.Flow(nominal_value= 1)},
            outputs={bus2: solph.flows.Flow()},
                    loss_rate=0.001, 
                    initial_storage_level= 0.9,
                    nominal_storage_capacity= 20,
                    inflow_conversion_factor=0.98, outflow_conversion_factor=0.99,
                    
                    
                    ),
)

energysystem.add(
    solph.components.Converter(
        label="Transformer",
        inputs={bus: solph.flows.Flow()},
        outputs= {bus2: solph.flows.Flow()},
        conversion_factors={bus2: 0.96},
    )
)

print(" -- Finished setup --")
model = solph.Model(energysystem)
solution= model.solve(solver='gurobi',solve_kwargs={'tee': True})     # "cbc"/ "gurobi"
print(solution)

results = processing.results(model)
column_name = (('your_storage_label', 'True'), 'storage_content')
SC = views.node(results,'storage')
print(SC)
