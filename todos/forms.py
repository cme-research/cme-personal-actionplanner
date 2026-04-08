from django import forms

from .models import Attachment, Note, Subtask, TodoItem, Topic


class TodoItemForm(forms.ModelForm):
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
