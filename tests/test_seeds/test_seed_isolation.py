"""
Test de regresión para A5: un seed que lanza una excepción durante el
arranque (lifespan de FastAPI) no debe impedir que la API levante.

Antes, cada seed se llamaba directamente en el lifespan; una excepción
no controlada en cualquiera de ellos (ej. el bug de enrollment_seed en
A6) abortaba el proceso de uvicorn completo.
"""
from src.main import _run_seed


def test_run_seed_swallows_exception_and_continues():
    calls = []

    def broken_seed():
        calls.append("broken")
        raise ValueError("boom")

    def next_seed():
        calls.append("next")

    # No debe propagar la excepción
    _run_seed(broken_seed)
    _run_seed(next_seed)

    assert calls == ["broken", "next"]


def test_run_seed_runs_successful_seed_normally():
    calls = []

    def ok_seed():
        calls.append("ok")

    _run_seed(ok_seed)

    assert calls == ["ok"]
