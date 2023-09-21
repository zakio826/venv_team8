from django.urls import path

from . import views


app_name = 'tracker'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
    path('asset-list/', views.AssetListView.as_view(), name="asset_list"),
    path('asset-detail/<int:id>/', views.AssetDetailView.as_view(), name="asset_detail"),
    path('asset-create/', views.AssetCreateView.as_view(), name="asset_create"),
    path('image-add/<int:id>/', views.ImageAddView.as_view(), name="image_add"),
    path('item-add/<int:id>/', views.ItemAddView.as_view(), name="item_add"),
    path('group-join/', views.GroupJoinView.as_view(), name="group_join"),
]