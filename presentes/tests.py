import contextlib
import re
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse

from .models import (
    Compra, Grupo, GrupoMembro, MercadoLivreToken, Notificacao, Presente, PrecoHistorico,
    PushSubscription, SugestaoCompra,
    Usuario,
)
from .mercadolivre_api import _titulo_da_descricao, buscar_produto, extrair_ids, obter_access_token
from .push import enviar_push
from .scrapers import ScraperFactory, limpar_url_rastreio
from .relevancia import calcular_relevancia, resultado_relevante
from .services import IAService


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


class ListaUsuariosCardUniformeTest(TestCase):
    """
    Todos os cards precisam ter a mesma altura. O que quebrava isso era a linha
    de preco do card comprado: selo "Comprado" + preco + temperatura + melhor
    oferta nao cabiam nos 328px uteis, a linha quebrava em duas e o card ficava
    19px mais alto (447 em vez de 428), levando a fileira inteira junto.

    Temperatura e melhor oferta agora aparecem so em item ativo - que e como a
    visualizacao "Por Membro" da mesma pagina ja se comportava. O selo saiu do
    corpo do card e virou o indicador "Ja comprado" no rodape.
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

        self.client.force_login(self.eu)

    def _presente(self, descricao, status):
        presente = Presente.objects.create(
            grupo=self.grupo, usuario=self.outro,
            descricao=descricao, preco='12345.00', status=status,
        )
        # sugestao mais barata: e ela que alimenta a pilula de melhor oferta
        SugestaoCompra.objects.create(
            grupo=self.grupo, presente=presente,
            preco_sugerido='146.20', local_compra='Loja Teste',
        )
        return presente

    def test_item_ativo_mostra_a_melhor_oferta(self):
        self._presente('Perfume importado', 'ATIVO')

        html = self.client.get(reverse('lista_usuarios')).content.decode()
        self.assertIn('Melhor oferta encontrada', html)

    def test_item_comprado_nao_mostra_melhor_oferta(self):
        self._presente('Perfume importado', 'COMPRADO')

        html = self.client.get(reverse('lista_usuarios')).content.decode()
        self.assertNotIn('Melhor oferta encontrada', html)
        self.assertIn('Comprado', html)

    def test_selo_comprado_nao_ocupa_linha_propria_acima_do_titulo(self):
        """O selo discreto no corpo do card deu lugar ao banner COMPRADO,
        que fica logo abaixo da imagem e ocupa a largura toda."""
        self._presente('Perfume importado', 'COMPRADO')

        html = self.client.get(reverse('lista_usuarios')).content.decode()
        # o selo antigo tinha 'mb-2 self-start' por estar sozinho acima do titulo
        self.assertNotIn('bg-base-300 text-base-content/60 mb-2 self-start', html)
        self.assertIn('<div class="presente-banner-comprado">', html)


class ItemCompradoNaoPodeSerCompradoDeNovoTest(TestCase):
    """
    Na visualizacao por produto o card de item comprado ainda mostrava o botao
    "Comprar". O backend recusava a segunda compra, mas o usuario so descobria
    depois de clicar e confirmar, e recebia um aviso de erro.
    """

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')
        self.eu = Usuario.objects.create_user(
            email='eu@exemplo.com', username='eu', password='SenhaForte!2026',
            first_name='Eu', last_name='Mesmo',
        )
        self.dono = Usuario.objects.create_user(
            email='dono@exemplo.com', username='dono', password='SenhaForte!2026',
            first_name='Marcello', last_name='Silva',
        )
        for usuario in (self.eu, self.dono):
            GrupoMembro.objects.create(grupo=self.grupo, usuario=usuario)
            usuario.grupo_ativo = self.grupo
            usuario.save(update_fields=['grupo_ativo'])

        self.presente = Presente.objects.create(
            grupo=self.grupo, usuario=self.dono,
            descricao='Mata Formigas 10g, Formicel c/ 2 unidades', preco='28.00',
        )
        self.client.force_login(self.eu)

    def _html_lista(self):
        return self.client.get(reverse('lista_usuarios')).content.decode()

    def _comprar(self):
        self.presente.status = 'COMPRADO'
        self.presente.save(update_fields=['status'])

    def test_item_ativo_mostra_o_botao_comprar(self):
        html = self._html_lista()
        self.assertIn('<i class="bi bi-bag-heart"></i> Comprar', html)
        self.assertNotIn('<div class="presente-banner-comprado">', html)

    def test_item_comprado_nao_mostra_nada_de_compra(self):
        """Sem botao Comprar, sem sugestoes de lojas e sem link para a loja:
        nada que convide a comprar de novo."""
        SugestaoCompra.objects.create(
            grupo=self.grupo, presente=self.presente,
            preco_sugerido='19.90', local_compra='Loja Teste',
        )
        self.presente.url = 'https://loja.exemplo.com/produto'
        self.presente.save(update_fields=['url'])
        self._comprar()

        html = self._html_lista()
        self.assertNotIn('<i class="bi bi-bag-heart"></i> Comprar', html)
        self.assertNotIn('sugestões de lojas', html)
        self.assertNotIn('Ver produto original', html)

    def test_item_comprado_mostra_o_banner(self):
        self._comprar()

        html = self._html_lista()
        self.assertIn('<div class="presente-banner-comprado">', html)
        self.assertIn('Comprado', html)

    def test_so_a_imagem_fica_em_cinza_nao_o_card(self):
        """O filter fica na caixa da imagem. No card inteiro ele atingiria
        toda a subarvore e deixaria o banner cinza tambem."""
        self._comprar()

        html = self._html_lista()
        self.assertIn('presente-comprado"', html)
        self.assertIn('.presente-comprado .presente-img-box', html)
        # a opacidade vai no filter: a classe opacity-75 perde para o
        # animate-slide-up, que termina em opacity:1 com fill-mode both
        self.assertIn('filter: grayscale(1) opacity(0.75)', html)
        self.assertNotIn("{% if presente.status == 'COMPRADO' %}grayscale", html)

    def test_backend_recusa_a_segunda_compra(self):
        primeira = self.client.post(reverse('marcar_comprado', args=[self.presente.pk]))
        self.assertEqual(primeira.status_code, 302)

        self.presente.refresh_from_db()
        self.assertEqual(self.presente.status, 'COMPRADO')
        self.assertEqual(Compra.objects.filter(presente=self.presente).count(), 1)

        # segunda tentativa (ex.: POST direto, botao antigo em cache, dois cliques)
        segunda = self.client.post(reverse('marcar_comprado', args=[self.presente.pk]))
        self.assertEqual(segunda.status_code, 302)
        self.assertEqual(
            Compra.objects.filter(presente=self.presente).count(), 1,
            'a segunda compra nao pode gerar um novo registro',
        )

    def test_nao_e_possivel_comprar_o_proprio_presente(self):
        meu = Presente.objects.create(
            grupo=self.grupo, usuario=self.eu, descricao='Presente meu', preco='10.00',
        )
        self.client.post(reverse('marcar_comprado', args=[meu.pk]))

        meu.refresh_from_db()
        self.assertEqual(meu.status, 'ATIVO')
        self.assertEqual(Compra.objects.filter(presente=meu).count(), 0)


class RelevanciaDeResultadoTest(TestCase):
    """
    A busca de preco aceitava qualquer card que a pagina de resultados
    devolvesse, sem olhar o titulo. Um "Mata Formigas Formicel de R$ 28"
    terminava com melhor oferta de R$ 219 apontando para um serum facial.
    """

    FORMICEL = 'Mata Formigas 10g, Formicel c/ 2 unidades'

    def test_produto_sem_relacao_e_recusado(self):
        """O caso real relatado: serum facial no lugar do mata-formigas."""
        titulo = ('Serum TheSkcare Anti-envelhecimento de Celulas Tronco '
                  'de Maca com Colageno 30ml')
        self.assertEqual(calcular_relevancia(self.FORMICEL, titulo), 0.0)
        self.assertFalse(resultado_relevante(self.FORMICEL, titulo))

    def test_mesmo_produto_com_titulo_diferente_e_aceito(self):
        for titulo in (
            'Mata Formigas Formicel Gel 10g - 2 unidades',
            'Formicel Gel Mata Formigas Caseiras Tecnocell',
        ):
            with self.subTest(titulo=titulo):
                self.assertTrue(resultado_relevante(self.FORMICEL, titulo))

    def test_titulo_de_loja_verborragico_nao_e_punido(self):
        """Loja costuma encher o titulo de ruido; isso nao pode derrubar um
        resultado correto."""
        self.assertTrue(resultado_relevante(
            'Christian Dior Sauvage Eau De Toilette 200ml',
            'Perfume Masculino Dior Sauvage Eau de Toilette 200ml Importado Lacrado',
        ))

    def test_acessorio_do_produto_certo_e_recusado(self):
        """Acessorio e mais barato e venceria a ordenacao por menor preco."""
        presente = 'Smartwatch HUAWEI WATCH GT 6 Pro 46mm'
        for titulo in (
            'Pulseira de Silicone para Huawei Watch',
            'Pelicula de Vidro para Huawei Watch GT 6 Pro',
            'Capa Protetora para Huawei Watch GT 6',
        ):
            with self.subTest(titulo=titulo):
                self.assertFalse(resultado_relevante(presente, titulo))

    def test_acessorio_e_aceito_quando_o_presente_e_o_acessorio(self):
        self.assertTrue(resultado_relevante(
            'Capa de Silicone para controle PS5',
            'Capa de Silicone Protetora para Controle PS5 DualSense',
        ))

    def test_resultado_sem_titulo_e_recusado(self):
        """Sem titulo nao ha o que conferir - era por onde o produto errado
        entrava."""
        for titulo in ('', '   ', None):
            with self.subTest(titulo=titulo):
                self.assertFalse(resultado_relevante(self.FORMICEL, titulo))

    def test_numeros_e_unidades_nao_aproximam_produtos_diferentes(self):
        """"10g" e "2 unidades" nao identificam nada sozinhos."""
        self.assertFalse(resultado_relevante(
            self.FORMICEL, 'Creme Dental Infantil 10g kit com 2 unidades',
        ))

    def test_acentuacao_e_caixa_nao_atrapalham(self):
        self.assertTrue(resultado_relevante(
            'Máquina de Café Expresso Automática',
            'MAQUINA DE CAFE EXPRESSO AUTOMATICA INOX',
        ))


class SalvarSugestoesFiltraProdutoErradoTest(TestCase):
    """O filtro tambem vale para o que vem da IA, que erra o produto do mesmo
    jeito que o scraper."""

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')
        self.dono = Usuario.objects.create_user(
            email='dono@exemplo.com', username='dono', password='SenhaForte!2026',
            first_name='Marcello', last_name='Silva',
        )
        GrupoMembro.objects.create(grupo=self.grupo, usuario=self.dono)
        self.presente = Presente.objects.create(
            grupo=self.grupo, usuario=self.dono,
            descricao='Mata Formigas 10g, Formicel c/ 2 unidades', preco='28.00',
        )

    def test_sugestao_da_ia_com_produto_errado_nao_e_salva(self):
        IAService._salvar_sugestoes(self.presente, [
            {'loja': 'Magazine Luiza', 'produto': 'Serum TheSkcare Anti-envelhecimento 30ml',
             'url': 'https://magazineluiza.com.br/serum', 'preco': 219.66},
            {'loja': 'Zoom', 'produto': 'Serum TheSkcare Anti-envelhecimento 30ml',
             'url': 'https://zoom.com.br/serum', 'preco': 219.66},
        ])
        self.assertEqual(SugestaoCompra.objects.filter(presente=self.presente).count(), 0)

    def test_sugestao_da_ia_com_produto_certo_e_salva_com_o_titulo(self):
        IAService._salvar_sugestoes(self.presente, [
            {'loja': 'Amazon', 'produto': 'Mata Formigas Formicel Gel 10g 2 unidades',
             'url': 'https://amazon.com.br/formicel', 'preco': 28.00},
        ])
        sugestoes = SugestaoCompra.objects.filter(presente=self.presente)
        self.assertEqual(sugestoes.count(), 1)
        self.assertEqual(sugestoes.first().titulo_produto,
                         'Mata Formigas Formicel Gel 10g 2 unidades')

    def test_sugestao_da_ia_sem_o_campo_produto_nao_e_salva(self):
        """Era o formato antigo: sem titulo, nada podia ser conferido."""
        IAService._salvar_sugestoes(self.presente, [
            {'loja': 'Amazon', 'url': 'https://amazon.com.br/x', 'preco': 28.00},
        ])
        self.assertEqual(SugestaoCompra.objects.filter(presente=self.presente).count(), 0)

    def test_preco_de_produto_errado_nao_entra_no_historico(self):
        """Era o que estourava a temperatura do card em +684%."""
        IAService._salvar_sugestoes(self.presente, [
            {'loja': 'Zoom', 'produto': 'Serum TheSkcare Anti-envelhecimento 30ml',
             'url': 'https://zoom.com.br/serum', 'preco': 219.66},
        ])
        self.assertEqual(PrecoHistorico.objects.filter(presente=self.presente).count(), 0)


class BuscaDePrecoDescartaProdutoErradoTest(TestCase):
    """Caminho ponta a ponta do scraper, que foi onde o erro apareceu."""

    HTML_ZOOM = """
    <html><body>
      <div data-testid="product-card">
        <h2 data-testid="product-card::name">Serum TheSkcare Anti-envelhecimento 30ml</h2>
        <p data-testid="product-card::store-name">Menor preço via Magazine Luiza</p>
        <strong data-testid="product-card::price">R$ 219,66</strong>
        <a data-testid="product-card::card" href="/beleza/serum">ver</a>
      </div>
      <div data-testid="product-card">
        <h2 data-testid="product-card::name">Mata Formigas Formicel Gel 10g 2 unidades</h2>
        <p data-testid="product-card::store-name">Menor preço via Amazon</p>
        <strong data-testid="product-card::price">R$ 28,00</strong>
        <a data-testid="product-card::card" href="/casa/formicel">ver</a>
      </div>
    </body></html>
    """

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')
        self.dono = Usuario.objects.create_user(
            email='dono@exemplo.com', username='dono', password='SenhaForte!2026',
            first_name='Marcello', last_name='Silva',
        )
        GrupoMembro.objects.create(grupo=self.grupo, usuario=self.dono)
        self.presente = Presente.objects.create(
            grupo=self.grupo, usuario=self.dono,
            descricao='Mata Formigas 10g, Formicel c/ 2 unidades', preco='28.00',
        )

    def test_scraper_extrai_o_titulo_do_card(self):
        resposta = mock.Mock(status_code=200, content=self.HTML_ZOOM.encode())
        resposta.raise_for_status = mock.Mock()
        with mock.patch('presentes.services.requests.get', return_value=resposta):
            produtos = IAService.buscar_preco_zoom('Mata Formigas Formicel')

        self.assertEqual(len(produtos), 2)
        self.assertEqual(produtos[0]['titulo'], 'Serum TheSkcare Anti-envelhecimento 30ml')
        self.assertEqual(produtos[1]['titulo'], 'Mata Formigas Formicel Gel 10g 2 unidades')

    def test_so_o_resultado_do_produto_certo_vira_sugestao(self):
        resposta = mock.Mock(status_code=200, content=self.HTML_ZOOM.encode())
        resposta.raise_for_status = mock.Mock()

        with mock.patch('presentes.services.requests.get', return_value=resposta), \
                mock.patch.object(IAService, 'buscar_sugestoes_gemini',
                                  return_value=(False, 'sem chave')), \
                mock.patch.object(IAService, 'buscar_preco_buscape', return_value=[]), \
                mock.patch.object(IAService, 'buscar_imagem_para_presente', return_value=None):
            sucesso, _ = IAService.buscar_sugestoes_reais(self.presente)

        self.assertTrue(sucesso)
        sugestoes = list(SugestaoCompra.objects.filter(presente=self.presente))
        self.assertEqual(len(sugestoes), 1)
        self.assertEqual(sugestoes[0].titulo_produto,
                         'Mata Formigas Formicel Gel 10g 2 unidades')
        self.assertEqual(float(sugestoes[0].preco_sugerido), 28.00)

    def test_quando_nada_corresponde_nenhuma_sugestao_e_criada(self):
        html_so_errado = self.HTML_ZOOM.replace(
            '<h2 data-testid="product-card::name">Mata Formigas Formicel Gel 10g 2 unidades</h2>',
            '<h2 data-testid="product-card::name">Tablet Apple iPad 11 128GB</h2>',
        )
        resposta = mock.Mock(status_code=200, content=html_so_errado.encode())
        resposta.raise_for_status = mock.Mock()

        with mock.patch('presentes.services.requests.get', return_value=resposta), \
                mock.patch.object(IAService, 'buscar_sugestoes_gemini',
                                  return_value=(False, 'sem chave')), \
                mock.patch.object(IAService, 'buscar_preco_buscape', return_value=[]), \
                mock.patch.object(IAService, 'buscar_imagem_para_presente', return_value=None):
            sucesso, mensagem = IAService.buscar_sugestoes_reais(self.presente)

        self.assertFalse(sucesso)
        self.assertIn('corresponde', mensagem)
        self.assertEqual(SugestaoCompra.objects.filter(presente=self.presente).count(), 0)
        self.assertEqual(PrecoHistorico.objects.filter(presente=self.presente).count(), 0)


class LimparHistoricoPrecosTest(TestCase):
    """
    O filtro de relevancia impede novos precos errados, mas nao desfaz os que
    ja estao gravados - e sao eles que mantem a temperatura errada no card.
    """

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia Silva')
        self.dono = Usuario.objects.create_user(
            email='dono@exemplo.com', username='dono', password='SenhaForte!2026',
            first_name='Marcello', last_name='Silva',
        )
        GrupoMembro.objects.create(grupo=self.grupo, usuario=self.dono)

        # o caso relatado: item de R$ 28 com um ponto de R$ 219,66 de outro produto
        self.presente = Presente.objects.create(
            grupo=self.grupo, usuario=self.dono,
            descricao='Mata Formigas 10g, Formicel c/ 2 unidades', preco='28.00',
        )
        PrecoHistorico.objects.create(presente=self.presente, preco='28.00',
                                      loja='Amazon', fonte='cadastro')
        PrecoHistorico.objects.create(presente=self.presente, preco='27.50',
                                      loja='Amazon', fonte='pesquisa_semanal')
        self.ponto_errado = PrecoHistorico.objects.create(
            presente=self.presente, preco='219.66', loja='Zoom', fonte='sugestao')

    def _rodar(self, *args):
        saida = StringIO()
        call_command('limpar_historico_precos', *args, stdout=saida)
        return saida.getvalue()

    def test_sem_aplicar_nada_e_removido(self):
        saida = self._rodar()

        self.assertIn('219.66', saida)
        self.assertIn('--aplicar', saida)
        self.assertEqual(PrecoHistorico.objects.filter(presente=self.presente).count(), 3)

    def test_com_aplicar_o_ponto_errado_sai_e_os_certos_ficam(self):
        self._rodar('--aplicar')

        restantes = PrecoHistorico.objects.filter(presente=self.presente)
        self.assertEqual(restantes.count(), 2)
        self.assertFalse(restantes.filter(id=self.ponto_errado.id).exists())

    def test_temperatura_volta_ao_normal_depois_da_limpeza(self):
        self.assertEqual(self.presente.temperatura()['codigo'], 'frio')

        self._rodar('--aplicar')

        presente = Presente.objects.get(pk=self.presente.pk)
        self.assertNotEqual(presente.temperatura()['codigo'], 'frio')

    def test_preco_muito_abaixo_da_referencia_tambem_e_removido(self):
        """Acessorio barato no lugar do produto deixa o rastro para baixo."""
        barato = PrecoHistorico.objects.create(
            presente=self.presente, preco='2.00', loja='Zoom', fonte='sugestao')

        self._rodar('--aplicar')
        self.assertFalse(PrecoHistorico.objects.filter(id=barato.id).exists())

    def test_variacao_normal_de_preco_e_preservada(self):
        """Oscilacao real de mercado nao pode ser confundida com produto errado."""
        normal = PrecoHistorico.objects.create(
            presente=self.presente, preco='35.00', loja='Amazon', fonte='pesquisa_semanal')

        self._rodar('--aplicar')
        self.assertTrue(PrecoHistorico.objects.filter(id=normal.id).exists())

    def test_presente_sem_preco_de_referencia_e_ignorado(self):
        sem_preco = Presente.objects.create(
            grupo=self.grupo, usuario=self.dono, descricao='Presente sem preco')
        ponto = PrecoHistorico.objects.create(
            presente=sem_preco, preco='999.00', loja='Zoom', fonte='sugestao')

        self._rodar('--aplicar')
        self.assertTrue(PrecoHistorico.objects.filter(id=ponto.id).exists())

    def test_fator_mais_frouxo_preserva_o_ponto(self):
        self._rodar('--aplicar', '--fator', '10')
        self.assertTrue(PrecoHistorico.objects.filter(id=self.ponto_errado.id).exists())

    def test_limita_a_um_presente(self):
        outro = Presente.objects.create(
            grupo=self.grupo, usuario=self.dono, descricao='Outro presente', preco='50.00')
        ponto_outro = PrecoHistorico.objects.create(
            presente=outro, preco='900.00', loja='Zoom', fonte='sugestao')

        self._rodar('--aplicar', '--presente', str(self.presente.pk))

        self.assertFalse(PrecoHistorico.objects.filter(id=self.ponto_errado.id).exists())
        self.assertTrue(PrecoHistorico.objects.filter(id=ponto_outro.id).exists())

    def test_sugestoes_sem_titulo_saem_so_com_a_opcao(self):
        sem_titulo = SugestaoCompra.objects.create(
            grupo=self.grupo, presente=self.presente, local_compra='Zoom',
            url_compra='https://zoom.com.br/x', preco_sugerido='219.66')
        com_titulo = SugestaoCompra.objects.create(
            grupo=self.grupo, presente=self.presente, local_compra='Amazon',
            titulo_produto='Mata Formigas Formicel Gel 10g',
            url_compra='https://amazon.com.br/x', preco_sugerido='28.00')

        self._rodar('--aplicar')
        self.assertTrue(SugestaoCompra.objects.filter(id=sem_titulo.id).exists())

        self._rodar('--aplicar', '--sugestoes')
        self.assertFalse(SugestaoCompra.objects.filter(id=sem_titulo.id).exists())
        self.assertTrue(SugestaoCompra.objects.filter(id=com_titulo.id).exists())

    def test_fator_invalido_e_recusado(self):
        with self.assertRaises(CommandError):
            self._rodar('--fator', '1')


class ExtrairInfoProdutoBloqueioAntiRoboTest(TestCase):
    """Mercado Livre redireciona para /gz/account-verification quando bloqueia
    a consulta. Isso não é falha do parser: não deve abrir issue."""

    URL = 'https://www.mercadolivre.com.br/p/MLB2070594105?pdp_filters=item_id%3AMLB7136159042'

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='bloqueio@exemplo.com', username='bloqueio', password='SenhaForte!2026',
        )
        self.client.force_login(self.usuario)

    def _resposta_bloqueada(self):
        resposta = mock.Mock()
        resposta.url = 'https://www.mercadolivre.com.br/gz/account-verification?go=' + self.URL
        resposta.content = b'<html><head><title>Mercado Libre</title></head><body></body></html>'
        resposta.raise_for_status.return_value = None
        return resposta

    def test_bloqueio_retorna_erro_claro_sem_criar_issue(self):
        with mock.patch('presentes.scrapers.requests.get', return_value=self._resposta_bloqueada()), \
                mock.patch('presentes.github_helper.criar_issue_falha_scraping') as criar_issue:
            resposta = self.client.post(reverse('extrair_info_produto'), {'url': self.URL})

        self.assertEqual(resposta.status_code, 400)
        dados = resposta.json()
        self.assertEqual(dados['error_type'], 'blocked')
        self.assertIn('manualmente', dados['error'])
        criar_issue.assert_not_called()


@override_settings(MERCADOLIVRE_CLIENT_ID='app-id', MERCADOLIVRE_CLIENT_SECRET='app-secret')
class MercadoLivreAPITest(TestCase):
    URL = ('https://www.mercadolivre.com.br/p/MLB2070594105?pdp_filters=item_id%3AMLB7136159042'
           '&sid=cart#polycard_client=cart_list&wid=MLB7136159042&sid=cart')

    def _resposta(self, status, dados):
        resposta = mock.Mock(status_code=status, text=str(dados))
        resposta.json.return_value = dados
        return resposta

    def _token(self, expira_em):
        return MercadoLivreToken.objects.create(
            access_token='token-atual', refresh_token='refresh-atual', expira_em=expira_em,
        )

    def test_extrai_ids_de_anuncio_e_produto(self):
        self.assertEqual(extrair_ids(self.URL), ('MLB7136159042', 'MLB2070594105'))
        self.assertEqual(
            extrair_ids('https://produto.mercadolivre.com.br/MLB-123456789-fone-bluetooth-_JM'),
            ('MLB123456789', None),
        )

    def _api_falsa(self, rotas):
        """requests.get que responde conforme o caminho da URL ({trecho: (status, dados)})"""
        def get(url, **kwargs):
            for trecho, (status, dados) in rotas.items():
                if trecho in url:
                    return self._resposta(status, dados)
            return self._resposta(404, {'message': 'not_found'})
        return mock.patch('presentes.mercadolivre_api.requests.get', side_effect=get)

    # Respostas reais da API para anuncios de terceiros: /items bloqueado, catalogo liberado
    ROTAS_CATALOGO = {
        '/items/MLB7136159042/description': (200, {'plain_text': 'Paquímetro Manual 150 mm\n\nDetalhes...'}),
        '/items/': (403, {'message': 'Access to the requested resource is forbidden', 'error': 'access_denied'}),
        '/products/MLB2070594105/items': (200, {'results': [
            {'item_id': 'MLB5378977671', 'price': 31.76},
            {'item_id': 'MLB7136159042', 'price': 33.47},
        ]}),
        '/products/MLB2070594105': (200, {'name': 'Vernier Caliper',
                                          'pictures': [{'url': 'https://http2.mlstatic.com/cat.jpg'}]}),
    }

    def test_scraper_usa_catalogo_da_api(self):
        self._token(timezone.now() + timedelta(hours=1))

        # requests.get e o mesmo objeto nos dois modulos: um patch so cobre API e pagina
        with self._api_falsa(self.ROTAS_CATALOGO) as get:
            resultado = ScraperFactory.extract_product_info(self.URL)

        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['titulo'], 'Paquímetro Manual 150 mm')
        self.assertEqual(resultado['preco'], 33.47)  # preco do anuncio do link, nao o menor
        self.assertEqual(resultado['imagem_url'], 'https://http2.mlstatic.com/cat.jpg')
        chamadas = [c.args[0] for c in get.call_args_list]
        self.assertTrue(all('api.mercadolibre.com' in url for url in chamadas))  # nao acessou a pagina
        self.assertEqual(get.call_args[1]['headers']['Authorization'], 'Bearer token-atual')

    def test_link_de_anuncio_acha_produto_pelo_titulo(self):
        self._token(timezone.now() + timedelta(hours=1))
        rotas = {
            '/products/search': (200, {'results': [{'id': 'MLB999'}, {'id': 'MLB2070594105'}]}),
            '/products/MLB999/items': (200, {'results': [{'item_id': 'MLB111', 'price': 10}]}),
            **self.ROTAS_CATALOGO,
        }
        url = 'https://produto.mercadolivre.com.br/MLB-7136159042-paquimetro-manual-150-mm-_JM'

        with self._api_falsa(rotas):
            resultado = buscar_produto(url)

        # MLB999 nao contem o anuncio: so o produto que contem e usado
        self.assertEqual(resultado, ('Paquímetro Manual 150 mm', 33.47, 'https://http2.mlstatic.com/cat.jpg'))

    def test_link_de_anuncio_fora_do_catalogo_traz_so_titulo(self):
        self._token(timezone.now() + timedelta(hours=1))
        rotas = {'/products/search': (200, {'results': []}), '/items/': (403, {})}
        url = 'https://produto.mercadolivre.com.br/MLB-123456789-fone-bluetooth-sem-fio-_JM'

        with self._api_falsa(rotas):
            self.assertEqual(buscar_produto(url), ('Fone bluetooth sem fio', None, None))

    def test_obtem_token_por_client_credentials(self):
        novo = {'access_token': 'token-app', 'expires_in': 21600, 'scope': 'read'}

        with mock.patch('presentes.mercadolivre_api.requests.post', return_value=self._resposta(200, novo)) as post:
            self.assertEqual(obter_access_token(), 'token-app')

        self.assertEqual(post.call_args[1]['data']['grant_type'], 'client_credentials')
        self.assertEqual(post.call_args[1]['data']['client_id'], 'app-id')
        self.assertEqual(MercadoLivreToken.objects.get().access_token, 'token-app')

    def test_renova_token_vencido_e_guarda_novo_refresh(self):
        self._token(timezone.now() - timedelta(minutes=1))
        novo = {'access_token': 'token-novo', 'refresh_token': 'refresh-novo', 'expires_in': 21600}

        with mock.patch('presentes.mercadolivre_api.requests.post', return_value=self._resposta(200, novo)) as post:
            self.assertEqual(obter_access_token(), 'token-novo')

        self.assertEqual(post.call_args[1]['data']['grant_type'], 'refresh_token')
        self.assertEqual(post.call_args[1]['data']['refresh_token'], 'refresh-atual')
        token = MercadoLivreToken.objects.get()
        self.assertEqual(token.refresh_token, 'refresh-novo')

    @override_settings(MERCADOLIVRE_CLIENT_ID='', MERCADOLIVRE_CLIENT_SECRET='')
    def test_sem_credenciais_cai_na_pagina(self):
        with mock.patch('presentes.mercadolivre_api.requests.get') as api:
            self.assertIsNone(buscar_produto(self.URL))
        api.assert_not_called()

    def test_callback_rejeita_state_invalido(self):
        admin = Usuario.objects.create_superuser(
            email='admin@exemplo.com', username='admin', password='SenhaForte!2026',
        )
        self.client.force_login(admin)
        sessao = self.client.session
        sessao['mercadolivre_oauth_state'] = 'esperado'
        sessao.save()

        with mock.patch('presentes.mercadolivre_api.requests.post') as post:
            self.client.get(reverse('mercadolivre_callback'), {'code': 'abc', 'state': 'outro'})

        post.assert_not_called()
        self.assertFalse(MercadoLivreToken.objects.exists())

    def test_callback_guarda_token(self):
        admin = Usuario.objects.create_superuser(
            email='admin@exemplo.com', username='admin', password='SenhaForte!2026',
        )
        self.client.force_login(admin)
        sessao = self.client.session
        sessao['mercadolivre_oauth_state'] = 'esperado'
        sessao.save()
        dados = {'access_token': 'tok', 'refresh_token': 'ref', 'expires_in': 21600}

        with mock.patch('presentes.mercadolivre_api.requests.post', return_value=self._resposta(200, dados)) as post:
            self.client.get(reverse('mercadolivre_callback'), {'code': 'abc', 'state': 'esperado'})

        self.assertEqual(post.call_args[1]['data']['grant_type'], 'authorization_code')
        self.assertEqual(post.call_args[1]['data']['code'], 'abc')
        self.assertEqual(MercadoLivreToken.objects.get().refresh_token, 'ref')


class PushRotasTest(TestCase):
    """O base.html chama /api/push/vapid-key/ e /api/push/subscribe/ em toda pagina logada."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='push@exemplo.com', username='push', password='SenhaForte!2026',
        )
        self.client.force_login(self.usuario)

    @override_settings(VAPID_PUBLIC_KEY='')
    def test_vapid_key_sem_chave_retorna_json_vazio(self):
        resposta = self.client.get('/api/push/vapid-key/')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json(), {'public_key': ''})

    @override_settings(VAPID_PUBLIC_KEY='chave-publica')
    def test_vapid_key_com_chave(self):
        self.assertEqual(self.client.get('/api/push/vapid-key/').json(), {'public_key': 'chave-publica'})

    def test_subscribe_salva_assinatura(self):
        dados = {'endpoint': 'https://push.exemplo.com/abc', 'keys': {'p256dh': 'p', 'auth': 'a'}}
        resposta = self.client.post('/api/push/subscribe/', data=dados, content_type='application/json')
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(PushSubscription.objects.filter(usuario=self.usuario, endpoint=dados['endpoint']).exists())


