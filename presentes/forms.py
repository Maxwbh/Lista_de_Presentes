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
    avatar = forms.CharField(required=False, widget=forms.HiddenInput(attrs={
        'id': 'avatar-input'
    }))
    foto = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'hidden',
        'id': 'foto-input',
        'accept': 'image/*'
    }))

    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'username', 'password1', 'password2', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class EditarPerfilForm(forms.ModelForm):
    """Form para edição do perfil do usuário (sem alteração de senha)."""
    first_name = forms.CharField(required=True, label='Nome', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Seu nome'
    }))
    last_name = forms.CharField(required=True, label='Sobrenome', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Seu sobrenome'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'seu@email.com'
    }))
    telefone = forms.CharField(required=False, label='Telefone', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': '(00) 00000-0000'
    }))
    avatar = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'id': 'avatar-input'}))
    foto = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'hidden', 'id': 'foto-input', 'accept': 'image/*'
    }))
    remover_foto = forms.BooleanField(required=False, widget=forms.HiddenInput(attrs={'id': 'remover-foto-input'}))

    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email', 'telefone', 'username', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este email já está em uso por outra conta.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = Usuario.objects.filter(username__iexact=username).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')
        return username


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
