from django.urls import path

from . import views


app_name = 'tracker'
urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('inquiry/', views.InquiryView.as_view(), name="inquiry"),
    path('asset-list/', views.AssetListView.as_view(), name="asset_list"),
    path('asset-detail/<int:id>/', views.AssetDetailView.as_view(), name="asset_detail"),
    path('asset-multi-create/', views.AssetMultiCreateView.as_view(), name="asset_multi_create"),

    path('asset-create/', views.AssetCreateView.as_view(), name="asset_create"),
    path('asset-create/image-add/<int:id>/', views.ImageAddView.as_view(), name="image_add"),
    path('asset-create/item-add/<int:id>/', views.ItemAddView.as_view(), name="item_add"),
    path('asset-create/history-add/<int:id>/', views.HistoryAddView.as_view(), name="history_add"),

    path('asset-check/image-add/<int:id>/', views.ImageAddView.as_view(), name="check_image_add"),
    path('asset-check/<int:id>/', views.HistoryAddView.as_view(), name="asset_check"),
    # path('asset-check/history-add/<int:id>/', views.HistoryAddView.as_view(), name="history_add"),

    path('create_group/', views.create_group, name='create_group'),
    path('join_group/', views.join_group, name='join_group'),
    path('mypage/', views.mypage, name='mypage'),
    path('group_detail/<int:group_id>/', views.group_detail, name='group_detail'),

    path('test-page/<int:id>/', views.TestPageView.as_view(), name="test_page"),
]