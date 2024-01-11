from django.contrib import admin
from django.urls import path

from experiments import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('experiments/<int:experiment_id>/', views.experiment_detail, name='experiment_detail')
]
