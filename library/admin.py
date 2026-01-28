from django.contrib import admin
from .models import Book, StudentProfile, Transaction, SearchLog

# ==========================================
# 1. تخصيص واجهة إدارة الكتب
# ==========================================
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    # الأعمدة التي تظهر في القائمة
    list_display = ('title', 'author', 'category', 'total_copies', 'available_copies', 'created_at')
    
    # حقول البحث
    search_fields = ('title', 'author', 'isbn', 'tags')
    
    # الفلاتر الجانبية
    list_filter = ('category', 'created_at')
    
    # الحقول للقراءة فقط (لا يمكن تعديلها يدوياً)
    readonly_fields = ('created_at',)
    
    # تقسيم الحقول في صفحة التعديل لترتيب أفضل
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('title', 'author', 'isbn', 'category')
        }),
        ('التفاصيل الذكية (AI)', {
            'fields': ('description', 'tags'),
            'description': 'يتم استخدام الوصف والوسوم في خوارزميات التوصية والبحث الدلالي'
        }),
        ('إدارة المخزون', {
            'fields': ('total_copies', 'available_copies', 'cover_image_url')
        }),
    )

# ==========================================
# 2. تخصيص واجهة ملفات الطلاب
# ==========================================
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'major')
    search_fields = ('student_id', 'user__username', 'user__email', 'major')
    list_filter = ('major',)

# ==========================================
# 3. تخصيص واجهة عمليات الإعارة (Transactions)
# ==========================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # الأعمدة الظاهرة (لاحظ استخدام status بدلاً من is_returned)
    list_display = ('book', 'student', 'status', 'request_date', 'borrow_date', 'return_date', 'is_overdue')
    
    # الفلاتر الجانبية (تم تصحيح الخطأ هنا)
    list_filter = ('status', 'request_date', 'borrow_date')
    
    # البحث
    search_fields = ('book__title', 'student__user__username', 'student__student_id')
    
    # إمكانية تعديل الحالة مباشرة من القائمة دون الدخول للتفاصيل
    list_editable = ('status',)
    
    # الإجراءات المخصصة (Bulk Actions)
    actions = ['approve_requests', 'mark_returned', 'reject_requests']

    @admin.action(description='✅ الموافقة على طلبات الاستعارة المحددة')
    def approve_requests(self, request, queryset):
        """
        إجراء جماعي لتحويل الطلبات من 'قيد الانتظار' إلى 'نشط'.
        يقوم تلقائياً بخصم النسخ وتحديد تاريخ الإعارة عبر دالة save() في الموديل.
        """
        updated_count = 0
        for trans in queryset:
            if trans.status == 'pending':
                trans.status = 'active'
                trans.save()
                updated_count += 1
        self.message_user(request, f"تمت الموافقة على {updated_count} طلب بنجاح.")

    @admin.action(description='↩️ تسجيل إرجاع الكتب المحددة')
    def mark_returned(self, request, queryset):
        """
        إجراء جماعي لتسجيل إرجاع الكتب.
        يعيد النسخ للمخزون تلقائياً.
        """
        updated_count = 0
        for trans in queryset:
            if trans.status == 'active':
                trans.status = 'returned'
                trans.save()
                updated_count += 1
        self.message_user(request, f"تم تسجيل إرجاع {updated_count} كتاب.")

    @admin.action(description='❌ رفض الطلبات المحددة')
    def reject_requests(self, request, queryset):
        """
        رفض طلبات الاستعارة.
        """
        rows_updated = queryset.update(status='rejected')
        self.message_user(request, f"تم رفض {rows_updated} طلب.")

# ==========================================
# 4. تخصيص واجهة سجلات البحث (Gap Analysis)
# ==========================================
@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'result_count', 'timestamp')
    list_filter = ('timestamp', 'result_count')
    search_fields = ('query_text',)
    readonly_fields = ('timestamp',)
    
    # عرض العمليات التي لم تجد نتائج بلون مختلف (اختياري، يظهر في التفاصيل)
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-timestamp')