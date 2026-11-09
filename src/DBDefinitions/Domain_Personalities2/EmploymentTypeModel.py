from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.DBDefinitions.BaseModel import BaseDBModel, IDType


class EmploymentTypeModel(BaseDBModel):
    __tablename__ = "employmenttypes"

    path_attribute_name = "path"
    parent_attribute_name = "parent"
    parent_id_attribute_name = "parent_id"
    children_attribute_name = "children"

    path: Mapped[Optional[str]] = mapped_column(
        index=True,
        nullable=True,
        default=None,
        comment="materializovaná cesta id od kořene, např. <root_id>/<parent_id>/<id>",
    )

    name: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="název typu zaměstnání, např. Dohoda o provedení práce"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        default=None, nullable=True, comment="anglický název typu zaměstnání"
    )

    parent_id: Mapped[Optional[IDType]] = mapped_column(
        ForeignKey("employmenttypes.id"),
        index=True,
        nullable=True,
        default=None,
        comment="nadřazený typ zaměstnání, None = kořen",
    )

    parent = relationship(
        "EmploymentTypeModel",
        viewonly=True,
        remote_side="EmploymentTypeModel.id",
        uselist=False,
    )

    children = relationship(
        "EmploymentTypeModel",
        back_populates="parent",
        uselist=True,
        init=True,
        cascade="save-update",
    )
