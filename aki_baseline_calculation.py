import pandas as pd
from statistics import mean, median, variance

def _chunk_list_in_steps(values:list, chunk_size:int) -> list:
    """
    Cuts an array into equal chunks.
    
    Args:
        values: A List with values you want to cut into chunks
        chunk_size: Size of a singe chunk

    Returns: An array with multiple arrays with the length of the chunk size
    """
    if len(values) < chunk_size:
        return [values.tolist()]

    return [values[index:index+chunk_size] for index in range(len(values)-chunk_size)]


def statistical_creatinine_baseline_single_patient(cr_data:pd.DataFrame, chunck_penalty:float = 0.5, cr_calculation_method = mean) -> float:
    """
    Calculates the Cr Baseline value for a single patient. Make sure the values in cr_data are sorted by time.

    Args:

        cr_data:list -> A list containing floats of creatinin values ordered by date.
        chunck_penalty:float -> A number between 0 and 1 to give a penalty to the chuncksize for the selected values to determen the Creatinine baseline.
        cr_calculation_method:function -> Method to account the Creatinine values in one chunk. Function should have a list of floats as input. Standart is the mean, other functions worth testing could be the median.

    Retruns: A DataFrame with a baseline Cr value for a patient 
    """

    chunk_size = round(len(cr_data)*chunck_penalty)
    if chunk_size < 10:
        chunk_size = 10

    ## Chunck list of creatinine values
    chuncked_creat = _chunk_list_in_steps(cr_data, chunk_size)

    lowest_av = float('inf')
    lowest_var = float('inf')

    ## Iterate through every chunk and find the chunk with the lowest average value and the least variance in the values
    for creat in chuncked_creat:

        if len(creat) < 2:
            if len(chuncked_creat) == 1:
                lowest_av = creat[0]
            continue

        mean_cr = cr_calculation_method(creat)
        variance_cr = variance(creat)

        if lowest_var > variance_cr and lowest_av > mean_cr:
            lowest_av = mean_cr
            lowest_var = variance_cr

    return lowest_av


def statistical_creatinine_baseline(cr_data:pd.DataFrame, chunck_penalty:float = 0.5, cr_calculation_method = mean) -> pd.DataFrame:
    """
    Calculates a statistical variance of the AKI Baseline for a datafram. Timeline of creatinine values are needed.

    Args:

        cr_data:pd.DataFrame -> A data frame with the columns PatientID, Cr_Value and Date
        chunck_penalty:float -> A number between 0 and 1 to give a penalty to the chuncksize for the selected values to determen the Creatinine baseline
        cr_calculation_method:function -> Method to account the Creatinine values in one chunk. Function should have a list of floats as input. Standart is the mean, other functions worth testing could be the median.

    Retruns: A DataFrame with a baseline Cr value for every patient in the provided dataframe

    """
    columns = ["PatientID", "Create_Baseline"]
    create_baseline = pd.DataFrame(columns = columns)
    cr_data = cr_data.sort_values(by = ['Date'])

    ## Iteration for every patient id
    for paID in cr_data["PatientID"].unique():

        data = dict((key, "") for key in columns)
        data["PatientID"] = paID

        ## Get all creatinine entrys in the dataframe for the current patient
        unchuncked = cr_data[cr_data["PatientID"] == paID]["Cr_Value"].values

        data["Create_Baseline"] = statistical_creatinine_baseline_single_patient(unchuncked, chunck_penalty, cr_calculation_method)

        create_baseline = create_baseline.append(data, ignore_index = True)

    return create_baseline