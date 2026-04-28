import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Siparis, KuryeProfil

def harita_view(request, siparis_id):
    """
    Sipariş takip haritasını render eder.
    A: Kurye, B: İşletme, C: Müşteri
    """
    siparis = get_object_or_404(Siparis, id=siparis_id)
    return render(request, 'demo/harita.html', {
        'siparis': siparis,
        'google_maps_api_key': 'BURAYA_GOOGLE_MAPS_API_KEY_GELECEK'
    })

@csrf_exempt
def kurye_konum_guncelle(request):
    """
    Kuryenin telefonundan gelen anlık konum bilgisini kaydeder.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            lat = data.get('lat')
            lng = data.get('lng')

            if user_id and lat and lng:
                profil = KuryeProfil.objects.get(user_id=user_id)
                profil.anlik_enlem = float(lat)
                profil.anlik_boylam = float(lng)
                profil.save()
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'invalid_request'}, status=400)
