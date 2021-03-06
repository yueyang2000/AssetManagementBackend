''' URLS for App asset, start with api/asset/ '''
from django.urls import path

from . import views

urlpatterns = [
    path('list', views.asset_list),
    path('add', views.asset_add),
    path('edit', views.asset_edit),
    path('history', views.asset_history),
    path('query', views.asset_query),
    path('available', views.asset_available_list),
    path('retire', views.asset_retire),

    path('category/tree', views.category_tree),
    path('category/delete', views.category_delete),
    path('category/add', views.category_add),
    path('category/edit', views.category_edit),

    path('custom/edit', views.custom_attr_edit),
    path('custom/list', views.custom_attr_list),

    path('allocate', views.asset_allocate),
]
