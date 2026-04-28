from django.shortcuts import render
from django.views import View

class LandingPageView(View):
    """
    Ana domain (anatoliabox.store) için Coming Soon sayfası.
    """
    def get(self, request):
        return render(request, 'index.html')
