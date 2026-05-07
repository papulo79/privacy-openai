"""Transformadores de anonimización personalizados.

Cada transformador recibe el texto original y la etiqueta del span detectado,
y devuelve el texto transformado según una estrategia específica.
"""

import hashlib
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseTransformer(ABC):
    """Interfaz base para transformadores de anonimización."""

    @abstractmethod
    def transform(self, text: str, label: str) -> str:
        """Transforma un texto detectado según su etiqueta.

        Args:
            text: Texto original detectado.
            label: Etiqueta del span (ej. private_person, private_email, etc.).

        Returns:
            Texto transformado.
        """
        ...


class RedactedTransformer(BaseTransformer):
    """Transformador por defecto: reemplaza todo por <REDACTED>."""

    def transform(self, text: str, label: str) -> str:
        return "<REDACTED>"


class InitialsTransformer(BaseTransformer):
    """Transformador de iniciales.

    - Nombres: Alice Johnson -> A.J.
    - Emails: alice@email.com -> a***@e***.com
    - Teléfonos: 555-123-4567 -> 555-***-4567
    - Direcciones: 123 Main Street -> 123 M.S.
    - Fechas: 15/03/1990 -> **/**/****
    - URLs: https://example.com -> https://*****.com
    - Cuentas/secretos: ****1234
    """

    def transform(self, text: str, label: str) -> str:
        if label == "private_person":
            return self._person_initials(text)
        elif label == "private_email":
            return self._email_mask(text)
        elif label == "private_phone":
            return self._phone_mask(text)
        elif label == "private_address":
            return self._address_mask(text)
        elif label == "private_date":
            return self._date_mask(text)
        elif label == "private_url":
            return self._url_mask(text)
        elif label in ("account_number", "secret"):
            return self._account_mask(text)
        return "<REDACTED>"

    def _person_initials(self, text: str) -> str:
        """Alice Johnson -> A.J."""
        words = text.split()
        initials = [w[0].upper() + "." for w in words if w[0].isalpha()]
        return "".join(initials) if initials else "<REDACTED>"

    def _email_mask(self, text: str) -> str:
        """alice@email.com -> a***@e***.com"""
        if "@" not in text:
            return "<REDACTED>"
        local, domain = text.rsplit("@", 1)
        local_masked = local[0] + "***" if len(local) > 1 else "***"
        if "." in domain:
            domain_parts = domain.split(".")
            domain_masked = ".".join(
                [p[0] + "***" if len(p) > 1 else p for p in domain_parts[:-1]]
            ) + "." + domain_parts[-1]
        else:
            domain_masked = domain[0] + "***" if len(domain) > 1 else "***"
        return f"{local_masked}@{domain_masked}"

    def _phone_mask(self, text: str) -> str:
        """555-123-4567 -> 555-***-4567 (mantiene prefijo y sufijo)"""
        digits = re.sub(r"\D", "", text)
        if len(digits) < 4:
            return "***"
        # Mantener primeros 3 y últimos 2 dígitos
        visible_start = digits[:3]
        visible_end = digits[-2:]
        masked = "*" * (len(digits) - 5)
        return f"{visible_start}{masked}{visible_end}"

    def _address_mask(self, text: str) -> str:
        """123 Main Street -> 123 M.S."""
        words = text.split()
        result = []
        for word in words:
            if word.isdigit():
                result.append(word)  # Mantener números
            elif len(word) > 0 and word[0].isalpha():
                result.append(word[0].upper() + ".")
            else:
                result.append(word)
        return " ".join(result)

    def _date_mask(self, text: str) -> str:
        """15/03/1990 -> **/**/****"""
        # Reemplazar todos los dígitos por asteriscos
        return re.sub(r"\d", "*", text)

    def _url_mask(self, text: str) -> str:
        """https://example.com/path -> https://*****.com/****"""
        # Mantener protocolo si existe
        protocol = ""
        rest = text
        if "://" in text:
            protocol, rest = text.split("://", 1)
            protocol += "://"

        # Mask domain parts except TLD
        if "/" in rest:
            domain, path = rest.split("/", 1)
        else:
            domain, path = rest, ""

        if "." in domain:
            parts = domain.split(".")
            masked_domain = ".".join(
                ["*****" if i < len(parts) - 1 else p for i, p in enumerate(parts)]
            )
        else:
            masked_domain = "*****"

        masked_path = "/" + "****" if path else ""
        return f"{protocol}{masked_domain}{masked_path}"

    def _account_mask(self, text: str) -> str:
        """ES91 2345 6789 -> **** **** 6789"""
        digits = re.sub(r"\D", "", text)
        if len(digits) <= 4:
            return "****"
        visible = digits[-4:]
        masked_len = len(digits) - 4
        # Agrupar en bloques de 4
        masked = ""
        for i in range(0, masked_len, 4):
            chunk_size = min(4, masked_len - i)
            masked += "*" * chunk_size + " "
        return f"{masked.strip()} {visible}".strip()


