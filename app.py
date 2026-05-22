from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote_plus

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("DB_PATH", BASE_DIR / "app.db"))


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS preparo_config (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            categoria TEXT NOT NULL,
            modo_calculo TEXT NOT NULL,
            unidade_resultado TEXT NOT NULL,
            rotulo_resultado TEXT NOT NULL,
            massa_molar REAL NOT NULL,
            pureza REAL,
            densidade REAL,
            frasco_final TEXT NOT NULL,
            tipo_substancia TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS padronizacao_config (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE,
            estrategia TEXT NOT NULL,
            divisor_equivalencia REAL NOT NULL DEFAULT 1
        )
        """
    )


def insert_preparo_config(connection: sqlite3.Connection, raw: Dict[str, Any]) -> None:
    massa_molar = parse_decimal(raw.get("massa_molar"))
    pureza = parse_decimal(raw.get("pureza"))
    densidade = parse_decimal(raw.get("densidade"))

    if massa_molar is None:
        raise ValueError("O campo 'massa_molar' é obrigatório e deve ser numérico.")

    if raw.get("modo_calculo") == "liquido_concentrado":
        if pureza is None or densidade is None:
            raise ValueError("Os campos 'pureza' e 'densidade' são obrigatórios para compostos líquidos concentrados.")

    connection.execute(
        """
        INSERT INTO preparo_config (
            nome, categoria, modo_calculo, unidade_resultado, rotulo_resultado,
            massa_molar, pureza, densidade, frasco_final, tipo_substancia
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            raw["nome"],
            raw["categoria"],
            raw["modo_calculo"],
            raw["unidade_resultado"],
            raw["rotulo_resultado"],
            massa_molar,
            pureza,
            densidade,
            raw["frasco_final"],
            raw["tipo_substancia"],
        ),
    )


def insert_padronizacao_config(connection: sqlite3.Connection, raw: Dict[str, Any]) -> None:
    divisor = float(raw.get("divisor_equivalencia", 1.0))
    connection.execute(
        """
        INSERT INTO padronizacao_config (nome, estrategia, divisor_equivalencia)
        VALUES (?, ?, ?)
        """,
        (raw["nome"], raw["estrategia"], divisor),
    )


def load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_decimal(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    raw_text = str(raw).strip().replace(",", ".")
    if raw_text == "":
        return None
    return float(raw_text)


@dataclass(frozen=True)
class SolutionConfig:
    nome: str
    categoria: str
    modo_calculo: str
    unidade_resultado: str
    rotulo_resultado: str
    massa_molar: float
    pureza: float | None
    densidade: float | None
    frasco_final: str
    tipo_substancia: str

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "SolutionConfig":
        return cls(
            nome=raw["nome"],
            categoria=raw["categoria"],
            modo_calculo=raw["modo_calculo"],
            unidade_resultado=raw["unidade_resultado"],
            rotulo_resultado=raw["rotulo_resultado"],
            massa_molar=parse_decimal(raw["massa_molar"]),
            pureza=parse_decimal(raw.get("pureza")),
            densidade=parse_decimal(raw.get("densidade")),
            frasco_final=raw["frasco_final"],
            tipo_substancia=raw["tipo_substancia"],
        )


@dataclass(frozen=True)
class PadronizacaoConfig:
    nome: str
    estrategia: str
    divisor_equivalencia: float = 1.0

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "PadronizacaoConfig":
        return cls(
            nome=raw["nome"],
            estrategia=raw["estrategia"],
            divisor_equivalencia=float(raw.get("divisor_equivalencia", 1.0)),
        )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection() as connection:
        create_tables(connection)
        if connection.execute("SELECT 1 FROM preparo_config LIMIT 1").fetchone() is None:
            for item in load_json("preparo_substancias.json"):
                insert_preparo_config(connection, item)
        if connection.execute("SELECT 1 FROM padronizacao_config LIMIT 1").fetchone() is None:
            for item in load_json("padronizacao_substancias.json"):
                insert_padronizacao_config(connection, item)
        connection.commit()


def load_db_configs() -> tuple[Dict[str, "SolutionConfig"], Dict[str, "PadronizacaoConfig"]]:
    with get_db_connection() as connection:
        preparo_rows = connection.execute("SELECT * FROM preparo_config ORDER BY nome").fetchall()
        padronizacao_rows = connection.execute("SELECT * FROM padronizacao_config ORDER BY nome").fetchall()

    return (
        {
            row["nome"]: SolutionConfig.from_dict({
                "nome": row["nome"],
                "categoria": row["categoria"],
                "modo_calculo": row["modo_calculo"],
                "unidade_resultado": row["unidade_resultado"],
                "rotulo_resultado": row["rotulo_resultado"],
                "massa_molar": row["massa_molar"],
                "pureza": row["pureza"],
                "densidade": row["densidade"],
                "frasco_final": row["frasco_final"],
                "tipo_substancia": row["tipo_substancia"],
            })
            for row in preparo_rows
        },
        {
            row["nome"]: PadronizacaoConfig.from_dict({
                "nome": row["nome"],
                "estrategia": row["estrategia"],
                "divisor_equivalencia": row["divisor_equivalencia"],
            })
            for row in padronizacao_rows
        },
    )


def add_preparo_config(raw: Dict[str, Any]) -> None:
    with get_db_connection() as connection:
        create_tables(connection)
        insert_preparo_config(connection, raw)
        connection.commit()

    global PREPARO_CONFIGS, PADRONIZACAO_CONFIGS
    PREPARO_CONFIGS, PADRONIZACAO_CONFIGS = load_db_configs()


def add_padronizacao_config(raw: Dict[str, Any]) -> None:
    with get_db_connection() as connection:
        create_tables(connection)
        insert_padronizacao_config(connection, raw)
        connection.commit()

    global PREPARO_CONFIGS, PADRONIZACAO_CONFIGS
    PREPARO_CONFIGS, PADRONIZACAO_CONFIGS = load_db_configs()


init_db()
PREPARO_CONFIGS, PADRONIZACAO_CONFIGS = load_db_configs()


def fmt(value: float, ndigits: int = 4) -> str:
    text = f"{value:.{ndigits}f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def wikipedia_search_url(term: str) -> str:
    return f"https://pt.wikipedia.org/wiki/Especial:Pesquisar?search={quote_plus(term)}"


def parse_positive_float(name: str, payload: Dict[str, Any]) -> float:
    raw = str(payload.get(name, "")).strip().replace(",", ".")
    if not raw:
        raise ValueError(f"Informe um valor para '{name}'.")
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"O campo '{name}' deve ser numérico.") from exc
    if value <= 0:
        raise ValueError(f"O campo '{name}' deve ser maior que zero.")
    return value


