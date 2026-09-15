from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from .models import (
    Compra, Grupo, GrupoMembro, Presente, PrecoHistorico, SugestaoCompra, Usuario,
)
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
