from django import forms
from .models import LearningOutcome, Exam, ExamLOWeight

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
