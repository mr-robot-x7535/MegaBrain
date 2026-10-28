import argparse
import hashlib
import json
import logging
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

CATEGORIAS = {
    "Imagens": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf"},
    "Planilhas": {".xls", ".xlsx", ".csv", ".ods"},
    "Apresentacoes": {".ppt", ".pptx", ".odp"},
    "Videos": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "Audios": {".mp3", ".wav", ".aac", ".flac", ".ogg"},
    "Compactados": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Executaveis": {".exe", ".msi", ".bat", ".sh", ".app"}
}

def calcular_hash(arquivo):
    sha256 = hashlib.sha256()

    with arquivo.open("rb") as entrada:
        for bloco in iter(lambda: entrada.read(1024 * 1024), b""):
            sha256.update(bloco)

    return sha256.hexdigest()

def identificar_categoria(arquivo):
    extensao = arquivo.suffix.lower()

    for categoria, extensoes in CATEGORIAS.items():
        if extensao in extensoes:
            return categoria

    return "Outros"

def destino_unico(destino):
    if not destino.exists():
        return destino

    contador = 1

    while True:
        candidato = destino.with_name(
            f"{destino.stem}_{contador}{destino.suffix}"
        )

        if not candidato.exists():
            return candidato

        contador += 1

def organizar(pasta, simular=False):
    pasta = pasta.expanduser().resolve()

    if not pasta.is_dir():
        raise ValueError(f"Pasta invalida: {pasta}")

    arquivos = [
        arquivo
        for arquivo in pasta.iterdir()
        if arquivo.is_file()
    ]

    hashes = {}
    relatorio = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "pasta": str(pasta),
        "simulacao": simular,
        "arquivos_analisados": len(arquivos),
        "organizados": [],
        "duplicados": [],
        "erros": []
    }

    for arquivo in arquivos:
        try:
            identificador = calcular_hash(arquivo)

            if identificador in hashes:
                relatorio["duplicados"].append({
                    "arquivo": arquivo.name,
                    "original": hashes[identificador]
                })
                continue

            hashes[identificador] = arquivo.name
            categoria = identificar_categoria(arquivo)
            destino = pasta / categoria / arquivo.name

            relatorio["organizados"].append({
                "arquivo": arquivo.name,
                "categoria": categoria,
                "destino": str(destino)
            })

            if not simular:
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(
                    str(arquivo),
                    str(destino_unico(destino))
                )

        except (OSError, PermissionError) as erro:
            relatorio["erros"].append({
                "arquivo": arquivo.name,
                "erro": str(erro)
            })

    relatorio["resumo_categorias"] = dict(
        Counter(
            item["categoria"]
            for item in relatorio["organizados"]
        )
    )

    caminho_relatorio = pasta / (
        f"relatorio_{datetime.now():%Y%m%d_%H%M%S}.json"
    )

    if not simular:
        caminho_relatorio.write_text(
            json.dumps(relatorio, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

    print(json.dumps(relatorio, indent=4, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(
        description="MegaBrain: automacao inteligente de arquivos"
    )

    parser.add_argument("pasta", type=Path)
    parser.add_argument(
        "--simular",
        action="store_true"
    )

    argumentos = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        organizar(argumentos.pasta, argumentos.simular)
    except (ValueError, OSError) as erro:
        logging.error("%s", erro)
        raise SystemExit(1)

if __name__ == "__main__":
    main()