from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_sprint4_producao"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cidade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=100)),
                ("distancia_km", models.PositiveIntegerField()),
                ("demanda", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "CIDADES",
                "verbose_name": "Cidade",
                "verbose_name_plural": "Cidades",
            },
        ),
        migrations.CreateModel(
            name="Distribuicao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantidade", models.PositiveIntegerField()),
                ("preco_unitario", models.DecimalField(max_digits=10, decimal_places=2)),
                ("custo_transporte", models.DecimalField(max_digits=10, decimal_places=2)),
                ("data_envio", models.DateTimeField(auto_now_add=True)),
                ("cidade", models.ForeignKey(on_delete=models.deletion.CASCADE, to="app.cidade")),
                ("grupo", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="envios", to="app.grupo")),
            ],
            options={
                "db_table": "DISTRIBUICOES",
                "ordering": ["-data_envio"],
                "verbose_name": "Distribuição",
                "verbose_name_plural": "Distribuições",
            },
        ),
    ]
