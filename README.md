# Site de Química

Agora as substâncias ficam em arquivos JSON dentro de `data/`.

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
