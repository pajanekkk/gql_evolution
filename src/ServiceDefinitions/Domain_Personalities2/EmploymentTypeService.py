from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import EmploymentTypeModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class EmploymentTypeService(BaseService[IDLoader[EmploymentTypeModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[EmploymentTypeModel]:
        return ctx.loaders.EmploymentTypeModel
