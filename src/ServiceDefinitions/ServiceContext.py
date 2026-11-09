import dataclasses
import typing

from src.Dataloaders import LoaderMap

if typing.TYPE_CHECKING:
    from src.ServiceDefinitions.Domain_Events.EventService import EventService as _EventService
    from src.ServiceDefinitions.Domain_Events.EventInvitationService import EventInvitationService as _EventInvitationService
    from src.ServiceDefinitions.Domain_Personalities2.ContactService import ContactService as _ContactService
    from src.ServiceDefinitions.Domain_Personalities2.ContactTypeService import ContactTypeService as _ContactTypeService
    from src.ServiceDefinitions.Domain_Personalities2.EmploymentService import EmploymentService as _EmploymentService
    from src.ServiceDefinitions.Domain_Personalities2.EmploymentTypeService import EmploymentTypeService as _EmploymentTypeService


@dataclasses.dataclass(frozen=True)
class ServiceRegistry:
    @property
    def EventService(self) -> type['_EventService']:
        from src.ServiceDefinitions.Domain_Events.EventService import EventService
        return EventService

    @property
    def EventInvitationService(self) -> type['_EventInvitationService']:
        from src.ServiceDefinitions.Domain_Events.EventInvitationService import EventInvitationService
        return EventInvitationService

    @property
    def ContactService(self) -> type['_ContactService']:
        from src.ServiceDefinitions.Domain_Personalities2.ContactService import ContactService
        return ContactService

    @property
    def ContactTypeService(self) -> type['_ContactTypeService']:
        from src.ServiceDefinitions.Domain_Personalities2.ContactTypeService import ContactTypeService
        return ContactTypeService

    @property
    def EmploymentService(self) -> type['_EmploymentService']:
        from src.ServiceDefinitions.Domain_Personalities2.EmploymentService import EmploymentService
        return EmploymentService

    @property
    def EmploymentTypeService(self) -> type['_EmploymentTypeService']:
        from src.ServiceDefinitions.Domain_Personalities2.EmploymentTypeService import EmploymentTypeService
        return EmploymentTypeService


SERVICES = ServiceRegistry()


@dataclasses.dataclass
class ServiceContext:
    loaders: LoaderMap
    user: typing.Any = None
    ug_client: typing.Callable[..., typing.Awaitable[typing.Any]] | None = None
    request: typing.Any = None
    session: typing.Any = None
    Services: ServiceRegistry = SERVICES

    # uoishelpers helpers commonly expect info.context to behave like a dict
    # with at least the key "loaders". Keeping these methods lets us pass a
    # typed ServiceContext directly as Strawberry context.
    def __getitem__(self, key: str) -> typing.Any:
        return getattr(self, key)

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)
