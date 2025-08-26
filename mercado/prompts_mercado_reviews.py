# 4. Buyer persona (ahora con nombres de autores)
def prompt_buyer_persona(texto: str, nombres_autores: list[str]) -> str:
    autores_str = ", ".join(nombres_autores[:10])
    return _call(f"""Basado en estos reviews y los nombres de usuarios, describe quién es el buyer persona (edad, tipo de usuario, intereses, emociones, perfil de compra).
Puedes inferir género, edad o contexto cultural si los nombres lo permiten.

Reviews:
{texto}

Nombres de usuarios:
{autores_str}
""")
