from django.test import TestCase
from django.urls import reverse

from .models import Grupo, GrupoMembro, Presente, Usuario


class ConviteGrupoFluxoTest(TestCase):
    """
    Cobre o fluxo de entrada por link de convite, incluindo o caso de quem
    ainda nao tem conta: o convite precisa sobreviver ao cadastro e o usuario
    deve cair na tela principal ja com o grupo selecionado.
    """

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')
        self.url_convite = reverse('convite_grupo', args=[self.grupo.codigo_convite])

    def _dados_cadastro(self, email='novo@exemplo.com', username='novo'):
        return {
            'email': email,
            'username': username,
            'first_name': 'Novo',
            'last_name': 'Usuario',
            'password1': 'SenhaForte!2026',
            'password2': 'SenhaForte!2026',
        }

    def test_convite_deslogado_redireciona_para_login_com_next(self):
        resposta = self.client.get(self.url_convite)
        self.assertRedirects(resposta, f"{reverse('login')}?next={self.url_convite}")

    def test_cadastro_respeita_next_e_consome_o_convite(self):
        """Regressao: o cadastro ignorava ?next=, jogava o usuario no dashboard
        sem grupo e ele terminava na tela de 'crie um grupo'."""
        resposta = self.client.post(
            f"{reverse('registro')}?next={self.url_convite}",
            self._dados_cadastro(),
            follow=True,
        )

        # Cadastro -> convite -> dashboard, sem passar por criar_grupo
        self.assertEqual(
            [url for url, _ in resposta.redirect_chain],
            [self.url_convite, reverse('dashboard')],
        )
        self.assertEqual(resposta.status_code, 200)

        usuario = Usuario.objects.get(email='novo@exemplo.com')
        self.assertEqual(usuario.grupo_ativo, self.grupo)
        self.assertTrue(GrupoMembro.objects.filter(grupo=self.grupo, usuario=usuario).exists())

    def test_cadastro_sem_next_continua_indo_para_o_dashboard(self):
        resposta = self.client.post(reverse('registro'), self._dados_cadastro())
        self.assertRedirects(resposta, reverse('dashboard'), target_status_code=302)

    def test_cadastro_ignora_next_para_host_externo(self):
        resposta = self.client.post(
            f"{reverse('registro')}?next=https://exemplo-malicioso.com/",
            self._dados_cadastro(),
        )
        self.assertRedirects(resposta, reverse('dashboard'), target_status_code=302)

    def test_convite_ativa_o_grupo_mesmo_com_outro_grupo_ja_ativo(self):
        outro = Grupo.objects.create(nome='Amigos do Trabalho')
        usuario = Usuario.objects.create_user(
            email='ja@exemplo.com', username='ja', password='SenhaForte!2026',
            first_name='Ja', last_name='Existe',
        )
        GrupoMembro.objects.create(grupo=outro, usuario=usuario)
        usuario.grupo_ativo = outro
        usuario.save()

        self.client.force_login(usuario)
        resposta = self.client.get(self.url_convite)
        self.assertRedirects(resposta, reverse('dashboard'))

        usuario.refresh_from_db()
        self.assertEqual(usuario.grupo_ativo, self.grupo)

    def test_convite_de_quem_ja_e_membro_leva_ao_dashboard(self):
        usuario = Usuario.objects.create_user(
            email='membro@exemplo.com', username='membro', password='SenhaForte!2026',
            first_name='Ja', last_name='Membro',
        )
        GrupoMembro.objects.create(grupo=self.grupo, usuario=usuario)

        self.client.force_login(usuario)
        resposta = self.client.get(self.url_convite)
        self.assertRedirects(resposta, reverse('dashboard'))

        usuario.refresh_from_db()
        self.assertEqual(usuario.grupo_ativo, self.grupo)
        self.assertEqual(GrupoMembro.objects.filter(grupo=self.grupo, usuario=usuario).count(), 1)

    def test_grupo_desativado_nao_entra(self):
        self.grupo.ativo = False
        self.grupo.save()
        usuario = Usuario.objects.create_user(
            email='x@exemplo.com', username='x', password='SenhaForte!2026',
            first_name='X', last_name='Y',
        )
        self.client.force_login(usuario)

        resposta = self.client.get(self.url_convite)
        self.assertRedirects(resposta, reverse("grupos_lista"), target_status_code=302)
        self.assertFalse(GrupoMembro.objects.filter(grupo=self.grupo, usuario=usuario).exists())


class ConvitePropagacaoNextTemplateTest(TestCase):
    """O ?next= precisa sobreviver a navegacao entre login e cadastro."""

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')
        self.url_convite = reverse('convite_grupo', args=[self.grupo.codigo_convite])

    def test_login_propaga_next_no_link_de_cadastro(self):
        resposta = self.client.get(f"{reverse('login')}?next={self.url_convite}")
        self.assertContains(resposta, f"{reverse('registro')}?next=")

    def test_registro_propaga_next_no_form_e_no_link_de_login(self):
        resposta = self.client.get(f"{reverse('registro')}?next={self.url_convite}")
        self.assertContains(resposta, 'name="next"')
        self.assertContains(resposta, f"{reverse('login')}?next=")


class ListaUsuariosImagemTest(TestCase):
    """
    As imagens dos presentes precisam ter tamanho fixo (360x270, 4:3 dentro do
    card de 360x428). Antes o tamanho vinha de aspect-ratio sobre a largura da
    coluna, e uma imagem alta esticava a linha inteira do grid.
    """

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')

        self.eu = Usuario.objects.create_user(
            email='eu@exemplo.com', username='eu', password='SenhaForte!2026',
            first_name='Eu', last_name='Mesmo',
        )
        self.outro = Usuario.objects.create_user(
            email='outro@exemplo.com', username='outro', password='SenhaForte!2026',
            first_name='Marcello', last_name='Silva',
        )
        for usuario in (self.eu, self.outro):
            GrupoMembro.objects.create(grupo=self.grupo, usuario=usuario)
            usuario.grupo_ativo = self.grupo
            usuario.save(update_fields=['grupo_ativo'])

        Presente.objects.create(
            grupo=self.grupo, usuario=self.outro,
            descricao='Perfume Dior Sauvage 200ml', preco='856.00',
        )

        self.client.force_login(self.eu)

    def test_caixa_de_imagem_tem_tamanho_fixo_nas_duas_visualizacoes(self):
        resposta = self.client.get(reverse('lista_usuarios'))
        self.assertEqual(resposta.status_code, 200)
        html = resposta.content.decode()

        # As duas views da pagina (por usuario e por produto) usam a caixa fixa
        self.assertEqual(html.count('presente-img-box bg-base-200'), 2)
        self.assertNotIn('aspect-[4/3]', html)

    def test_css_define_o_padrao_360x428(self):
        resposta = self.client.get(reverse('lista_usuarios'))
        html = resposta.content.decode()

        self.assertIn('max-width: 360px', html)
        self.assertIn('height: 270px', html)
        self.assertIn('object-fit: contain', html)
