from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe

from movies.models import Region
from .models import UserProfile

class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))

class CustomUserCreationForm(UserCreationForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Optional: choose the region you primarily purchase from.'
    )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('region',)

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})
        self.fields['region'].queryset = Region.objects.all().order_by('name')
        self.fields['region'].empty_label = 'Select a region (optional)'

    def save(self, commit=True):
        user = super().save(commit=commit)
        region = self.cleaned_data.get('region')
        if commit:
            profile = getattr(user, 'profile', None)
            if profile is None:
                profile = UserProfile.objects.create(user=user)
            profile.region = region
            profile.save()
        else:
            self._pending_region = region
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['region']
        widgets = {
            'region': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['region'].queryset = Region.objects.all().order_by('name')
        self.fields['region'].empty_label = 'Select a region'
