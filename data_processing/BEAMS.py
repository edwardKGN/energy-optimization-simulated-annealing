import numpy as np

from numpy.random import rand, randn
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime, timedelta

class StreamData:
    # Production Data
    pd_prod_plan = None
    grade_dict = None

    # Time Discretization
    time_blocks = None
    datetime_array = None

    # Streams Enthalpy Holding > Essential for Optimizer to remember prior Batches
    cache_stream_holding_dict = {}


    def __init__(self, grade_dict, pd_prod_plan, time_blocks):
        self.pd_prod_plan = pd_prod_plan
        self.grade_dict = grade_dict
        self.time_blocks = time_blocks

    # Getters
    def get_pd_prod_plan(self):
        return self.pd_prod_plan
    
    def get_grade_dict(self):
        return self.grade_dict
    
    def get_time_blocks(self):
        return self.time_blocks
    
    def get_cache_stream_holding_dict(self):
        return self.cache_stream_holding_dict
    
    def get_datetime_array(self):
        return self.datetime_array
    
    # Setters
    def set_cache_stream_holding_dict(self, stream_holding_dict):
        self.cache_stream_holding_dict = stream_holding_dict

    def set_datetime_array(self):
        prod_plan_dict = self.PRISM(row=0)
        
        start_datetime = []
        for stream in prod_plan_dict:
            if prod_plan_dict[stream][list(prod_plan_dict[stream].keys())[0]] == prod_plan_dict[stream][list(prod_plan_dict[stream].keys())[0]]: 
                datetime_data = datetime.strptime(prod_plan_dict[stream][list(prod_plan_dict[stream].keys())[1]], 
                                                "%d/%m/%y %H:%M")
                start_datetime.append(datetime_data)
            
        start_datetime = min(start_datetime)

        datetime_array = [start_datetime]

        for iter in np.arange(1, self.time_blocks):
            datetime_array.append(datetime_array[iter-1] + timedelta(minutes=15))

        # print(f"datetime_array > \n{datetime_array}, len > {len(datetime_array)}")
    
        self.datetime_array = datetime_array
    
    def PRISM(self, row):
        """
        PRoduction Input Stream Management (PRISM)

        Convert user input into machine to minimize variability of human input.

        .csv input file is to have only values for production plan. to leave blank for remainder to indicate batch limits / duration

        Goes through a row and generate prod_plan_dict 
        """
        # Determine stream names and number of streams
        ls_stream_names = self.pd_prod_plan.columns.levels[0].values
        ls_stream_subvalues = self.pd_prod_plan.columns.levels[1].values

        prod_plan_dict = {}
        for streams in ls_stream_names:
            # Convert non-nan, numpy.float64 data to remove '.0' and maintain as string
            input_grade = self.pd_prod_plan[streams][ls_stream_subvalues[0]].values[row]
            if input_grade == input_grade:
                if isinstance(self.pd_prod_plan[streams].values[row][0], float) or isinstance(self.pd_prod_plan[streams].values[row][0], np.int64):
                    input_grade = str(int(self.pd_prod_plan[streams].values[row][0]))
        
            prod_plan_dict[streams] = {"grade": input_grade, 
                                       "start": self.pd_prod_plan[streams][ls_stream_subvalues[1]].values[row]}
        
        return prod_plan_dict
    
    # Stream Builders
    def single_stream_builder(self, grade, stream_shift):
        # If nan, then put in blank, to return stream shift array
        if grade != grade:
            # print(f"is NaN")
            stream_shift_array = np.zeros(self.time_blocks)
        else:
            grade_run_time = len(self.grade_dict[grade])

            stream_shift_array = np.zeros(self.time_blocks - grade_run_time)
            stream_shift_array = np.concatenate([self.grade_dict[grade], stream_shift_array], axis=0)

            # Shift array by # time blocks specified by stream shift
            stream_shift_array = np.roll(stream_shift_array, stream_shift)
        
        # print(f"shifted array \n{stream_shift_array}\n")
        return stream_shift_array
    
    def multi_stream_builder(self, x, prod_plan_dict):
        stream_holding_dict = {}        

        for index, stream in enumerate(list(prod_plan_dict.keys())):
            stream_holding_dict[stream] = self.single_stream_builder(grade=prod_plan_dict[stream]['grade'], stream_shift=x[index])

        return stream_holding_dict

