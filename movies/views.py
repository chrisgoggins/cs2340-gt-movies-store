from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, MovieRequest, MovieRequestVote
from django.contrib.auth.decorators import login_required
from django.db.models import Count

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
def requests_page(request):
    template_data = { 'title': 'Movie Requests' }
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if name and description:
                MovieRequest.objects.create(
                    name=name,
                    description=description,
                    user=request.user
                )
            return redirect('movies.requests')
        elif action == 'delete':
            req_id = request.POST.get('request_id')
            if req_id:
                movie_request = get_object_or_404(MovieRequest, id=req_id, user=request.user)
                movie_request.delete()
            return redirect('movies.requests')

    # GET (or fallthrough): list current user's requests
    my_requests = MovieRequest.objects.filter(user=request.user).order_by('-created_at')
    template_data['my_requests'] = my_requests
    return render(request, 'movies/requests.html', { 'template_data': template_data })

@login_required
def community_requests(request):
    template_data = { 'title': 'Community Requests' }
    # List all requests with vote counts
    requests_qs = MovieRequest.objects.all().order_by('-created_at').annotate(
        vote_count=Count('votes')
    )

    # Determine which requests current user has voted on
    voted_ids = set(
        MovieRequestVote.objects.filter(user=request.user).values_list('request_id', flat=True)
    )

    template_data['requests'] = requests_qs
    template_data['voted_ids'] = voted_ids
    return render(request, 'movies/requests_all.html', { 'template_data': template_data })

@login_required
def toggle_request_vote(request, req_id):
    if request.method != 'POST':
        return redirect('movies.requests_all')
    movie_request = get_object_or_404(MovieRequest, id=req_id)
    existing = MovieRequestVote.objects.filter(request=movie_request, user=request.user).first()
    if existing:
        existing.delete()
    else:
        MovieRequestVote.objects.create(request=movie_request, user=request.user)
    return redirect('movies.requests_all')
