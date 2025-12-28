"""
URL configuration for future project.

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
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
print("=" * 80)
print("DEBUG: future/urls.py is being loaded")
print("=" * 80)

from django.contrib import admin
print("DEBUG: django.contrib.admin imported in urls.py")
print(f"DEBUG: admin.site = {admin.site}")
print(f"DEBUG: admin.site._registry in urls.py = {list(admin.site._registry.keys())}")

from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('eys.urls')),
]

print(f"DEBUG: urlpatterns configured with admin.site.urls")
print(f"DEBUG: admin.site._registry after urlpatterns = {list(admin.site._registry.keys())}")
print("=" * 80)
print("DEBUG: future/urls.py loading complete")
print("=" * 80)

