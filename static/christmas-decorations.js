/* ===================================
   CHRISTMAS DECORATIONS - ANIMATED SNOWFLAKES
   Flocos de neve animados e decorações natalinas
   =================================== */

(function() {
    'use strict';

    // Configuração dos flocos de neve
    const config = {
        snowflakeCount: 50,
        minSize: 2,
        maxSize: 6,
        minDuration: 10,
        maxDuration: 30,
        wind: true
    };

    // Criar container para os flocos de neve
    function createSnowContainer() {
        const container = document.createElement('div');
        container.id = 'snow-container';
        container.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            overflow: hidden;
        `;
        document.body.appendChild(container);
        return container;
    }

    // Criar um floco de neve individual
    function createSnowflake() {
        const snowflake = document.createElement('div');
        const size = Math.random() * (config.maxSize - config.minSize) + config.minSize;
        const startPosition = Math.random() * 100;
        const endPosition = startPosition + (Math.random() * 20 - 10); // Movimento lateral
        const duration = Math.random() * (config.maxDuration - config.minDuration) + config.minDuration;
        const delay = Math.random() * 5;
        const opacity = Math.random() * 0.6 + 0.4;

        snowflake.innerHTML = '❄';
        snowflake.style.cssText = `
            position: absolute;
            top: -20px;
            left: ${startPosition}%;
            font-size: ${size}px;
            color: rgba(255, 255, 255, ${opacity});
            user-select: none;
            pointer-events: none;
            animation: snowfall-${Date.now()}-${Math.random()} ${duration}s linear ${delay}s infinite;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
        `;

        // Criar animação única para cada floco
        const keyframes = `
            @keyframes snowfall-${Date.now()}-${Math.random()} {
                0% {
                    transform: translateY(0) translateX(0) rotate(0deg);
                    opacity: ${opacity};
                }
                50% {
                    opacity: ${opacity * 1.2};
                }
                100% {
                    transform: translateY(100vh) translateX(${endPosition - startPosition}vw) rotate(360deg);
                    opacity: 0;
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = keyframes;
        document.head.appendChild(styleSheet);

        return snowflake;
    }

    // Criar estrelas brilhantes no background
    function createStars() {
        const starsContainer = document.createElement('div');
        starsContainer.id = 'stars-container';
        starsContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        `;

        // Criar várias estrelas
        for (let i = 0; i < 30; i++) {
            const star = document.createElement('div');
            const size = Math.random() * 3 + 1;
            const left = Math.random() * 100;
            const top = Math.random() * 100;
            const duration = Math.random() * 3 + 2;
            const delay = Math.random() * 5;

            star.innerHTML = '✨';
            star.style.cssText = `
                position: absolute;
                left: ${left}%;
                top: ${top}%;
                font-size: ${size}px;
                opacity: 0;
                animation: twinkle ${duration}s ease-in-out ${delay}s infinite;
            `;

            starsContainer.appendChild(star);
        }

        // Adicionar animação de piscar para as estrelas
        const twinkleStyle = document.createElement('style');
        twinkleStyle.textContent = `
            @keyframes twinkle {
                0%, 100% { opacity: 0; transform: scale(1); }
                50% { opacity: 0.8; transform: scale(1.2); }
            }
        `;
        document.head.appendChild(twinkleStyle);

        document.body.appendChild(starsContainer);
    }

    // Criar ornamentos decorativos nas bordas
    function createOrnaments() {
        const ornaments = document.createElement('div');
        ornaments.id = 'ornaments-container';
        ornaments.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        `;

        // Ornamentos no topo esquerdo
        const topLeft = document.createElement('div');
        topLeft.innerHTML = '🎄';
        topLeft.style.cssText = `
            position: absolute;
            top: 20px;
            left: 20px;
            font-size: 40px;
            opacity: 0.3;
            animation: sway 3s ease-in-out infinite;
        `;

        // Ornamentos no topo direito
        const topRight = document.createElement('div');
        topRight.innerHTML = '🎁';
        topRight.style.cssText = `
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 35px;
            opacity: 0.3;
            animation: sway 4s ease-in-out infinite reverse;
        `;

        // Ornamentos embaixo esquerdo
        const bottomLeft = document.createElement('div');
        bottomLeft.innerHTML = '🔔';
        bottomLeft.style.cssText = `
            position: absolute;
            bottom: 20px;
            left: 20px;
            font-size: 30px;
            opacity: 0.3;
            animation: swing 2s ease-in-out infinite;
        `;

        // Ornamentos embaixo direito
        const bottomRight = document.createElement('div');
        bottomRight.innerHTML = '⭐';
        bottomRight.style.cssText = `
            position: absolute;
            bottom: 20px;
            right: 20px;
            font-size: 35px;
            opacity: 0.3;
            animation: rotate-star 10s linear infinite;
        `;

        ornaments.appendChild(topLeft);
        ornaments.appendChild(topRight);
        ornaments.appendChild(bottomLeft);
        ornaments.appendChild(bottomRight);

        // Adicionar animações
        const ornamentsStyle = document.createElement('style');
        ornamentsStyle.textContent = `
            @keyframes sway {
                0%, 100% { transform: rotate(-5deg); }
                50% { transform: rotate(5deg); }
            }

            @keyframes swing {
                0%, 100% { transform: rotate(-10deg); }
                50% { transform: rotate(10deg); }
            }

            @keyframes rotate-star {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(ornamentsStyle);

        document.body.appendChild(ornaments);
    }

    // Inicializar todas as decorações
    function initChristmasDecorations() {
        // Verificar se o usuário prefere reduzir movimento (acessibilidade)
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        if (!prefersReducedMotion) {
            // Criar estrelas de fundo
            createStars();

            // Criar container de neve
            const snowContainer = createSnowContainer();

            // Criar flocos de neve
            for (let i = 0; i < config.snowflakeCount; i++) {
                setTimeout(() => {
                    snowContainer.appendChild(createSnowflake());
                }, i * 100);
            }

            // Criar ornamentos decorativos
            createOrnaments();

            console.log('🎄 Decorações natalinas ativadas!');
        } else {
            console.log('⚙️ Animações reduzidas (preferência do usuário)');
        }
    }

    // Opção para desativar/ativar decorações
    window.toggleChristmasDecorations = function(enable) {
        const containers = [
            document.getElementById('snow-container'),
            document.getElementById('stars-container'),
            document.getElementById('ornaments-container')
        ];

        containers.forEach(container => {
            if (container) {
                container.style.display = enable ? 'block' : 'none';
            }
        });
    };

    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChristmasDecorations);
    } else {
        initChristmasDecorations();
    }

    // Criar partículas ao clicar (efeito mágico de neve)
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
            createClickEffect(e.pageX, e.pageY);
        }
    });

    function createClickEffect(x, y) {
        const particleCount = 8;
        const particles = [];

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.innerHTML = ['❄', '✨', '⭐'][Math.floor(Math.random() * 3)];
            particle.style.cssText = `
                position: fixed;
                left: ${x}px;
                top: ${y}px;
                font-size: ${Math.random() * 10 + 10}px;
                pointer-events: none;
                z-index: 10000;
                animation: particle-burst-${i} 1s ease-out forwards;
            `;

            const angle = (360 / particleCount) * i;
            const distance = 50;
            const endX = Math.cos(angle * Math.PI / 180) * distance;
            const endY = Math.sin(angle * Math.PI / 180) * distance;

            const keyframes = `
                @keyframes particle-burst-${i} {
                    0% {
                        transform: translate(0, 0) scale(1);
                        opacity: 1;
                    }
                    100% {
                        transform: translate(${endX}px, ${endY}px) scale(0);
                        opacity: 0;
                    }
                }
            `;

            const styleSheet = document.createElement('style');
            styleSheet.textContent = keyframes;
            document.head.appendChild(styleSheet);

            document.body.appendChild(particle);

            setTimeout(() => {
                particle.remove();
                styleSheet.remove();
            }, 1000);
        }
    }

})();
