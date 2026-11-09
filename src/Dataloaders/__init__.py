from uoishelpers.dataloaders.LoaderMapBase import LoaderMapBase
from uoishelpers.dataloaders.IDLoader import IDLoader

import src.DBDefinitions
from src.DBDefinitions import (
    BaseDBModel,
    EventModel,
    EventInvitationModel,
    ContactModel,
    ContactTypeModel,
    EmploymentModel,
    EmploymentTypeModel,
)


class LoaderMap(LoaderMapBase[BaseDBModel]):
    BaseModel = BaseDBModel

    EventModel: IDLoader[src.DBDefinitions.EventModel] = None
    EventInvitationModel: IDLoader[src.DBDefinitions.EventInvitationModel] = None
    ContactModel: IDLoader[src.DBDefinitions.ContactModel] = None
    ContactTypeModel: IDLoader[src.DBDefinitions.ContactTypeModel] = None
    EmploymentModel: IDLoader[src.DBDefinitions.EmploymentModel] = None
    EmploymentTypeModel: IDLoader[src.DBDefinitions.EmploymentTypeModel] = None

    def __init__(self, session):
        super().__init__(session)
        self.EventModel = self.get(EventModel)
        self.EventInvitationModel = self.get(EventInvitationModel)
        self.ContactModel = self.get(ContactModel)
        self.ContactTypeModel = self.get(ContactTypeModel)
        self.EmploymentModel = self.get(EmploymentModel)
        self.EmploymentTypeModel = self.get(EmploymentTypeModel)

    def get_by_name(self, name: str):
        return getattr(self, name)


def createLoadersContext(session):
    """Compatibility helper for places expecting a dict context."""
    return {'loaders': LoaderMap(session)}
