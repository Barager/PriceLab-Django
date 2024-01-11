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
    except Experiment.DoesNotExist:
        raise Http404('experiment not found')
    return render(request,'experiment_detail.html', {
        'experiment': experiment,
    })



