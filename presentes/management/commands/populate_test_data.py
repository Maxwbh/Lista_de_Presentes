from django.core.management.base import BaseCommand
from presentes.models import Usuario, Presente, Grupo, GrupoMembro
from django.contrib.auth.hashers import make_password
import random
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cria usuários, grupos e presentes de teste para desenvolvimento com dados reais de lojas'

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

        self.stdout.write(self.style.WARNING(f'Criando {num_users} usuários com {gifts_per_user} presentes cada...'))

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

        # Lista de nomes para usuários
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

        # Lista de presentes com URLs reais de produtos brasileiros
        # Formato: (descrição_fallback, url_real, preco_fallback)
        presentes_exemplos = [
            # Amazon Brasil
            ('Kindle Paperwhite', 'https://www.amazon.com.br/dp/B08N3J8GTX', 499.00),
            ('Echo Dot 5ª Geração', 'https://www.amazon.com.br/dp/B09B8V1LZ3', 349.00),
            ('Fire TV Stick 4K', 'https://www.amazon.com.br/dp/B08XVYZ1Y5', 449.00),
            ('Mouse Logitech MX Master 3S', 'https://www.amazon.com.br/dp/B09HM94VDS', 599.00),
            ('Teclado Mecânico Logitech', 'https://www.amazon.com.br/dp/B07ZGXJ4R7', 450.00),
            ('Fone JBL Tune 510BT', 'https://www.amazon.com.br/dp/B08F28N8TP', 199.00),
            ('Garrafa Térmica Stanley', 'https://www.amazon.com.br/dp/B07VFFSGCH', 220.00),
            ('Mochila Swissport', 'https://www.amazon.com.br/dp/B07G5D5VNQ', 180.00),
            ('Power Bank Anker 20000mAh', 'https://www.amazon.com.br/dp/B07QXV6N1B', 199.90),
            ('Webcam Logitech C920', 'https://www.amazon.com.br/dp/B006JH8T3S', 350.00),

            # Kabum - Eletrônicos
            ('SSD Kingston 1TB', 'https://www.kabum.com.br/produto/130858', 450.00),
            ('Monitor LG 27 UltraGear', 'https://www.kabum.com.br/produto/385005', 1200.00),
            ('Headset Gamer HyperX', 'https://www.kabum.com.br/produto/86089', 299.00),
            ('Microfone USB Fifine', 'https://www.kabum.com.br/produto/129589', 280.00),
            ('Mousepad Gamer Havit', 'https://www.kabum.com.br/produto/104026', 49.90),
            ('Hub USB-C Baseus', 'https://www.kabum.com.br/produto/304721', 129.00),
            ('Cadeira Gamer DT3 Sports', 'https://www.kabum.com.br/produto/97278', 1100.00),

            # Mercado Livre
            ('Controle Xbox Wireless', 'https://produto.mercadolivre.com.br/MLB-1856828084', 399.00),
            ('Smartwatch Xiaomi Band 8', 'https://produto.mercadolivre.com.br/MLB-3180157424', 299.00),
            ('Caixa de Som JBL Flip 6', 'https://produto.mercadolivre.com.br/MLB-2150396817', 599.00),

            # Magazine Luiza
            ('Air Fryer Philips', 'https://www.magazineluiza.com.br/air-fryer/p/234158700', 499.00),
            ('Liquidificador Arno', 'https://www.magazineluiza.com.br/liquidificador/p/221344500', 189.00),
            ('Cafeteira Nespresso', 'https://www.magazineluiza.com.br/cafeteira-nespresso/p/237043000', 399.00),

            # Produtos genéricos com dados fixos (fallback caso APIs falhem)
            ('Kit Iluminação LED', 'https://www.kabum.com.br/produto/305214', 120.00),
            ('Suporte para Notebook', 'https://www.amazon.com.br/dp/B07DFKG1X5', 89.90),
            ('Filtro de Linha', 'https://www.kabum.com.br/produto/102837', 79.90),
            ('Caneca Térmica', 'https://www.amazon.com.br/dp/B07Y8PRDFT', 49.90),
            ('Livro Clean Code', 'https://www.amazon.com.br/dp/8576082675', 65.00),
            ('LEGO Star Wars', 'https://www.amazon.com.br/dp/B07W7XNRQS', 450.00),
            ('Câmera GoPro Hero 11', 'https://www.amazon.com.br/dp/B0B3MQJFJX', 2500.00),
        ]

        usuarios_criados = 0
        presentes_criados = 0

        for i in range(num_users):
            # Selecionar dados do usuário
            primeiro_nome, ultimo_nome, email = nomes[i % len(nomes)]

            # Adicionar número ao email para evitar duplicatas
            email = email.replace('@', f'{i+1}@')
            username = f'{primeiro_nome.lower()}.{ultimo_nome.lower()}{i+1}'

            # Verificar se usuário já existe
            if Usuario.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'  Usuário {email} já existe, pulando...'))
                continue

            # Criar usuário
            usuario = Usuario.objects.create(
                username=username,
                email=email,
                first_name=primeiro_nome,
                last_name=ultimo_nome,
                password=make_password('senha123'),  # Senha padrão para teste
                ativo=True,
                grupo_ativo=grupo_teste  # Definir grupo ativo
            )
            usuarios_criados += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Criado usuário: {primeiro_nome} {ultimo_nome} ({email})'))

            # Adicionar usuário ao grupo de teste
            # Primeiro usuário é mantenedor, demais são membros
            e_mantenedor = (i == 0)
            GrupoMembro.objects.get_or_create(
                grupo=grupo_teste,
                usuario=usuario,
                defaults={'e_mantenedor': e_mantenedor}
            )
            tipo_membro = 'Mantenedor' if e_mantenedor else 'Membro'
            self.stdout.write(f'  → Adicionado ao grupo como {tipo_membro}')

            # Criar presentes para este usuário
            presentes_usuario = random.sample(presentes_exemplos, min(gifts_per_user, len(presentes_exemplos)))

            for descricao_fallback, url, preco_fallback in presentes_usuario:
                # Tentar extrair informações reais do produto usando scrapers específicos
                from presentes.scrapers import ScraperFactory

                descricao = descricao_fallback
                preco = preco_fallback
                imagem_url = None

                self.stdout.write(f'  → Buscando informações de: {url[:50]}...')

                # Novo formato de retorno (dict ao invés de tupla)
                resultado = ScraperFactory.extract_product_info(url)

                if resultado and resultado.get('success'):
                    # Extração bem-sucedida
                    if resultado.get('titulo'):
                        descricao = resultado.get('titulo')
                    if resultado.get('preco'):
                        preco = resultado.get('preco')
                    if resultado.get('imagem_url'):
                        imagem_url = resultado.get('imagem_url')
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Dados extraídos com sucesso!'))
                else:
                    # Falha na extração (rede ou parsing)
                    error_type = resultado.get('error_type', 'unknown') if resultado else 'unknown'
                    if error_type == 'network':
                        self.stdout.write(self.style.WARNING(f'    ⚠ Erro de rede: usando dados padrão'))
                    elif error_type == 'parsing':
                        self.stdout.write(self.style.WARNING(f'    ⚠ Erro de parsing: usando dados padrão'))
                    else:
                        self.stdout.write(self.style.WARNING(f'    ⚠ Usando dados padrão (falha na extração)'))

                # 70% de chance de ser ATIVO, 30% de ser COMPRADO
                status = 'ATIVO' if random.random() < 0.7 else 'COMPRADO'

                # Criar presente com associação ao grupo
                presente = Presente.objects.create(
                    usuario=usuario,
                    grupo=grupo_teste,  # Associar ao grupo
                    descricao=descricao,
                    url=url,
                    preco=preco,
                    status=status
                )
                presentes_criados += 1

                status_icon = '✓' if status == 'ATIVO' else '✗'
                self.stdout.write(f'  {status_icon} Criado: {descricao[:50]} - R$ {preco:.2f} ({status})')

                # Pequeno delay para evitar rate limiting
                time.sleep(0.5)

        # Resumo
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Grupo: {grupo_teste.nome}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total de usuários criados: {usuarios_criados}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total de presentes criados: {presentes_criados}'))
        self.stdout.write('\n' + self.style.WARNING('IMPORTANTE:'))
        self.stdout.write(self.style.WARNING('  • Todos os usuários têm a senha: senha123'))
        self.stdout.write(self.style.WARNING('  • Todos foram adicionados ao grupo: ' + grupo_teste.nome))
        self.stdout.write(self.style.WARNING('  • Primeiro usuário é Mantenedor, demais são Membros'))
        self.stdout.write('='*60)
