---
name: Modern SaaS Design System
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1b1b1d'
  surface-container: '#1f1f21'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#343536'
  on-surface: '#e4e2e4'
  on-surface-variant: '#c5c6cd'
  inverse-surface: '#e4e2e4'
  inverse-on-surface: '#303032'
  outline: '#8f9097'
  outline-variant: '#44474d'
  surface-tint: '#b9c7e4'
  primary: '#b9c7e4'
  on-primary: '#233148'
  primary-container: '#0a192f'
  on-primary-container: '#74829d'
  inverse-primary: '#515f78'
  secondary: '#adc7ff'
  on-secondary: '#002e68'
  secondary-container: '#4a8eff'
  on-secondary-container: '#00285b'
  tertiary: '#b8c8da'
  on-tertiary: '#223240'
  tertiary-container: '#091a27'
  on-tertiary-container: '#738394'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#b9c7e4'
  on-primary-fixed: '#0d1c32'
  on-primary-fixed-variant: '#39475f'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc7ff'
  on-secondary-fixed: '#001a41'
  on-secondary-fixed-variant: '#004493'
  tertiary-fixed: '#d4e4f6'
  tertiary-fixed-dim: '#b8c8da'
  on-tertiary-fixed: '#0d1d2a'
  on-tertiary-fixed-variant: '#394857'
  background: '#131315'
  on-background: '#e4e2e4'
  surface-variant: '#343536'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  body-base:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  label-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
  code:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-page: 32px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Marka ve Stil

Bu tasarım sistemi, "yıldırım hızında" performans ve sarsılmaz bir profesyonellik hissi uyandırmak için kurgulanmıştır. Linear'ın işlevsel verimliliği ile Stripe'ın görsel estetiğini harmanlayarak, teknoloji odaklı kullanıcılar için optimize edilmiş bir deneyim sunar.

**Tasarım Stili:**
*   **Minimalizm:** Gereksiz tüm süslemelerden arındırılmış, boşlukların (whitespace) hiyerarşiyi belirlediği bir yapı.
*   **Glassmorphism Accents:** Katman derinliğini belirtmek için kullanılan yarı saydam yüzeyler ve arka plan bulanıklıkları (backdrop blur).
*   **Hız Odaklılık:** Düşük gecikme hissi uyandıran keskin geçişler ve yüksek kontrastlı etkileşim alanları.

Hedef kitle, karmaşık verileri hızlıca işlemek isteyen geliştiriciler, ürün yöneticileri ve teknoloji profesyonelleridir. UI, "güvenilir, teknik ve çevik" bir karakter sergiler.

## Renkler

Renk paleti, derinlik ve odaklanma sağlamak için koyu mod (Dark Mode) üzerine inşa edilmiştir.

*   **Ana Arka Plan (Deep Navy):** Derin lacivert tonu, arayüzün temelini oluşturur ve göz yorgunluğunu azaltır.
*   **Vurgu Rengi (Electric Blue):** Etkileşimli öğeler, butonlar ve aktif durumlar için yüksek enerjili bir mavi tercih edilmiştir.
*   **Yardımcı Renk (Slate Gray):** İkincil metinler ve sınır çizgileri için nötr bir denge sağlar.
*   **Durum Renkleri (High-Contrast):**
    *   **Aktif (Green):** Canlı yeşil, sistemin operasyonel olduğunu belirtir.
    *   **Meşgul (Red):** Keskin kırmızı, aciliyet ve yoğunluk ifade eder.
    *   **Beklemede (Amber):** Sıcak kehribar, geçiş süreçlerini temsil eder.

## Tipografi

Bu tasarım sisteminde tipografi, işlevselliğin merkezindedir. **Inter** font ailesi, ekran okunabilirliği ve teknik duruşu nedeniyle seçilmiştir.

*   **Hiyerarşi:** Başlıklarda negatif 'letter-spacing' kullanılarak daha sıkı ve modern bir görünüm elde edilir. 
*   **Okunabilirlik:** Gövde metinlerinde (body) satır yüksekliği (line-height) ferah tutularak uzun süreli okumalarda konfor sağlanır.
*   **Mikro-Metinler:** Etiketler ve küçük açıklamalar için orta ağırlıkta (medium) fontlar kullanılarak netlik korunur.

## Yerleşim ve Boşluklar

Tasarım, 8 piksellik (8pt) bir ızgara sistemi üzerine kuruludur. Bu, tüm bileşenlerin birbiriyle matematiksel bir uyum içinde olmasını sağlar.

*   **Esnek Izgara (Fluid Grid):** İçerik, ekran genişliğine göre genişler ancak okunabilirlik için maksimum genişlik sınırlarına (max-width) tabidir.
*   **Yoğunluk:** SaaS panel yapısı gereği dikey boşluklar (stacking) minimize edilmiştir; bu sayede tek ekranda daha fazla veri görünür kılınır.
*   **Hizalama:** Tüm metinler ve ikonlar, temel 4px birimiyle hizalanarak "pixel-perfect" bir görünüm elde edilir.

## Derinlik ve Katmanlar

Z-eksenindeki hiyerarşi, gölgelerden ziyade cam efekti (glassmorphism) ve ton farklılıklarıyla yönetilir.

*   **Cam Efekti:** Modal pencereler, yan menüler ve açılır listeler için `backdrop-filter: blur(12px)` ve düşük opaklıklı beyaz (`rgba(255, 255, 255, 0.05)`) dolgu kullanılır.
*   **Sınır Çizgileri:** Katmanları ayırmak için sert gölgeler yerine, `1px` kalınlığında, Slate Gray tonunda yarı saydam çizgiler tercih edilir.
*   **Işık Kaynağı:** Sayfanın üst kısmından gelen hafif bir degrade (gradient), aktif yüzeyleri arka plandan ayırmak için kullanılır.

## Formlar ve Şekiller

Keskinlik ve profesyonellik vurgusu için düşük yarıçaplı (radius) köşeler tercih edilmiştir.

*   **Soft Corners:** Standart bileşenler (butonlar, giriş alanları) 4px (`0.25rem`) köşe yumuşatmasına sahiptir.
*   **Kapsayıcılar:** Kartlar ve paneller 8px (`0.5rem`) köşe değerini aşmaz.
*   **Dinamizm:** Tam yuvarlak (pill-shaped) yapılar yalnızca durum rozetleri (badges) için kullanılır, bu da onların sistem genelinde ayrışmasını sağlar.

## Bileşenler

Bileşen kütüphanesi, hız ve netlik prensiplerini yansıtır.

*   **Butonlar:** Ana butonlar Electric Blue dolgulu, ikincil butonlar ise ince çerçeveli (ghost) yapıdadır. Hover durumunda "glow" efekti (düşük opaklıklı dış parıltı) uygulanır.
*   **Durum Rozetleri (Status Badges):** Yüksek kontrastlıdır. Örneğin, "Aktif" rozeti koyu yeşil arka plan üzerine parlak yeşil metinle kurgulanır.
*   **Giriş Alanları (Inputs):** Odaklanıldığında (focus), kenarlık rengi Electric Blue'ya döner ve arka plandaki lacivert tonu hafifçe açılır.
*   **Kartlar:** Arka planla kontrast oluşturacak şekilde bir ton daha açık navy kullanılır ve 1px saydam sınır çizgisiyle çevrelenir.
*   **Veri Listeleri:** Stripe tarzı, satırlar arası ince ayırıcılar ve üzerine gelindiğinde (hover) beliren hafif renk değişimleri ile veri takibi kolaylaştırılır.