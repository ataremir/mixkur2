from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import IsletmeProfil
from .forms import IsletmeKayitForm

User = get_user_model()


# ─────────────────────────── DEKORATÖRLER ───────────────────────────

def isletme_veya_admin_required(view_func):
    """
    View dekoratörü: Sadece ISLETME veya ADMIN rolündeki kullanıcılar erişebilir.
    COURIER rolündekiler kesinlikle GİREMEZ.
    """
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/giris/')

        user_role = getattr(request.user, 'role', None)

        if user_role in ['ISLETME', 'ADMIN'] or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        # COURIER veya SHOP → ana sayfaya yönlendir
        return redirect('http://anatoliabox.store/')

    return _wrapped


# ─────────────────────────── GİRİŞ / ÇIKIŞ ───────────────────────────

def isletme_giris(request):
    """
    isletme.anatoliabox.store/giris/ — İşletme giriş sayfası.
    Sadece ISLETME ve ADMIN rolündeki kullanıcılar giriş yapabilir.
    """
    if request.user.is_authenticated:
        user_role = getattr(request.user, 'role', None)
        if user_role in ['ISLETME', 'ADMIN'] or request.user.is_staff:
            return redirect('/dashboard/')
        # Giriş yapmış ama yetkisiz kullanıcıyı ana sayfaya at
        return redirect('http://anatoliabox.store/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            user_role = getattr(user, 'role', None)

            # COURIER rolü kesinlikle giremez
            if user_role == 'COURIER':
                messages.error(request, 'Bu panele erişim yetkiniz bulunmamaktadır.')
                return render(request, 'isletme/giris.html')

            # SHOP rolü de bu panele giremesin
            if user_role == 'SHOP':
                messages.error(request, 'Bu panel sadece işletmeler içindir.')
                return render(request, 'isletme/giris.html')

            login(request, user)
            next_url = request.GET.get('next', '/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')

    return render(request, 'isletme/giris.html')


def isletme_cikis(request):
    """Çıkış yap ve giriş sayfasına yönlendir."""
    logout(request)
    return redirect('/giris/')


# ─────────────────────────── KAYIT ───────────────────────────

def isletme_kayit(request):
    """
    isletme.anatoliabox.store/kayit/ — İşletme kayıt formu.
    Başarılı kayıtta otomatik giriş yapılıp dashboard'a yönlendirilir.
    """
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        form = IsletmeKayitForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Kullanıcı oluştur
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        role='ISLETME',
                        phone_number=form.cleaned_data['telefon'],
                    )

                    # İşletme profili oluştur
                    IsletmeProfil.objects.create(
                        user=user,
                        isletme_adi=form.cleaned_data['isletme_adi'],
                        telefon=form.cleaned_data['telefon'],
                        sektor=form.cleaned_data['sektor'],
                        adres=form.cleaned_data['adres'],
                        il=form.cleaned_data.get('il', ''),
                        ilce=form.cleaned_data.get('ilce', ''),
                    )

                    # Otomatik giriş yap
                    login(request, user)
                    messages.success(request, f'Hoş geldiniz, {user.username}! İşletmeniz başarıyla kaydedildi.')
                    return redirect('/dashboard/')

            except Exception as e:
                messages.error(request, f'Kayıt sırasında bir hata oluştu: {str(e)}')
    else:
        form = IsletmeKayitForm()

    return render(request, 'isletme/kayit.html', {'form': form})


# ─────────────────────────── DASHBOARD ───────────────────────────

@login_required(login_url='/giris/')
@isletme_veya_admin_required
def isletme_dashboard(request):
    """
    isletme.anatoliabox.store/dashboard/ — İşletme yönetim paneli.
    Sadece ISLETME ve ADMIN rolündekiler erişebilir.
    """
    user = request.user
    profil = None

    try:
        profil = user.isletme_profil
    except IsletmeProfil.DoesNotExist:
        # Admin kullanıcılarının profili olmayabilir
        pass

    context = {
        'user': user,
        'profil': profil,
    }

    return render(request, 'isletme/dashboard.html', context)


@login_required(login_url='/giris/')
@isletme_veya_admin_required
def isletme_profil_duzenle(request):
    """
    İşletme profil düzenleme sayfası.
    """
    user = request.user

    try:
        profil = user.isletme_profil
    except IsletmeProfil.DoesNotExist:
        messages.error(request, 'Profil bulunamadı.')
        return redirect('/dashboard/')

    if request.method == 'POST':
        profil.isletme_adi = request.POST.get('isletme_adi', profil.isletme_adi)
        profil.telefon = request.POST.get('telefon', profil.telefon)
        profil.sektor = request.POST.get('sektor', profil.sektor)
        profil.adres = request.POST.get('adres', profil.adres)
        profil.il = request.POST.get('il', profil.il)
        profil.ilce = request.POST.get('ilce', profil.ilce)
        profil.save()
        messages.success(request, 'Profil bilgileriniz güncellendi.')
        return redirect('/dashboard/')

    context = {
        'profil': profil,
        'sektor_secenekleri': IsletmeProfil.Sektor.choices,
    }
    return render(request, 'isletme/profil_duzenle.html', context)