def calcular_preparo(config: SolutionConfig, concentracao: float, volume_final: float) -> float:
    if config.modo_calculo == "liquido_concentrado":
        if not config.pureza or not config.densidade:
            raise ValueError(f"Configuração incompleta para {config.nome}.")
        return (concentracao * volume_final * config.massa_molar) / (1000 * config.pureza * config.densidade)

    if config.modo_calculo == "solido":
        return concentracao * (volume_final / 1000) * config.massa_molar

    raise ValueError(f"Modo de cálculo desconhecido: {config.modo_calculo}.")


def procedimento_preparo(config: SolutionConfig, conc: float, volume_final: float, valor: float) -> str:
    volume_txt = fmt(volume_final)
    conc_txt = fmt(conc)
    valor_txt = fmt(valor)

    if config.unidade_resultado == "mL":
        return (
            "1) Adicione uma pequena porção de água deionizada em um béquer.\n"
            "2) Coloque o béquer em banho de gelo, evitando o contato da água de refrigeração com o interior do recipiente.\n"
            f"3) Com o auxílio de uma pipeta, transfira cuidadosamente {valor_txt} mL do {config.tipo_substancia} concentrado ao béquer contendo água.\n"
            "4) Agite a solução com um bastão de vidro.\n"
            "5) Após o resfriamento, transfira a solução para um balão volumétrico.\n"
            f"6) Complete o volume até {volume_txt} mL com água deionizada.\n"
            f"7) Homogeneíze e transfira para um {config.frasco_final}.\n"
            f"8) Rotule a solução preparada ({conc_txt} mol/L)."
        )

    substancia = "do sal" if config.categoria == "sal" else "da base"
    return (
        f"1) Pese exatamente cerca de {valor_txt} g {substancia}.\n"
        f"2) Transfira uma porção de água para um béquer apropriado ao preparo de {volume_txt} mL de solução.\n"
        "3) Coloque o béquer em banho de gelo, evitando o contato da água de refrigeração com o interior do recipiente.\n"
        "4) Adicione cuidadosamente o sólido ao béquer, agitando com bastão de vidro.\n"
        "5) Quando a solução atingir temperatura ambiente, transfira para um balão volumétrico.\n"
        f"6) Complete o volume até {volume_txt} mL com água deionizada.\n"
        f"7) Homogeneíze e transfira para um {config.frasco_final}.\n"
        f"8) Rotule a solução preparada ({conc_txt} mol/L)."
    )