class EnvioPushTest(TestCase):
    """Envio real pelo pywebpush, so com o POST ao servico de push simulado."""

    def setUp(self):
        import base64
        import os

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        from .push import gerar_chaves_vapid

        def b64url(dados):
            return base64.urlsafe_b64encode(dados).rstrip(b'=').decode()

        self.publica, self.privada = gerar_chaves_vapid()
        self.usuario = Usuario.objects.create_user(
            email='push@exemplo.com', username='push', password='SenhaForte!2026',
        )
        # Chaves que o navegador geraria ao assinar
        self.chave_navegador = ec.generate_private_key(ec.SECP256R1())
        self.auth = os.urandom(16)
        p256dh = self.chave_navegador.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        self.assinatura = PushSubscription.objects.create(
            usuario=self.usuario, endpoint='https://fcm.googleapis.com/fcm/send/abc',
            p256dh=b64url(p256dh), auth=b64url(self.auth),
        )

    def _settings(self):
        return override_settings(
            VAPID_PUBLIC_KEY=self.publica, VAPID_PRIVATE_KEY=self.privada,
            VAPID_ADMIN_EMAIL='maxwbh@gmail.com',
        )

    def test_envia_payload_criptografado_e_assinado(self):
        import json

        import http_ece

        with self._settings(), mock.patch('pywebpush.requests.post',
                                          return_value=mock.Mock(status_code=201)) as post:
            self.assertEqual(enviar_push(self.usuario, 'Seu presente foi comprado!'), 1)

        args, kwargs = post.call_args
        self.assertEqual(args[0], self.assinatura.endpoint)
        self.assertIn('vapid t=', kwargs['headers']['Authorization'])
        self.assertIn(f'k={self.publica}', kwargs['headers']['Authorization'])

        corpo = http_ece.decrypt(kwargs['data'], private_key=self.chave_navegador,
                                 auth_secret=self.auth, version='aes128gcm')
        self.assertEqual(json.loads(corpo), {
            'title': 'Lista de Presentes', 'body': 'Seu presente foi comprado!', 'url': '/notificacoes/',
        })

    def test_remove_assinatura_expirada(self):
        with self._settings(), mock.patch('pywebpush.requests.post',
                                          return_value=mock.Mock(status_code=410, text='Gone')):
            self.assertEqual(enviar_push(self.usuario, 'Teste'), 0)
        self.assertFalse(PushSubscription.objects.exists())

    def test_sem_chaves_nao_envia(self):
        with override_settings(VAPID_PRIVATE_KEY=''), mock.patch('pywebpush.requests.post') as post:
            self.assertEqual(enviar_push(self.usuario, 'Teste'), 0)
        post.assert_not_called()

    def test_notificacao_criada_dispara_push_apos_commit(self):
        with self._settings(), mock.patch('presentes.push.enviar_push') as enviar, \
                mock.patch('presentes.push.connection.close'):
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                notificacao = Notificacao.objects.create(usuario=self.usuario, mensagem='Oi')
            self.assertEqual(len(callbacks), 1)
            # Executa a thread de forma sincrona para o teste
            with mock.patch('presentes.push.threading.Thread') as thread:
                callbacks[0]()
            alvo, args = thread.call_args[1]['target'], thread.call_args[1]['args']
            alvo(*args)
        enviar.assert_called_once_with(notificacao.usuario, 'Oi')


