from django.shortcuts import render
from django.http import Http404

from .models import Experiment

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

def dashboard(request, experiment_id):
    try:
        experiment = Experiment.objects.get(id=experiment_id)
    except Experiment.DoesNotExist:
        raise Http404('experiment not found')
    return render(request, 'dashboard.html', {
        'experiment': experiment,
    })



