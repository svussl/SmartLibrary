from django.urls import path
from . import views

# تعريف اسم التطبيق لاستخدامه في القوالب (Namespace)
# مثال للاستخدام في HTML: {% url 'library:home' %}
app_name = 'library'

urlpatterns = [
    # ==========================================
    # 1. روابط المصادقة (Authentication URLs)
    # ==========================================
    # صفحة إنشاء حساب طالب جديد
    path('register/', views.register, name='register'),
    
    # صفحة تسجيل الدخول
    path('login/', views.login_view, name='login'),
    
    # رابط تسجيل الخروج
    path('logout/', views.logout_view, name='logout'),

    # ==========================================
    # 2. روابط النظام الأساسية (Core URLs)
    # ==========================================
    # الصفحة الرئيسية (تعرض الكتب المقترحة ولوحة المشرف السريعة)
    path('', views.home, name='home'),
    
    # صفحة نتائج البحث الدلالي (تستخدم الذكاء الاصطناعي)
    path('search/', views.search_view, name='search'),
    
    # صفحة تفاصيل الكتاب (وتحوي التوصيات المشابهة وزر الاستعارة)
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),

    # ==========================================
    # 3. رابط الملف الشخصي (Profile URL)
    # ==========================================
    # صفحة الملف الشخصي وسجل الاستعارات للطالب
    path('profile/', views.profile_view, name='profile'),

    # ==========================================
    # 4. روابط التحليل والإحصاء (Analytics URL)
    # ==========================================
    # لوحة التحليلات الذكية (للمشرفين فقط)
    path('analytics/', views.analytics_dashboard, name='analytics'),

    # ==========================================
    # 5. روابط إدارة العمليات (Transactions URLs) - جديد
    # ==========================================
    # رابط طلب الاستعارة (يستخدمه الطالب عند ضغط زر "استعارة")
    path('borrow/<int:book_id>/', views.borrow_request, name='borrow_request'),
    
    # رابط إدارة العملية (يستخدمه المشرف للموافقة أو الإرجاع)
    # transaction_id: رقم العملية
    # action: نوع الإجراء (approve, return, reject)
    path('transaction/<int:transaction_id>/<str:action>/', views.manage_transaction, name='manage_transaction'),
]