class ExtrairInfoProdutoTextoSemLinkTest(TestCase):
    """Nome do produto digitado no campo do link nao deve virar requisicao para 'https://sabonete natura'."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='link@exemplo.com', username='link', password='SenhaForte!2026',
        )
        self.client.force_login(self.usuario)

    def test_texto_sem_link_retorna_erro_claro_sem_acessar_rede(self):
        for texto in ('sabonete natura', 'sabonete'):
            with mock.patch('presentes.scrapers.requests.get') as get:
                resposta = self.client.post(reverse('extrair_info_produto'), {'url': texto})
            self.assertEqual(resposta.status_code, 400)
            self.assertEqual(resposta.json()['error_type'], 'invalid_url')
            get.assert_not_called()

    def test_link_sem_protocolo_continua_aceito(self):
        with mock.patch('presentes.scrapers.ScraperFactory.extract_product_info',
                        return_value={'success': True, 'titulo': 'Sabonete', 'preco': 10.0, 'imagem_url': ''}) as extrair:
            resposta = self.client.post(reverse('extrair_info_produto'), {'url': 'www.natura.com.br/p/sabonete'})
        self.assertEqual(resposta.status_code, 200)
        extrair.assert_called_once_with('https://www.natura.com.br/p/sabonete')


class CompartilharPeloCelularTest(TestCase):
    """Destino do share_target do manifest.json (compartilhar pelo Android)."""

    def setUp(self):
        self.grupo = Grupo.objects.create(nome='Familia')
        self.usuario = Usuario.objects.create_user(
            email='celular@exemplo.com', username='celular', password='SenhaForte!2026',
        )
        GrupoMembro.objects.create(grupo=self.grupo, usuario=self.usuario)
        self.usuario.grupo_ativo = self.grupo
        self.usuario.save()
        self.client.force_login(self.usuario)

    def _destino(self, resposta):
        from urllib.parse import parse_qs, urlparse
        self.assertEqual(resposta.status_code, 302)
        destino = urlparse(resposta['Location'])
        self.assertEqual(destino.path, reverse('adicionar_presente'))
        return {k: v[0] for k, v in parse_qs(destino.query).items()}

    def test_link_no_texto_como_o_app_do_mercado_livre(self):
        texto = 'Paquímetro Manual 150 mm https://produto.mercadolivre.com.br/MLB-7136159042-paquimetro-_JM'
        params = self._destino(self.client.get(reverse('compartilhar'), {'text': texto}))
        self.assertEqual(params['url'], 'https://produto.mercadolivre.com.br/MLB-7136159042-paquimetro-_JM')
        self.assertEqual(params['descricao'], 'Paquímetro Manual 150 mm')

    def test_campos_title_e_url(self):
        params = self._destino(self.client.get(reverse('compartilhar'), {
            'title': 'Fone Bluetooth', 'url': 'https://www.amazon.com.br/dp/B0TESTE',
        }))
        self.assertEqual(params, {'url': 'https://www.amazon.com.br/dp/B0TESTE', 'descricao': 'Fone Bluetooth'})

    def test_expande_link_curto(self):
        original = 'https://www.mercadolivre.com.br/p/MLB2070594105?pdp_filters=item_id%3AMLB7136159042'
        bloqueio = mock.Mock(url='https://www.mercadolivre.com.br/gz/account-verification?go='
                                 + 'https%3A%2F%2Fwww.mercadolivre.com.br%2Fp%2FMLB2070594105%3Fpdp_filters%3Ditem_id%253AMLB7136159042',
                             history=[])
        with mock.patch('presentes.mercadolivre_api.requests.get', return_value=bloqueio):
            params = self._destino(self.client.get(reverse('compartilhar'), {
                'text': 'Olha isso https://mercadolivre.com/sec/2abcXYZ',
            }))
        self.assertEqual(params['url'], original)

    def test_sem_link_preenche_so_a_descricao(self):
        params = self._destino(self.client.get(reverse('compartilhar'), {'text': 'Sabonete Natura'}))
        self.assertEqual(params, {'descricao': 'Sabonete Natura'})

    def test_tela_de_adicionar_ja_vem_preenchida_e_busca_sozinha(self):
        resposta = self.client.get(reverse('adicionar_presente'), {
            'url': 'https://www.amazon.com.br/dp/B0TESTE', 'descricao': 'Fone Bluetooth',
        })
        self.assertContains(resposta, 'value="https://www.amazon.com.br/dp/B0TESTE"')
        self.assertContains(resposta, 'Fone Bluetooth')
        # Busca automatica do link compartilhado
        self.assertContains(resposta, 'Link recebido pelo compartilhamento do celular')

    def test_tela_de_adicionar_ignora_url_que_nao_e_http(self):
        resposta = self.client.get(reverse('adicionar_presente'), {'url': 'javascript:alert(1)'})
        self.assertNotContains(resposta, 'javascript:alert(1)')
        self.assertNotContains(resposta, 'Link recebido pelo compartilhamento do celular')

    def test_manifest_declara_share_target(self):
        import json
        from pathlib import Path

        from django.conf import settings
        manifest = json.loads((Path(settings.BASE_DIR) / 'static' / 'manifest.json').read_text())
        self.assertEqual(manifest['share_target']['action'], reverse('compartilhar'))
        self.assertEqual(manifest['share_target']['params'], {'title': 'title', 'text': 'text', 'url': 'url'})


class RegistroAcessosTest(TestCase):
    """Despertares do servidor e acessos por hora para ajustar o keep-alive."""

    NAVEGADOR = 'Mozilla/5.0 (Linux; Android 14) Chrome/141.0 Mobile Safari/537.36'

    def setUp(self):
        from .acessos import RegistroAcessoMiddleware
        RegistroAcessoMiddleware._despertar_registrado = False

    def test_primeiro_acesso_registra_despertar_ignorando_health_do_render(self):
        from .models import DespertarServidor

        self.client.get('/health/', HTTP_USER_AGENT='Render/1.0')
        self.assertFalse(DespertarServidor.objects.exists())

        self.client.get(reverse('login'), HTTP_USER_AGENT=self.NAVEGADOR)
        self.client.get(reverse('login'), HTTP_USER_AGENT=self.NAVEGADOR)

        despertar = DespertarServidor.objects.get()
        self.assertEqual(despertar.origem, 'USUARIO')
        self.assertEqual(despertar.caminho, reverse('login'))

    def test_despertar_pelo_keep_alive_e_marcado_como_monitor(self):
        from .models import DespertarServidor

        self.client.get('/health/', HTTP_USER_AGENT='curl/8.5.0')
        self.assertEqual(DespertarServidor.objects.get().origem, 'MONITOR')

    def test_conta_so_acessos_de_pessoas(self):
        from .models import AcessoHora

        self.client.get(reverse('login'), HTTP_USER_AGENT=self.NAVEGADOR)
        self.client.get(reverse('login'), HTTP_USER_AGENT=self.NAVEGADOR)
        self.client.get('/health/', HTTP_USER_AGENT=self.NAVEGADOR)  # caminho ignorado
        self.client.get(reverse('login'), HTTP_USER_AGENT='curl/8.5.0')  # monitor

        registro = AcessoHora.objects.get()
        self.assertEqual(registro.acessos, 2)
        self.assertEqual(registro.hora, timezone.localtime().hour)

    def test_resumo_sugere_cron_utc_para_horas_de_pico(self):
        from .acessos import resumo_acessos
        from .models import AcessoHora

        hoje = timezone.localdate()
        AcessoHora.objects.create(data=hoje, hora=20, acessos=80)  # pico a noite
        AcessoHora.objects.create(data=hoje, hora=21, acessos=15)
        AcessoHora.objects.create(data=hoje, hora=3, acessos=5)

        resumo = resumo_acessos(dias=7, limite_percentual=10)

        self.assertEqual(resumo['total_acessos'], 100)
        self.assertEqual(resumo['horas_pico'], [20, 21])
        # Uma hora antes do pico: 19h-21h em Sao Paulo (UTC-3) = 22h-00h UTC
        self.assertEqual(resumo['faixas_sugeridas_local'], ['19:00-21:59'])
        self.assertEqual(resumo['cron_keep_alive_utc'], ['*/14 0 * * *', '*/14 22-23 * * *'])

    def test_resumo_so_para_superusuario(self):
        usuario = Usuario.objects.create_user(email='comum@exemplo.com', username='comum', password='SenhaForte!2026')
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse('acessos_resumo')).status_code, 403)

        admin = Usuario.objects.create_superuser(email='adm@exemplo.com', username='adm', password='SenhaForte!2026')
        self.client.force_login(admin)
        resposta = self.client.get(reverse('acessos_resumo'), {'dias': 7})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('cron_keep_alive_utc', resposta.json())

    @override_settings(CRON_TOKEN='token-relatorio')
    def test_resumo_com_token_do_cron_sem_login(self):
        # Workflow relatorio-acessos.yml: analise sem precisar de alguem logado
        url = reverse('acessos_resumo')
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.get(url, HTTP_X_CRON_TOKEN='errado').status_code, 403)
        resposta = self.client.get(url, {'dias': 7}, HTTP_X_CRON_TOKEN='token-relatorio')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json()['periodo_dias'], 7)

    @override_settings(CRON_TOKEN='')
    def test_sem_cron_token_configurado_header_vazio_nao_libera(self):
        resposta = self.client.get(reverse('acessos_resumo'), HTTP_X_CRON_TOKEN='')
        self.assertEqual(resposta.status_code, 403)


class SenhaSimplesTest(TestCase):
    """Senha simples de 4 digitos permitida no cadastro e na redefinicao."""

    def test_validador_aceita_quatro_digitos_e_recusa_menos(self):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        validate_password('1234')
        with self.assertRaises(ValidationError):
            validate_password('123')


class RedefinicaoSenhaTest(TestCase):
    """Token sem estado (vale depois de o servidor reiniciar) e e-mail opcional."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='ana@exemplo.com', username='ana', password='SenhaAntiga!2026', first_name='Ana',
        )

    def test_link_redefine_senha_uma_unica_vez(self):
        from .senha import token_redefinicao

        url = reverse('redefinir_senha', args=[token_redefinicao(self.usuario)])
        self.assertContains(self.client.get(url), 'name="nova_senha"')

        resposta = self.client.post(url, {'nova_senha': '1234', 'confirmar_senha': '1234'})
        self.assertRedirects(resposta, reverse('login'), fetch_redirect_response=False)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('1234'))

        # Trocar a senha invalida o link
        self.assertNotContains(self.client.get(url), 'name="nova_senha"')

    def test_token_invalido(self):
        resposta = self.client.get(reverse('redefinir_senha', args=['abc.def']))
        self.assertNotContains(resposta, 'name="nova_senha"')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    def test_sem_email_configurado_orienta_procurar_administrador(self):
        with mock.patch('presentes.emails.EmailMultiAlternatives.send') as enviar:
            resposta = self.client.post(reverse('esqueceu_senha'), {'email': 'ana@exemplo.com'})
        self.assertContains(resposta, 'Peça ao administrador')
        enviar.assert_not_called()

    @override_settings(EMAIL_BACKEND='presentes.email_backend.BrevoEmailBackend', BREVO_API_KEY='chave-teste',
                       DEFAULT_FROM_EMAIL='Lista de Presentes <maxwbh@gmail.com>')
    def test_envia_email_pela_api_da_brevo(self):
        from .senha import usuario_do_token

        with mock.patch('presentes.email_backend.requests.post',
                        return_value=mock.Mock(status_code=201)) as post:
            resposta = self.client.post(reverse('esqueceu_senha'), {'email': 'ana@exemplo.com'})

        self.assertContains(resposta, 'você receberá as instruções')
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(kwargs['headers']['api-key'], 'chave-teste')
        self.assertEqual(kwargs['json']['sender'], {'email': 'maxwbh@gmail.com', 'name': 'Lista de Presentes'})
        self.assertEqual(kwargs['json']['to'], [{'email': 'ana@exemplo.com'}])
        # O link enviado funciona
        token = re.search(r'/redefinir-senha/([^/]+)/', kwargs['json']['textContent']).group(1)
        self.assertEqual(usuario_do_token(token), self.usuario)

    def test_acao_do_admin_gera_link(self):
        admin_user = Usuario.objects.create_superuser(email='adm@exemplo.com', username='adm', password='SenhaForte!2026')
        self.client.force_login(admin_user)
        resposta = self.client.post(reverse('admin:presentes_usuario_changelist'), {
            'action': 'gerar_link_redefinicao_senha', '_selected_action': [self.usuario.pk],
        }, follow=True)
        self.assertContains(resposta, '/redefinir-senha/')


