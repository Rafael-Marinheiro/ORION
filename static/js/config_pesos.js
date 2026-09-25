/* Soma dos pesos do 12.2 enquanto o professor digita.

   A validacao do servidor continua sendo a que manda -- ela recusa qualquer
   soma diferente de 1. Isto so evita descobrir o erro depois de enviar. */
(function () {
    'use strict';

    var bloco = document.querySelector('[data-pesos]');
    var saida = document.querySelector('[data-soma-pesos]');
    if (!bloco || !saida) { return; }

    var campos = bloco.querySelectorAll('input[type="number"], input[type="text"]');
    if (!campos.length) { return; }

    function somar() {
        var total = 0;
        for (var i = 0; i < campos.length; i++) {
            total += parseFloat(String(campos[i].value).replace(',', '.')) || 0;
        }
        var fechada = Math.abs(total - 1) < 0.0001;
        saida.textContent = 'Soma dos pesos: ' + total.toFixed(4).replace('.', ',') +
            (fechada ? '' : ' — precisa dar 1,0000');
        saida.dataset.estado = fechada ? 'ok' : 'pendente';
    }

    for (var i = 0; i < campos.length; i++) {
        campos[i].addEventListener('input', somar);
    }
    somar();
}());
