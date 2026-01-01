# """
# URL configuration for config project.
#
# The `urlpatterns` list routes URLs to views. For more information please see:
#     https://docs.djangoproject.com/en/5.2/topics/http/urls/
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to urlpatterns:  path('', views.home, name='home')
# Class-based views
#     1. Add an import:  from other_app.views import Home
#     2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
# Including another URLconf
#     1. Import the include() function: from django.urls import include, path
#     2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
# """
# from django.contrib import admin
# from django.urls import path, include, re_path
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
#
#
# # swagger ui da korinishida chiqarish
#
# schema_view = get_schema_view(
#     openapi.Info(
#         title="API Documentation",
#         default_version='v1',
#         description="Bizning API Swagger docs",
#
#     ),
#     public=True,
#     permission_classes=[permissions.AllowAny]
# )
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#
#
#     # Swagger/ redoc
#     re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
#     path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
#     path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
#
#
# ]



# ---------------------------------------------------------------------


from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ---------------- Swagger sozlamalari ----------------
schema_view = get_schema_view(
    openapi.Info(
        title="Education Platform API",
        default_version="v1",
        description="Professional API documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# ---------------- Asosiy URL Config ------------------
urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication (masalan JWT yoki DRF auth)
    path('api/auth/', include('rest_framework.urls')),

    # COURSE app uchun API
    path('api/course/', include(('course.urls', 'course'), namespace='course')),

    # STUDENT app uchun API
    path('api/student/', include(('student.urls', 'student'), namespace='student')),

    # Swagger
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('ai/', include('chatai.urls')),

]


# media yuklangan media chiqishi uchun
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

