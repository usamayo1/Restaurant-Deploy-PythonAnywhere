from django import forms

from .models import Feedback


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["rating", "message"]
        widgets = {
            "rating": forms.Select(
                choices=[
                    (5, "Excellent"),
                    (4, "Very Good"),
                    (3, "Good"),
                    (2, "Fair"),
                    (1, "Poor"),
                ],
                attrs={
                    "autocomplete": "off",
                },
            ),
            "message": forms.Textarea(
                attrs={
                    "placeholder": "Tell us about your experience...",
                    "rows": 4,
                    "autocomplete": "off",
                }
            ),
        }
