# Rise of ≥26μmol/la or 0.3mg/dl within 48h Or 50–99% Cr rise from baseline within 7 days (1.50–1.99 × baseline) -> Level 1
# 100–199% Cr rise from baseline within 7 daysb (2.00–2.99 × baseline) -> Level 2
# ≥200% Cr rise from baseline within 7 daysb (≥3.00 × baseline) -> Level 3
# Permanent Graft loss; When the values does not return to the baseline after 90 days prior the aki incident. We choose 90 instead of 30 days, because the data tends to be undersampled  -> Level 4
# RIFLE -> https://litfl.com/rifle-criteria-and-akin-classification/
import pandas as pd
_AKI_LEVEL_DICT_RIFLE = {0:"No Risk", 1:"Risk", 2:"Injury", 3:"Failure", 4:"Loss of kidney function", 5:"End-stage kidney disease"}

def aki_level_seven_days(cr_baseline:float, cr_value:float, time_delta_in_days:int) -> int:
    """
    Calculates the level of aki depending on the Creatinine baseline, the current value and the delta time

    Args:
        cr_baseline:float -> Baseline of Patient
        cr_value:float -> Current value of Cr
        time_delta_in_days:int -> Delta time between point that is looked at and current point

    Returns: The level of AKI between 0 and 3
    """
    aki_level = 0
    if cr_value >= cr_baseline * 1.5 and cr_value <= cr_baseline * 1.99 and time_delta_in_days <= 7:
        aki_level = 1
    if cr_value >= cr_baseline * 2.0 and cr_value <= cr_baseline * 2.99 and time_delta_in_days <= 7:
        aki_level = 2
    if cr_value >= cr_baseline * 3.0 and time_delta_in_days <= 7:
        aki_level = 3

    return aki_level


def aki_level_two_days(current_cr_value:float, past_cr_value:float, time_delta:pd.Timedelta) -> int:
    """ 
    Calculates the level of aki to the special two day conditaion, where the Kreatinine value has to rise by 0.3 mg/dl within two days.

    Args:
        current_cr_value:float -> The value which should be classified as an AKI
        past_cr_value:float -> The kreatinine value prior the current_cr_value within two days
        time_delta:pd.Timedelta -> Time delta between current_cr_value and past_cr_value

    Returns: Either 1 or 0 for the level of aki found

    """
    aki_level = 0
    if (current_cr_value - past_cr_value) >= 0.3 and time_delta <= 2:
        aki_level = 1

    return aki_level

def check_for_permanent_graft_loss(df_slice:pd.DataFrame, 
                                current_date:pd.Timestamp,
                                baseline:float, 
                                time_span_in_days:int = 30, 
                                percentage_treshold:float = 0.8) -> bool:
    """ 
    Checks if the found AKI is actually a permanent loss of graft.

    Args:
        df_slice:pd.DataFrame -> slice of data frame that includes all dates from the aki to the end of the timeseries
        current_date:pd.Timestamp -> The date of AKI
        baseline:float -> Baseline Creatinine Value
        time_span_in_days:int -> The timespan to check if the creatinine value has normalized
        percentage_treshold:float -> Threshold of how many values need to be abouth the baseline in the timeframe to count as a graft loss. Value should be between 0 and 1.

    Returns: True when permanent graft loss has been detected, otherwise false 
    """
    compliance_values = []
    dates_collected = []
    for index, values in df_slice.iterrows():

        if (values["Date"] - current_date).days <= time_span_in_days and values["Date"] not in dates_collected:
            compliance_values.append(get_compliance_cr_value(baseline, values["Cr_Value"]))
            dates_collected.append(values["Date"])
        else:
            break

    if len(compliance_values) >= 3 and compliance_values.count('Abnormal+')/len(compliance_values) >= percentage_treshold:
        return True
    return False


def get_compliance_cr_value(cr_baseline:float, cr_value:float) -> str:
    """ 
    Calculates the Compliance of the Creatinine values to the baseline

    Args:
        cr_baseline: Baseline value of patient
        cr_value: The date of AKI

    Returns: Return Abnormal- when value is to low, Normal when value is in range of the baseline and Abnormal+ when value is to high
    """
    if cr_baseline * 0.699 > cr_value:
       return "Abnormal-"
    elif cr_baseline * 0.7 < cr_value and cr_baseline * 1.499 > cr_value:
        return "Normal"
    elif cr_baseline * 1.5 < cr_value:
        return "Abnormal+"

def clean_duplicate_akis(to_clean:pd.dataFrame) -> pd.DataFrame:
    to_clean = to_clean.drop(columns = ["Index"])

    for index, value in to_clean.iterrows():

        date = value["Date"]
        relevant_date = to_clean[(to_clean["Date"] <= date) & (to_clean["Date"] >= (date - pd.Timedelta(7, unit='d')))]
        date_to_keep = relevant_date[relevant_date["Cr_Value"] == relevant_date["Cr_Value"].max()]["Date"].values[0]
        dates = relevant_date[relevant_date["Date"] != date_to_keep]["Date"].values

        to_clean.loc[to_clean["Date"].isin(dates), "AKI_Level"] = 0

    return to_clean

