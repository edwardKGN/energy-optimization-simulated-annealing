"""
Grade Enthalpy Input Stream Translator (GEIST)

Convert user input into machine to minimize variability of human input.

.csv input file is to have only values for grade enthalpy data. to leave blank for remainder to indicate batch limits / duration
"""
import numpy as np
import pandas as pd
# import json  # Safe function not operational > unable to read int64
# import pickle

# import constants as constants

# Grade Enthalpy Data Pre-Processing (Convert from CSV to Useful Analytical Data)
def GEIST(pd_data):
    # Extract All Grades Present
    ls_grade_names = pd_data.columns.values
    ls_grade_names = ls_grade_names[1:]  # Ignore Time Block Column Name <KEY FORMATTING LIMITATION>
    
    grade_dict = {}

    for grade in ls_grade_names:
        grade_enthalpy = np.array(pd_data[grade].values)

        # print(f"{grade}:\n{grade_enthalpy}\n")

        grade_enthalpy_mask = np.logical_not(np.isnan(grade_enthalpy))

        # print(f"{grade} mask:\n{grade_enthalpy_mask}\n")

        true_grade_enthalpy = grade_enthalpy[grade_enthalpy_mask]

        # print(f"{grade} true enthalpy:\n{true_grade_enthalpy}\n")

        # Convert non-nan, numpy.float64 data to remove '.0' and maintain as string
        input_grade = grade
        if input_grade == input_grade:
            if isinstance(input_grade, float):
                input_grade = str(int(input_grade))

        grade_dict[input_grade] = list(true_grade_enthalpy)  # create function that reads from .csv

    # print(f"grade_dict >\n{grade_dict}")
    return grade_dict