import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from src.DBDefinitions.BaseModel import BaseDBModel, UUIDColumn, UUIDFKey, IDType
###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#
###########################################################################################################################

class ContactModel(BaseDBModel):
    __tablename__ = "contacts"

    path_attribute_name = "path"
    parent_attribute_name = "parent"
    parent_id_attribute_name = "parent_id"
    children_attribute_name = "children"

    personality_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=True,
        default=None,
        comment="osoba, které se kontakt týká"
    )
    contact_type: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="typ kontaktu, např. private_email, private_phone, emergency_contact"
    )
    value: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="hodnota kontaktu"
    )
    preferred: Mapped[Optional[bool]] = mapped_column(
        default=False,
        nullable=True,
        comment="zda jde o preferovaný kontakt"
    )

    user = relationship(
        "UserModel",
        back_populates="contacts",
        viewonly=True,
        uselist=False,
        init=False,
    )