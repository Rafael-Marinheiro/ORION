/* Marca no sumario a secao que esta sendo lida.
 *
 * Sem isso o sumario fixo mostra sete links iguais e nao diz onde a pessoa
 * esta -- numa pagina de referencia consultada no meio da rodada, perder a
 * posicao e o que faz voltar ao topo.
 *
 * Degrada em silencio: sem IntersectionObserver, os links continuam
 * funcionando como ancoras comuns.
 */
(function () {
    "use strict";

    var sumario = document.querySelector("[data-sumario]");
    if (!sumario || !("IntersectionObserver" in window)) return;

    var links = {};
    sumario.querySelectorAll("a[href^='#']").forEach(function (link) {
        links[link.getAttribute("href").slice(1)] = link;
    });

    var alvos = Object.keys(links)
        .map(function (id) { return document.getElementById(id); })
        .filter(Boolean);
    if (!alvos.length) return;

    var visiveis = new Set();

    function marcar() {
        // A secao corrente e a primeira visivel na ordem do documento, e
        // nao a ultima que disparou o observador: rolar para cima entrega
        // os eventos na ordem inversa.
        var atual = alvos.find(function (alvo) { return visiveis.has(alvo.id); });
        Object.keys(links).forEach(function (id) {
            if (atual && id === atual.id) {
                links[id].setAttribute("aria-current", "true");
            } else {
                links[id].removeAttribute("aria-current");
            }
        });
    }

    var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            if (entrada.isIntersecting) {
                visiveis.add(entrada.target.id);
            } else {
                visiveis.delete(entrada.target.id);
            }
        });
        marcar();
    }, {
        // A faixa de leitura: do topo ate pouco abaixo do meio da tela.
        rootMargin: "0px 0px -55% 0px",
    });

    alvos.forEach(function (alvo) { observador.observe(alvo); });
})();
