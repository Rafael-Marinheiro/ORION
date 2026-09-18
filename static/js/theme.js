/* ORION - tema, navegacao e contagem regressiva da rodada.
   Sem dependencias. Tudo degrada para o HTML servido pelo Django. */

(function () {
    'use strict';

    /* --- tema ---------------------------------------------------------- */
    var root = document.documentElement;
    var select = document.querySelector('[data-theme-select]');

    function store(key, value) {
        try { localStorage.setItem(key, value); } catch (e) { /* storage bloqueado */ }
    }

    if (select) {
        select.value = root.dataset.theme === 'light' ? 'light' : 'dark';
        select.addEventListener('change', function () {
            root.dataset.theme = select.value;
            store('orion-theme', select.value);
        });
    }

    /* --- navegacao movel ----------------------------------------------- */
    var navToggle = document.querySelector('[data-nav-toggle]');
    var navLinks = document.querySelector('[data-nav-links]');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            var open = navLinks.dataset.open === 'true';
            navLinks.dataset.open = open ? 'false' : 'true';
            navToggle.setAttribute('aria-expanded', open ? 'false' : 'true');
        });
    }

    /* --- menu de gestao ------------------------------------------------- */
    var menuToggle = document.querySelector('[data-menu-toggle]');

    if (menuToggle) {
        menuToggle.addEventListener('click', function (event) {
            event.stopPropagation();
            var open = menuToggle.getAttribute('aria-expanded') === 'true';
            menuToggle.setAttribute('aria-expanded', open ? 'false' : 'true');
        });
        document.addEventListener('click', function () {
            menuToggle.setAttribute('aria-expanded', 'false');
        });
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                menuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    /* --- boletim da rodada ---------------------------------------------- */
    /* A noticia chega uma vez. Reanimar a cada navegacao transformaria a
       manchete em ruido, e o aluno passaria a ignora-la -- que e o oposto
       do que ela existe para fazer. */
    var boletim = document.querySelector('[data-boletim]');

    if (boletim) {
        var rodada = boletim.dataset.rodada || '0';
        var chave = 'orion-boletim-visto';
        var visto = null;
        try { visto = localStorage.getItem(chave); } catch (e) { /* storage bloqueado */ }

        if (visto !== rodada) {
            boletim.dataset.novo = 'true';
            store(chave, rodada);
        }
    }

    /* --- contagem regressiva da rodada ---------------------------------- */
    /* O servidor ja entrega a data de fechamento formatada. Isto so a
       transforma em tempo restante e marca urgencia visual. */
    var clock = document.querySelector('[data-deadline]');
    var output = clock && clock.querySelector('[data-countdown]');
    var status = document.querySelector('[data-countdown-status]');

    if (clock && output) {
        var deadline = new Date(clock.dataset.deadline);

        if (!isNaN(deadline.getTime())) {
            var lastAnnounced = null;

            var tick = function () {
                var restante = deadline - new Date();

                if (restante <= 0) {
                    clock.dataset.state = 'expired';
                    clock.firstElementChild.textContent = 'Fechada em';
                    output.textContent = deadline.toLocaleString('pt-BR', {
                        day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                    });
                    if (status) { status.textContent = 'A rodada foi fechada.'; }
                    return;
                }

                var totalMin = Math.floor(restante / 60000);
                var h = Math.floor(totalMin / 60);
                var m = totalMin % 60;
                var s = Math.floor((restante % 60000) / 1000);

                output.textContent = h > 0
                    ? h + 'h ' + String(m).padStart(2, '0') + 'min'
                    : String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');

                clock.dataset.state = totalMin < 60 ? 'urgent' : 'normal';

                /* anuncia so nas viradas que importam, nao a cada segundo */
                if (status) {
                    var marco = null;
                    if (totalMin === 60) { marco = 'Falta 1 hora para o fechamento da rodada.'; }
                    else if (totalMin === 15) { marco = 'Faltam 15 minutos para o fechamento da rodada.'; }
                    else if (totalMin === 5) { marco = 'Faltam 5 minutos para o fechamento da rodada.'; }
                    if (marco && marco !== lastAnnounced) {
                        status.textContent = marco;
                        lastAnnounced = marco;
                    }
                }

                window.setTimeout(tick, totalMin >= 60 ? 30000 : 1000);
            };

            tick();
        }
    }
}());
