import plotly.graph_objects as go
import pandas as pd

def visualize_aki_data(aki_data:pd.DataFrame, baseline_value:int = 0):
    """
    A Function that visualizes the history of an AKI patient. Best used with the dataframe extracted by aki.detection.detect_aki.

    Args:

        aki_data:pd.DataFrame -> A DataFrame with the columns AKI_Level, Date and Cr_Value
        baseline_value:float (Optional) -> The Creatinine baseline of the patient. 

    Returns:
        A Plotly Figure
    """
    baseline_string = f"Baseline Cr Value: {round(baseline_value, 2)}"

    if baseline_value == 0:
        baseline_string = ""

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=aki_data['Date'], y=aki_data["Cr_Value"], name='Creatinine Level', line=dict(width=3)))
    fig.add_trace(go.Scatter(x=aki_data[aki_data["AKI_Level"] == 1]['Date'], y=aki_data[aki_data["AKI_Level"] == 1]["Cr_Value"], mode='markers', name='AKI Level 1',  marker_color='rgba(0, 0, 0, .9)')) 
    fig.add_trace(go.Scatter(x=aki_data[aki_data["AKI_Level"] == 2]['Date'], y=aki_data[aki_data["AKI_Level"] == 2]["Cr_Value"], mode='markers', name='AKI Level 2',  marker_color='rgba(0,255,0, .9)'))
    fig.add_trace(go.Scatter(x=aki_data[aki_data["AKI_Level"] == 3]['Date'], y=aki_data[aki_data["AKI_Level"] == 3]["Cr_Value"], mode='markers', name='AKI Level 3',  marker_color='rgba(255, 100, 100, .9)'))
    fig.add_trace(go.Scatter(x=aki_data[aki_data["AKI_Level"] == 4]['Date'], y=aki_data[aki_data["AKI_Level"] == 4]["Cr_Value"], mode='markers', name='Permanent Graft Loss',  marker_color='rgba(255, 255, 100, .9)'))
    fig.update_layout(
        title={
            'text' : f"Creatinine by Days. {baseline_string}",
            'x':0.12,
            },
        xaxis_title="Time in days",
        yaxis_title="Creatinine in mg/dl",
        font=dict(
            family="Courier New, monospace",
            size=12,
        ))

    return fig
#fig.show()
