import flee.flee as flee
import time
import datamanager.handle_refugee_data as handle_refugee_data
import pandas as pd
import numpy as np
import os as os
import outputanalysis.analysis as a
import markovflee

"""
Generation 1 code. Incorporates only distance, travel always takes one day.
"""

if __name__ == "__main__":
  print("Testing basic data handling and simulation kernel.")

  flee.SimulationSettings.MinMoveSpeed=100.0
  flee.SimulationSettings.MaxMoveSpeed=250.0
  flee.SimulationSettings.MaxWalkSpeed=50.0

  end_time = 100

  locations_list=[True]
  # factors=[1000,200,50,10,20,5,100,2,1]
  factors=[200]
  runs=25
  large=True

  path='Results_{}_{}/'.format(flee.SimulationSettings.MaxMoveSpeed,large)
  os.makedirs(path, exist_ok=True)

  for factor in factors:
    for locations in locations_list:

      df=np.empty(shape=(0,10))

      tic=time.time()

      for run in range(runs):
        e = flee.Ecosystem()

        if large:
          l1 = e.addLocation("A", movechance=0.5)
          l2 = e.addLocation("B", movechance=0.6)
          l3 = e.addLocation("C", movechance=0.2)
          l4 = e.addLocation("D", movechance=0.2)
          l5 = e.addLocation("E", movechance=0.01,capacity=18000)
          l6 = e.addLocation("F", movechance=0.01,capacity=17000)
          l7 = e.addLocation("G", movechance=0.15)
          l8 = e.addLocation("H", movechance=0.8)
          l9 = e.addLocation("I", movechance=0.95)
          l10 = e.addLocation("J", movechance=0.4)
          l11 = e.addLocation("K", movechance=0.2)
          l12 = e.addLocation("L", movechance=0.4)

          e.linkUp("A","B","80.00")
          e.linkUp("A","C","130.00")
          e.linkUp("A","D","52.0")
          e.linkUp("B","D","30.0")
          e.linkUp("F", "D", "180.0")
          e.linkUp("E", "D", "160.0")
          e.linkUp("B", "C", "33.0")
          e.linkUp("A", "L", "73.0")
          e.linkUp("H", "L", "13.0")
          e.linkUp("H", "G", "25.0")
          e.linkUp("C", "G", "65.0")
          e.linkUp("H", "E", "150.0")
          e.linkUp("K", "E", "230.0")
          e.linkUp("K", "B", "75.0")
          e.linkUp("J", "L", "53.0")
          e.linkUp("J", "I", "40.0")
          e.linkUp("J", "B", "75.0")
          e.linkUp("J", "K", "80.0")


        else:
          l1 = e.addLocation("A", movechance=0.3)
          l2 = e.addLocation("B", movechance=0.3)

          l3 = e.addLocation("C", movechance=0.0)
          l4 = e.addLocation("D", movechance=0.0)

          e.linkUp("A","B","80.00")
          e.linkUp("A","C","130.00")
          e.linkUp("A","D","52.0")
          e.linkUp("B","D","30.0")
          e.linkUp("B", "C", "33.0")

        d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory="test_data", start_date="2010-01-01", data_layout="data_layout.csv")
        refresh_probs = True

        for t in range(0,end_time):
          new_refs = factor*d.get_new_refugees(t)

        # Insert refugee agents
          if locations:
            l1.IncrementNumAgents(new_refs)
          else:
            for i in range(0, new_refs):
              e.addAgent(location=l1)

          # Set this if new routes appear in the graph or if routes are closed.
          # refresh_probs=True

          # Propagate the model by one time step.
          if locations:
            refresh_probs=e.evolveLocations(refresh_probs)
          else:
            e.evolve()

          df=np.append(df,[[run,t,l1.numAgents+l2.numAgents+l3.numAgents+l4.numAgents, l1.numAgents, l2.numAgents, l3.numAgents, l4.numAgents, l5.numAgents, l6.numAgents, l7.numAgents]],axis=0)

      np.savetxt(path+'time_{}_{}_{}_dp_new'.format(locations,factor,runs),np.asarray([time.time()-tic]))
      print(time.time()-tic)
      np.savetxt(path+'results_{}_{}_{}_dp_new'.format(locations,factor,runs),df,delimiter=';')
