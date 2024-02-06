
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import seaborn as sns
import numpy as np
import os
import pandas as pd

from sklearn.impute import SimpleImputer
from django.apps import apps
from experiments.models import User  # Import the User model from your app

def ensure_directory_exists(directory):
    os.makedirs(directory, exist_ok=True)


def generate_sum_plot(df, experiment, experiment_folder):
    # Convert data to daily frequency
    df['rent_ended_at_cest'] = pd.to_datetime(df['rent_ended_at_cest']).dt.floor('H')

    # Calculate cumulative sum minutes driven for treatment and control groups
    treatment_group = experiment.treatment_group.values_list('customer_uuid', flat=True)
    control_group = experiment.control_group.values_list('customer_uuid', flat=True)

    df_treatment = df[df['customer_uuid'].isin(treatment_group)]
    df_control = df[df['customer_uuid'].isin(control_group)]

    df_treatment = df_treatment.sort_values(by='rent_ended_at_cest')
    df_control = df_control.sort_values(by='rent_ended_at_cest')

    # Calculate cumulative sum for the entire dataset
    df_treatment['cumulative_sum_minutes_treatment'] = df_treatment['minutes_driven'].cumsum()
    df_control['cumulative_sum_minutes_control'] = df_control['minutes_driven'].cumsum()

    # Calculate sum of minutes driven at each time point
    df_treatment['sum_minutes_treatment'] = df_treatment.groupby('rent_ended_at_cest')['minutes_driven'].transform('sum')
    df_control['sum_minutes_control'] = df_control.groupby('rent_ended_at_cest')['minutes_driven'].transform('sum')

    # Set color palette
    sns.set_palette(["#0A3D29", "#9FBBAD"])

    # Plotting
    plt.figure(figsize=(13, 2.8))
    
    # Plot sum of minutes driven for treatment group
    plt.plot(df_treatment['rent_ended_at_cest'], 
             df_treatment['sum_minutes_treatment'],
             label='Treatment Group', color='#0A3D29', linewidth=2, )

    # Plot sum of minutes driven for control group
    plt.plot(df_control['rent_ended_at_cest'], 
             df_control['sum_minutes_control'],
             label='Control Group', color='#9FBBAD', linewidth=2, )
    
    # Customize date format on the x-axis
    date_format = DateFormatter("%d-%m-%Y")
    plt.gca().xaxis.set_major_formatter(date_format)

    # plt.xlabel('Date')
    plt.ylabel('Driving Time (Minutes)')
    plt.title('Sum of Daily Driving Time Per Group')
    # plt.xticks(rotation=30, ha='right', size=7)
   
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    # Add background color
    plt.gca().set_facecolor('#FFFFFF')

    plt.show()
    
    # Save the plot for each covariate
    plot_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "../static", experiment_folder, 'sum_minutes_driven_plot.png'
    )

    ensure_directory_exists(os.path.dirname(plot_filename))  # Ensure the directory exists
    plt.savefig(plot_filename)

    # Return the relative path from the static directory
    return os.path.relpath(plot_filename, start=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static')))


def generate_cumulative_sum_plot(df, experiment, experiment_folder):
    # Convert data to daily frequency
    df['rent_ended_at_cest'] = pd.to_datetime(df['rent_ended_at_cest']).dt.floor('H')

    # Calculate cumulative sum minutes driven for treatment and control groups
    treatment_group = experiment.treatment_group.values_list('customer_uuid', flat=True)
    control_group = experiment.control_group.values_list('customer_uuid', flat=True)

    df_treatment = df[df['customer_uuid'].isin(treatment_group)]
    df_control = df[df['customer_uuid'].isin(control_group)]

    df_treatment = df_treatment.sort_values(by='rent_ended_at_cest')
    df_control = df_control.sort_values(by='rent_ended_at_cest')

    # Calculate cumulative sum for the entire dataset
    df_treatment['cumulative_sum_minutes_treatment'] = df_treatment['minutes_driven'].cumsum()
    df_control['cumulative_sum_minutes_control'] = df_control['minutes_driven'].cumsum()

    # Set color palette
    sns.set_palette(["#0A3D29", "#9FBBAD"])

    # Plotting
    plt.figure(figsize=(13, 2.8))
    
    # Plot cumulative sum for treatment group
    plt.plot(df_treatment['rent_ended_at_cest'], 
             df_treatment['cumulative_sum_minutes_treatment'],
             label='Treatment Group', color='#0A3D29', linewidth=2)

    # Plot cumulative sum for control group
    plt.plot(df_control['rent_ended_at_cest'], 
             df_control['cumulative_sum_minutes_control'],
             label='Control Group', color='#9FBBAD', linewidth=2)
    
    # Customize date format on the x-axis
    date_format = DateFormatter("%d-%m-%Y")
    plt.gca().xaxis.set_major_formatter(date_format)

    # plt.xlabel('Date')
    plt.ylabel('Driving Time (Minutes)')
    plt.title('Cumulative Driving Time Evolution')
    # plt.xticks(rotation=30, ha='right', size=7)
   
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
     # Add background color
    plt.gca().set_facecolor('#FFFFFF')


    plt.show()

    
    # Save the plot for each covariate
    plot_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "../static", experiment_folder, 'cumulative_average_minutes_driven_plot.png'
    )

    ensure_directory_exists(os.path.dirname(plot_filename))  # Ensure the directory exists
    plt.savefig(plot_filename)

    # Return the relative path from the static directory
    return os.path.relpath(plot_filename, start=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static')))


def generate_covariate_representation_plots(experiment, experiment_folder, group_column):
    # Set color palette
    sns.set_palette(['#005b2b',  '#4c8c6a', '#99bdaa','#ccded4','#e5eee9', ])

    # Get relevant customer_uuids
    treatment_group_uuids = experiment.treatment_group.values_list('customer_uuid', flat=True)
    control_group_uuids = experiment.control_group.values_list('customer_uuid', flat=True)

    # Fetch User data for treatment and control groups
    treatment_data = User.objects.filter(customer_uuid__in=treatment_group_uuids)
    control_data = User.objects.filter(customer_uuid__in=control_group_uuids)

    # Convert QuerySets to DataFrames
    df_treatment = pd.DataFrame.from_records(treatment_data.values())
    df_control = pd.DataFrame.from_records(control_data.values())

    # Specify the covariate columns you want to plot
    covariate_columns = ['location_title']

    # Create a new figure for each covariate
    for covariate_column in covariate_columns:
        plt.figure(figsize=(10, 6))

        # Combine treatment and control data into a single DataFrame
        df_combined = pd.concat([df_treatment, df_control])

        # Create a new column 'Group' to distinguish treatment and control groups
        df_combined['Group'] = df_combined['customer_uuid'].apply(lambda x: 'Treatment' if x in treatment_group_uuids else 'Control')

        # Count the occurrences of each city in treatment and control groups
        df_counts = df_combined.groupby(['Group', covariate_column]).size().unstack(fill_value=0)

        # Normalize counts to get proportions
        df_proportions = df_counts.div(df_counts.sum(axis=1), axis=0)

        # Create the stacked bar plot
        df_proportions.plot(kind='bar', stacked=True)

        plt.title(f'Stratification in Treatment and Control Groups (Covariate: City)')
        plt.xticks(ticks=range(len(df_proportions.index)), labels=df_proportions.index, rotation=0)
        plt.xlabel('Group')
        plt.ylabel('Proportion')
        plt.legend(title='City', bbox_to_anchor=(1, 1))


        # Save the plot for each covariate
        plot_filename = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "../static", experiment_folder, f'{covariate_column}_representation_plot.png'
        )
        plt.savefig(plot_filename, bbox_inches='tight')

        # Close the current figure to avoid overlapping plots
        plt.close()

    # Return the relative paths from the static directory for all generated plots
    plot_filenames = [os.path.relpath(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "../static", experiment_folder, f'{covariate_column}_representation_plot.png'
    ), start=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))) for covariate_column in covariate_columns]

    return plot_filenames