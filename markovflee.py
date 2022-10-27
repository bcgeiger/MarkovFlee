from flee import flee
from datamanager import handle_refugee_data, read_period
from datamanager import DataTable  # DataTable.subtract_dates()
from flee import InputGeography
import numpy as np
import outputanalysis.analysis as a
import sys
import csv
import time
import os as os
from flee.SimulationSettings import SimulationSettings

# To run this script, please put it in the root directory of MarkovFlee and simply write the following command: 
# -------------------  pyhton3 markovflee.py <name of the conflict> ------------------------------------------

def AddInitialRefugees(e, d, loc):
  """ Add the initial refugees to a location, using the location name"""
  num_refugees = int(d.get_field(loc.name, 0, FullInterpolation=True))
  for i in range(0, num_refugees):
    e.addAgent(location=loc)

start_time = time.time()
original_stdout = sys.stdout # Save a reference to the original standard output

if __name__ == "__main__":

  locations=True  # MarkovFlee: If this flag is set to TRUE, then MarkovFlee will be used instead of Flee
  runs=1

  config = sys.argv[1]
  path=('examples/{0}'.format(config))

  input_csv_directory = ("{}/input_csv".format(path))

  validation_data_directory = ("{}/source_data".format(path))

  os.makedirs(path, exist_ok=True)

  start_date,end_time = read_period.read_conflict_period("{}/conflict_period.csv".format(input_csv_directory))

  tic = time.time()
  
  for run in range(runs):
    
    df = np.empty(shape=(0, 10))
    
    e = flee.Ecosystem()

    ig = InputGeography.InputGeography()

    ig.ReadLocationsFromCSV("{0}/locations.csv".format(input_csv_directory))

    ig.ReadLinksFromCSV("{0}/routes.csv".format(input_csv_directory))

    ig.ReadClosuresFromCSV("{0}/closures.csv".format(input_csv_directory))

    e,lm = ig.StoreInputGeographyInEcosystem(e)

    #print("Network data loaded")

    d = handle_refugee_data.RefugeeTable(csvformat="generic", data_directory=validation_data_directory, start_date=start_date, data_layout="data_layout.csv")

    d.ReadL1Corrections("{0}/registration_corrections.csv".format(input_csv_directory))

    camp_locations = e.get_camp_names()

    output_header_string = "Day,"

    for l in camp_locations:
      #AddInitialRefugees(e,d,lm[l])
      output_header_string += "%s sim,%s data,%s error," % (lm[l].name, lm[l].name, lm[l].name)

    output_header_string += "Total error,refugees in camps (UNHCR),total refugees (simulation),raw UNHCR refugee count,refugees in camps (simulation),refugee_debt"

    with open('{}/out.csv'.format(path), 'w', newline='') as f:

      writer = csv.writer(f,delimiter=',')
      writer.writerow(output_header_string.split(','))

      # Set up a mechanism to incorporate temporary decreases in refugees
      refugee_debt = 0
      refugees_raw = 0 #raw (interpolated) data from TOTAL UNHCR refugee count only.

      refresh_probs = True  # MarkovFlee requires a flag to update journey probabilities (e.g., when the graph changes)

      for t in range(0,end_time):

        conflict_flag=ig.AddNewConflictZones(e,t)  # MarkovFlee updates journey probabilities if the graph changes

        # Determine number of new refugees to insert into the system.
        new_refs = d.get_daily_difference(t, FullInterpolation=True) - refugee_debt
        refugees_raw += d.get_daily_difference(t, FullInterpolation=True)
        if new_refs < 0:
          refugee_debt = -new_refs
          new_refs = 0
        elif refugee_debt > 0:
          refugee_debt = 0

        # Main iteration: If locations=TRUE, MarkovFlee is called
        if locations:
          agents_list = np.random.multinomial(new_refs,pvals=e.conflict_weights/e.conflict_pop)
          for ind in range(len(e.conflict_zones)):
            e.locations[ind].IncrementNumAgents(agents_list[ind])
            if SimulationSettings.TakeRefugeesFromPopulation:
              e.locations[ind].pop-=agents_list[ind]
          e.refresh_conflict_weights()
          t_data = t
          closure_flag=e.enact_border_closures(t)  # MarkovFlee updates journey probabilities if routes change
          refresh_probs=e.evolveLocations(refresh_probs + conflict_flag + closure_flag)
          total_num_agents=0
          for l in e.locations:
            total_num_agents+=l.numAgents
        else:
          e.add_agents_to_conflict_zones(new_refs)
          e.refresh_conflict_weights()
          t_data = t
          e.enact_border_closures(t)
          e.evolve()
          total_num_agents = e.numAgents()


        # Calculation of error terms
        errors = []
        abs_errors = []
        loc_data = []

        camps = []
        for i in camp_locations:
          camps += [lm[i]]
          loc_data += [d.get_field(i, t)]

        refugees_in_camps_sim = []
        for c in camps:
          refugees_in_camps_sim.append(c.numAgents)

        # calculate errors
        j=0
        for i in camp_locations:
          errors += [a.rel_error(lm[i].numAgents, loc_data[j])]
          abs_errors += [a.abs_error(lm[i].numAgents, loc_data[j])]

          j += 1

        output = "%s" % t

        for i in range(0,len(errors)):
          output += ",%s,%s,%s" % (lm[camp_locations[i]].numAgents, loc_data[i], errors[i])


        if refugees_raw>0:
          output += ",%s,%s,%s,%s,%s,%s" % (float(np.sum(abs_errors))/float(refugees_raw), int(sum(loc_data)), total_num_agents, refugees_raw, sum(refugees_in_camps_sim), refugee_debt)
        else:
          output += ",0,0,0,0,0,0"

        writer.writerow(output.split(','))


      #df = np.append(df, [refugees_in_camps_sim], axis=0)

    #np.savetxt(path+'results_ssudan_{}_{}_dp_moremovement'.format(locations,run), df, delimiter=';')


  with open('{0}/execution_time.txt'.format(path), 'w') as f:
      sys.stdout = f # Change the standard output to the file we created.
      print('The execution time is:--- %s seconds ---' % (time.time() - start_time))
      sys.stdout = original_stdout # Reset the standard output to its original value