class ScraperBloqueioCaptchaTest(TestCase):
    """Issue #7: pagina de captcha (Radware) tratada como produto."""

    def test_pagina_de_captcha_vira_bloqueio(self):
        html = b'<html><head><title>Radware Bot Manager Captcha</title></head><body></body></html>'
        resposta = mock.Mock(url='https://www.lojadomecanico.com.br/produto/604405', content=html)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            resultado = ScraperFactory.extract_product_info('https://www.lojadomecanico.com.br/produto/604405')
        self.assertEqual(resultado['error_type'], 'blocked')
        criar_issue.assert_not_called()


@override_settings(GITHUB_AUTO_CREATE_ISSUES=True, GITHUB_TOKEN='token-teste')
class IssueDuplicadaTest(TestCase):
    """Issues #12, #13 e #14: a mesma issue criada varias vezes."""

    def setUp(self):
        from . import github_helper
        github_helper._ISSUES_RECENTES.clear()

    def test_issue_recem_criada_nao_duplica_mesmo_sem_aparecer_na_listagem(self):
        # Issues #26 a #29: a listagem do GitHub ainda nao mostrava a issue criada
        # segundos antes, e a mesma issue foi aberta 4 vezes
        from .github_helper import criar_issue_erro_geral

        criada = mock.Mock(status_code=201, json=mock.Mock(return_value={
            'number': 26, 'html_url': 'u', 'body': 'URL: https://loja.com/1',
            'comments': 0, 'comments_url': 'https://api.github.com/repos/x/y/issues/26/comments'}))
        with mock.patch('presentes.github_helper.requests.get',
                        return_value=mock.Mock(status_code=200, json=mock.Mock(return_value=[]))), \
                mock.patch('presentes.github_helper.requests.post', return_value=criada) as post:
            primeira = criar_issue_erro_geral('[AUTO] Site X', 'URL: https://loja.com/1',
                                              contexto={'URL': 'https://loja.com/1'})
            segunda = criar_issue_erro_geral('[AUTO] Site X', 'URL: https://loja.com/1',
                                             contexto={'URL': 'https://loja.com/1'})

        post.assert_called_once()
        self.assertEqual(primeira['issue_number'], 26)
        self.assertEqual(segunda['issue_number'], 26)

    def test_reaproveita_issue_aberta_com_mesmo_titulo(self):
        from .github_helper import criar_issue_erro_geral

        abertas = [{'number': 12, 'title': '[AUTO] Site não mapeado: www.comprasparaguai.com.br',
                    'html_url': 'https://github.com/Maxwbh/Lista_de_Presentes/issues/12'}]
        with mock.patch('presentes.github_helper.requests.get',
                        return_value=mock.Mock(status_code=200, json=mock.Mock(return_value=abertas))), \
                mock.patch('presentes.github_helper.requests.post') as post:
            resultado = criar_issue_erro_geral('[AUTO] Site não mapeado: www.comprasparaguai.com.br', 'x')

        post.assert_not_called()
        self.assertEqual(resultado['issue_number'], 12)

    def test_nova_ocorrencia_vira_comentario_na_issue_aberta(self):
        from .github_helper import criar_issue_erro_geral

        abertas = [{'number': 22, 'title': '[AUTO] Leitura incompleta em site mapeado: produto.mercadolivre.com.br',
                    'html_url': 'u', 'body': 'URL: https://produto.mercadolivre.com.br/MLB-1',
                    'comments': 0, 'comments_url': 'https://api.github.com/repos/x/y/issues/22/comments'}]
        with mock.patch('presentes.github_helper.requests.get',
                        return_value=mock.Mock(status_code=200, json=mock.Mock(return_value=abertas))), \
                mock.patch('presentes.github_helper.requests.post') as post:
            criar_issue_erro_geral(abertas[0]['title'], 'detalhes do MLB-2',
                                   contexto={'URL': 'https://produto.mercadolivre.com.br/MLB-2'})
            # A mesma URL de novo nao comenta outra vez
            criar_issue_erro_geral(abertas[0]['title'], 'detalhes do MLB-1',
                                   contexto={'URL': 'https://produto.mercadolivre.com.br/MLB-1'})

        post.assert_called_once()
        self.assertEqual(post.call_args[0][0], abertas[0]['comments_url'])
        self.assertIn('Nova ocorrência', post.call_args[1]['json']['body'])
        self.assertIn('detalhes do MLB-2', post.call_args[1]['json']['body'])

    def test_cria_quando_nao_existe(self):
        from .github_helper import criar_issue_erro_geral

        criada = mock.Mock(status_code=201, json=mock.Mock(return_value={'number': 20, 'html_url': 'u'}))
        with mock.patch('presentes.github_helper.requests.get',
                        return_value=mock.Mock(status_code=200, json=mock.Mock(return_value=[]))), \
                mock.patch('presentes.github_helper.requests.post', return_value=criada) as post:
            resultado = criar_issue_erro_geral('[AUTO] Site novo', 'x')

        post.assert_called_once()
        self.assertEqual(resultado['issue_number'], 20)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   DEFAULT_FROM_EMAIL='ListadePresentes <no-reply@exemplo.com>',
                   SITE_URL='https://lista.exemplo.com')
