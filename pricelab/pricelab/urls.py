from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static


from experiments import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('experiments/', include('experiments.urls')),  # Include the app's URLs here
    path('', views.home, name='home'),
    path('experiments/<int:experiment_id>/', views.experiment_detail, name='experiment_detail'),
    path('dashboard/<int:experiment_id>/', views.dashboard, name='dashboard'),
    path('publish_results/<int:experiment_id>/', views.publish_results, name='publish_results'),
]



