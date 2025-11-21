from django.core.management.base import BaseCommand
from presentes.models import Usuario, Presente
from django.contrib.auth.hashers import make_password
import random


class Command(BaseCommand):
    help = 'Cria usuários e presentes de teste para desenvolvimento'

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

        # Lista de presentes variados
        presentes_exemplos = [
            ('Notebook Gamer', 'https://zoom.com.br', 3500.00),
            ('Mouse Sem Fio Logitech', 'https://zoom.com.br', 89.90),
            ('Teclado Mecânico RGB', 'https://zoom.com.br', 450.00),
            ('Fone de Ouvido Bluetooth', 'https://zoom.com.br', 299.00),
            ('Webcam Full HD', 'https://zoom.com.br', 350.00),
            ('Monitor 27 polegadas', 'https://zoom.com.br', 1200.00),
            ('SSD 1TB', 'https://zoom.com.br', 450.00),
            ('Cadeira Gamer', 'https://zoom.com.br', 1100.00),
            ('Microfone Condensador', 'https://zoom.com.br', 280.00),
            ('Kit Iluminação LED', 'https://zoom.com.br', 120.00),
            ('Kindle Paperwhite', 'https://amazon.com.br', 499.00),
            ('Echo Dot 5ª Geração', 'https://amazon.com.br', 349.00),
            ('Fire TV Stick 4K', 'https://amazon.com.br', 449.00),
            ('Smartwatch Samsung', 'https://zoom.com.br', 899.00),
            ('Fone JBL Tune 510BT', 'https://zoom.com.br', 199.00),
            ('Caixa de Som Portátil', 'https://zoom.com.br', 159.00),
            ('Power Bank 20000mAh', 'https://zoom.com.br', 79.90),
            ('Suporte para Notebook', 'https://zoom.com.br', 89.90),
            ('Hub USB-C 7 em 1', 'https://zoom.com.br', 129.00),
            ('Mousepad Gamer XXL', 'https://zoom.com.br', 49.90),
            ('Livro Clean Code', 'https://amazon.com.br', 65.00),
            ('Livro The Pragmatic Programmer', 'https://amazon.com.br', 89.00),
            ('Garrafa Térmica Stanley', 'https://amazon.com.br', 220.00),
            ('Mochila para Notebook', 'https://zoom.com.br', 180.00),
            ('Planta Suculenta Decorativa', 'https://example.com', 35.00),
            ('Caneca Personalizada', 'https://example.com', 29.90),
            ('Lego Star Wars', 'https://amazon.com.br', 450.00),
            ('Controle Xbox Wireless', 'https://zoom.com.br', 399.00),
            ('Headset Gamer HyperX', 'https://zoom.com.br', 299.00),
            ('Câmera GoPro Hero 11', 'https://zoom.com.br', 2500.00),
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
                ativo=True
            )
            usuarios_criados += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Criado usuário: {primeiro_nome} {ultimo_nome} ({email})'))

            # Criar presentes para este usuário
            presentes_usuario = random.sample(presentes_exemplos, min(gifts_per_user, len(presentes_exemplos)))

            for descricao, url, preco in presentes_usuario:
                # 70% de chance de ser ATIVO, 30% de ser COMPRADO
                status = 'ATIVO' if random.random() < 0.7 else 'COMPRADO'

                presente = Presente.objects.create(
                    usuario=usuario,
                    descricao=descricao,
                    url=url,
                    preco=preco,
                    status=status
                )
                presentes_criados += 1

                status_icon = '✓' if status == 'ATIVO' else '✗'
                self.stdout.write(f'  {status_icon} Presente: {descricao} - R$ {preco:.2f} ({status})')

        # Resumo
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✓ Total de usuários criados: {usuarios_criados}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Total de presentes criados: {presentes_criados}'))
        self.stdout.write('\n' + self.style.WARNING('IMPORTANTE: Todos os usuários têm a senha: senha123'))
        self.stdout.write('='*60)