class EmailsTest(TestCase):
    """Redefinicao de senha, boas-vindas e presente comprado."""

    @contextlib.contextmanager
    def _enviar_apos_commit(self):
        """
        Roda os envios agendados para depois do commit, de forma sincrona.

        O connection.close() da thread fica simulado durante todo o bloco,
        inclusive quando os callbacks rodam na saida do
        captureOnCommitCallbacks: senao fecharia a conexao do proprio teste
        (no PostgreSQL do CI isso quebra os testes seguintes).
        """
        def iniciar(thread):
            thread._target(*thread._args, **thread._kwargs)
        with mock.patch('presentes.emails.connection.close'), \
                mock.patch('presentes.emails.threading.Thread.start', iniciar), \
                self.captureOnCommitCallbacks(execute=True):
            yield

    def test_boas_vindas_no_cadastro(self):
        from django.core import mail

        with self._enviar_apos_commit():
            self.client.post(reverse('registro'), {
                'email': 'novo@exemplo.com', 'first_name': 'Bia', 'last_name': 'Souza', 'username': 'bia',
                'password1': '1234', 'password2': '1234', 'avatar': 'avatar1',
            })

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['novo@exemplo.com'])
        self.assertIn('Bem-vindo', email.subject)
        self.assertIn('Bia', email.body)
        self.assertIn('https://lista.exemplo.com/adicionar-presente/', email.body)
        self.assertIn('Adicionar meu primeiro presente', email.alternatives[0][0])

    def test_presente_comprado_avisa_dono_sem_dizer_quem_comprou(self):
        from django.core import mail

        grupo = Grupo.objects.create(nome='Familia')
        dono = Usuario.objects.create_user(email='dono@exemplo.com', username='dono', password='1234', first_name='Ana')
        comprador = Usuario.objects.create_user(email='comprador@exemplo.com', username='comp', password='1234',
                                                first_name='Carlos')
        for usuario in (dono, comprador):
            GrupoMembro.objects.create(grupo=grupo, usuario=usuario)
            usuario.grupo_ativo = grupo
            usuario.save()
        presente = Presente.objects.create(grupo=grupo, usuario=dono, descricao='Fone & Capa', preco='99.90')

        self.client.force_login(comprador)
        with self._enviar_apos_commit():
            self.client.post(reverse('marcar_comprado', args=[presente.pk]))

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['dono@exemplo.com'])
        self.assertIn('Fone & Capa', email.body)  # texto sem escapar HTML
        self.assertNotIn('Carlos', email.body)
        self.assertNotIn('Carlos', email.alternatives[0][0])

    def test_redefinicao_envia_texto_e_html_com_o_link(self):
        from django.core import mail

        Usuario.objects.create_user(email='ana@exemplo.com', username='ana', password='1234', first_name='Ana')
        self.client.post(reverse('esqueceu_senha'), {'email': 'ana@exemplo.com'})

        email = mail.outbox[0]
        link = re.search(r'https?://\S+/redefinir-senha/\S+/', email.body).group(0)
        self.assertIn(link, email.alternatives[0][0])
        self.assertIn('24 horas', email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    def test_sem_email_configurado_nao_agenda_nada(self):
        from .emails import agendar_boas_vindas

        usuario = Usuario.objects.create_user(email='x@exemplo.com', username='x', password='1234')
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            agendar_boas_vindas(usuario)
        self.assertEqual(callbacks, [])


class IssueSiteNaoMapeadoTest(TestCase):
    """Issue de site nao mapeado so quando o scraper generico le os dados de forma incompleta."""

    def _extrair(self, html):
        resposta = mock.Mock(url='https://loja-nova.com.br/produto/1', content=html)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            resultado = ScraperFactory.extract_product_info('https://loja-nova.com.br/produto/1')
        return resultado, criar_issue

    def test_leitura_completa_nao_abre_issue(self):
        html = (b'<html><head><title>Loja</title>'
                b'<meta property="og:title" content="Shampoo 1L">'
                b'<meta property="og:image" content="https://loja-nova.com.br/foto.jpg">'
                b'<meta property="product:price:amount" content="309.90"></head></html>')
        resultado, criar_issue = self._extrair(html)
        self.assertTrue(resultado['success'])
        criar_issue.assert_not_called()

    def test_leitura_sem_preco_abre_issue(self):
        html = (b'<html><head><title>Loja</title>'
                b'<meta property="og:title" content="Shampoo 1L">'
                b'<meta property="og:image" content="https://loja-nova.com.br/foto.jpg"></head></html>')
        resultado, criar_issue = self._extrair(html)
        self.assertTrue(resultado['success'])
        criar_issue.assert_called_once()
        self.assertEqual(criar_issue.call_args[1]['titulo'], '[AUTO] Site não mapeado: loja-nova.com.br')
        # A issue mostra o log da leitura (resposta da pagina)
        descricao = criar_issue.call_args[1]['descricao']
        self.assertIn('### Log da Extração', descricao)
        self.assertIn('HTTP', descricao)

    def test_leitura_sem_imagem_abre_issue_dizendo_o_que_faltou(self):
        html = (b'<html><head><title>Loja</title>'
                b'<meta property="og:title" content="Shampoo 1L">'
                b'<meta property="product:price:amount" content="309.90"></head></html>')
        resultado, criar_issue = self._extrair(html)
        self.assertTrue(resultado['success'])
        criar_issue.assert_called_once()
        self.assertIn('faltou: imagem', criar_issue.call_args[1]['descricao'])
        self.assertEqual(criar_issue.call_args[1]['contexto']['Dados faltando'], 'imagem')

    def test_leitura_sem_titulo_abre_issue_de_falha_de_extracao(self):
        html = (b'<html><head>'
                b'<meta property="og:image" content="https://loja-nova.com.br/foto.jpg">'
                b'<meta property="product:price:amount" content="309.90"></head></html>')
        resposta = mock.Mock(url='https://loja-nova.com.br/produto/1', content=html)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta), \
                mock.patch('presentes.github_helper.criar_issue_falha_scraping') as falha_scraping:
            resultado = ScraperFactory.extract_product_info('https://loja-nova.com.br/produto/1')
        self.assertEqual(resultado['error_type'], 'parsing')
        falha_scraping.assert_called_once()
        kwargs = falha_scraping.call_args[1]
        self.assertIn('Nao foi possivel extrair titulo', kwargs['erro'])
        self.assertTrue(any('Página obtida' in linha for linha in kwargs['log_extracao']))
        self.assertTrue(resultado['log_extracao'])

    def test_descricao_com_aviso_entre_simbolos_nao_vira_titulo(self):
        texto = '*****************ATENÇÃO FRETE GRÁTIS ******************\nPelúcia de vaca 45 cm\n'
        with mock.patch('presentes.mercadolivre_api._get', return_value={'plain_text': texto}):
            self.assertEqual(_titulo_da_descricao('MLB123', 'token'), 'Pelúcia de vaca 45 cm')

    def test_anuncio_ml_fora_do_catalogo_nao_abre_issue(self):
        # Limite do Mercado Livre, nao defeito no codigo: so informa o motivo
        url = 'https://produto.mercadolivre.com.br/MLB-5186755357'
        with mock.patch('presentes.mercadolivre_api.buscar_produto', return_value=('Pelúcia', None, None)), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            resultado = ScraperFactory.extract_product_info(url)
        self.assertTrue(resultado['success'])
        self.assertIn('fora do catálogo', resultado['aviso'])
        criar_issue.assert_not_called()

    def test_site_mapeado_sem_motivo_conhecido_continua_abrindo_issue(self):
        url = 'https://produto.mercadolivre.com.br/MLB-5186755357'
        with mock.patch('presentes.mercadolivre_api.buscar_produto', return_value=('Pelúcia', 99.9, None)), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            ScraperFactory.extract_product_info(url)
        criar_issue.assert_called_once()
        self.assertIn('bug', criar_issue.call_args[1]['labels'])

    def test_descricao_so_com_separador_nao_vira_titulo(self):
        texto = '________________________________________________\nLuva de treino roxa tamanho M\n'
        with mock.patch('presentes.mercadolivre_api._get', return_value={'plain_text': texto}):
            self.assertEqual(_titulo_da_descricao('MLB123', 'token'), 'Luva de treino roxa tamanho M')

    def _extrair_site_mapeado(self, dados):
        url = 'https://www.kabum.com.br/produto/1'
        with mock.patch('presentes.scrapers.KabumScraper.extract', return_value=dados), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            resultado = ScraperFactory.extract_product_info(url)
        return resultado, criar_issue

    def test_site_mapeado_com_leitura_completa_nao_abre_issue(self):
        resultado, criar_issue = self._extrair_site_mapeado(
            ('Mouse', 99.9, 'https://www.kabum.com.br/foto.jpg'))
        self.assertTrue(resultado['success'])
        criar_issue.assert_not_called()

    def test_site_mapeado_sem_preco_abre_issue_de_ajuste(self):
        resultado, criar_issue = self._extrair_site_mapeado(
            ('Mouse', None, 'https://www.kabum.com.br/foto.jpg'))
        self.assertTrue(resultado['success'])
        criar_issue.assert_called_once()
        kwargs = criar_issue.call_args[1]
        self.assertEqual(kwargs['titulo'], '[AUTO] Leitura incompleta em site mapeado: www.kabum.com.br')
        self.assertEqual(kwargs['contexto']['Scraper usado'], 'KabumScraper')
        self.assertEqual(kwargs['contexto']['Dados faltando'], 'preço')


