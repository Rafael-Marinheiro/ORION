/* 2.1 -- operacao offline temporaria.
 *
 * O documento: "o sistema podera ser operado em modo offline temporario, o
 * que significa que os grupos poderao trabalhar em suas analises e decisoes
 * sem a necessidade de estarem constantemente conectados a internet. A
 * conexao sera exigida apenas nos momentos de envio das decisoes."
 *
 * O 2.1.1 fecha o escopo: "o simulador nao podera ser operado inteiramente
 * offline, pois o envio das decisoes e a atualizacao dos dados exigem
 * conexao". Entao nao ha service worker nem fila de sincronizacao: o que
 * precisa sobreviver a uma queda e o que o aluno DIGITOU e ainda nao
 * enviou. Isso cabe em localStorage.
 *
 * O rascunho e por maquina e por rodada, some depois do envio, e nunca
 * substitui valor que o servidor ja devolveu preenchido.
 */
(function () {
    "use strict";

    var painel = document.querySelector("[data-rascunho]");
    if (!painel) return;

    var chaveBase = "orion:rascunho:" + (painel.dataset.rascunho || "painel");
    var armazem = null;
    try {
        armazem = window.localStorage;
        armazem.setItem(chaveBase + ":teste", "1");
        armazem.removeItem(chaveBase + ":teste");
    } catch (erro) {
        // Janela anonima, armazenamento bloqueado ou cota estourada. O painel
        // funciona igual; so nao guarda rascunho.
        armazem = null;
    }

    var campos = painel.querySelectorAll(
        "form input:not([type=hidden]):not([type=submit]):not([type=checkbox]):not([type=radio]), form select, form textarea"
    );

    function chaveDoCampo(campo) {
        var form = campo.form;
        var nomeDoForm = form ? (form.dataset.form || form.id || "f") : "f";
        return chaveBase + ":" + nomeDoForm + ":" + campo.name;
    }

    function restaurar() {
        if (!armazem) return;
        campos.forEach(function (campo) {
            if (!campo.name || campo.value) return; // servidor tem prioridade
            var guardado = armazem.getItem(chaveDoCampo(campo));
            if (guardado !== null) campo.value = guardado;
        });
    }

    function guardar(campo) {
        if (!armazem || !campo.name) return;
        try {
            if (campo.value) {
                armazem.setItem(chaveDoCampo(campo), campo.value);
            } else {
                armazem.removeItem(chaveDoCampo(campo));
            }
        } catch (erro) {
            /* cota estourada: segue sem rascunho */
        }
    }

    function limparForm(form) {
        if (!armazem) return;
        Array.prototype.forEach.call(form.elements, function (campo) {
            if (campo.name) armazem.removeItem(chaveDoCampo(campo));
        });
    }

    restaurar();

    campos.forEach(function (campo) {
        campo.addEventListener("input", function () { guardar(campo); });
        campo.addEventListener("change", function () { guardar(campo); });
    });

    // Enviou: o rascunho daquele formulario cumpriu o papel.
    painel.querySelectorAll("form").forEach(function (form) {
        form.addEventListener("submit", function () { limparForm(form); });
    });

    // Aviso de conexao. O 2.1 permite decidir offline; so o envio exige rede,
    // e o aluno precisa saber disso ANTES de clicar em submeter.
    var aviso = document.querySelector("[data-conexao]");
    if (!aviso) return;

    function atualizarConexao() {
        var offline = navigator.onLine === false;
        aviso.hidden = !offline;
        painel.querySelectorAll("button[type=submit]").forEach(function (botao) {
            botao.dataset.offline = offline ? "1" : "";
        });
    }

    window.addEventListener("online", atualizarConexao);
    window.addEventListener("offline", atualizarConexao);
    atualizarConexao();
})();
