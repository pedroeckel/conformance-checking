# utils_xes.py
from __future__ import annotations
import io
import os
import gzip
import tempfile
from typing import Union, Optional
from pm4py.objects.log.importer.xes import importer as xes_importer

def _looks_gzip(data: bytes, name: Optional[str]) -> bool:
    # sinaliza .gz por nome OU pelo cabeçalho (1f 8b)
    if name and name.lower().endswith(".gz"):
        return True
    return len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B

def read_xes_any(src: Union[str, bytes, bytearray, io.BytesIO, "UploadedFile"]):
    """
    Lê XES de várias fontes (path, bytes, BytesIO, st.UploadedFile) e devolve EventLog PM4Py.
    Garante compatibilidade com pm4py.xes.importer.iterparse que requer caminho (str).
    """
    # 1) caminho já é string -> usar direto
    if isinstance(src, str):
        return xes_importer.apply(src)

    # 2) UploadedFile do Streamlit
    name = getattr(src, "name", None)
    if hasattr(src, "getvalue"):
        data = src.getvalue()
    elif hasattr(src, "read"):
        # BytesIO ou arquivo-like
        try:
            # UploadedFile.read() retorna bytes; BytesIO.read() idem
            data = src.read()
        finally:
            # reposiciona, caso o chamador queira reler
            try:
                src.seek(0)
            except Exception:
                pass
    elif isinstance(src, (bytes, bytearray)):
        data = bytes(src)
    elif isinstance(src, io.BytesIO):
        data = src.getvalue()
    else:
        raise TypeError(f"Tipo de origem não suportado para XES: {type(src)}")

    # 3) escrever em arquivo temporário com sufixo adequado
    gz = _looks_gzip(data, name)
    suffix = ".xes.gz" if gz else ".xes"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
        tmp.flush(); tmp.close()
        log = xes_importer.apply(tmp.name)
    finally:
        # limpar arquivo temporário
        try:
            os.unlink(tmp.name)
        except Exception:
            pass
    return log