class DecathlonScraperTest(TestCase):
    """Decathlon: preco vem do JSON-LD (ProductGroup com uma variante por tamanho)."""

    HTML = (
        '<html><head><title>Luva | Decathlon</title>'
        '<meta property="og:title" content="Luva Corength Roxa">'
        '<script type="application/ld+json">[{"@type": "ProductGroup", "name": "Luva Corength Roxa",'
        ' "image": ["https://decathlonpro.vtexassets.com/luva.jpg"], "hasVariant": ['
        '{"@type": "Product", "sku": "1", "offers": {"price": 79.99, '
        '"availability": "https://schema.org/OutOfStock"}},'
        '{"@type": "Product", "sku": "2", "offers": {"price": 71.99, '
        '"availability": "https://schema.org/InStock"}},'
        '{"@type": "Product", "sku": "3", "offers": {"price": 65.00, '
        '"availability": "https://schema.org/InStock"}}]}]</script>'
        '</head></html>'
    ).encode()

    def _extrair(self, url):
        resposta = mock.Mock(url=url, content=self.HTML, status_code=200)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta) as get, \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            resultado = ScraperFactory.extract_product_info(url)
        return resultado, criar_issue, get

    def test_le_titulo_preco_e_imagem_do_json_ld(self):
        resultado, criar_issue, _ = self._extrair('https://www.decathlon.com.br/luva-8948970/p')
        self.assertTrue(resultado['success'])
        self.assertFalse(resultado['used_generic_scraper'])
        self.assertEqual(resultado['titulo'], 'Luva Corength Roxa')
        # Primeira variante em estoque
        self.assertEqual(resultado['preco'], 71.99)
        self.assertEqual(resultado['imagem_url'], 'https://decathlonpro.vtexassets.com/luva.jpg')
        criar_issue.assert_not_called()

    def test_usa_o_preco_da_variante_do_link(self):
        resultado, _, _ = self._extrair('https://www.decathlon.com.br/luva-8948970/p?skuId=3')
        self.assertEqual(resultado['preco'], 65.00)

    def test_remove_parametros_de_rastreio_da_url(self):
        _, _, get = self._extrair('https://www.decathlon.com.br/luva-8948970/p?utm_source=chatgpt.com&skuId=3')
        self.assertEqual(get.call_args[0][0], 'https://www.decathlon.com.br/luva-8948970/p?skuId=3')