class HashTransformer(BaseTransformer):
    """Transformador de hash: genera un hash corto y consistente del texto.

    Útil cuando necesitas poder correlacionar ocurrencias del mismo dato
    sin revelar el valor real.
    """

    def __init__(self, length: int = 8) -> None:
        self.length = length

    def transform(self, text: str, label: str) -> str:
        h = hashlib.sha256(text.lower().encode()).hexdigest()[:self.length]
        return f"[{label.upper()}:{h}]"


class PartialMaskTransformer(BaseTransformer):
    """Transformador de máscara parcial.

    Muestra solo una parte del dato:
    - Nombres: A***** J*******
    - Emails: a****@e*****.com
    - Teléfonos: 555-***-4567
    """

    def transform(self, text: str, label: str) -> str:
        if label == "private_person":
            return self._mask_words(text, visible_first=1)
        elif label == "private_email":
            return self._mask_email(text)
        elif label == "private_phone":
            return self._mask_phone(text)
        elif label == "private_address":
            return self._mask_address(text)
        elif label == "private_date":
            return self._mask_date(text)
        elif label == "private_url":
            return self._mask_url(text)
        elif label in ("account_number", "secret"):
            return self._mask_account(text)
        return "<REDACTED>"

    def _mask_words(self, text: str, visible_first: int = 1) -> str:
        words = text.split()
        masked = []
        for word in words:
            if len(word) <= visible_first:
                masked.append(word)
            else:
                masked.append(word[:visible_first] + "*" * (len(word) - visible_first))
        return " ".join(masked)

    def _mask_email(self, text: str) -> str:
        if "@" not in text:
            return "<REDACTED>"
        local, domain = text.rsplit("@", 1)
        local_masked = local[0] + "*" * (len(local) - 1) if len(local) > 1 else "*"
        if "." in domain:
            parts = domain.split(".")
            domain_masked = ".".join(
                [p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts[:-1]]
            ) + "." + parts[-1]
        else:
            domain_masked = domain
        return f"{local_masked}@{domain_masked}"

    def _mask_phone(self, text: str) -> str:
        digits = re.sub(r"\D", "", text)
        if len(digits) < 7:
            return "*" * len(digits)
        # Mostrar primeros 3 y últimos 2
        return digits[:3] + "*" * (len(digits) - 5) + digits[-2:]

    def _mask_address(self, text: str) -> str:
        words = text.split()
        result = []
        for word in words:
            if word.isdigit():
                result.append(word)
            elif len(word) > 2:
                result.append(word[:2] + "*" * (len(word) - 2))
            else:
                result.append(word)
        return " ".join(result)

    def _mask_date(self, text: str) -> str:
        return re.sub(r"\d", "*", text)

    def _mask_url(self, text: str) -> str:
        protocol = ""
        rest = text
        if "://" in text:
            protocol, rest = text.split("://", 1)
            protocol += "://"
        if "/" in rest:
            domain, path = rest.split("/", 1)
        else:
            domain, path = rest, ""
        if "." in domain:
            parts = domain.split(".")
            masked = ".".join([p[:2] + "*" * max(0, len(p) - 2) for p in parts])
        else:
            masked = domain[:2] + "*" * max(0, len(domain) - 2)
        return f"{protocol}{masked}/{path}" if path else f"{protocol}{masked}"

    def _mask_account(self, text: str) -> str:
        digits = re.sub(r"\D", "", text)
        if len(digits) <= 4:
            return "****"
        return "*" * (len(digits) - 4) + digits[-4:]


# Registro de transformadores disponibles
TRANSFORMERS: Dict[str, BaseTransformer] = {
    "redacted": RedactedTransformer(),
    "initials": InitialsTransformer(),
    "hash": HashTransformer(),
    "partial": PartialMaskTransformer(),
}


def get_transformer(name: str) -> BaseTransformer:
    """Devuelve un transformador por nombre.

    Args:
        name: Nombre del transformador.

    Returns:
        Instancia del transformador.

    Raises:
        ValueError: Si el transformador no existe.
    """
    if name not in TRANSFORMERS:
        available = ", ".join(TRANSFORMERS.keys())
        raise ValueError(f"Transformador '{name}' no encontrado. Disponibles: {available}")
    return TRANSFORMERS[name]


def list_transformers() -> List[str]:
    """Devuelve la lista de nombres de transformadores disponibles."""
    return list(TRANSFORMERS.keys())
