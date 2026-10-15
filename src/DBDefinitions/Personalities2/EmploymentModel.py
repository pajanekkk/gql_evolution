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

class EmploymentModel(BaseDBModel):
    __tablename__ = "employments"

    personality_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=True,
        default=None,
        comment="osoba, které se zaměstnání týká"
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="název zaměstnavatele"
    )
    position: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="pracovní pozice"
    )
    department: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="organizační část zaměstnavatele"
    )
    started: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=None,
        nullable=True,
        comment="začátek pracovního poměru"
    )
    finished: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=None,
        nullable=True,
        comment="konec pracovního poměru, None = stále trvá"
    )
    description: Mapped[Optional[str]] = mapped_column(
        default=None,
        nullable=True,
        comment="popis činnosti nebo pracovní náplně"
    )

    user = relationship(
        "UserModel",
        back_populates="employments",
        viewonly=True,
        uselist=False,
        init=False,
    )