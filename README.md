# Site de Química

Agora as substâncias ficam em arquivos JSON dentro de `data/`.

## Origem do projeto

Este projeto é **totalmente baseado** no repositório original  
[`appCalculadoraSolucoes2019`](https://github.com/MarcoRazAndrade/appCalculadoraSolucoes2019),  
desenvolvido por **MarcoRazAndrade**.

A presente versão adapta a aplicação original para o ambiente web, reorganizando a lógica em uma arquitetura com backend em **Flask**, frontend em **HTML/CSS** e documentação para desenvolvedores com **Sphinx**.

Todo o crédito pela concepção original da calculadora pertence ao autor do repositório de origem.

> Esta adaptação deve ser utilizada em conformidade com os termos de licenciamento definidos no projeto original.

---

## Onde adicionar novas substâncias

### Preparo de soluções
Edite:

- `data/preparo_substancias.json`

Cada item tem este formato:

```json
{
  "nome": "Ácido Acético",
  "categoria": "ácido",
  "modo_calculo": "liquido_concentrado",
  "unidade_resultado": "mL",
  "rotulo_resultado": "Volume a ser pipetado",
  "massa_molar": 60.05,
  "pureza": 0.997,
  "densidade": 1.05,
  "frasco_final": "frasco de vidro",
  "tipo_substancia": "ácido"
}
```

#### Modos de cálculo aceitos

- `liquido_concentrado`
  - usa `massa_molar`, `pureza` e `densidade`
- `solido`
  - usa `massa_molar`

### Padronização
Edite:

- `data/padronizacao_substancias.json`

Exemplo:

```json
{
  "nome": "Ácido Clorídrico",
  "estrategia": "acido_forte_carbonato",
  "divisor_equivalencia": 2
}
```

#### Estratégias aceitas

- `acido_fraco_base_secundaria`
- `acido_forte_carbonato`
- `base_forte_biftalato`

## Depois de editar

Reinicie o Flask:

```bash
flask --app app run --debug --port 5001
```
