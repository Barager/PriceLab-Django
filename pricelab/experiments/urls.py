from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'experiments'

urlpatterns = [
    path('<int:experiment_id>/', views.view_results, name='view_results'),
]

