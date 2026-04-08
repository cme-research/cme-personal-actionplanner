import datetime

from django import forms

from .models import Attachment, Note, Subtask, TodoItem, Topic


class TodoItemForm(forms.ModelForm):
    estimation_days = forms.IntegerField(
        required=False,
        min_value=0,
        label="Estimation (days)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Days"}),
    )
    estimation_hours = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=23,
        label="Estimation (hours)",
        widget=forms.NumberInput(attrs={"class": "form-control", "placeholder": "Hours"}),
    )

    class Meta:
        model = TodoItem
        fields = [
            "name",
            "description",
            "due_date",
            "priority",
            "item_type",
            "topic",
            "state",
            "recurrence",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "due_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "item_type": forms.TextInput(attrs={"class": "form-control"}),
            "topic": forms.Select(attrs={"class": "form-select"}),
            "state": forms.Select(attrs={"class": "form-select"}),
            "recurrence": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.estimation:
            total_seconds = int(self.instance.estimation.total_seconds())
            self.fields["estimation_days"].initial = total_seconds // 86400
            self.fields["estimation_hours"].initial = (total_seconds % 86400) // 3600

    def save(self, commit=True):
        instance = super().save(commit=False)
        days = self.cleaned_data.get("estimation_days") or 0
        hours = self.cleaned_data.get("estimation_hours") or 0
        if days or hours:
            instance.estimation = datetime.timedelta(days=days, hours=hours)
        else:
            instance.estimation = None
        if commit:
            instance.save()
        return instance


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }


class SubtaskForm(forms.ModelForm):
    class Meta:
        model = Subtask
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Subtask name"}
            ),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 2, "placeholder": "Add a note..."}
            ),
        }


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["file"]
        widgets = {
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search todos..."}
        ),
    )
    topic = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        required=False,
        empty_label="All Topics",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    state = forms.ChoiceField(
        choices=[("", "All States")] + list(TodoItem.State.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    priority = forms.ChoiceField(
        choices=[("", "All Priorities")] + list(TodoItem.Priority.choices),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
