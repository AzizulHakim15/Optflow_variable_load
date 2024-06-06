### relevant imports
import os
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

# oemof-solph needs to be installed (in respective py-venv)
import oemof.solph as solph
from oemof.tools import economics
from oemof.solph import *
from oemof.solph.buses.experimental import ElectricalBus
from oemof.solph.components import Sink
from oemof.solph.components import Source
from oemof.solph.flows import Flow


### setup energysystem

# Example Non-linear EnergySystemy

# wind (Source)                   ->  |->  (Transformer1)  -> |<--> (Storage) 
# Pv (Source)                     ->  |->  (Transformer2)  -> |-> Load_A, veriable (Sink)               
#                                         Thermal(Source)  -> |----------> (Transformer3) ---------->| 
#                                                                                                    | -> Load_B, veriable(Sink)

###############################################################

print("-- Setup EnergySystem --")

### EnergySystem
my_index = pd.date_range('1/1/2023', periods=8760, freq='H')
energysystem = solph.EnergySystem(timeindex = my_index)

### Create and add buses to the energysystem
        
bus_wind = solph.buses.Bus(label="Wind_bus")
bus_PV = solph.buses.Bus(label="PV_bus")
bus_main = solph.buses.Bus(label="Common_Bus")
bus_load = solph.buses.Bus(label="Load_bus")

energysystem.add( bus_wind,bus_PV,bus_main,bus_load)
#investment of storage
invst= economics.annuity(500, 20, 0.05)

### Add Sources

energysystem.add(
    solph.components.Source(
        label="Wind",
        outputs={
            bus_wind: solph.flows.Flow(
                nominal_value = 550e6,
                min=0.182,                            #Minimum power flow in MW
                max=1,                                #Maximum power flow in MW
                variable_costs= 568.921562,           # Per unit cost
                #variable_costs= 561+ 7.92* Unit_1_gen + 0.001562 * Unit_1_gen * Unit_1_gen,
            )
         },
    )
)
        
energysystem.add(
    solph.components.Source(
        label="PV",
        outputs={
            bus_PV: solph.flows.Flow(
                    nominal_value= 470e6,
                    min=0.171,
                    max= 1,
                    variable_costs=317.85194,
                                        
            )  
        },
    )
)
        
energysystem.add(
    solph.components.Source(
        label="Thermal", 
        outputs={ 
            bus_main: solph.flows.Flow(
                nominal_value = 280e6,
                min=0.25,
                max= 1,
                variable_costs=85.97482,
            )},
     )
)
        
    

### Sinks

pth_to_data ="C:\\Users\\azizul\\Desktop\\hyBit\\"
flnm = 'load.csv'
data = pd.read_csv( os.path.join(pth_to_data, flnm))

# Load | variable
energysystem.add(
    solph.components.Sink(
        label="Load_A",
        inputs={
            bus_main: solph.flows.Flow(   
                nominal_value= 1,
                fix = data["load_a"],
                        
                        
            )
        },
    )
)
# Load | fixed

energysystem.add(
    solph.components.Sink(
        label="Load_B",
        inputs={
            bus_load: solph.flows.Flow(   
                nominal_value= 1,
                fix = data["load_b"],
                        
                        
            )
        },
    )
)

energysystem.add(
    solph.components.GenericStorage(
            label='storage',
            inputs={bus_main: solph.flows.Flow()},
            outputs={bus_main: solph.flows.Flow()},
                    loss_rate=0.001, 
                    initial_storage_level= 0.75,
                    nominal_storage_capacity= 100e6,
                    inflow_conversion_factor=0.98, outflow_conversion_factor=0.97,
                    
                    
                    ),
)
def non_quadratic_cost(flow):
    return 10*flow**0.8
energysystem.add(
    solph.components.Converter(
        label="Transformer1",
        inputs={bus_wind: solph.flows.Flow()},
        outputs= {bus_main: solph.flows.Flow(variable_costs = non_quadratic_cost(0.8))},
        conversion_factors={bus_PV: 0.98},
    )
)
energysystem.add(
    solph.components.Converter(
        label="Transformer2",
        inputs={bus_PV: solph.flows.Flow()},
        outputs= {bus_main: solph.flows.Flow(variable_costs= 10)},
        conversion_factors={bus_PV: 0.98},
    )
)
energysystem.add(
    solph.components.Converter(
        label="Transformer3",
        inputs={bus_main: solph.flows.Flow()},
        outputs= {bus_load: solph.flows.Flow(variable_costs=10)},
        conversion_factors={bus_PV: 0.975},
    )
)
print(" -- Finished setup --")
model = solph.Model(energysystem)
solution= model.solve(solver='scip', solve_kwargs={'tee': True})     # "cbc"/ "gurobi"
print(solution)

results = processing.results(model)
column_name = (('your_storage_label', 'True'), 'storage_content')
SC = views.node(results, bus_main,bus_load)
print(SC)