class LimparUrlRastreioTest(TestCase):

    def test_remove_utm_gclid_e_fbclid(self):
        self.assertEqual(
            limpar_url_rastreio('https://loja.com/p?id=7&utm_source=x&utm_medium=y&gclid=1&fbclid=2'),
            'https://loja.com/p?id=7')

    def test_url_sem_query_fica_igual(self):
        self.assertEqual(limpar_url_rastreio('https://loja.com/p'), 'https://loja.com/p')


class BuscarImagensAdminTest(TestCase):
    """Botao e acao do admin que buscam no site a imagem dos presentes sem imagem."""

    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            email='adm-img@exemplo.com', username='adm-img', password='SenhaForte!2026')
        self.client.force_login(self.admin)
        self.sem_imagem = Presente.objects.create(
            usuario=self.admin, descricao='Tesoura', url='https://www.loja.com.br/tesoura')
        self.sem_link = Presente.objects.create(usuario=self.admin, descricao='Sabonete')
        self.com_imagem = Presente.objects.create(
            usuario=self.admin, descricao='Meia', url='https://www.loja.com.br/meia', imagem_base64='aGVsbG8=')
        self.url_botao = reverse('admin:presentes_presente_buscar_imagens')

    def _leitura(self, preco=59.9):
        return {'success': True, 'titulo': 'Tesoura', 'preco': preco,
                'imagem_url': 'https://www.loja.com.br/foto.jpg'}

    def _foto(self):
        resposta = mock.Mock(content=b'jpeg', headers={'content-type': 'image/jpeg'})
        resposta.raise_for_status.return_value = None
        return resposta

    def test_filtro_sem_imagem_e_botao_com_total(self):
        resposta = self.client.get(reverse('admin:presentes_presente_changelist') + '?tem_imagem=nao')
        self.assertContains(resposta, 'Buscar imagens que faltam (1)')
        descricoes = [p.descricao for p in resposta.context['cl'].result_list]
        self.assertCountEqual(descricoes, ['Tesoura', 'Sabonete'])

    def test_botao_busca_imagem_e_preco_que_faltavam(self):
        with mock.patch('presentes.scrapers.ScraperFactory.extract_product_info',
                        return_value=self._leitura()) as extrair, \
                mock.patch('presentes.services.requests.get', return_value=self._foto()):
            resposta = self.client.post(self.url_botao, follow=True)
        # So o presente sem imagem e com link e consultado
        extrair.assert_called_once_with('https://www.loja.com.br/tesoura')
        self.sem_imagem.refresh_from_db()
        self.assertTrue(self.sem_imagem.tem_imagem())
        self.assertEqual(str(self.sem_imagem.preco), '59.90')
        self.assertContains(resposta, '1 de 1 presente(s) ganharam imagem')
        self.assertContains(resposta, 'ganharam também o preço')

    def test_preco_existente_nao_e_alterado(self):
        self.sem_imagem.preco = 10
        self.sem_imagem.save()
        with mock.patch('presentes.scrapers.ScraperFactory.extract_product_info',
                        return_value=self._leitura()), \
                mock.patch('presentes.services.requests.get', return_value=self._foto()):
            self.client.post(self.url_botao)
        self.sem_imagem.refresh_from_db()
        self.assertEqual(str(self.sem_imagem.preco), '10.00')

    def test_muitos_presentes_rodam_em_segundo_plano(self):
        for i in range(6):
            Presente.objects.create(usuario=self.admin, descricao=f'Item {i}', url=f'https://loja.com/{i}')
        with mock.patch('presentes.admin.threading.Thread') as thread:
            resposta = self.client.post(self.url_botao, follow=True)
        thread.return_value.start.assert_called_once()
        self.assertContains(resposta, 'Busca de imagem iniciada para 7 presentes')

    def test_registra_o_motivo_quando_nao_acha_a_foto(self):
        casos = [
            ({'success': True, 'titulo': 'Pelúcia', 'preco': None, 'imagem_url': None,
              'aviso': 'Anúncio fora do catálogo do Mercado Livre'}, 'fora do catálogo'),
            ({'success': False, 'error_type': 'blocked', 'error_message': 'x'}, 'bloqueou a consulta'),
            ({'success': False, 'error_type': 'network', 'error_message': 'HTTP 404'}, 'HTTP 404'),
        ]
        for leitura, esperado in casos:
            with mock.patch('presentes.scrapers.ScraperFactory.extract_product_info', return_value=leitura):
                resposta = self.client.post(self.url_botao, follow=True)
            self.sem_imagem.refresh_from_db()
            self.assertIn(esperado, self.sem_imagem.busca_imagem_resultado)
            self.assertIsNotNone(self.sem_imagem.busca_imagem_em)
            # A mensagem do admin mostra o motivo de cada presente
            self.assertContains(resposta, f'Tesoura: {self.sem_imagem.busca_imagem_resultado}')

    def test_foto_encontrada_fica_registrada(self):
        with mock.patch('presentes.scrapers.ScraperFactory.extract_product_info',
                        return_value=self._leitura()), \
                mock.patch('presentes.services.requests.get', return_value=self._foto()):
            self.client.post(self.url_botao)
        self.sem_imagem.refresh_from_db()
        self.assertEqual(self.sem_imagem.busca_imagem_resultado, 'Foto encontrada. Preço preenchido.')

    def test_get_nao_dispara_busca(self):
        with mock.patch('presentes.admin._buscar_imagens') as buscar:
            self.client.get(self.url_botao)
        buscar.assert_not_called()


