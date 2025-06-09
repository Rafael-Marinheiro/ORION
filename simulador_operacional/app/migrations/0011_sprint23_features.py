from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("app", "0010_merge_20250609_1451"),
    ]

    operations = [
        migrations.CreateModel(
            name="Jogo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                ("ativo", models.BooleanField(default=True)),
                ("data_criacao", models.DateTimeField(auto_now_add=True)),
                ("config", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="jogos", to="app.gameconfig")),
            ],
            options={
                "verbose_name": "Jogo",
                "verbose_name_plural": "Jogos",
                "db_table": "JOGOS",
            },
        ),
        migrations.AddField(
            model_name="grupo",
            name="jogo",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name="grupos", to="app.jogo"),
        ),
        migrations.AddField(
            model_name="rodada",
            name="jogo",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name="rodadas", to="app.jogo"),
        ),
        migrations.CreateModel(
            name="Investimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rodada", models.PositiveIntegerField(default=1)),
                ("categoria", models.CharField(choices=[('marketing','Marketing'), ('maquinas','Aquisição de Máquinas'), ('rh','Recursos Humanos'), ('financeiro','Aplicações Financeiras')], max_length=20)),
                ("valor", models.DecimalField(decimal_places=2, max_digits=12)),
                ("data", models.DateTimeField(auto_now_add=True)),
                ("grupo", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="investimentos", to="app.grupo")),
            ],
            options={
                "verbose_name": "Investimento",
                "verbose_name_plural": "Investimentos",
                "db_table": "INVESTIMENTOS",
                "ordering": ["-data"],
            },
        ),
    ]
