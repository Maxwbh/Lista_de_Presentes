from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from presentes.models import (
    Usuario, Presente, Grupo, GrupoMembro, Compra, Notificacao,
    SugestaoCompra, PrecoHistorico, PesquisaPrecoLog,
)
import base64
import os
import random
import logging

logger = logging.getLogger(__name__)

# Pares de cores (gradiente) para as imagens geradas
CORES_IMAGEM = [
    ('#fda4af', '#e11d48'),  # rose
    ('#6ee7b7', '#059669'),  # emerald
    ('#93c5fd', '#2563eb'),  # blue
    ('#fcd34d', '#d97706'),  # amber
    ('#c4b5fd', '#7c3aed'),  # violet
    ('#67e8f9', '#0891b2'),  # cyan
]


def gerar_imagem_produto(emoji, nome):
    """
    Gera uma imagem SVG de produto (gradiente + emoji + nome) em base64.
    Offline e determinística — substitui o scraping de fotos, que era lento
    e falhava com frequência (bloqueio de bots nas lojas).
    """
    # Só gradiente + emoji centralizado. O NOME do produto NÃO é embutido na
    # imagem: o card já exibe o título, e texto embutido colidia com o selo de
    # preço (bottom-left), deixando o layout "bagunçado".
    cor1, cor2 = random.choice(CORES_IMAGEM)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="450" viewBox="0 0 600 450">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{cor1}"/><stop offset="100%" stop-color="{cor2}"/>'
        f'</linearGradient></defs>'
        f'<rect width="600" height="450" fill="url(#g)"/>'
        f'<circle cx="300" cy="225" r="115" fill="#ffffff" fill-opacity="0.20"/>'
        f'<circle cx="300" cy="225" r="82" fill="#ffffff" fill-opacity="0.25"/>'
        f'<text x="300" y="272" font-size="130" text-anchor="middle">{emoji}</text>'
        f'</svg>'
    )
    return base64.b64encode(svg.encode('utf-8')).decode('utf-8')


