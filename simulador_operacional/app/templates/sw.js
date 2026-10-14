/* 2.1 -- operacao offline temporaria.
 *
 * O ORION e renderizado no servidor: sem service worker, o aluno que perde
 * a rede e troca de tela recebe a pagina de erro do navegador -- nao ha
 * aplicacao para usar. Este arquivo guarda a casca e as ultimas telas
 * visitadas, para que o 2.1 valha: "trabalhar em suas analises e decisoes
 * sem a necessidade de estarem constantemente conectados".
 *
 * O que ele NAO faz, de proposito: enfileirar envio. O 2.1.1 diz que "o
 * envio das decisoes exige conexao" e o 11.1 fecha a rodada no instante
 * exato do prazo. Submissao entregue depois do prazo porque estava na fila
 * fura a regra e e injusta com quem enviou em tempo. Por isso todo POST vai
 * direto a rede e falha quando nao ha rede.
 */

var VERSAO = "orion-v1";
var CASCA = [
    "/static/css/styles.css",
    "/static/css/fontes.css",
    "/static/js/theme.js",
    "/static/js/charts.js",
    "/static/js/rascunho.js",
    "/static/js/chart.umd.min.js",
    "/static/img/orion-emblem.png",
    "/offline/",
];

self.addEventListener("install", function (evento) {
    evento.waitUntil(
        caches.open(VERSAO).then(function (cache) {
            // `addAll` falha inteiro se um item falhar; aqui um arquivo
            // ausente nao pode impedir o registro do worker.
            return Promise.all(
                CASCA.map(function (url) {
                    return cache.add(url).catch(function () { return null; });
                })
            );
        }).then(function () { return self.skipWaiting(); })
    );
});

self.addEventListener("activate", function (evento) {
    evento.waitUntil(
        caches.keys().then(function (nomes) {
            return Promise.all(
                nomes.filter(function (nome) { return nome !== VERSAO; })
                     .map(function (nome) { return caches.delete(nome); })
            );
        }).then(function () { return self.clients.claim(); })
    );
});

self.addEventListener("fetch", function (evento) {
    var requisicao = evento.request;

    // Envio de decisao, login, troca de configuracao: sempre rede.
    if (requisicao.method !== "GET") return;

    var url = new URL(requisicao.url);
    if (url.origin !== self.location.origin) return;
    // A area administrativa e a API nunca saem do cache: dado velho ali
    // engana quem esta operando a rodada.
    if (url.pathname.startsWith("/admin") || url.pathname.startsWith("/api")) {
        return;
    }

    var estatico = url.pathname.startsWith("/static/");

    if (estatico) {
        // Arquivo versionado por querystring: cache primeiro.
        evento.respondWith(
            caches.match(requisicao).then(function (guardado) {
                return guardado || fetch(requisicao).then(function (resposta) {
                    return guardar(requisicao, resposta);
                });
            })
        );
        return;
    }

    // Tela: rede primeiro, para o aluno ver o estado real da rodada sempre
    // que houver conexao. O cache so entra quando a rede falha.
    evento.respondWith(
        fetch(requisicao)
            .then(function (resposta) { return guardar(requisicao, resposta); })
            .catch(function () {
                return caches.match(requisicao).then(function (guardado) {
                    return guardado || caches.match("/offline/");
                });
            })
    );
});

function guardar(requisicao, resposta) {
    if (!resposta || resposta.status !== 200 || resposta.type === "opaque") {
        return resposta;
    }
    var copia = resposta.clone();
    caches.open(VERSAO).then(function (cache) {
        cache.put(requisicao, copia).catch(function () { /* cota */ });
    });
    return resposta;
}
