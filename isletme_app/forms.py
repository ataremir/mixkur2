from django import forms
from django.contrib.auth import get_user_model
from .models import IsletmeProfil

User = get_user_model()


class IsletmeKayitForm(forms.Form):
    """
    İşletme kayıt formu.
    Hem kullanıcı hem de işletme profil bilgileri tek formda toplanır.
    """
    # Kullanıcı bilgileri
    username = forms.CharField(
        max_length=150,
        label='Kullanıcı Adı',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': 'Kullanıcı adınızı girin',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        label='E-posta',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': 'E-posta adresinizi girin',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )
    password_confirm = forms.CharField(
        label='Şifre Tekrar',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )

    # İşletme bilgileri
    isletme_adi = forms.CharField(
        max_length=200,
        label='İşletme Adı',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': 'İşletmenizin adını girin',
        })
    )
    telefon = forms.CharField(
        max_length=15,
        label='Telefon',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': '05xx xxx xx xx',
        })
    )
    sektor = forms.ChoiceField(
        choices=IsletmeProfil.Sektor.choices,
        label='Sektör',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
        })
    )
    adres = forms.CharField(
        label='Açık Adres',
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': 'Tam adresinizi girin',
            'rows': 3,
        })
    )
    il = forms.CharField(
        max_length=50,
        label='İl',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': 'İl',
        })
    )
    ilce = forms.CharField(
        max_length=50,
        label='İlçe',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg '
                     'text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 '
                     'focus:ring-1 focus:ring-cyan-500 transition-all duration-300',
            'placeholder': 'İlçe',
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu e-posta adresi zaten kayıtlı.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Şifreler eşleşmiyor.')

        return cleaned_data
