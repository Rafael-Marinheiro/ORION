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

    /* --- fluxo de decisao ---------------------------------------------- */
    var flow = document.querySelector('[data-decision-flow]');

    if (flow) {
        var steps = Array.prototype.slice.call(flow.querySelectorAll('[data-flow-target]'));
        var panels = Array.prototype.slice.call(document.querySelectorAll('[data-flow-panel]'));
        var flowStatus = flow.querySelector('[data-flow-status]');

        function showStep(target, focusStep) {
            steps.forEach(function (step) {
                var selected = step.dataset.flowTarget === target;
                step.setAttribute('aria-selected', selected ? 'true' : 'false');
                step.tabIndex = selected ? 0 : -1;
                step.classList.toggle('is-active', selected);
                if (selected && focusStep) { step.focus(); }
            });
            panels.forEach(function (panel) {
                panel.hidden = panel.dataset.flowPanel !== target;
            });
            flow.dataset.ready = 'true';
            if (flowStatus) {
                var current = steps.filter(function (step) { return step.dataset.flowTarget === target; })[0];
                flowStatus.textContent = current ? 'Etapa ' + current.querySelector('span').textContent + ': ' + current.textContent.trim() + '.' : '';
            }
        }

        steps.forEach(function (step, index) {
            step.addEventListener('click', function () { showStep(step.dataset.flowTarget, false); });
            step.addEventListener('keydown', function (event) {
                if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') { return; }
                event.preventDefault();
                var next = event.key === 'ArrowRight' ? (index + 1) % steps.length : (index - 1 + steps.length) % steps.length;
                showStep(steps[next].dataset.flowTarget, true);
            });
        });
        showStep('compra', false);
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

                var estado = totalMin < 60 ? 'urgent' : 'normal';
                /* A virada para a ultima hora e o unico momento em que a
                   interface se move sozinha. Uma vez so, nao a cada tick. */
                if (estado === 'urgent' && clock.dataset.state !== 'urgent') {
                    clock.dataset.virada = '';
                    setTimeout(function () { delete clock.dataset.virada; }, 400);
                }
                clock.dataset.state = estado;

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

    /* --- realce da praca sob o cursor ----------------------------------- */
    /* Mapa e lista mostram a mesma praca em dois lugares. Apontar para uma
       delas acende as duas e apaga as outras. Sem este script os dois
       seguem legiveis: o realce e acrescimo, nao suporte. */
    var pracas = document.querySelector('[data-pracas]');

    if (pracas) {
        var alvos = pracas.querySelectorAll('[data-praca]');

        var realcar = function (nome) {
            for (var i = 0; i < alvos.length; i++) {
                var alvo = alvos[i];
                var igual = alvo.dataset.praca === nome;
                alvo.classList.toggle('is-realce', nome !== null && igual);
                alvo.classList.toggle('is-apagado', nome !== null && !igual);
            }
        };

        var daPraca = function (evento) {
            var alvo = evento.target.closest && evento.target.closest('[data-praca]');
            return alvo ? alvo.dataset.praca : null;
        };

        pracas.addEventListener('pointerover', function (evento) {
            var nome = daPraca(evento);
            if (nome) { realcar(nome); }
        });
        pracas.addEventListener('focusin', function (evento) {
            var nome = daPraca(evento);
            if (nome) { realcar(nome); }
        });
        pracas.addEventListener('pointerleave', function () { realcar(null); });
        pracas.addEventListener('focusout', function () { realcar(null); });
    }
}());
