from django import forms
from django.contrib.auth import get_user_model
from ckeditor.widgets import CKEditorWidget

from .models import (
    Course,
    CourseThreshold,
    LearningOutcome,
    Exam,
    ExamLOWeight,
    Announcement,
    AnnouncementComment,
    Assignment,
    Submission,
    AssignmentCriterion,
    AssignmentGroup,
    CourseMaterial,
    AssignmentTemplate,
)

User = get_user_model()


class LOForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ["title", "description"]
        labels = {
            "title": "LO Başlığı",
            "description": "LO Açıklaması",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["name", "scheduled_at", "description"]
        widgets = {
            "scheduled_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }
        labels = {
            "name": "Sınav Adı",
            "scheduled_at": "Sınav Tarihi ve Saati",
            "description": "Sınav Açıklaması",
        }


class ExamLOWeightForm(forms.ModelForm):
    class Meta:
        model = ExamLOWeight
        fields = ["learning_outcome", "weight"]


class CourseThresholdForm(forms.ModelForm):
    class Meta:
        model = CourseThreshold
        fields = ["stable_min", "watch_min", "pass_min"]
        labels = {
            "stable_min": "İstikrarlı alt sınırı",
            "watch_min": "Takipte alt sınırı",
            "pass_min": "Geçme eşiği",
        }
        help_texts = {
            "stable_min": "Bu puan ve üzeri öğrenciler İstikrarlı sayılır.",
            "watch_min": "Bu puan ve üzeri (İstikrarlı altı) öğrenciler Takipte sayılır.",
            "pass_min": "Bu puan ve üzeri öğrenciler dersi geçer olarak işaretlenir.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_style = "width:100%; padding:10px 12px; border:1px solid #e2e2e2; border-radius:10px; font-size:15px;"
        for name, field in self.fields.items():
            field.widget.attrs["style"] = base_style
            field.widget.attrs["step"] = "0.01"
            field.widget.attrs["min"] = "0"
            field.widget.attrs["max"] = "100"


class AnnouncementForm(forms.ModelForm):
    body = forms.CharField(widget=CKEditorWidget(), label="Açıklama / Mesaj")

    class Meta:
        model = Announcement
        fields = ["title", "body", "course", "attachment", "pinned"]
        labels = {
            "title": "Duyuru Başlığı",
            "course": "İlgili Ders (opsiyonel)",
            "attachment": "Dosya Eki (opsiyonel)",
            "pinned": "Sabit",
        }
        widgets = {
            "pinned": forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            teacher_courses = Course.objects.filter(instructor=user)
            self.fields["course"].queryset = teacher_courses
        self.fields["course"].required = False
        self.fields["course"].empty_label = "Genel duyuru (tüm öğrenciler)"
        base_input_style = (
            "width:100%; padding:12px 14px; border:1px solid #e2e2e2; border-radius:10px; "
            "font-size:15px; font-family:inherit; background:#fff;"
        )
        select_style = base_input_style + " background:#fdfdfd;"
        self.fields["title"].widget.attrs.update(
            {
                "placeholder": "Örn. Haftalık bilgilendirme, sınav duyurusu...",
                "style": base_input_style,
            }
        )
        self.fields["course"].widget.attrs.update(
            {
                "style": select_style,
            }
        )
        self.fields["attachment"].widget.attrs.update(
            {
                "style": base_input_style,
            }
        )
        self.fields["pinned"].widget.attrs.update(
            {
                "style": "width:auto;",
            }
        )


class CommentForm(forms.ModelForm):
    class Meta:
        model = AnnouncementComment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Yorumunuzu buraya yazın..."}
            ),
        }
        labels = {
            "body": "",
        }


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


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = [
            "course",
            "title",
            "description",
            "due_at",
            "max_score",
            "attachment",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        labels = {
            "course": "Ders",
            "title": "Başlık",
            "description": "Açıklama",
            "due_at": "Teslim Tarihi",
            "max_score": "Maksimum Puan",
            "attachment": "Dosya eki",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["course"].queryset = Course.objects.filter(instructor=user)
        self.fields["course"].empty_label = "Ders seçin"
        self.fields["course"].required = True
        base_style = "width:100%; padding:10px 12px; border:1px solid #e2e2e2; border-radius:10px; font-size:14px;"
        for name, field in self.fields.items():
            if hasattr(field, "widget"):
                field.widget.attrs.setdefault("style", base_style)


class SubmissionForm(forms.ModelForm):
    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
        label="Dosya(lar)",
    )

    class Meta:
        model = Submission
        fields = ["file", "text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4, "placeholder": "Açıklama / notlar (opsiyonel)"}),
        }
        labels = {
            "file": "Dosya",
            "text": "Not",
        }


class GradeSubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        criteria = kwargs.pop("criteria", None)
        existing_scores = kwargs.pop("existing_scores", {})
        super().__init__(*args, **kwargs)
        if criteria:
            for crit in criteria:
                field_name = f"criterion_{crit.id}"
                self.fields[field_name] = forms.DecimalField(
                    required=False,
                    max_digits=5,
                    decimal_places=2,
                    label=f"{crit.title} (max {crit.max_score})",
                )
                if existing_scores and crit.id in existing_scores:
                    self.fields[field_name].initial = existing_scores[crit.id].score
                self.fields[f"{field_name}_feedback"] = forms.CharField(
                    required=False,
                    widget=forms.Textarea(attrs={"rows": 2}),
                    label=f"{crit.title} geri bildirim",
                )
                if existing_scores and crit.id in existing_scores:
                    self.fields[f"{field_name}_feedback"].initial = existing_scores[crit.id].feedback

    class Meta:
        model = Submission
        fields = ["score", "feedback"]
        widgets = {
            "feedback": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "score": "Puan",
            "feedback": "Geribildirim",
        }


class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = ["course", "week", "title", "description", "attachment"]
        labels = {
            "course": "Ders",
            "week": "Hafta",
            "title": "Başlık",
            "description": "Açıklama",
            "attachment": "Dosya",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["course"].queryset = Course.objects.filter(instructor=user)
        self.fields["course"].empty_label = "Ders seçin"


class AssignmentTemplateForm(forms.ModelForm):
    class Meta:
        model = AssignmentTemplate
        fields = ["title", "description", "max_score", "attachment"]
        labels = {
            "title": "Şablon Başlığı",
            "description": "Açıklama",
            "max_score": "Maksimum Puan",
            "attachment": "Dosya",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class AssignmentCriterionForm(forms.ModelForm):
    class Meta:
        model = AssignmentCriterion
        fields = ["title", "max_score", "order"]
        labels = {
            "title": "Kriter",
            "max_score": "Maksimum Puan",
            "order": "Sıra",
        }


class AssignmentGroupForm(forms.ModelForm):
    class Meta:
        model = AssignmentGroup
        fields = ["name", "members"]
        labels = {
            "name": "Grup adı",
            "members": "Üyeler",
        }
        widgets = {
            "members": forms.SelectMultiple(attrs={"size": 8}),
        }

    def __init__(self, *args, **kwargs):
        students_qs = kwargs.pop("students_qs", None)
        super().__init__(*args, **kwargs)
        if students_qs is not None:
            self.fields["members"].queryset = students_qs
