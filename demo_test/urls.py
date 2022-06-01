from django.urls import path
from . import views

urlpatterns = [
    path('view-pdf/', views.GeneratePdf.as_view(), name='view_pdf'),
    path('download-pdf/', views.GeneratePDF.as_view(), name='download_pdf'),
    
    path('generate_obj_pdf/<int:pk>/', views.generate_obj_pdf, name='generate_obj_pdf'),
]

