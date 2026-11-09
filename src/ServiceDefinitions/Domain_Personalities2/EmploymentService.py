from uoishelpers.dataloaders.IDLoader import IDLoader

from src.DBDefinitions import EmploymentModel
from src.ServiceDefinitions.BaseService import BaseService
from src.ServiceDefinitions.ServiceContext import ServiceContext


class EmploymentService(BaseService[IDLoader[EmploymentModel]]):
    @classmethod
    async def getLoader(cls, ctx: ServiceContext) -> IDLoader[EmploymentModel]:
        return ctx.loaders.EmploymentModel