def standard_solution_message(volume_standard: float, c_std: float, mass_std: float, volume_erlenmeyer: float) -> str:
    return (
        f"1) Prepare {fmt(volume_standard)} mL de uma solução de padrão primário de concentração {fmt(c_std)} mol/L:\n\n"
        f"   (i) Pese exatamente cerca de {fmt(mass_std)} g de carbonato de sódio anidro;\n"
        f"   (ii) Transfira este sólido a um balão de {fmt(volume_standard)} mL;\n"
        "   (iii) Adicione água deionizada até a marca do menisco;\n"
        "   (iv) Agite para homogeneizar a solução.\n\n"
        f"2) Transfira quantitativamente {fmt(volume_erlenmeyer)} mL desta solução a um erlenmeyer.\n"
        "3) Adicione uma porção de água deionizada até obter uma quantidade apreciável de solução no interior do erlenmeyer.\n"
        "4) Adicione 2 gotas de solução aquosa de Alaranjado de Metila 0,05% p/p.\n"
        "5) Adicione a solução de ácido a ser titulada em uma bureta.\n"
        "6) Adicione o ácido, gota a gota, ao erlenmeyer, até observar a mudança da coloração de amarelo para alaranjado.\n"
        "7) Anote o volume no qual esta viragem é observada (V equivalência).\n"
        "8) Repita este procedimento até obter uma triplicata de valores de V equivalência."
    )


def direct_standard_message(mass_std: float, reagent_name: str, indicator: str, titrant_kind: str, color_change: str) -> str:
    return (
        f"1) Pese exatamente cerca de {fmt(mass_std)} g de {reagent_name}.\n"
        "2) Transfira este sólido a um erlenmeyer.\n"
        "3) Adicione uma porção de água deionizada até obter uma quantidade apreciável de solução, agitando até dissolução quase completa.\n"
        f"4) Adicione 2 gotas de {indicator}.\n"
        f"5) Adicione a solução de {titrant_kind} a ser titulada em uma bureta.\n"
        f"6) Adicione a solução, gota a gota, ao erlenmeyer, até observar {color_change}.\n"
        "7) Anote o volume no qual esta viragem é observada (V equivalência).\n"
        "8) Repita este procedimento até obter uma triplicata de valores de V equivalência."
    )


def calculate_padronizacao(option: str, concentration: float, endpoint_volume: float) -> Dict[str, Any]:
    if option not in PADRONIZACAO_CONFIGS:
        raise ValueError("Substância de padronização não reconhecida.")

    config = PADRONIZACAO_CONFIGS[option]
    result: Dict[str, Any] = {
        "substancia": option,
        "concentracao": fmt(concentration),
        "volume_viragem": fmt(endpoint_volume),
        "wikipedia_url": wikipedia_search_url(option),
        "metodo_1": None,
        "metodo_2": None,
    }

    if config.estrategia == "acido_fraco_base_secundaria":
        if 3 * endpoint_volume > 250:
            raise ValueError("Escolha volumes de viragem menores.")

        result["metodo_1"] = {
            "titulo": "Método 1",
            "status": "ok",
            "resumo": "Usa solução padrão secundária de NaOH.",
            "procedimento": (
                f"1) Prepare uma solução de hidróxido de sódio {fmt(concentration)} mol/L e padronize-a previamente.\n"
                f"2) Transfira quantitativamente {fmt(endpoint_volume)} mL da solução de ácido a um erlenmeyer.\n"
                "3) Adicione uma porção de água deionizada até obter uma quantidade apreciável de solução no interior do erlenmeyer.\n"
                "4) Adicione 2 gotas de solução etanólica de Fenolftaleína 1% p/p.\n"
                "5) Adicione a solução padrão secundário em uma bureta.\n"
                "6) Adicione a base, gota a gota, ao erlenmeyer, até observar a mudança da coloração de incolor para rosa claro.\n"
                "7) Anote o volume no qual esta viragem é observada (V equivalência).\n"
                "8) Repita este procedimento até obter uma triplicata de valores de V equivalência."
            ),
        }
        result["metodo_2"] = {
            "titulo": "Método 2",
            "status": "info",
            "resumo": "Método 1 mais indicado para padronização deste ácido.",
            "procedimento": None,
        }
        return result

    if config.estrategia == "acido_forte_carbonato":
        divisor = config.divisor_equivalencia
        c_std = concentration / divisor
        volume_erlenmeyer = (endpoint_volume * concentration / divisor) / c_std

        if 3 * endpoint_volume <= 100:
            volume_standard = 100.0
        elif 100.1 <= 3 * endpoint_volume <= 250:
            volume_standard = 250.0
        else:
            volume_standard = None

        if volume_standard is not None:
            mass_std = c_std * (volume_standard / 1000) * 105.98
            result["metodo_1"] = {
                "titulo": "Método 1",
                "status": "ok",
                "resumo": "Usa carbonato de sódio como padrão primário.",
                "procedimento": standard_solution_message(volume_standard, c_std, mass_std, volume_erlenmeyer),
            }
        else:
            result["metodo_1"] = {
                "titulo": "Método 1",
                "status": "erro",
                "resumo": "Escolha volumes de viragem menores.",
                "procedimento": None,
            }

        if endpoint_volume < 100:
            mass_std = (endpoint_volume / 1000) * (concentration / divisor) * 105.98
            result["metodo_2"] = {
                "titulo": "Método 2",
                "status": "ok",
                "resumo": "Padrão primário adicionado diretamente ao erlenmeyer.",
                "procedimento": direct_standard_message(
                    mass_std=mass_std,
                    reagent_name="carbonato de sódio anidro",
                    indicator="solução aquosa de Alaranjado de Metila 0,05% p/p",
                    titrant_kind="ácido",
                    color_change="a mudança da coloração de amarelo para alaranjado",
                ),
            }
        else:
            result["metodo_2"] = {
                "titulo": "Método 2",
                "status": "erro",
                "resumo": "Escolha volumes de viragem menores que 100 mL.",
                "procedimento": None,
            }
        return result

    if config.estrategia == "base_forte_biftalato":
        result["metodo_1"] = {
            "titulo": "Método 1",
            "status": "info",
            "resumo": "Método 2 mais indicado para padronização desta base.",
            "procedimento": None,
        }
        if endpoint_volume >= 100:
            result["metodo_2"] = {
                "titulo": "Método 2",
                "status": "erro",
                "resumo": "Escolha volumes de viragem menores que 100 mL.",
                "procedimento": None,
            }
            return result

        mass_std = (endpoint_volume / 1000) * concentration * 204.22
        result["metodo_2"] = {
            "titulo": "Método 2",
            "status": "ok",
            "resumo": "Usa biftalato de potássio como padrão primário.",
            "procedimento": direct_standard_message(
                mass_std=mass_std,
                reagent_name="biftalato de potássio",
                indicator="solução etanólica de Fenolftaleína 1% p/p",
                titrant_kind="base",
                color_change="a mudança da coloração de incolor para rósea claro",
            ),
        }
        return result

    raise ValueError("Estratégia de padronização não reconhecida.")


