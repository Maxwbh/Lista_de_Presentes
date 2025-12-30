from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Presente, Grupo, GrupoMembro

class UsuarioRegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'seu@email.com'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Seu nome'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Seu sobrenome'
    }))
    
    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'username', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'seu@email.com'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Senha'
    }))

class PresenteForm(forms.ModelForm):
    url_imagem = forms.URLField(
        required=False,
        label='URL da Imagem',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://exemplo.com/imagem.jpg',
            'id': 'url-imagem-input'
        })
    )

    class Meta:
        model = Presente
        fields = ['descricao', 'url', 'preco', 'imagem']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva o presente...'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://... (opcional)'
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'style': 'display: none;'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Garantir que URL não seja obrigatória
        self.fields['url'].required = False
        # Reordenar campos
        self.order_fields(['descricao', 'url_imagem', 'imagem', 'url', 'preco'])


class GrupoForm(forms.ModelForm):
    """Form para criacao e edicao de grupos"""
    url_imagem = forms.URLField(
        required=False,
        label='URL da Imagem do Grupo',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://exemplo.com/logo-grupo.jpg',
            'id': 'grupo-url-imagem-input'
        })
    )

    class Meta:
        model = Grupo
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do grupo',
                'maxlength': 200
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descricao do grupo (opcional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descricao'].required = False
        self.order_fields(['nome', 'descricao', 'url_imagem'])
