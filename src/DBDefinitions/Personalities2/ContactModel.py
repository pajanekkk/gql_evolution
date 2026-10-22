from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from src.DBDefinitions.BaseModel import BaseDBModel, UUIDFKey, IDType


class ContactModel(BaseDBModel):
    __tablename__ = "contacts"

    personality_id: Mapped[Optional[IDType]] = UUIDFKey(
        nullable=True, index=True, default=None, comment="osoba, které se kontakt týká"
    )

    contact_type: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="typ kontaktu, např. private_email, private_phone, emergency_contact",
    )
    value: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="hodnota kontaktu"
    )
    preferred: Mapped[Optional[bool]] = mapped_column(
        default=False, nullable=True, comment="zda jde o preferovaný kontakt"
    )
