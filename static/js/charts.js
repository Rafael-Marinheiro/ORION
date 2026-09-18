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

    function paleta() {
        /* ordem estavel: series 1..3 sempre com a mesma cor entre telas */
        return [token('--o-star'), token('--o-ok'), token('--o-warn'), token('--o-bad')];
    }

    function build(spec) {
        var canvas = document.getElementById(spec.canvas);
        if (!canvas) { return null; }

        var cores = paleta();
        var ink = token('--o-ink');
        var dim = token('--o-ink-dim');
        var linha = token('--o-line');

        var chart = new Chart(canvas, {
            type: spec.type || 'bar',
            data: {
                labels: spec.labels || [],
                datasets: (spec.series || []).map(function (s, i) {
                    var cor = cores[i % cores.length];
                    return {
                        label: s.label,
                        data: s.data,
                        backgroundColor: cor,
                        borderColor: cor,
                        borderWidth: 1,
                        borderRadius: 3
                    };
                })
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: ink, boxWidth: 12, usePointStyle: true } },
                    tooltip: { padding: 10 }
                },
                scales: {
                    x: { ticks: { color: dim }, grid: { color: linha } },
                    y: { ticks: { color: dim }, grid: { color: linha }, beginAtZero: true }
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
