from django.shortcuts import render


def index(request):
    """Main page: candidates list with search and sorting."""
    return render(request, 'frontend/index.html')


def register(request):
    """Candidate registration form."""
    return render(request, 'frontend/register.html')


def candidate_detail(request, pk):
    """Candidate detail page."""
    return render(request, 'frontend/candidate_detail.html', {'candidate_id': pk})
