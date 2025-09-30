from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='movies.index'),
    path('<int:id>/', views.show, name='movies.show'),
    path('<int:id>/review/create/', views.create_review, name='movies.create_review'),
    path('<int:id>/review/<int:review_id>/edit/', views.edit_review, name='movies.edit_review'),
    path('<int:id>/review/<int:review_id>/delete/', views.delete_review, name='movies.delete_review'),
    path('requests/', views.requests_page, name='movies.requests'),
    path('requests/all/', views.requests_all_page, name='movies.requests_all'),
    path('requests/<int:id>/vote/', views.request_vote, name='movies.request_vote'),
]
