"""
URL configuration for omnipredict_ide project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls')).
"""
from django.contrib import admin
from django.urls import path, include

from predictions import views_admin
from predictions.views import home

urlpatterns = [
    path("admin/collected-data/", admin.site.admin_view(views_admin.collected_data_view),
                 name="admin-collected-data"),
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("upload/", include("predictions.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("accounts.urls"))
]

