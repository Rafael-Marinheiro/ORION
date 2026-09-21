/* ORION - monta os graficos declarados em window.orionCharts.
   Le as cores dos tokens CSS, entao o grafico acompanha o tema da pagina.
   Se o Chart.js nao carregar, mostra o texto de fallback e sai. */

(function () {
    'use strict';

    var specs = window.orionCharts || [];
    if (!specs.length) { return; }

    function token(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    function show(id) {
        var el = id && document.getElementById(id);
        if (el) { el.hidden = false; }
    }

    if (!window.Chart) {
        specs.forEach(function (spec) {
            var canvas = document.getElementById(spec.canvas);
            if (canvas) { canvas.style.display = 'none'; }
            show(spec.fallback);
        });
        return;
    }

    var instances = [];

    /* Paleta categorica em ordem FIXA. A ordem e o mecanismo de seguranca
       para daltonismo -- foi validada par a par nessa sequencia, entao nao
       reordene nem cicle. Serie alem do ultimo slot vira cinza e avisa, em
       vez de repetir uma cor e tornar o grafico ilegivel. */
    function paleta() {
        return [
            token('--o-series-1'),
            token('--o-series-2'),
            token('--o-series-3'),
            token('--o-series-4'),
            token('--o-series-5'),
            token('--o-series-6'),
            token('--o-series-7'),
            token('--o-series-8'),
            token('--o-series-9'),
            token('--o-series-10')
        ];
    }

    function corDaSerie(cores, i) {
        if (i < cores.length) { return cores[i]; }
        if (console && console.warn) {
            console.warn('orion/charts: serie ' + (i + 1) + ' passa dos ' +
                cores.length + ' slots da paleta; agrupe em "Outros" ou separe o grafico.');
        }
        return token('--o-ink-dim');
    }

    function build(spec) {
        var canvas = document.getElementById(spec.canvas);
        if (!canvas) { return null; }

        var cores = paleta();
        var ink = token('--o-ink');
        var dim = token('--o-ink-dim');
        var linha = token('--o-line');
        var superficie = token('--o-panel');

        var chart = new Chart(canvas, {
            type: spec.type || 'bar',
            data: {
                labels: spec.labels || [],
                datasets: (spec.series || []).map(function (s, i) {
                    var cor = corDaSerie(cores, i);
                    var linhaDaSerie = s.type === 'line';
                    if (linhaDaSerie) {
                        /* a linha fica sem preenchimento para nao competir
                           com as barras que ela atravessa */
                        return {
                            label: s.label,
                            data: s.data,
                            type: 'line',
                            backgroundColor: 'transparent',
                            borderColor: cor,
                            borderWidth: 2,
                            pointRadius: 4,
                            pointBackgroundColor: cor,
                            pointBorderColor: superficie,
                            pointBorderWidth: 2,
                            tension: 0.25,
                            fill: false,
                            spanGaps: true
                        };
                    }
                    return {
                        label: s.label,
                        data: s.data,
                        backgroundColor: cor,
                        /* 2px da cor da superficie separam os segmentos
                           empilhados e as barras vizinhas */
                        borderColor: superficie,
                        borderWidth: spec.stacked ? 2 : 1,
                        borderRadius: 4,
                        borderSkipped: false
                    };
                })
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: spec.indexAxis || 'x',
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: spec.legenda !== false,
                        labels: { color: ink, boxWidth: 12, usePointStyle: true }
                    },
                    tooltip: { padding: 10 }
                },
                scales: {
                    x: {
                        stacked: !!spec.stacked,
                        ticks: { color: dim },
                        grid: { color: linha }
                    },
                    y: {
                        stacked: !!spec.stacked,
                        ticks: {
                            color: dim,
                            stepSize: spec.integerY ? 1 : undefined,
                            precision: spec.integerY ? 0 : undefined
                        },
                        grid: { color: linha },
                        beginAtZero: spec.yMin === undefined,
                        min: spec.yMin,
                        max: spec.yMax,
                        reverse: !!spec.reverseY
                    }
                }
            }
        });

        return { chart: chart, spec: spec };
    }

    specs.forEach(function (spec) {
        var made = build(spec);
        if (made) { instances.push(made); }
    });

    /* o tema troca sem recarregar: redesenha com os tokens novos */
    new MutationObserver(function () {
        instances.forEach(function (item) {
            item.chart.destroy();
        });
        var novos = [];
        specs.forEach(function (spec) {
            var made = build(spec);
            if (made) { novos.push(made); }
        });
        instances = novos;
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}());
