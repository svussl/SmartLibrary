from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.utils import timezone
from .models import Book, SearchLog, Transaction, StudentProfile
from .ai_engine import SmartLibraryAI
from .forms import UserRegistrationForm

# ==========================================
# دالة مساعدة لفحص الصلاحيات (Admin Check)
# ==========================================
def is_admin(user):
    """
    تقوم هذه الدالة بالتحقق مما إذا كان المستخدم مشرفاً (Superuser).
    تستخدم لحماية لوحة التحليلات وإدارة العمليات.
    """
    return user.is_superuser

# ==========================================
# 1. نظام المصادقة (Authentication)
# ==========================================

def register(request):
    """صفحة إنشاء حساب طالب جديد"""
    if request.user.is_authenticated:
        return redirect('library:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # إنشاء ملف الطالب
            StudentProfile.objects.create(
                user=user,
                student_id=form.cleaned_data['student_id'],
                major=form.cleaned_data['major']
            )
            
            login(request, user)
            messages.success(request, f"مرحباً بك {user.first_name}! تم إنشاء حسابك بنجاح.")
            return redirect('library:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'library/register.html', {'form': form})

def login_view(request):
    """صفحة تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('library:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"أهلاً بعودتك، {user.first_name}!")
                return redirect('library:home')
            else:
                messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة.")
        else:
            messages.error(request, "الرجاء التحقق من البيانات المدخلة.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'library/login.html', {'form': form})

def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    messages.info(request, "تم تسجيل الخروج بنجاح.")
    return redirect('library:login')

# ==========================================
# 2. الوظائف الرئيسية (Core Features)
# ==========================================

@login_required
def home(request):
    """الصفحة الرئيسية: تعرض أحدث الكتب أو التوصيات"""
    # 1. جلب الكتب المقترحة (AI Recommendations) إذا توفرت بيانات
    ai_engine = SmartLibraryAI()
    recommended_books = []
    
    # محاولة جلب توصيات بناءً على تخصص الطالب أو آخر استعارة
    if hasattr(request.user, 'studentprofile'):
        # هنا يمكن تطوير المنطق لجلب كتب حسب التخصص
        # حالياً سنجلب أحدث الكتب كافتراضي
        pass

    # إذا لم توجد توصيات خاصة، نعرض أحدث الكتب المضافة
    if not recommended_books:
        books = Book.objects.all().order_by('-created_at')[:8]
    else:
        books = recommended_books

    return render(request, 'library/home.html', {'books': books})

@login_required
def search_view(request):
    """صفحة البحث الدلالي (Semantic Search)"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        # 1. تسجيل عملية البحث لتحليل الفجوة لاحقاً
        # نبحث أولاً هل سيجد نتائج أم لا، ثم نسجل
        ai_engine = SmartLibraryAI()
        results = ai_engine.semantic_search(query)
        
        # تسجيل في السجل
        SearchLog.objects.create(
            user=request.user,
            query_text=query,
            result_count=len(results)
        )
    
    return render(request, 'library/search.html', {'results': results, 'query': query})

@login_required
def book_detail(request, book_id):
    """صفحة تفاصيل الكتاب مع التوصيات المشابهة"""
    book = get_object_or_404(Book, id=book_id)
    
    # 1. جلب كتب مشابهة (AI)
    ai_engine = SmartLibraryAI()
    similar_titles = ai_engine.get_recommendations(book.id)
    similar_books = Book.objects.filter(title__in=similar_titles)
    
    # 2. التحقق من حالة الاستعارة للطالب الحالي
    active_transaction = Transaction.objects.filter(
        student__user=request.user,
        book=book,
        is_returned=False
    ).exclude(status='rejected').first()

    context = {
        'book': book,
        'similar_books': similar_books,
        'active_transaction': active_transaction
    }
    return render(request, 'library/detail.html', context)

# ==========================================
# 3. إدارة العمليات (Transactions)
# ==========================================

@login_required
def borrow_request(request, book_id):
    """معالجة طلب استعارة كتاب"""
    book = get_object_or_404(Book, id=book_id)
    student = get_object_or_404(StudentProfile, user=request.user)

    # التحقق من توفر نسخ
    if book.available_copies < 1:
        messages.error(request, "عذراً، لا توجد نسخ متاحة حالياً.")
        return redirect('library:book_detail', book_id=book.id)

    # التحقق من عدم وجود طلب مسبق نشط
    existing_loan = Transaction.objects.filter(
        student=student, 
        book=book, 
        is_returned=False
    ).exclude(status='rejected').exists()

    if existing_loan:
        messages.warning(request, "لديك طلب مسبق لهذا الكتاب قيد المعالجة أو لديك الكتاب بالفعل.")
        return redirect('library:book_detail', book_id=book.id)

    # إنشاء الطلب
    Transaction.objects.create(
        student=student,
        book=book,
        status='pending',
        request_date=timezone.now()
    )
    
    messages.success(request, "تم إرسال طلب الاستعارة بنجاح! بانتظار موافقة المشرف.")
    return redirect('library:profile')

@login_required
def profile_view(request):
    """الملف الشخصي للطالب وسجل استعاراته"""
    try:
        student = request.user.studentprofile
    except StudentProfile.DoesNotExist:
        messages.error(request, "ملف الطالب غير موجود.")
        return redirect('library:home')

    transactions = Transaction.objects.filter(student=student).order_by('-request_date')
    
    return render(request, 'library/profile.html', {
        'student': student,
        'transactions': transactions
    })

# ==========================================
# 4. لوحة الإدارة والتحليلات (Admin Only)
# ==========================================

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """
    لوحة التحليلات (Dashboard).
    تعرض إحصائيات بصرية وأرقام تساعد في اتخاذ القرار.
    """
    
    # 1. قائمة الطلبات المعلقة
    pending_requests = Transaction.objects.filter(status='pending').order_by('request_date')

    # 2. الكتب المعارة حالياً
    active_loans = Transaction.objects.filter(status='active').order_by('due_date')

    # 3. الأكثر استعارة (Top 5)
    most_borrowed = Transaction.objects.values('book__title') \
        .annotate(total_borrows=Count('id')) \
        .order_by('-total_borrows')[:5]

    # 4. متوسط مدة الاستعارة (تم تصحيح الخطأ هنا) ✅
    # نستخدم status='returned' بدلاً من is_returned=True لأنها غير مدعومة في الفلتر المباشر
    avg_duration_data = Transaction.objects.filter(status='returned') \
        .annotate(duration=ExpressionWrapper(
            F('return_date') - F('borrow_date'), 
            output_field=DurationField()
        )) \
        .values('book__title') \
        .annotate(avg_days=Avg('duration')) \
        .order_by('-avg_days')[:5]

    # 5. تحليل الفجوة (Gap Analysis)
    gap_analysis = SearchLog.objects.filter(result_count=0) \
        .values('query_text') \
        .annotate(attempts=Count('id')) \
        .order_by('-attempts')[:5]

    context = {
        'pending_requests': pending_requests,
        'active_loans': active_loans,
        'most_borrowed': most_borrowed,
        'avg_duration_data': avg_duration_data,
        'gap_analysis': gap_analysis,
    }
    
    return render(request, 'library/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def manage_transaction(request, transaction_id, action):
    """
    دالة للمشرف للموافقة على الطلبات أو تسجيل الإرجاع من خلال الرابط المباشر
    """
    trans = get_object_or_404(Transaction, id=transaction_id)
    
    if action == 'approve':
        if trans.book.available_copies > 0:
            trans.status = 'active'
            # يقوم مودل Transaction بتحديث التواريخ وخصم النسخة تلقائياً عند الحفظ
            trans.save()
            messages.success(request, f"تمت الموافقة على طلب الطالب {trans.student.user.get_full_name()}.")
        else:
            messages.error(request, "لا توجد نسخ كافية للموافقة على هذا الطلب.")
            
    elif action == 'reject':
        trans.status = 'rejected'
        trans.save()
        messages.info(request, "تم رفض الطلب.")
        
    elif action == 'return':
        trans.status = 'returned'
        # سيقوم المودل بزيادة النسخ وتحديد تاريخ الإرجاع
        trans.save()
        messages.success(request, "تم تسجيل إرجاع الكتاب بنجاح.")

    return redirect('library:analytics')