def BEAMS(StreamDataObject, stagger_limits, flag_optimizer=True):
    StreamDataObject.set_datetime_array()

    datetime_array = StreamDataObject.get_datetime_array()
    # print(f"datetime_array >\n{datetime_array}")

    # Required format for optimizer
    def wrapped_cost_function(x):
        return cost_function(x, 
                             prod_plan_dict=prod_plan_dict, 
                             StreamDataObject=StreamDataObject)
    
    # Lower Bounds Translator
    def translate_datetime_to_time_block(datetime_array, prod_plan_dict):
        ls_low_bounds = []
        for stream in prod_plan_dict:
            # print(f"stream > {stream}")

            if prod_plan_dict[stream][list(prod_plan_dict[stream].keys())[0]] == prod_plan_dict[stream][list(prod_plan_dict[stream].keys())[0]]: 
                datetime_data = datetime.strptime(prod_plan_dict[stream][list(prod_plan_dict[stream].keys())[1]], 
                                                    "%d/%m/%y %H:%M")
                low_bound_index = None
                for index in range(0, len(datetime_array)):
                    if index < (len(datetime_array)):
                        # print(f"index > {index}")
                        if datetime_array[index] <= datetime_data and datetime_data < datetime_array[index+1]:
                            low_bound_index = index
            
            # if no start date e.g. no batch starting > to instead give index 0, will be corrected later as following batch have own start date
            else: 
                low_bound_index = 0
                            
            if low_bound_index is None:
                print(f"Error > Datetime not found within discretized datetime array")
                
            ls_low_bounds.append(low_bound_index)
            
        print(f"ls_low_bounds > {ls_low_bounds}")
        return ls_low_bounds

    best_array = []

    for row in np.arange(len(StreamDataObject.get_pd_prod_plan())):
    # for row in np.arange(0, 2):
        print(f"\nrow > {row}")
        prod_plan_dict = StreamDataObject.PRISM(row=row)

        if row == 0:
            print(f"Zeroth Row")
            ls_low_bounds = translate_datetime_to_time_block(datetime_array=datetime_array, prod_plan_dict=prod_plan_dict)

            first = True  

            bounds = []
            for index, stream in enumerate(prod_plan_dict):
                if prod_plan_dict[stream]['grade'] == prod_plan_dict[stream]['grade']:  # if not nan <indicate no shift>
                    # Lock 1st non-NAN stream with the smallest lower boundary to same value as anchor
                    if first and ls_low_bounds[index] == min(ls_low_bounds): 
                        # TODO Time Array Upgrade to detect earliest stream and lock that one
                        bounds.append([ls_low_bounds[index], ls_low_bounds[index]])
                        first = False
                    else:
                        bounds.append([ls_low_bounds[index], (ls_low_bounds[index]+stagger_limits[index])])
                else: # if NaN lock to same value
                    bounds.append([ls_low_bounds[index], ls_low_bounds[index]])
                
                StreamDataObject.cache_stream_holding_dict[stream] = np.zeros(StreamDataObject.time_blocks)
        else:
            # Following batches to take grade pre-shift + staggering to as lower boundary to avoid overlapping with prior batches. 
            print(f"Non-Zeroth Row")
            # prev_prod_plan_dict = StreamDataObject.PRISM_basic(row=row-1) # NOTE Mismatch of above
            prev_prod_plan_dict = StreamDataObject.PRISM(row=row-1)

            # Recalculate prior stream_holding_dict for Optimizer's reference
            for index, stream in enumerate(prod_plan_dict):
                StreamDataObject.cache_stream_holding_dict[stream] += StreamDataObject.single_stream_builder(
                    grade=prev_prod_plan_dict[stream]['grade'], 
                    stream_shift=best[index])
            
            ls_low_bounds = translate_datetime_to_time_block(datetime_array=datetime_array, prod_plan_dict=prod_plan_dict)

            # Works regardless of reading prod_plan_V2 or prev_prod_planas it reads from same pd
            bounds = []
            for index, stream in enumerate(prod_plan_dict):  
                if prev_prod_plan_dict[stream]['grade'] != prev_prod_plan_dict[stream]['grade']: # Only Applicable for Blank Prior
                    low_bound = ls_low_bounds[index]  # BUG unable to detect if there is a Grade occupying the spot. Require another layer to fix this e.g. an Array Holding Batch IDs that block out time blocks 
                else:
                    # Setup to be back to back only
                    low_bound = len(StreamDataObject.grade_dict[prev_prod_plan_dict[stream]['grade']]) + best[index]

                    # Condition to set low bound to follow Planner's schedule
                    if ls_low_bounds[index] > low_bound:
                        # print(f"Using Planner's Low Bound")
                        low_bound = ls_low_bounds[index]  
                
                if prod_plan_dict[stream]['grade'] == prod_plan_dict[stream]['grade']:  # if not nan <indicate no shift>
                    bounds.append([low_bound, (low_bound+stagger_limits[index])])
                else:
                    bounds.append([low_bound, low_bound])
                
        bounds = np.asarray(bounds, dtype=np.int64)  # Ensure correct type fed to optimizer
        print(f"bounds >\n{bounds}")

        if flag_optimizer == True:
            best, best_eval = simulated_annealing_int(objective=wrapped_cost_function, bounds=bounds)
        else:
            # Extract Low Bounds of each Row
            best = np.transpose(bounds[:,0])

        print(f"best > {best}")
        best_array.append(best)

    return best_array

