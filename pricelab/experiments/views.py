from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from .models import Experiment
from django.http import HttpResponse, JsonResponse
import pandas as pd
from datetime import timedelta
import os


import numpy as np
import random

from .utils import query_db
from .forms import AnalysisForm, SegmentationForm
from .models import Experiment
from .plot import generate_cumulative_sum_plot, generate_covariate_representation_plots, generate_sum_plot
from .tests import run_tests

def home(request):
    experiments = Experiment.objects.all()

    for experiment in experiments:
        experiment.calculated_color = experiment.calculate_color()

    return render(request, 'home.html', {
        'experiments': experiments,
    })

def experiment_detail(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
        treatment_group = experiment.treatment_group.all()
        control_group = experiment.control_group.all()
    except Experiment.DoesNotExist:
        raise Http404('Experiment not found')

    return render(request, 'experiment_detail.html', {
        'experiment': experiment,
        'treatment_group': treatment_group,
        'control_group': control_group,
    })
    

def publish_results(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        raise Http404('Experiment not found')

    # Update the 'published' attribute to True
    experiment.published = True
    experiment.save()

    # Redirect to the dashboard with the updated results
    return redirect('dashboard', experiment_id=experiment_id)


def dashboard(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        raise Http404('Experiment not found')
    
    # Check if results are published
    if experiment.published:

        # Fetch the data needed for the dashboard, including results and plot paths
        start = experiment.start_date
        end = start + timedelta(days=experiment.duration_days)

        # Extract customer UUIDs
        treatment_customer_uuids = tuple(str(uuid) for uuid in experiment.treatment_group.values_list('customer_uuid', flat=True))
        control_customer_uuids = tuple(str(uuid) for uuid in experiment.control_group.values_list('customer_uuid', flat=True))

        # Create SQL query
        columns = """
            customer_uuid, reservation_id, city, distance_km, minutes_driven, net_price_excl_vat,
            extended_reservation_price_excl_vat, drive_minute_price_excl_vat, park_minute_price_excl_vat,
            unlock_price_excl_vat, gross_price_excl_vat, discount_excl_vat, rent_started_at_cest, rent_ended_at_cest
        """

        sql_query = f"""
            SELECT {columns}
            FROM mrt_reservation
            WHERE (customer_uuid IN {treatment_customer_uuids}
                    OR customer_uuid IN {control_customer_uuids})
                AND rent_ended_at_cest BETWEEN :start AND :end
        """

        # Create parameter dictionary for the query
        params = {
            'start': start,
            'end': end,
        }

        # Create a folder for the experiment if it doesn't exist
        experiment_folder = f'experiment_plots/experiment_{experiment_id}'
        os.makedirs(experiment_folder, exist_ok=True)

        df = query_db(sql_query=sql_query, params=params).sort_values(by='rent_ended_at_cest')

        # Assuming you have a column named 'group_column' and 'metric_to_compare'
        # Get selected tests
        selected_tests = [str(test) for test in experiment.selected_tests.all()]
        # print(f'Select tests: {selected_tests}')
        
        # Run tests
        results = run_tests(df, selected_tests, treatment_customer_uuids, control_customer_uuids)

        # Generate plots
        plot_path = generate_cumulative_sum_plot(df, experiment, experiment_folder)
        sum_plot_path = generate_sum_plot(df, experiment, experiment_folder)
        # print("Sum Plot Path:", sum_plot_path)

        covariate_plot_paths = generate_covariate_representation_plots(experiment, experiment_folder, 'group_column')
        print('=-+_=-=-=--=-=-==')
        
        print(plot_path, covariate_plot_paths, results)
        # Return the data for the dashboard
        return render(request, 'dashboard.html', {
            'experiment': experiment,
            'results': results,
            'plot_path': plot_path,
            'sum_plot': sum_plot_path,
            'covariate_plot_paths': covariate_plot_paths,
            # Add other data needed for the dashboard
        })
        
    else:
        # If results are not published, show a message
        return render(request, 'dashboard.html', {
            'experiment': experiment,
        })
    
def segmentation(request, object_id):
    experiment = Experiment.objects.get(id=object_id)
    form = SegmentationForm(request.POST or None, instance=experiment)
    
    if request.method == 'POST':
        if 'assign_treatment_button' in request.POST and request.POST['assign_treatment_button'] == 'on':
            # Call the logic from Experiment.save when the custom button is clicked
            experiment.save()
            messages.success(request, 'Treatment and control groups assigned successfully.')
    
    
    return render(
        request,
        'admin/experiments/experiment/segmentation_form.html',
        {'form': form, 'experiment': experiment},
    )
    
    
 
def view_results(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        raise Http404('Experiment not found')

    start = experiment.start_date
    end = start + timedelta(days=experiment.duration_days)

    # Extract customer UUIDs
    treatment_customer_uuids = tuple(str(uuid) for uuid in experiment.treatment_group.values_list('customer_uuid', flat=True))
    control_customer_uuids = tuple(str(uuid) for uuid in experiment.control_group.values_list('customer_uuid', flat=True))

    # Create SQL query
    columns = """
        customer_uuid, reservation_id, city, distance_km, minutes_driven, net_price_excl_vat,
        extended_reservation_price_excl_vat, drive_minute_price_excl_vat, park_minute_price_excl_vat,
        unlock_price_excl_vat, gross_price_excl_vat, discount_excl_vat, rent_started_at_cest, rent_ended_at_cest
    """

    sql_query = f"""
        SELECT {columns}
        FROM mrt_reservation
        WHERE (customer_uuid IN {treatment_customer_uuids}
                OR customer_uuid IN {control_customer_uuids})
            AND rent_ended_at_cest BETWEEN :start AND :end
    """

    # Create parameter dictionary for the query
    params = {
        'start': start,
        'end': end,
    }

    # Create a folder for the experiment if it doesn't exist
    experiment_folder = f'experiment_plots/experiment_{experiment_id}'
    os.makedirs(experiment_folder, exist_ok=True)

    df = query_db(sql_query=sql_query, params=params).sort_values(by='rent_ended_at_cest')
    # df = pd.read_csv('experiment.csv')
    # df.to_csv('experiment.csv', index=False)
    
        # Assuming you have a column named 'group_column' and 'metric_to_compare'
    
        # Get selected tests
    selected_tests = [str(test) for test in experiment.selected_tests.all()]
    # print(f'Select tests: {selected_tests}')
    # Run tests
    results = run_tests(df, selected_tests, treatment_customer_uuids, control_customer_uuids)

    plot_path = generate_cumulative_sum_plot(df, experiment, experiment_folder)
    sum_plot_path = generate_sum_plot(df, experiment, experiment_folder)
    # print("Sum Plot Path:", sum_plot_path)


    covariate_plot_paths = generate_covariate_representation_plots(experiment, experiment_folder, 'group_column')

    # print(plot_path, covariate_plot_paths)
    return render(request, 'admin/experiments/experiment/view_results.html', {
        'experiment': experiment,
        'plot_path': plot_path,
        'sum_plot': sum_plot_path,
        'covariate_plot_paths': covariate_plot_paths,
        'results': results,
    })