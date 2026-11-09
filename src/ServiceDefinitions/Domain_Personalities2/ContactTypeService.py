from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import ContactTypeModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class ContactTypeService(BaseService[IDLoader[ContactTypeModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[ContactTypeModel]:
        return ctx.loaders.ContactTypeModel