def rename_aki_levels_to_rifle(aki_level:int)->str:
    """
    Takes an integer from 0 to 5 and converts it to the corrisponding Aki string

    Args:
        aki_level:int -> Integer that reflects the level of the aki

    Returns: A string that describs the level of the aki
    """

    if aki_level > 5:
        return aki_level
    
    return _AKI_LEVEL_DICT_RIFLE[aki_level]
    

def detect_akis(cr_data:pd.DataFrame, 
                cr_baselines:pd.DataFrame, 
                detect_permanent_graft_loss:bool = True, 
                permanent_graft_loss_time_threshold:int = 30,
                clean_duplicate_akis:bool = True) -> pd.DataFrame:
    """
    Detects AKI's based on on the RIFLE score. Will detect AKI Level 1,2 and 3, plus a permanent Graft loss

    Args: 
        cr_data:pd.DataFrame -> A DateFrame consisting of the columns PatientID, Cr_Value and Date
        cr_baselines:pd.DataFrame -> A DataFrame consisting of the columns PatientID and Create_Baseline
        detect_permanent_graft_loss:bool -> If true the algo will check for permanent graft loss, if false found AKI's will not be checkt for graft losses
        permanent_graft_loss_time_threshold:int -> The Threshold of time in which the algo considers an AKI to be a PGL after the AKI incident. Per definition this is 30 day, but if you data is undersampled it can help to choose a higher value. 
        clean_duplicate_akis:bool -> Within 7 days the Cr value can actally rise to fast, so that insead of one the Algo might end up with multiple akis where only one should be. Setting this true will clean up the found akis a bit.
        
    Returns: A Dataframe with the AKI occurences
    """
    output = pd.DataFrame()

    columns = ["PatientID","Date", "Value", "AKI_Level", "Compliance"]

    for paID in cr_data["PatientID"].unique():
        
        ## Filter Dataframe for patient id and drop duplicate dates while keeping the first value of each duplicate date.
        temp_data = []
        baseline = cr_baselines[cr_baselines["PatientID"] == paID]["Create_Baseline"].values[0]
        cr_df_slice = cr_data[cr_data["PatientID"] == paID]
        cr_df_slice = cr_df_slice.drop_duplicates(subset = ["Date"], keep = 'first')
        cr_df_slice = cr_df_slice.reset_index()

        count_of_cr_values = len(cr_df_slice)

        ## Iterates on the index of the current value so operations of previous and future values are easier
        for index in range(len(cr_df_slice)):

            data = dict((key, "") for key in columns)

            ## Collect basic data from row
            row = cr_df_slice.iloc[index]
            data["Index"] = row.index
            data["PatientID"] = paID
            data["AKI_Level"] = 0
            data["Compliance"] = get_compliance_cr_value(baseline, row["Cr_Value"])
            data["Date"] = row["Date"]
            data["Cr_Value"] = row["Cr_Value"]

            current_date = data["Date"]

            ## Arrays collecting values from the previous seven days
            cr_values = []
            past_dates = []
            time_deltas = []

            ## Collecting values from the previous seven days
            for date_index in range(index+1):
                past_date = cr_df_slice.iloc[date_index]["Date"]

                if (current_date - past_date).days <= 7:
                    past_dates.append(past_date)
                    cr_values.append(cr_df_slice.iloc[date_index]["Cr_Value"])
                    time_deltas.append((current_date - past_date).days)

            ## For all entries that are as close as two days calculate the special two day case for aki
            if any((time_delta <= 2) for time_delta in time_deltas):

                for index in range(len(time_deltas)):
                    if time_deltas[index] <= 2:
                        temp_aki = aki_level_two_days(
                        current_cr_value = data["Cr_Value"], 
                        past_cr_value = cr_values[index], 
                        time_delta = time_deltas[index]
                        )

                        if temp_aki != 0:
                            data["AKI_Level"] = temp_aki

            ## For all entries that occure seven days prior the current date check for aki
            ## At least two previous values within the prior seven days have to be present, to run this. Other wise we consider it undersampled
            if all(((x <= data["Cr_Value"]) for x in cr_values)) and \
                len(cr_values) >= 2:

                for deltatime_index in range(len(time_deltas)):
                    temp_aki = aki_level_seven_days(baseline, data["Cr_Value"], time_deltas[deltatime_index])

                    if temp_aki > data["AKI_Level"]:
                        data["AKI_Level"] = temp_aki

                    ## If an AKI has been found check if it is actally a permanent graft loss
                    if data["AKI_Level"] > 0 and \
                     check_for_permanent_graft_loss(cr_df_slice.iloc[index: count_of_cr_values], current_date, baseline) and \
                     detect_permanent_graft_loss:
                        data["AKI_Level"] = 4

                    if data["AKI_Level"] > 0 and \
                        check_for_permanent_graft_loss(cr_df_slice.iloc[index: count_of_cr_values], current_date, baseline, time_span_in_days = 90) and  \
                        detect_permanent_graft_loss:
                        data["AKI_Level"] = 5

            temp_data.append(data)

        ## Clean the data for each patient.
        ## Look at a time window of 7 days for the whole time series and keeps the highes value
        if clean_duplicate_akis == True:
            output = output.append(clean_duplicate_akis(temp_data))
        else:
            output = output.append(temp_data)

    output = output["AKI_Level"].apply(lambda aki: rename_aki_levels_to_rifle(aki))

    return output