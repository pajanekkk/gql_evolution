from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import ContactModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class ContactService(BaseService[IDLoader[ContactModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[ContactModel]:
        return ctx.loaders.ContactModel
