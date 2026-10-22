import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from src.DBDefinitions.BaseModel import BaseDBModel, UUIDFKey, IDType


class EmploymentModel(BaseDBModel):
    __tablename__ = "employments"

    personality_id: Mapped[Optional[IDType]] = UUIDFKey(
        index=True,
        nullable=True,
        default=None,
        comment="osoba, které se zaměstnání týká",
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="název zaměstnavatele"
    )
    position: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="pracovní pozice"
    )
    department: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="organizační část zaměstnavatele"
    )
    started: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=None, nullable=True, comment="začátek pracovního poměru"
    )
    finished: Mapped[Optional[datetime.datetime]] = mapped_column(
        default=None,
        nullable=True,
        comment="konec pracovního poměru, None = stále trvá",
    )
    description: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="popis činnosti nebo pracovní náplně"
    )
