from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # مسار لوحة تحكم الإدارة
    path('admin/', admin.site.urls),
    
    # ربط جميع روابط تطبيق المكتبة
    path('', include('library.urls')),
]

# لتتمكن من رؤية صور أغلفة الكتب أثناء التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)