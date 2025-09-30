from django.contrib import admin

from .models import Movie, Review, MovieRequest, MovieRequestVote

class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']

admin.site.register(Movie)
admin.site.register(Review)
admin.site.register(MovieRequest)
admin.site.register(MovieRequestVote)