/* Abertura da rodada: o numero da proxima rodada e o estado da turma
   acompanham a turma escolhida.

   O sistema ja sabe qual e a proxima rodada de cada turma -- pedir o numero
   de memoria so criava chance de erro. Sem este script o formulario segue
   funcionando: o servidor ja entrega a turma e o numero certos no primeiro
   carregamento, e valida os dois no envio. */
(function () {
    'use strict';

    var dados = document.getElementById('estado-turmas');
    var campoJogo = document.getElementById('id_jogo');
    var campoNumero = document.getElementById('id_numero');
    var aviso = document.querySelector('[data-estado-turma]');
    if (!dados || !campoJogo || !campoNumero || !aviso) { return; }

    var estados = {};
    JSON.parse(dados.textContent).forEach(function (estado) {
        estados[estado.valor] = estado;
    });

    function atualizar(trocouDeTurma) {
        var estado = estados[campoJogo.value];
        if (!estado) {
            aviso.hidden = true;
            return;
        }

        /* Digitou um numero a mao? Respeita. So a troca de turma reescreve. */
        if (trocouDeTurma) { campoNumero.value = estado.proxima; }

        var texto;
        var tom = 'info';
        if (estado.pendente) {
            /* 11.1: quem fecha a rodada e o prazo. Abrir outra por cima
               deixa duas rodadas recebendo decisao ao mesmo tempo. */
            texto = 'A rodada ' + estado.pendente + ' desta turma ainda não foi encerrada.';
            tom = 'warning';
        } else if (estado.encerrada) {
            texto = 'Esta turma já fechou as ' + estado.total + ' rodadas configuradas.';
            tom = 'warning';
        } else {
            texto = 'Próxima rodada desta turma: ' + estado.proxima +
                (estado.total ? ' de ' + estado.total : '') + '.';
        }

        aviso.textContent = texto;
        aviso.className = 'o-note o-note--' + tom;
        aviso.hidden = false;
    }

    campoJogo.addEventListener('change', function () { atualizar(true); });
    atualizar(false);

    /* --- evento da rodada ------------------------------------------------ */
    /* Progressive disclosure: os campos do evento so aparecem depois que o
       professor diz que quer determinar um. Sem o script, tudo fica visivel
       e o formulario continua valido -- e o servidor que decide o que e
       obrigatorio. */
    var bloco = document.querySelector('[data-evento]');
    if (!bloco) { return; }

    var ligar = bloco.querySelector('#id_adicionar_evento');
    var corpo = bloco.querySelector('[data-evento-corpo]');
    var catalogo = bloco.querySelector('[data-evento-catalogo]');
    var novo = bloco.querySelector('[data-evento-novo]');
    var origens = bloco.querySelectorAll('input[name="origem_evento"]');
    if (!ligar || !corpo) { return; }

    function origemEscolhida() {
        for (var i = 0; i < origens.length; i++) {
            if (origens[i].checked) { return origens[i].value; }
        }
        return 'catalogo';
    }

    function mostrar() {
        corpo.hidden = !ligar.checked;
        var criando = origemEscolhida() === 'novo';
        if (catalogo) { catalogo.hidden = criando; }
        if (novo) { novo.hidden = !criando; }
    }

    ligar.addEventListener('change', mostrar);
    for (var i = 0; i < origens.length; i++) {
        origens[i].addEventListener('change', mostrar);
    }
    mostrar();
}());