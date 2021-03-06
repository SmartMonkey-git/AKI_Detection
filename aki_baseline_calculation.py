import pandas as pd
from statistics import mean, median, variance

_CEATININE_BY_GENER = {"m" : 1.0, "f" : 0.8}

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

    Retruns: A DataFrame with a baseline Cr value in mg/dl for a patient 
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

    Retruns: A DataFrame with a baseline Cr value in mg/dl for every patient in the provided dataframe

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


def get_gender_fixed_baseline_creatinine(gender:str):
    """
    Calculates a gender based Creatinine baseline. Definition by this Paper: https://academic.oup.com/ndt/article/25/12/3911/1863037

    Args:
        gender:str -> A string that implies the wanted gener. Can be m, male, f or female.

    Returns: A Creatinine Baseline value in mg/dl that depends solely on the gender
    """

    return _CEATININE_BY_GENER[gender.lower()[0]]


def get_revised_baseline_creatinine(age:int, is_female:bool, is_black:bool):
    """
    Calculates a Creatinine baseline base on gender, ethnicity and age. Definition by this Paper: https://academic.oup.com/ndt/article/25/12/3911/1863037

        Args:
            age:int -> age of the patient in year
            is_female:bool -> if the patient is femal or not
            is_black:bool -> if the patient is has black skin color or not

    Returns: A Creatinine Baseline value in mg/dl
    """
    return 0.74 - 0.2*int(is_female) + 0.08*int(is_black) + 0.003*age


def get_MDRD_baseline_creatinine(age:int, is_female:bool, is_black:bool):
    """
    Calculates the creatninine baseline based on the MDRD formular. Found in this Paper: https://academic.oup.com/ndt/article/25/12/3911/1863037

    Args:
        age:int -> age of the patient in year
        is_female:bool -> if the patient is femal or not
        is_black:bool -> if the patient is has black skin color or not
    
    Returns: A Creatinine Baseline value in mg/dl
    """
    return 75/pow((186 * pow(age, -0.203) * 0.742*int(is_female) * 1.21*int(is_black)), -0.887)
    

def get_CKD_EPI_glomerular_filtration_rate(age:int, is_female:bool, is_black:bool, min_cr_value:float = 1, max_cr_value:float = 1):
    """
    Caluclates the glomerular filtration rate of a patient. Definition by this Paper: https://www.acpjournals.org/doi/abs/10.7326/0003-4819-150-9-200905050-00006?journalCode=aim

        Args:
            age:int -> age of the patient in year
            is_female:bool -> if the patient is femal or not
            is_black:bool -> if the patient is has black skin color or not
            min_cr_value:float -> minimum creatinine value of the patients history in mg/dl
            max_cr_value:float -> maximum creatinine value of the patients history in mg/dl

    Returns: The glomerular filtration rate of a patient in mL/s/1.73 m2
    """
    gender_value = [0.9, 0.7][int(is_female)]
    alpha = [-411, -0.329][int(is_female)]
    ethnicity_value = [144, 166][int(is_black)]

    grf = ethnicity_value * pow((min_cr_value/gender_value), alpha) * pow((max_cr_value/gender_value), -1.209) * pow(0.993, age) * 1.018*int(is_female) + 1.159*int(is_black)
    return grf
