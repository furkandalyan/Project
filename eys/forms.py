from django import forms
from django.contrib.auth import get_user_model

from .models import Course, LearningOutcome, Exam, ExamLOWeight, Announcement

User = get_user_model()

class LOForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ['title', 'description']
        labels = {
            'title': 'LO Başlığı',
            'description': 'LO Açıklaması',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'scheduled_at', 'description']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'name': 'Sınav Adı',
            'scheduled_at': 'Sınav Tarihi ve Saati',
            'description': 'Sınav Açıklaması',
        }

class ExamLOWeightForm(forms.ModelForm):
    class Meta:
        model = ExamLOWeight
        fields = ['learning_outcome', 'weight']


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'course', 'pinned']
        labels = {
            'title': 'Duyuru Başlığı',
            'body': 'Açıklama / Mesaj',
            'course': 'İlgili Ders (opsiyonel)',
            'pinned': 'Sabit',
        }
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
            'pinned': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            teacher_courses = Course.objects.filter(instructor=user)
            self.fields['course'].queryset = teacher_courses
        self.fields['course'].required = False
        self.fields['course'].empty_label = "Genel duyuru (tüm öğrenciler)"
        base_input_style = "width:100%; padding:12px 14px; border:1px solid #e2e2e2; border-radius:10px; font-size:15px; font-family:inherit; background:#fff;"
        textarea_style = base_input_style + " min-height:160px;"
        select_style = base_input_style + " background:#fdfdfd;"
        self.fields['title'].widget.attrs.update({
            'placeholder': 'Örn. Haftalık bilgilendirme, sınav duyurusu...',
            'style': base_input_style,
        })
        self.fields['body'].widget.attrs.update({
            'placeholder': 'Mesajınızı buraya yazın. Öğrenciler açıklamayı birebir görecek.',
            'style': textarea_style,
        })
        self.fields['course'].widget.attrs.update({
            'style': select_style,
        })
        self.fields['pinned'].widget.attrs.update({
            'style': 'width:auto;',
        })


class ProfileUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Yeni Parola",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Yeni parola (değiştirmek istemezsen boş bırak)",
            }
        ),
    )
    confirm_password = forms.CharField(
        label="Parola Tekrar",
        required=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Yeni parolayı tekrar gir",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Ad",
            "last_name": "Soyad",
            "email": "E-posta",
        }
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Adınızı girin",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Soyadınızı girin",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "iletisim@ornek.edu.tr",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_style = "width:100%; padding:12px 14px; border:1px solid #e2e2e2; border-radius:10px; font-size:15px; font-family:inherit; background:#fff;"
        for field in ["first_name", "last_name", "email", "new_password", "confirm_password"]:
            if field in self.fields:
                widget = self.fields[field].widget
                existing_style = widget.attrs.get("style", "")
                widget.attrs["style"] = base_style + existing_style

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password or confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("Yeni parola ile tekrar alanı eşleşmiyor.")
            if new_password and len(new_password) < 8:
                raise forms.ValidationError("Yeni parola en az 8 karakter olmalıdır.")
        return cleaned_data
