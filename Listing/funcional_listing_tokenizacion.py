def priorizar_tokens(
    cuartiles_directa: list,
    cuartiles_especial: list,
    cuartiles_diferenciacion: list
) -> pd.DataFrame:
    """
    Construye listado de tokens únicos priorizados por tier estratégico, volumen y cuartiles seleccionados.
    """
    df = tokenizar_keywords()
    if df.empty or "tier" not in df.columns:
        st.warning(
            "La tabla de keywords tokenizadas no está disponible o no tiene columna 'tier'.")
        return pd.DataFrame()

    # Filtrar por volumen > 400
    df = df[df["Search Volume"] > 400].copy()

    # Cuartiles internos
    def asignar_q(x, serie):
        try:
            return pd.qcut(serie, 4, labels=["Q1", "Q2", "Q3", "Q4"])[x.name]
        except Exception:
            return None

    df["cuartil"] = None
    for tier_objetivo in ["Oportunidad directa", "Especialización", "Diferenciación"]:
        mask = df["tier"] == tier_objetivo
        if mask.sum() > 4:
            df.loc[mask, "cuartil"] = df[mask].apply(
                lambda x: asignar_q(x, df[mask]["Search Volume"]), axis=1)

    # Mapeo de etiquetas legibles
    mapa_cuartiles = {
        "Q1": "Bottom 25%",
        "Q2": "Medio 50%",
        "Q3": "Top 50%",
        "Q4": "Top 25%"
    }

    def es_valido(row):
        tier = row["tier"]
        cuartil_legible = mapa_cuartiles.get(str(row.get("cuartil")), None)

        if tier in ["Core", "Oportunidad crítica"]:
            return True
        if tier == "Oportunidad directa" and cuartil_legible in cuartiles_directa:
            return True
        if tier == "Especialización" and cuartil_legible in cuartiles_especial:
            return True
        if tier == "Diferenciación" and cuartil_legible in cuartiles_diferenciacion:
            return True
        return False

    df_filtrada = df[df.apply(es_valido, axis=1)].copy()

    # Priorización jerárquica
    prioridad = {
        "Core": 1,
        "Oportunidad crítica": 2,
        "Oportunidad directa": 3,
        "Especialización": 4,
        "Diferenciación": 5
    }

    df_filtrada["tokens"] = df_filtrada["tokens"].apply(
        lambda x: x if isinstance(x, list) else [])
    registros = []

    for _, row in df_filtrada.iterrows():
        tier = row["tier"]
        for token in row["tokens"]:
            registros.append((token, tier))

    df_tokens = pd.DataFrame(registros, columns=["token", "tier"])

    df_tokens["prioridad"] = df_tokens["tier"].map(prioridad)
    df_tokens.sort_values("prioridad", inplace=True)

    tokens_finales = {}
    for _, row in df_tokens.iterrows():
        token = row["token"]
        tier = row["tier"]
        if token not in tokens_finales:
            tokens_finales[token] = {"frecuencia": 1, "tier_origen": tier}
        else:
            tokens_finales[token]["frecuencia"] += 1

    df_resultado = pd.DataFrame([
        {"token": k, "frecuencia": v["frecuencia"],
            "tier_origen": v["tier_origen"]}
        for k, v in tokens_finales.items()
    ])

    return df_resultado
