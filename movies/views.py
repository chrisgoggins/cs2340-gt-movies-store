from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import localtime

from .models import Movie, Review, Rating, Region, MovieRequest, MovieRequestVote
from cart.models import Item
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, F

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()

    movies = movies.annotate(
        avg_rating=Avg('ratings__value'),
        rating_count=Count('ratings')
    )
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    rating_data = movie.ratings.aggregate(
        average=Avg('value'),
        total=Count('id')
    )
    user_rating_value = None
    if request.user.is_authenticated:
        user_rating = movie.ratings.filter(user=request.user).first()
        if user_rating:
            user_rating_value = user_rating.value
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data['average_rating'] = rating_data['average']
    template_data['rating_count'] = rating_data['total']
    template_data['user_rating'] = user_rating_value
    template_data['rating_choices'] = [1, 2, 3, 4, 5]
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
def rate_movie(request, id):
    if request.method != 'POST':
        return redirect('movies.show', id=id)

    movie = get_object_or_404(Movie, id=id)
    action = request.POST.get('action', 'set')

    if action == 'clear':
        Rating.objects.filter(movie=movie, user=request.user).delete()
        return redirect('movies.show', id=id)

    rating_value = request.POST.get('rating')

    try:
        rating_value = int(rating_value)
    except (TypeError, ValueError):
        return redirect('movies.show', id=id)

    if rating_value < 1 or rating_value > 5:
        return redirect('movies.show', id=id)

    Rating.objects.update_or_create(
        movie=movie,
        user=request.user,
        defaults={'value': rating_value}
    )

    return redirect('movies.show', id=id)


@login_required
def popularity_map(request):
    regions = Region.objects.all()

    region_payload = []
    for region in regions:
        top_movies_qs = (
            Item.objects.filter(order__region=region)
            .values('movie_id')
            .annotate(title=F('movie__name'), total=Sum('quantity'))
            .order_by('-total')
        )
        top_movies = [
            {
                'movie_id': row['movie_id'],
                'title': row['title'],
                'total': row['total'],
            }
            for row in top_movies_qs[:5]
        ]
        total_purchases = sum(row['total'] for row in top_movies)
        region_payload.append(
            {
                'id': region.id,
                'name': region.name,
                'code': region.code,
                'center_lat': region.center_lat,
                'center_lng': region.center_lng,
                'top_movies': top_movies,
                'total_purchases': total_purchases,
            }
        )

    global_trending_qs = (
        Item.objects.values('movie_id')
        .annotate(title=F('movie__name'), total=Sum('quantity'))
        .order_by('-total')[:5]
    )
    global_trending = [
        {
            'movie_id': row['movie_id'],
            'title': row['title'],
            'total': row['total'],
        }
        for row in global_trending_qs
    ]

    user_purchase_history = []
    user_items = (
        Item.objects.filter(order__user=request.user)
        .select_related('movie', 'order__region')
        .order_by('-order__date')[:15]
    )
    for item in user_items:
        order_region = item.order.region
        user_purchase_history.append(
            {
                'order_id': item.order_id,
                'movie': item.movie.name,
                'quantity': item.quantity,
                'region_code': order_region.code if order_region else 'unassigned',
                'region_name': order_region.name if order_region else 'Unassigned',
                'date': localtime(item.order.date).strftime('%Y-%m-%d %H:%M'),
            }
        )

    user_region = None
    profile = getattr(request.user, 'profile', None)
    if profile and profile.region:
        user_region = profile.region.code

    template_data = {
        'title': 'Local Popularity Map',
        'regions': regions,
        'global_trending': global_trending,
        'region_payload': region_payload,
        'user_purchase_history': user_purchase_history,
        'user_region_code': user_region,
    }

    return render(request, 'movies/popularity_map.html', {'template_data': template_data})

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
def requests_all_page(request):
    template_data = { 'title': 'Movie Requests Voting' }

    requests = MovieRequest.objects.annotate(
        total_votes=Count("votes")
    ).order_by("-total_votes")

    voted_ids = MovieRequestVote.objects.filter(user=request.user).values_list("request_id", flat=True)

    template_data['requests'] = requests
    template_data['voted_ids'] = voted_ids

    return render(request, 'movies/requests_all.html', { 'template_data': template_data })

@login_required
def request_vote(request, id):
    if request.method != "POST":
        return redirect("movies.requests_all")

    movie_request = get_object_or_404(MovieRequest, id=id)
    existing_user_vote = MovieRequestVote.objects.filter(request=movie_request, user=request.user)

    if existing_user_vote:
        existing_user_vote.delete()
    else:
        MovieRequestVote.objects.create(request=movie_request, user=request.user)

    return redirect("movies.requests_all")
