import math

from app.config import Settings
from app.rag.embeddings import FakeEmbedder, get_embedder


def cos(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))  # vectors are unit length


def test_fake_embedder_shape_norm_and_repeatable():
    e = FakeEmbedder(384)
    v1, v2 = e.embed(["hostel fee refund", "hostel fee refund"])
    assert len(v1) == 384 and v1 == v2
    assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0)


def test_shared_words_are_closer_than_unrelated_text():
    q, near, far = FakeEmbedder().embed(["hostel fee refund", "refund of the hostel fee", "lab timetable"])
    assert cos(q, near) > cos(q, far)


def test_empty_text_is_not_a_zero_vector():
    assert any(FakeEmbedder().embed([""])[0])


def test_default_provider_is_fake():
    assert get_embedder(Settings(embedding_provider="fake")).model == "fake-384"