@app.route("/")
def index():
    return render_template(
        "index.html",
        solutions=sorted(PREPARO_CONFIGS.keys()),
        padronizacao_options=sorted(PADRONIZACAO_CONFIGS.keys()),
    )


@app.route("/api/preparo", methods=["POST"])
def api_preparo():
    try:
        payload = request.get_json(force=True)
        substancia = payload.get("substancia", "")
        concentration = parse_positive_float("concentracao", payload)
        volume = parse_positive_float("volume", payload)

        if substancia not in PREPARO_CONFIGS:
            raise ValueError("Substância não reconhecida.")

        config = PREPARO_CONFIGS[substancia]
        result_value = calcular_preparo(config, concentration, volume)
        return jsonify(
            {
                "ok": True,
                "substancia": config.nome,
                "rotulo": config.rotulo_resultado,
                "valor": fmt(result_value),
                "unidade": config.unidade_resultado,
                "procedimento": procedimento_preparo(config, concentration, volume, result_value),
                "wikipedia_url": wikipedia_search_url(config.nome),
            }
        )
    except ValueError as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 400


@app.route("/api/padronizacao", methods=["POST"])
def api_padronizacao():
    try:
        payload = request.get_json(force=True)
        substancia = payload.get("substancia", "")
        concentration = parse_positive_float("concentracao", payload)
        volume = parse_positive_float("volume_viragem", payload)
        return jsonify({"ok": True, **calculate_padronizacao(substancia, concentration, volume)})
    except ValueError as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 400


@app.route("/api/compounds", methods=["POST"])
def api_compounds():
    try:
        payload = request.get_json(force=True)
        tipo = payload.get("tipo", "").lower()

        if tipo == "preparo":
            add_preparo_config(payload)
            message = f"Composto de preparo '{payload.get('nome')}' adicionado com sucesso."
        elif tipo == "padronizacao":
            add_padronizacao_config(payload)
            message = f"Composto de padronização '{payload.get('nome')}' adicionado com sucesso."
        else:
            raise ValueError("Tipo de composto inválido. Use 'preparo' ou 'padronizacao'.")

        return jsonify({"ok": True, "mensagem": message})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "erro": "Já existe um composto com este nome."}), 400
    except ValueError as exc:
        return jsonify({"ok": False, "erro": str(exc)}), 400


@app.route("/api/configuracao")
def api_configuracao():
    return jsonify(
        {
            "preparo": [config.nome for config in PREPARO_CONFIGS.values()],
            "padronizacao": [config.nome for config in PADRONIZACAO_CONFIGS.values()],
        }
    )


if __name__ == "__main__":
    #app.run(debug=True)
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
