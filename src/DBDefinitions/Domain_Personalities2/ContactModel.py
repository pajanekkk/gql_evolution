from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.DBDefinitions.BaseModel import BaseDBModel, UUIDFKey, IDType


class ContactModel(BaseDBModel):
    __tablename__ = "contacts"

    user_id: Mapped[Optional[IDType]] = UUIDFKey(
        nullable=True, index=True, default=None, comment="uživatel, kterého se kontakt týká"
    )

    contact_type_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("contacttypes.id"),
        index=True,
        nullable=True,
        default=None,
        comment="typ kontaktu z katalogu (stromu) contacttypes, např. Soukromý e-mail",
    )
    value: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="hodnota kontaktu"
    )
    preferred: Mapped[Optional[bool]] = mapped_column(
        default=False, nullable=True, comment="zda jde o preferovaný kontakt"
    )