class Command(BaseCommand):
    help = 'Cria base de dados de teste completa: usuários, grupos, presentes, sugestões, histórico de preços (temperatura), compras e notificações'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=5,
            help='Número de usuários para criar (padrão: 5)',
        )
        parser.add_argument(
            '--gifts-per-user',
            type=int,
            default=5,
            help='Número de presentes por usuário (padrão: 5)',
        )

    def handle(self, *args, **options):
        num_users = options['users']
        gifts_per_user = options['gifts_per_user']

        self.stdout.write(self.style.WARNING(
            f'Criando {num_users} usuários com {gifts_per_user} presentes cada...'
        ))

        # Criar grupo de teste
        grupo_teste, criado = Grupo.objects.get_or_create(
            nome='Grupo de Testes',
            defaults={
                'descricao': 'Grupo criado automaticamente para testes de desenvolvimento',
                'ativo': True
            }
        )
        if criado:
            self.stdout.write(self.style.SUCCESS(f'✓ Grupo de teste criado: {grupo_teste.nome}'))
        else:
            self.stdout.write(self.style.WARNING(f'  Grupo de teste já existe: {grupo_teste.nome}'))

        nomes = [
            ('João', 'Silva', 'joao.silva@example.com'),
            ('Maria', 'Santos', 'maria.santos@example.com'),
            ('Pedro', 'Oliveira', 'pedro.oliveira@example.com'),
            ('Ana', 'Costa', 'ana.costa@example.com'),
            ('Carlos', 'Souza', 'carlos.souza@example.com'),
            ('Fernanda', 'Lima', 'fernanda.lima@example.com'),
            ('Ricardo', 'Ferreira', 'ricardo.ferreira@example.com'),
            ('Juliana', 'Alves', 'juliana.alves@example.com'),
            ('Paulo', 'Rodrigues', 'paulo.rodrigues@example.com'),
            ('Camila', 'Martins', 'camila.martins@example.com'),
        ]

        # (descrição, url, preço base, emoji para a imagem gerada)
        presentes_exemplos = [
            ('Kindle Paperwhite 16GB', 'https://www.amazon.com.br/dp/B08N3J8GTX', Decimal('499.00'), '📚'),
            ('Echo Dot 5ª Geração', 'https://www.amazon.com.br/dp/B09B8V1LZ3', Decimal('349.00'), '🔊'),
            ('Fire TV Stick 4K', 'https://www.amazon.com.br/dp/B08XVYZ1Y5', Decimal('449.00'), '📺'),
            ('Mouse Logitech MX Master 3S', 'https://www.amazon.com.br/dp/B09HM94VDS', Decimal('599.00'), '🖱️'),
            ('Teclado Mecânico Logitech', 'https://www.amazon.com.br/dp/B07ZGXJ4R7', Decimal('450.00'), '⌨️'),
            ('Fone JBL Tune 510BT', 'https://www.amazon.com.br/dp/B08F28N8TP', Decimal('199.00'), '🎧'),
            ('Garrafa Térmica Stanley 1L', 'https://www.amazon.com.br/dp/B07VFFSGCH', Decimal('220.00'), '🥤'),
            ('Mochila para Notebook', 'https://www.amazon.com.br/dp/B07G5D5VNQ', Decimal('180.00'), '🎒'),
            ('Power Bank Anker 20000mAh', 'https://www.amazon.com.br/dp/B07QXV6N1B', Decimal('199.90'), '🔋'),
            ('Webcam Logitech C920', 'https://www.amazon.com.br/dp/B006JH8T3S', Decimal('350.00'), '📷'),
            ('SSD Kingston 1TB NVMe', 'https://www.kabum.com.br/produto/130858', Decimal('450.00'), '💾'),
            ('Monitor LG 27" UltraGear', 'https://www.kabum.com.br/produto/385005', Decimal('1200.00'), '🖥️'),
            ('Headset Gamer HyperX', 'https://www.kabum.com.br/produto/86089', Decimal('299.00'), '🎮'),
            ('Microfone USB Fifine', 'https://www.kabum.com.br/produto/129589', Decimal('280.00'), '🎤'),
            ('Cadeira Gamer DT3 Sports', 'https://www.kabum.com.br/produto/97278', Decimal('1100.00'), '💺'),
            ('Controle Xbox Wireless', 'https://produto.mercadolivre.com.br/MLB-1856828084', Decimal('399.00'), '🎮'),
            ('Smartwatch Xiaomi Band 8', 'https://produto.mercadolivre.com.br/MLB-3180157424', Decimal('299.00'), '⌚'),
            ('Caixa de Som JBL Flip 6', 'https://produto.mercadolivre.com.br/MLB-2150396817', Decimal('599.00'), '🔊'),
            ('Air Fryer Philips Walita', 'https://www.magazineluiza.com.br/air-fryer/p/234158700', Decimal('499.00'), '🍟'),
            ('Cafeteira Nespresso Essenza', 'https://www.magazineluiza.com.br/cafeteira-nespresso/p/237043000', Decimal('399.00'), '☕'),
            ('Livro Clean Code', 'https://www.amazon.com.br/dp/8576082675', Decimal('65.00'), '📖'),
            ('LEGO Star Wars Millennium Falcon', 'https://www.amazon.com.br/dp/B07W7XNRQS', Decimal('450.00'), '🧱'),
            ('Câmera GoPro Hero 11', 'https://www.amazon.com.br/dp/B0B3MQJFJX', Decimal('2500.00'), '📹'),
            ('Caneca Térmica Stanley', 'https://www.amazon.com.br/dp/B07Y8PRDFT', Decimal('49.90'), '☕'),
            ('Hub USB-C Baseus 6 em 1', 'https://www.kabum.com.br/produto/304721', Decimal('129.00'), '🔌'),
        ]

        lojas = ['Amazon Brasil', 'Mercado Livre', 'Kabum', 'Magazine Luiza', 'Americanas', 'Casas Bahia']
        avatares = [f'avatar-{n}' for n in range(1, 21)]

        # Tendências de preço para a temperatura (multiplicadores semanais até o preço atual)
        # quente: preço caiu | frio: preço subiu | estavel: variação mínima
        tendencias = [
            ('quente', [Decimal('1.18'), Decimal('1.12'), Decimal('1.08'), Decimal('1.00')]),
            ('frio', [Decimal('0.85'), Decimal('0.90'), Decimal('0.96'), Decimal('1.00')]),
            ('estavel', [Decimal('1.02'), Decimal('0.99'), Decimal('1.01'), Decimal('1.00')]),
        ]

        usuarios_criados = []
        presentes_criados = 0
        sugestoes_criadas = 0
        historicos_criados = 0
        compras_criadas = 0

        agora = timezone.now()

        # Incluir o admin (maxwbh) no grupo de teste, com presentes próprios
        admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'maxwbh@gmail.com')
        admin = (Usuario.objects.filter(email=admin_email).first()
                 or Usuario.objects.filter(is_superuser=True).first())
        if admin:
            GrupoMembro.objects.get_or_create(
                grupo=grupo_teste,
                usuario=admin,
                defaults={'e_mantenedor': True}
            )
            if not admin.grupo_ativo:
                admin.grupo_ativo = grupo_teste
                admin.save(update_fields=['grupo_ativo'])
            if not admin.avatar:
                admin.avatar = random.choice(avatares)
                admin.save(update_fields=['avatar'])
            usuarios_criados.append(admin)
            self.stdout.write(self.style.SUCCESS(
                f'✓ Admin {admin.email} adicionado ao grupo como Mantenedor (receberá presentes)'
            ))
        else:
            self.stdout.write(self.style.WARNING('  Admin não encontrado, pulando...'))

        for i in range(num_users):
            primeiro_nome, ultimo_nome, email = nomes[i % len(nomes)]
            email = email.replace('@', f'{i+1}@')
            username = f'{primeiro_nome.lower()}.{ultimo_nome.lower()}{i+1}'

            if Usuario.objects.filter(email=email).exists():
                usuario = Usuario.objects.get(email=email)
                # Garantir vínculo de membro e grupo ativo mesmo para usuários
                # já existentes (execuções anteriores do gerador)
                GrupoMembro.objects.get_or_create(
                    grupo=grupo_teste,
                    usuario=usuario,
                    defaults={'e_mantenedor': False}
                )
                if not usuario.grupo_ativo:
                    usuario.grupo_ativo = grupo_teste
                    usuario.save(update_fields=['grupo_ativo'])
                usuarios_criados.append(usuario)
                self.stdout.write(self.style.WARNING(f'  Usuário {email} já existe, vínculo ao grupo garantido'))
                continue

            usuario = Usuario.objects.create(
                username=username,
                email=email,
                first_name=primeiro_nome,
                last_name=ultimo_nome,
                password=make_password('senha123'),
                ativo=True,
                avatar=random.choice(avatares),
                telefone=f'(31) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
                grupo_ativo=grupo_teste
            )
            usuarios_criados.append(usuario)
            self.stdout.write(self.style.SUCCESS(f'✓ Usuário: {primeiro_nome} {ultimo_nome} ({email})'))

            e_mantenedor = (i == 0)
            GrupoMembro.objects.get_or_create(
                grupo=grupo_teste,
                usuario=usuario,
                defaults={'e_mantenedor': e_mantenedor}
            )

        # Criar presentes com sugestões e histórico para todos os usuários
        for usuario in usuarios_criados:
            amostra = random.sample(presentes_exemplos, min(gifts_per_user, len(presentes_exemplos)))

            for descricao, url, preco_base, emoji in amostra:
                status = 'ATIVO' if random.random() < 0.7 else 'COMPRADO'

                presente = Presente.objects.create(
                    usuario=usuario,
                    grupo=grupo_teste,
                    descricao=descricao,
                    url=url,
                    preco=preco_base,
                    status=status,
                    imagem_base64=gerar_imagem_produto(emoji, descricao),
                    imagem_nome=f'{descricao[:40]}.svg',
                    imagem_tipo='image/svg+xml'
                )
                presentes_criados += 1

                # Sugestões de compra (2 a 4 lojas com preços ao redor do base)
                lojas_sorteadas = random.sample(lojas, random.randint(2, 4))
                for loja in lojas_sorteadas:
                    variacao = Decimal(str(round(random.uniform(0.88, 1.12), 2)))
                    SugestaoCompra.objects.create(
                        grupo=grupo_teste,
                        presente=presente,
                        local_compra=f'{loja} (IA)',
                        url_compra=url,
                        preco_sugerido=(preco_base * variacao).quantize(Decimal('0.01'))
                    )
                    sugestoes_criadas += 1

                # Histórico de preços semanal retroativo (temperatura de preços)
                codigo, multiplicadores = random.choice(tendencias)
                for semana, mult in enumerate(multiplicadores):
                    semanas_atras = len(multiplicadores) - 1 - semana
                    ponto = PrecoHistorico.objects.create(
                        presente=presente,
                        preco=(preco_base * mult).quantize(Decimal('0.01')),
                        loja=random.choice(lojas),
                        fonte='pesquisa_semanal' if semanas_atras > 0 else 'cadastro'
                    )
                    # Retroagir a data (auto_now_add impede definir na criação)
                    PrecoHistorico.objects.filter(pk=ponto.pk).update(
                        data=agora - timedelta(weeks=semanas_atras)
                    )
                    historicos_criados += 1

                # Compra + notificação para presentes comprados
                if status == 'COMPRADO':
                    compradores = [u for u in usuarios_criados if u != usuario]
                    if compradores:
                        comprador = random.choice(compradores)
                        Compra.objects.get_or_create(
                            presente=presente,
                            defaults={'grupo': grupo_teste, 'comprador': comprador}
                        )
                        Notificacao.objects.create(
                            grupo=grupo_teste,
                            usuario=usuario,
                            mensagem=f'🎁 Alguém comprou um presente da sua lista: {descricao[:60]}',
                            lida=random.random() < 0.5
                        )
                        compras_criadas += 1

                self.stdout.write(
                    f'  {"✓" if status == "ATIVO" else "✗"} {descricao[:45]} - '
                    f'R$ {preco_base} ({status}, temperatura: {codigo})'
                )

        # Reparar dados de execuções antigas: todo dono de presente do grupo
        # precisa ter vínculo de membro (sem isso a visão "Por Membro" fica vazia)
        donos = Usuario.objects.filter(presentes__grupo=grupo_teste).distinct()
        vinculos_criados = 0
        for dono in donos:
            _, criado_vinculo = GrupoMembro.objects.get_or_create(
                grupo=grupo_teste,
                usuario=dono,
                defaults={'e_mantenedor': False}
            )
            if criado_vinculo:
                vinculos_criados += 1
            if not dono.grupo_ativo:
                dono.grupo_ativo = grupo_teste
                dono.save(update_fields=['grupo_ativo'])
        if vinculos_criados:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Vínculo de membro criado para {vinculos_criados} dono(s) de presentes que estavam fora do grupo'
            ))

        # Reparar dados antigos: gerar/regenerar o placeholder limpo (emoji, sem
        # nome embutido) para quem está sem foto ou com o placeholder antigo.
        from django.db.models import Q
        emoji_por_descricao = {d: e for d, _, _, e in presentes_exemplos}
        alvos = Presente.objects.filter(grupo=grupo_teste).filter(
            Q(imagem_base64__isnull=True) | Q(imagem_base64='') | Q(imagem_tipo='image/svg+xml')
        )
        imagens_atualizadas = 0
        for presente in alvos:
            emoji = emoji_por_descricao.get(presente.descricao, '🎁')
            presente.imagem_base64 = gerar_imagem_produto(emoji, presente.descricao)
            presente.imagem_nome = f'{presente.descricao[:40]}.svg'
            presente.imagem_tipo = 'image/svg+xml'
            presente.save(update_fields=['imagem_base64', 'imagem_nome', 'imagem_tipo'])
            imagens_atualizadas += 1
        if imagens_atualizadas:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Imagens atualizadas para {imagens_atualizadas} presentes'
            ))

        # Registrar uma pesquisa de preços concluída (evita disparo imediato da semanal)
        PesquisaPrecoLog.objects.create(
            origem='comando',
            data_fim=agora,
            total_presentes=presentes_criados,
            sucessos=presentes_criados,
            erros=0
        )

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✓ Grupo: {grupo_teste.nome}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Usuários: {len(usuarios_criados)}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Presentes: {presentes_criados}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Sugestões de loja: {sugestoes_criadas}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Pontos de histórico de preço: {historicos_criados}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Compras registradas: {compras_criadas}'))
        self.stdout.write('\n' + self.style.WARNING('IMPORTANTE:'))
        self.stdout.write(self.style.WARNING('  • Todos os usuários têm a senha: senha123'))
        self.stdout.write(self.style.WARNING('  • Histórico cobre as temperaturas: quente 🔥, estável ➖ e frio ❄️'))
        self.stdout.write('=' * 60)
