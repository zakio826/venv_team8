from django.urls import path

from . import views


app_name = 'tracker'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
    path('asset-list/', views.AssetListView.as_view(), name="asset_list"),
    path('asset-detail/<str:asset_name>/', views.AssetDetailView.as_view(), name="asset_detail"),
    path('create_group/', views.create_group, name='create_group'),
    path('join_group/', views.join_group, name='join_group'),
    path('mypage/', views.mypage, name='mypage'),
    path('group_detail/<int:group_id>/', views.group_detail, name='group_detail'),
]