class PrecoMetaTagTest(TestCase):
    """Preco das meta tags: formato de maquina (ponto decimal) e moeda estrangeira."""

    def _extrair(self, html, url='https://www.loja-nova.com.br/produto/1'):
        resposta = mock.Mock(url=url, content=html.encode(), status_code=200)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral'):
            return ScraperFactory.extract_product_info(url)

    def test_ponto_decimal_da_meta_tag(self):
        # Antes '309.90' virava 30990 (o ponto era lido como separador de milhar)
        resultado = self._extrair(
            '<html><head><meta property="og:title" content="Shampoo">'
            '<meta property="product:price:amount" content="309.90"></head></html>')
        self.assertEqual(resultado['preco'], 309.90)

    def test_preco_em_dolar_usa_o_valor_em_reais_da_pagina(self):
        # Compras Paraguai: 'US$ 254,00 (R$ 1.371,60)', meta em USD
        resultado = self._extrair(
            '<html><head><meta property="og:title" content="SSD WD Green 2TB">'
            '<meta itemprop="price" content="254.00"><meta itemprop="priceCurrency" content="USD">'
            '</head><body><div class="cotacao">Dólar hoje: R$ 5,40</div>'
            '<div class="price"><span>US$ 254,00</span> <span>(R$ 1.371,60)</span></div></body></html>',
            url='https://www.comprasparaguai.com.br/ssd_54489/')
        self.assertEqual(resultado['preco'], 1371.60)

    def test_preco_em_dolar_sem_valor_em_reais_fica_vazio(self):
        resultado = self._extrair(
            '<html><head><meta property="og:title" content="SSD WD Green 2TB">'
            '<meta property="product:price:amount" content="254.00">'
            '<meta property="product:price:currency" content="USD"></head>'
            '<body><span class="price">Por 254,00</span></body></html>')
        self.assertIsNone(resultado['preco'])


class ConverterPrecoTest(TestCase):
    """Separador decimal em todas as leituras de preco (sites, meta tags, APIs e IA)."""

    def test_formatos(self):
        from .precos import converter_preco

        casos = {
            'R$ 1.371,60': 1371.60,   # brasileiro
            '1.371,60': 1371.60,
            '254,00': 254.00,
            '254,9': 254.90,
            'R$ 1.371': 1371.00,      # milhar sem centavos
            '1.371.600': 1371600.00,
            '254.00': 254.00,         # formato de maquina (meta tag / JSON)
            '254.0': 254.00,          # antes virava 2540
            '309.90': 309.90,         # antes virava 30990
            '1371.6': 1371.60,
            '1,371.60': 1371.60,      # formato americano
            '1,371': 1371.00,
            'US$ 254,00': 254.00,
            ' R$\xa049,90 ': 49.90,
            254: 254.00,
            1371.6: 1371.60,
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertAlmostEqual(converter_preco(entrada), esperado)

    def test_invalidos(self):
        from .precos import converter_preco

        for entrada in (None, '', 'Grátis', 'R$', '0,00', 0, -5, True, '.'):
            with self.subTest(entrada=entrada):
                self.assertIsNone(converter_preco(entrada))

    def test_decimal_com_duas_casas(self):
        from decimal import Decimal
        from .precos import converter_preco_decimal

        self.assertEqual(converter_preco_decimal('R$ 1.371,60'), Decimal('1371.60'))
        self.assertEqual(converter_preco_decimal('254.0'), Decimal('254.00'))
        self.assertIsNone(converter_preco_decimal('sem preço'))


class DadosEstruturadosTest(TestCase):
    """Issues #31 (Farm Rio) e #32 (amzn.to)."""

    def test_preco_de_oferta_embutida_em_atributo(self):
        # Farm Rio (deco.cx): o produto schema.org vem com URL-encoding num atributo
        from urllib.parse import quote
        oferta = quote('{"offers":{"@type":"AggregateOffer","priceCurrency":"BRL",'
                       '"highPrice":311.35,"lowPrice":311.35,"offerCount":2}}')
        html = ('<html><head><meta property="og:title" content="Calca Estampada">'
                '<meta property="og:image" content="https://farmrio.com.br/foto.jpg"></head>'
                f'<body><div data-dt-event="{oferta}"></div></body></html>').encode()
        resposta = mock.Mock(url='https://www.farmrio.com.br/calca/p', content=html, status_code=200)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral') as criar_issue:
            resultado = ScraperFactory.extract_product_info('https://www.farmrio.com.br/calca/p')
        self.assertEqual(resultado['preco'], 311.35)
        criar_issue.assert_not_called()

    def test_preco_do_json_ld_no_scraper_generico(self):
        html = ('<html><head><meta property="og:title" content="Tenis">'
                '<script type="application/ld+json">{"@type": "Product", "name": "Tenis",'
                ' "offers": {"@type": "Offer", "price": "199.90", "priceCurrency": "BRL"}}</script>'
                '</head></html>').encode()
        resposta = mock.Mock(url='https://loja.com.br/tenis', content=html, status_code=200)
        resposta.raise_for_status.return_value = None
        with mock.patch('presentes.scrapers.requests.get', return_value=resposta), \
                mock.patch('presentes.github_helper.criar_issue_erro_geral'):
            resultado = ScraperFactory.extract_product_info('https://loja.com.br/tenis')
        self.assertEqual(resultado['preco'], 199.90)

    def test_link_curto_da_amazon_usa_o_scraper_da_amazon(self):
        from .scrapers import AmazonScraper
        for url in ('https://amzn.to/4pxiozo', 'https://a.co/d/abc123'):
            with self.subTest(url=url):
                scraper, generico = ScraperFactory.get_scraper(url)
                self.assertIsInstance(scraper, AmazonScraper)
                self.assertFalse(generico)


class PaginasDeAdministracaoTest(TestCase):
    """/setup/ e /gerar-dados-teste/ alteram o banco: somente superusuarios."""

    def setUp(self):
        self.comum = Usuario.objects.create_user(
            email='comum-adm@exemplo.com', username='comum-adm', password='1234')
        self.admin = Usuario.objects.create_superuser(
            email='super-adm@exemplo.com', username='super-adm', password='SenhaForte!2026')

    def test_sem_login_vai_para_o_login(self):
        for nome in ('setup_grupos', 'gerar_dados_teste'):
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn('/login/', resposta['Location'])

    def test_post_sem_login_nao_executa_nada(self):
        with mock.patch('django.core.management.call_command') as comando:
            self.client.post(reverse('gerar_dados_teste'))
            self.client.post(reverse('setup_grupos'), {'acao': 'migrations'})
        comando.assert_not_called()
        self.assertFalse(Usuario.objects.filter(email__endswith='@example.com').exists())

    def test_usuario_comum_recebe_403(self):
        self.client.force_login(self.comum)
        for nome in ('setup_grupos', 'gerar_dados_teste'):
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 403)

    def test_superusuario_acessa(self):
        self.client.force_login(self.admin)
        for nome in ('setup_grupos', 'gerar_dados_teste'):
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)


class ValidacaoAppleTest(TestCase):
    """Login com Apple: Team ID em 'key', Key ID em 'secret' e a chave em settings."""

    CHAVE = '-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----'

    def _validar(self, app):
        from .social_validation import validar_formato
        return validar_formato('apple', app)

    def test_configuracao_completa(self):
        ok, _ = self._validar({'client_id': 'br.com.lista', 'key': 'TEAM123', 'secret': 'KEY456',
                               'settings': {'certificate_key': self.CHAVE}})
        self.assertTrue(ok)

    def test_sem_team_id_ou_sem_key_id(self):
        ok, msg = self._validar({'client_id': 'br.com.lista', 'key': '', 'secret': 'KEY456',
                                 'settings': {'certificate_key': self.CHAVE}})
        self.assertFalse(ok)
        self.assertIn('APPLE_TEAM_ID', msg)
        ok, msg = self._validar({'client_id': 'br.com.lista', 'key': 'TEAM123', 'secret': '',
                                 'settings': {'certificate_key': self.CHAVE}})
        self.assertFalse(ok)
        self.assertIn('APPLE_KEY_ID', msg)

    def test_nomes_novos_e_antigos_das_variaveis(self):
        import importlib
        from lista_presentes import settings as modulo
        novos = {'APPLE_TEAM_ID': 'TEAM123', 'APPLE_KEY_ID': 'KEY456', 'APPLE_CLIENT_SECRET': ''}
        antigos = {'APPLE_TEAM_ID': '', 'APPLE_KEY_ID': 'TEAM123', 'APPLE_CLIENT_SECRET': 'KEY456'}
        try:
            for nome, ambiente in (('novos', novos), ('antigos', antigos)):
                with self.subTest(nomes=nome), mock.patch.dict('os.environ', ambiente):
                    app = importlib.reload(modulo).SOCIALACCOUNT_PROVIDERS['apple']['APP']
                    self.assertEqual(app['key'], 'TEAM123')
                    self.assertEqual(app['secret'], 'KEY456')
        finally:
            importlib.reload(modulo)