def cost_function(x,  # Optimizer's Manipulated Variable from initial guesses <Shift Array>
                  prod_plan_dict,  # Input for manipulation
                  StreamDataObject):  # For Optimizer to remember prior grade shifts
    stream_holding_dict = StreamDataObject.multi_stream_builder(x=x, prod_plan_dict=prod_plan_dict)
    
    for stream in stream_holding_dict:
        stream_holding_dict[stream] = stream_holding_dict[stream] + StreamDataObject.cache_stream_holding_dict[stream]

    # AGGLOMERATION of each Stream data for Optimization
    cost_function_array = accumulate_multi_stream_data(stream_holding_dict=stream_holding_dict)

    # print(f"cost_function_holding_array > \n{cost_function_array}\n"
    #       f"max enthalpy > {np.max(cost_function_array)}")  # Expected return for optimizer

    # Optimizer expects a singular float
    return np.max(cost_function_array)


def simulated_annealing_int(objective, bounds, n_iterations=1000, temp=100, break_iter=50):
    # generate an initial point
    rng = np.random.default_rng()

    best = []
    for index, element in enumerate(bounds):
        # print(f"bounds[{index}] > {element}, element[{index}, 0] > {bounds[index, 0]} | element[{index}, 1] > {bounds[index, 1]} ")
        coord = rng.integers(low=bounds[index, 0], high=bounds[index, 1], endpoint=True)
        best.append(coord)

    print(f"initial guess > {best}")

    # evaluate the initial point
    best_eval = objective(best)
    
    # current working solution
    curr, curr_eval = best, best_eval

    # run the algorithm
    for i in range(n_iterations):
        # take a step
        step_size = np.zeros(len(bounds))

        # Avoid wasted iteration by getting step_size = [0, 0], meaning staying in the same place
        while (step_size == np.zeros(len(bounds))).all():
            step_size = []
            for index, element in enumerate(bounds):
                # print(f"bounds[{index}] > {element}, element[{index}, 0] > {bounds[index, 0]} | element[{index}, 1] > {bounds[index, 1]} ")
                coord = rng.integers(low=bounds[index, 0], high=bounds[index, 1], endpoint=True)
                step_size.append(coord)
        # print(f"step_size > {step_size}")

        candidate = step_size  # Update candidate with new coordinates
 
        """
        TODO Further upgrades
        Modify objective such that the selection criteria is established here instead of current setup where it directly gives the max. 
        This allows more complex conditions to be placed in the eval
        """
        # evaluate candidate point
        candidate_eval = objective(candidate)

        """
        Selection Criteria <Applicable for Enthalpy only>
        1. New Eval is lower than Prior <Minimizing Cost Function>

        TODO
        2. New Eval is greater than lower boundary   
        """
        # check for new best solution
        if candidate_eval < best_eval:
            # store new best point
            best, best_eval = candidate, candidate_eval
 
        # report progress
        # print('>%d f(%s) = %.5f' % (i, best, best_eval))
    
        # difference between candidate and current point evaluation
        diff = candidate_eval - curr_eval  # If < 0, then select as new. Focus to minimize.
    
        # calculate temperature for current epoch
        t = temp / float(i + 1)
    
        # calculate metropolis acceptance criterion
        metropolis = np.exp(-diff / t)

        # check if we should keep the new point 
        # Condition 1: Current Eval < Candidate
        # Condition 2: Random Chance of skipping Current Eval to avoid minima. Less chance of occurance at lower temp. 
        # <Improvement over Hill Climbing which may get trapped in local minima>
        
        if diff < 0 or rand() < metropolis:
            # print(f"Keeping current as candidate")
            # store the new current point
            curr, curr_eval = candidate, candidate_eval

    return [best, best_eval]


def accumulate_multi_stream_data(stream_holding_dict):
    multi_stream_holding_array = None

    for stream in stream_holding_dict:
        if multi_stream_holding_array is None:
            multi_stream_holding_array = stream_holding_dict[stream]
        else:
            multi_stream_holding_array = np.vstack([multi_stream_holding_array, stream_holding_dict[stream]])
    
    return np.sum(multi_stream_holding_array, axis=0)