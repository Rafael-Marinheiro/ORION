from django.urls import reverse
from django.test import override_settings


def test_feedback_saves_suggestion(client, tmp_path):
    roadmap = tmp_path / "roadmap.md"
    with override_settings(ROADMAP_FILE=roadmap):
        response = client.post(reverse("feedback"), {"suggestion": "Nova ideia", "email": "a@b.com"})
    assert response.status_code == 302
    assert roadmap.read_text(encoding="utf-8").startswith("- Nova ideia")
