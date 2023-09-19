from django.urls import path

from . import views


app_name = 'tracker'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
    path('asset-list/', views.AssetListView.as_view(), name="asset_list"),
    path('asset-detail/<int:id>/', views.AssetDetailView.as_view(), name="asset_detail"),
]