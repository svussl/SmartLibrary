from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# ==========================================
# 1. جدول الكتب (Library Books)
# ==========================================
class Book(models.Model):
    """
    يمثل هذا النموذج الكتاب المادي في المكتبة.
    يحتوي على البيانات الببليوغرافية بالإضافة إلى حقول الذكاء الاصطناعي.
    """
    title = models.CharField(max_length=255, verbose_name="عنوان الكتاب")
    author = models.CharField(max_length=255, verbose_name="المؤلف")
    isbn = models.CharField(max_length=13, unique=True, verbose_name="رقم ISBN")
    description = models.TextField(blank=True, verbose_name="وصف الكتاب")
    
    # حقل تخزين الكلمات المفتاحية المستخرجة ذكياً (Semantic Tags)
    # يستخدم هذا الحقل في خوارزميات البحث والتوصية
    tags = models.TextField(blank=True, verbose_name="الوسوم الذكية")
    
    category = models.CharField(max_length=100, blank=True, verbose_name="التصنيف")
    
    # إدارة المخزون
    total_copies = models.PositiveIntegerField(default=1, verbose_name="إجمالي النسخ")
    available_copies = models.PositiveIntegerField(default=1, verbose_name="النسخ المتاحة")
    
    # حقل لتخزين رابط غلاف الكتاب (اختياري)
    cover_image_url = models.URLField(blank=True, null=True, verbose_name="رابط الغلاف")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "كتاب"
        verbose_name_plural = "الكتب"
        ordering = ['-created_at']


# ==========================================
# 2. ملف الطالب (Student Profile)
# ==========================================
class StudentProfile(models.Model):
    """
    يربط مستخدم Django ببيانات الطالب الأكاديمية.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="المستخدم")
    student_id = models.CharField(max_length=20, unique=True, verbose_name="الرقم الجامعي")
    major = models.CharField(max_length=100, verbose_name="التخصص الأكاديمي")
    
    # البصمة المعرفية (Interest Fingerprint): يمكن استخدامها مستقبلاً لتخزين اهتمامات الطالب كمتجه
    interest_fingerprint = models.TextField(blank=True, verbose_name="البصمة المعرفية")

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

    class Meta:
        verbose_name = "ملف الطالب"
        verbose_name_plural = "ملفات الطلاب"


# ==========================================
# 3. جدول العمليات والإعارة (Transactions)
# ==========================================
class Transaction(models.Model):
    """
    يسجل حركة الكتب بين المكتبة والطلاب.
    يتضمن منطقاً ذكياً لتغيير حالة المخزون وتحديد التواريخ تلقائياً.
    """
    # حالات الطلب الممكنة
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار (طلب إلكتروني)'),
        ('active', 'جاري (تم التسليم للطالب)'),
        ('returned', 'تم الإرجاع للمكتبة'),
        ('rejected', 'مرفوض'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="الكتاب")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, verbose_name="الطالب")
    
    # التواريخ
    request_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    borrow_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاستلام الفعلي")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الاستحقاق")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الإرجاع")
    
    # حالة الطلب
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    
    # تقييم الطالب (لتحسين التوصيات مستقبلاً)
    user_rating = models.IntegerField(null=True, blank=True, verbose_name="التقييم (1-5)")

    def save(self, *args, **kwargs):
        """
        تجاوز دالة الحفظ لتطبيق المنطق التلقائي (Business Logic Automation).
        """
        # الحالة 1: الموافقة على الطلب وتسليم الكتاب (تحول من أي حالة إلى Active)
        # نتأكد أننا لم نحدد تاريخ الإعارة مسبقاً لمنع الخصم المزدوج
        if self.status == 'active' and not self.borrow_date:
            self.borrow_date = timezone.now()
            # مدة الإعارة الافتراضية 14 يوماً
            self.due_date = timezone.now() + timedelta(days=14)
            
            # خصم نسخة من المخزون
            if self.book.available_copies > 0:
                self.book.available_copies -= 1
                self.book.save()
            
        # الحالة 2: إرجاع الكتاب (تحول إلى Returned)
        # نتأكد أننا لم نحدد تاريخ الإرجاع مسبقاً
        if self.status == 'returned' and not self.return_date:
            self.return_date = timezone.now()
            
            # إعادة النسخة للمخزون
            self.book.available_copies += 1
            self.book.save()
            
        # حفظ التغييرات
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """خاصية لمعرفة هل الكتاب متأخر عن موعده"""
        if self.status == 'active' and self.due_date and timezone.now() > self.due_date:
            return True
        return False

    def __str__(self):
        return f"{self.book.title} - {self.student.user.username} ({self.get_status_display()})"

    class Meta:
        verbose_name = "عملية إعارة"
        verbose_name_plural = "عمليات الإعارة"
        ordering = ['-request_date']


# ==========================================
# 4. سجل البحث (Gap Analysis Logs)
# ==========================================
class SearchLog(models.Model):
    """
    يسجل كلمات البحث التي يستخدمها الطلاب.
    الهدف: تحليل الفجوة (Gap Analysis) لمعرفة الكتب المطلوبة وغير المتوفرة.
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المستخدم")
    query_text = models.CharField(max_length=255, verbose_name="نص البحث")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="وقت البحث")
    result_count = models.IntegerField(default=0, verbose_name="عدد النتائج")

    def __str__(self):
        return f"بحث عن: {self.query_text} ({self.result_count} نتائج)"

    class Meta:
        verbose_name = "سجل بحث"
        verbose_name_plural = "سجلات البحث"
        ordering = ['-timestamp']