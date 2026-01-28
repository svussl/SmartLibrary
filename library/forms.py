from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile

class UserRegistrationForm(forms.ModelForm):
    # حقول إضافية
    student_id = forms.CharField(
        label="الرقم الجامعي", 
        max_length=20, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'مثال: S-12345'})
    )
    major = forms.CharField(
        label="التخصص الدراسي", 
        max_length=100, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-control rounded-pill', 'placeholder': 'مثال: هندسة برمجيات'})
    )
    
    password = forms.CharField(
        label="كلمة المرور", 
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-pill'})
    )
    password_confirm = forms.CharField(
        label="تأكيد كلمة المرور", 
        widget=forms.PasswordInput(attrs={'class': 'form-control rounded-pill'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-pill'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
        }
        labels = {
            'username': 'اسم المستخدم (للأغراض التقنية)',
            'email': 'البريد الإلكتروني الجامعي',
            'first_name': 'الاسم الأول',
            'last_name': 'الكنية',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("كلمات المرور غير متطابقة")