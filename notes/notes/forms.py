from django import forms
from tinymce.widgets import TinyMCE

class NoteForm(forms.Form):
    title = forms.CharField(label='Title', widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Document name'}) )
    note = forms.CharField(label='Note', widget=TinyMCE( mce_attrs={'width':'100%', 'height':'400px' ,'placeholder':'Document name'}) )

